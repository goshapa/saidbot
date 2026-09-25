from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.db import init_db
from app.seed import seed_if_empty
from admin.auth import check_credentials, is_logged_in
from admin.templating import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_if_empty()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.ADMIN_PANEL_SECRET)


@app.get("/login")
async def login_form(request: Request):
    if is_logged_in(request):
        return RedirectResponse(url="/")
    return templates.TemplateResponse("login.html", {"request": request, "logged_in": False})


@app.post("/login")
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if check_credentials(username, password):
        request.session["logged_in"] = True
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "login.html", {"request": request, "logged_in": False, "error": "Неверный логин или пароль"}
    )


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")


from admin.routes import cards, orders, products  # noqa: E402

app.include_router(orders.router)
app.include_router(products.router)
app.include_router(cards.router)
