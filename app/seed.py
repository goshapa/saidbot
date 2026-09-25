from sqlalchemy import select

from app.db import async_session
from app.models import Category, PaymentCard, Product, ProductType


async def seed_if_empty() -> None:
    async with async_session() as session:
        result = await session.execute(select(Category).limit(1))
        if result.scalar_one_or_none() is not None:
            return

        stars_cat = Category(type=ProductType.STARS.value, title="Telegram Stars", sort_order=1)
        premium_cat = Category(
            type=ProductType.PREMIUM.value, title="Telegram Premium", sort_order=2
        )
        games_cat = Category(type=ProductType.GAME.value, title="Донат в игры", sort_order=3)
        session.add_all([stars_cat, premium_cat, games_cat])
        await session.flush()

        stars_products = [
            Product(
                category_id=stars_cat.id,
                title="50 Stars",
                amount=50,
                price=12000,
                recipient_label="Telegram-username получателя (без @)",
                sort_order=1,
            ),
            Product(
                category_id=stars_cat.id,
                title="100 Stars",
                amount=100,
                price=23000,
                recipient_label="Telegram-username получателя (без @)",
                sort_order=2,
            ),
            Product(
                category_id=stars_cat.id,
                title="250 Stars",
                amount=250,
                price=56000,
                recipient_label="Telegram-username получателя (без @)",
                sort_order=3,
            ),
            Product(
                category_id=stars_cat.id,
                title="500 Stars",
                amount=500,
                price=110000,
                recipient_label="Telegram-username получателя (без @)",
                sort_order=4,
            ),
            Product(
                category_id=stars_cat.id,
                title="1000 Stars",
                amount=1000,
                price=215000,
                recipient_label="Telegram-username получателя (без @)",
                sort_order=5,
            ),
        ]

        premium_products = [
            Product(
                category_id=premium_cat.id,
                title="Telegram Premium — 1 месяц",
                amount=1,
                price=65000,
                recipient_label="Telegram-username получателя (без @)",
                sort_order=1,
            ),
            Product(
                category_id=premium_cat.id,
                title="Telegram Premium — 3 месяца",
                amount=3,
                price=175000,
                recipient_label="Telegram-username получателя (без @)",
                sort_order=2,
            ),
            Product(
                category_id=premium_cat.id,
                title="Telegram Premium — 6 месяцев",
                amount=6,
                price=320000,
                recipient_label="Telegram-username получателя (без @)",
                sort_order=3,
            ),
            Product(
                category_id=premium_cat.id,
                title="Telegram Premium — 12 месяцев",
                amount=12,
                price=560000,
                recipient_label="Telegram-username получателя (без @)",
                sort_order=4,
            ),
        ]

        game_products = [
            Product(
                category_id=games_cat.id,
                title="PUBG Mobile — 60 UC",
                amount=60,
                price=18000,
                recipient_label="Player ID (UID) в игре",
                sort_order=1,
            ),
            Product(
                category_id=games_cat.id,
                title="Free Fire — 100 алмазов",
                amount=100,
                price=17000,
                recipient_label="Player ID в игре",
                sort_order=2,
            ),
            Product(
                category_id=games_cat.id,
                title="Mobile Legends — 100 алмазов",
                amount=100,
                price=19000,
                recipient_label="Game ID и Zone ID (через пробел)",
                sort_order=3,
            ),
        ]

        session.add_all(stars_products + premium_products + game_products)

        session.add(
            PaymentCard(
                bank_name="Humo",
                card_number="0000 0000 0000 0000",
                holder_name="IVAN IVANOV",
            )
        )

        await session.commit()
