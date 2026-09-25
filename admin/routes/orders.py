from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.db import async_session
from app.models import ORDER_STATUS_LABELS, Order, OrderStatus, Product, ProductType
from app.config import settings
from admin.auth import require_login
from admin.templating import templates
from admin.tg import get_file_bytes, send_message
from bot.services.fragment import fragment_stars_link

router = APIRouter()


@router.get("/")
async def dashboard(request: Request, status: str = ""):
    redirect = require_login(request)
    if redirect:
        return redirect

    async with async_session() as session:
        query = select(Order).options(selectinload(Order.user), selectinload(Order.product)).order_by(
            Order.created_at.desc()
        )
        if status:
            query = query.where(Order.status == status)
        orders = list((await session.execute(query)).scalars())

        total = (await session.execute(select(func.count(Order.id)))).scalar_one()
        awaiting_review = (
            await session.execute(
                select(func.count(Order.id)).where(Order.status == OrderStatus.AWAITING_REVIEW.value)
            )
        ).scalar_one()
        completed = (
            await session.execute(
                select(func.count(Order.id)).where(Order.status == OrderStatus.COMPLETED.value)
            )
        ).scalar_one()
        revenue = (
            await session.execute(
                select(func.coalesce(func.sum(Order.total_price), 0)).where(
                    Order.status.in_([OrderStatus.APPROVED.value, OrderStatus.COMPLETED.value])
                )
            )
        ).scalar_one()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "logged_in": True,
            "orders": orders,
            "status_labels": ORDER_STATUS_LABELS,
            "statuses": ORDER_STATUS_LABELS,
            "current_status": status,
            "currency": settings.CURRENCY,
            "stats": {
                "total": total,
                "awaiting_review": awaiting_review,
                "completed": completed,
                "revenue": revenue,
            },
        },
    )


@router.get("/orders/{order_id}")
async def order_detail(request: Request, order_id: int):
    redirect = require_login(request)
    if redirect:
        return redirect

    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .options(
                selectinload(Order.user),
                selectinload(Order.product).selectinload(Product.category),
            )
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()

    if order is None:
        return RedirectResponse(url="/", status_code=303)

    fragment_link = None
    product = order.product
    if (
        product is not None
        and product.category is not None
        and product.category.type == ProductType.STARS.value
        and order.recipient_info
    ):
        quantity = order.quantity if product.is_variable and order.quantity else (product.amount or order.quantity)
        if quantity:
            fragment_link = {
                "url": fragment_stars_link(quantity),
                "quantity": quantity,
            }

    return templates.TemplateResponse(
        "order_detail.html",
        {
            "request": request,
            "logged_in": True,
            "order": order,
            "status_labels": ORDER_STATUS_LABELS,
            "currency": settings.CURRENCY,
            "fragment_link": fragment_link,
        },
    )


@router.get("/orders/{order_id}/receipt")
async def order_receipt(request: Request, order_id: int):
    redirect = require_login(request)
    if redirect:
        return redirect

    async with async_session() as session:
        order = await session.get(Order, order_id)

    if order is None or not order.receipt_file_id:
        return Response(status_code=404)

    file_data = await get_file_bytes(order.receipt_file_id)
    if file_data is None:
        return Response(status_code=404)

    content, content_type = file_data
    return Response(content=content, media_type=content_type)


@router.post("/orders/{order_id}/status")
async def update_order_status(request: Request, order_id: int, action: str = Form(...)):
    redirect = require_login(request)
    if redirect:
        return redirect

    status_map = {
        "approve": (OrderStatus.APPROVED.value, None),
        "reject": (OrderStatus.REJECTED.value, "Оплата не подтверждена. Свяжитесь с поддержкой."),
        "complete": (OrderStatus.COMPLETED.value, None),
    }
    if action not in status_map:
        return RedirectResponse(url=f"/orders/{order_id}", status_code=303)

    new_status, comment = status_map[action]

    async with async_session() as session:
        result = await session.execute(
            select(Order).options(selectinload(Order.user)).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if order is None:
            return RedirectResponse(url="/", status_code=303)

        order.status = new_status
        if comment:
            order.admin_comment = comment
        tg_id = order.user.tg_id
        await session.commit()

    label = ORDER_STATUS_LABELS.get(new_status, new_status)
    text = f"Статус заказа №{order_id} изменён: {label}"
    if comment:
        text += f"\nКомментарий: {comment}"
    await send_message(tg_id, text)

    return RedirectResponse(url=f"/orders/{order_id}", status_code=303)
