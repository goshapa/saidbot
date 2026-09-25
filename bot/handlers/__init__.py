from aiogram import Router

from . import admin, catalog, my_orders, order, start, support

router = Router()
router.include_router(start.router)
router.include_router(catalog.router)
router.include_router(order.router)
router.include_router(my_orders.router)
router.include_router(support.router)
router.include_router(admin.router)
