from fastapi import Request
from fastapi.responses import RedirectResponse

from app.config import settings


def is_logged_in(request: Request) -> bool:
    return bool(request.session.get("logged_in"))


def require_login(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login", status_code=303)
    return None


def check_credentials(username: str, password: str) -> bool:
    return username == settings.ADMIN_PANEL_USERNAME and password == settings.ADMIN_PANEL_PASSWORD
