from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db import async_session
from app.models import Category, Product
from admin.auth import require_login
from admin.templating import templates

router = APIRouter()


@router.get("/products")
async def list_products(request: Request):
    redirect = require_login(request)
    if redirect:
        return redirect

    async with async_session() as session:
        result = await session.execute(
            select(Category).options(selectinload(Category.products)).order_by(Category.sort_order)
        )
        categories = list(result.scalars())

    return templates.TemplateResponse(
        "products.html",
        {"request": request, "logged_in": True, "categories": categories, "currency": settings.CURRENCY},
    )


@router.post("/products/create")
async def create_product(
    request: Request,
    category_id: int = Form(...),
    title: str = Form(...),
    price: float = Form(0),
    amount: int | None = Form(None),
    recipient_label: str = Form(""),
    requires_recipient: bool = Form(False),
    is_variable: bool = Form(False),
    unit_price: float | None = Form(None),
    min_quantity: int = Form(1),
    image_url: str = Form(""),
):
    redirect = require_login(request)
    if redirect:
        return redirect

    if is_variable:
        price = (unit_price or 0) * (min_quantity or 1)

    async with async_session() as session:
        product = Product(
            category_id=category_id,
            title=title,
            price=price,
            image_url=image_url.strip() or None,
            amount=amount,
            recipient_label=recipient_label or "Telegram-username получателя (без @)",
            requires_recipient=requires_recipient,
            is_variable=is_variable,
            unit_price=unit_price if is_variable else None,
            min_quantity=min_quantity if is_variable else 1,
        )
        session.add(product)
        await session.commit()

    return RedirectResponse(url="/products", status_code=303)


@router.get("/products/{product_id}/edit")
async def edit_product_form(request: Request, product_id: int):
    redirect = require_login(request)
    if redirect:
        return redirect

    async with async_session() as session:
        product = await session.get(Product, product_id)

    if product is None:
        return RedirectResponse(url="/products", status_code=303)

    return templates.TemplateResponse(
        "product_form.html", {"request": request, "logged_in": True, "product": product}
    )


@router.post("/products/{product_id}/edit")
async def edit_product(
    request: Request,
    product_id: int,
    title: str = Form(...),
    price: float = Form(0),
    amount: int | None = Form(None),
    recipient_label: str = Form(""),
    requires_recipient: bool = Form(False),
    is_active: bool = Form(False),
    is_variable: bool = Form(False),
    unit_price: float | None = Form(None),
    min_quantity: int = Form(1),
    image_url: str = Form(""),
):
    redirect = require_login(request)
    if redirect:
        return redirect

    if is_variable:
        price = (unit_price or 0) * (min_quantity or 1)

    async with async_session() as session:
        product = await session.get(Product, product_id)
        if product is None:
            return RedirectResponse(url="/products", status_code=303)

        product.title = title
        product.price = price
        product.image_url = image_url.strip() or None
        product.amount = amount
        product.recipient_label = recipient_label or product.recipient_label
        product.requires_recipient = requires_recipient
        product.is_active = is_active
        product.is_variable = is_variable
        product.unit_price = unit_price if is_variable else None
        product.min_quantity = min_quantity if is_variable else 1
        await session.commit()

    return RedirectResponse(url="/products", status_code=303)


@router.post("/products/{product_id}/delete")
async def delete_product(request: Request, product_id: int):
    redirect = require_login(request)
    if redirect:
        return redirect

    async with async_session() as session:
        product = await session.get(Product, product_id)
        if product is not None:
            await session.delete(product)
            await session.commit()

    return RedirectResponse(url="/products", status_code=303)
