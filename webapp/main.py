import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db import async_session, init_db
from app.models import Category, Order, OrderStatus, Product, User
from app.seed import seed_if_empty
from bot.services.orders import get_active_card, get_or_create_user
from webapp.telegram_auth import validate_init_data
from webapp.tg_api import send_receipt_to_admins


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_if_empty()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org", "https://webk.telegram.org", "https://webz.telegram.org"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _auth(x_telegram_init_data: str = Header(default="")) -> dict:
    data = validate_init_data(x_telegram_init_data)
    if data is None:
        raise HTTPException(status_code=401, detail="Invalid Telegram init data")
    user_json = data.get("user")
    if not user_json:
        raise HTTPException(status_code=401, detail="No user in init data")
    try:
        return json.loads(user_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=401, detail="Malformed user data")


@app.get("/api/catalog")
async def get_catalog():
    async with async_session() as session:
        result = await session.execute(
            select(Category)
            .options(selectinload(Category.products))
            .where(Category.is_active.is_(True))
            .order_by(Category.sort_order)
        )
        categories = list(result.scalars())

    return [
        {
            "id": c.id,
            "type": c.type,
            "title": c.title,
            "products": [
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "amount": p.amount,
                    "price": p.price,
                    "is_variable": p.is_variable,
                    "unit_price": p.unit_price,
                    "min_quantity": p.min_quantity,
                    "requires_recipient": p.requires_recipient,
                    "recipient_label": p.recipient_label,
                }
                for p in sorted(c.products, key=lambda p: p.sort_order)
                if p.is_active
            ],
        }
        for c in categories
    ]


@app.get("/api/me")
async def get_me(x_telegram_init_data: str = Header(default="")):
    tg_user = _auth(x_telegram_init_data)
    return {"id": tg_user["id"], "username": tg_user.get("username"), "currency": settings.CURRENCY}


@app.get("/api/me/orders")
async def my_orders(x_telegram_init_data: str = Header(default="")):
    tg_user = _auth(x_telegram_init_data)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_user["id"]))
        user = result.scalar_one_or_none()

        orders = []
        if user is not None:
            result = await session.execute(
                select(Order)
                .options(selectinload(Order.product))
                .where(Order.user_id == user.id)
                .order_by(Order.created_at.desc())
                .limit(20)
            )
            orders = list(result.scalars())

    return [
        {
            "id": o.id,
            "product_title": o.product.title,
            "total_price": o.total_price,
            "status": o.status,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]


@app.post("/api/orders")
async def create_order(
    product_id: int = Form(...),
    recipient_info: str = Form(""),
    quantity: int = Form(1),
    x_telegram_init_data: str = Header(default=""),
):
    tg_user = _auth(x_telegram_init_data)

    async with async_session() as session:
        product = await session.get(Product, product_id)
        if product is None or not product.is_active:
            raise HTTPException(status_code=404, detail="Товар не найден")

        if product.requires_recipient and not recipient_info.strip():
            raise HTTPException(status_code=400, detail="Укажите получателя")

        if product.is_variable:
            if quantity < product.min_quantity:
                raise HTTPException(
                    status_code=400, detail=f"Минимальное количество — {product.min_quantity}"
                )
            total_price = product.unit_price * quantity
        else:
            quantity = 1
            total_price = product.price

        card = await get_active_card(session)
        if card is None:
            raise HTTPException(status_code=503, detail="Оплата временно недоступна")

        user = await get_or_create_user(
            session, tg_user["id"], tg_user.get("username"), tg_user.get("first_name")
        )

        order = Order(
            user_id=user.id,
            product_id=product.id,
            quantity=quantity,
            total_price=total_price,
            recipient_info=recipient_info.strip() or None,
        )
        session.add(order)
        await session.flush()
        order_id = order.id
        await session.commit()

    return {
        "order_id": order_id,
        "product_title": product.title,
        "total_price": total_price,
        "currency": settings.CURRENCY,
        "card": {
            "bank_name": card.bank_name,
            "card_number": card.card_number,
            "holder_name": card.holder_name,
        },
    }


@app.post("/api/orders/{order_id}/receipt")
async def upload_receipt(
    order_id: int,
    file: UploadFile = File(...),
    x_telegram_init_data: str = Header(default=""),
):
    tg_user = _auth(x_telegram_init_data)

    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.user), selectinload(Order.product))
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if order is None or order.user.tg_id != tg_user["id"]:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Пустой файл")

        file_id = await send_receipt_to_admins(order, content)
        order.receipt_file_id = file_id
        order.status = OrderStatus.AWAITING_REVIEW.value
        await session.commit()

    return {"status": "ok"}


@app.get("/")
async def index():
    return FileResponse(
        "webapp/static/index.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


app.mount("/", StaticFiles(directory="webapp/static"), name="static")
