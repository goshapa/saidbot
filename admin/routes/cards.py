from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.db import async_session
from app.models import PaymentCard
from admin.auth import require_login
from admin.templating import templates

router = APIRouter()


@router.get("/cards")
async def list_cards(request: Request):
    redirect = require_login(request)
    if redirect:
        return redirect

    async with async_session() as session:
        cards = list((await session.execute(select(PaymentCard))).scalars())

    return templates.TemplateResponse("cards.html", {"request": request, "logged_in": True, "cards": cards})


@router.post("/cards/create")
async def create_card(
    request: Request,
    bank_name: str = Form(...),
    card_number: str = Form(...),
    holder_name: str = Form(...),
):
    redirect = require_login(request)
    if redirect:
        return redirect

    async with async_session() as session:
        session.add(PaymentCard(bank_name=bank_name, card_number=card_number, holder_name=holder_name))
        await session.commit()

    return RedirectResponse(url="/cards", status_code=303)


@router.post("/cards/{card_id}/toggle")
async def toggle_card(request: Request, card_id: int):
    redirect = require_login(request)
    if redirect:
        return redirect

    async with async_session() as session:
        card = await session.get(PaymentCard, card_id)
        if card is not None:
            card.is_active = not card.is_active
            await session.commit()

    return RedirectResponse(url="/cards", status_code=303)


@router.post("/cards/{card_id}/delete")
async def delete_card(request: Request, card_id: int):
    redirect = require_login(request)
    if redirect:
        return redirect

    async with async_session() as session:
        card = await session.get(PaymentCard, card_id)
        if card is not None:
            await session.delete(card)
            await session.commit()

    return RedirectResponse(url="/cards", status_code=303)
