import os
import secrets
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.vpn_service import vpn_service
from app.repository.vpn_repository import config_repo

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "supersecretpassword123")

templates = Jinja2Templates(directory="app/templates")


# --- AUTH DEPENDENCY ---

def get_current_user(request: Request):
    if not request.session.get("authenticated"):
        return None
    return request.session.get("username")


def require_auth(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return user


# --- AUTH ROUTES (no prefix) ---

auth_router = APIRouter(tags=["Auth"])


@auth_router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("authenticated"):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@auth_router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    ok_user = secrets.compare_digest(username, ADMIN_USERNAME)
    ok_pass = secrets.compare_digest(password, ADMIN_PASSWORD)
    if ok_user and ok_pass:
        request.session["authenticated"] = True
        request.session["username"] = username
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Неверный логин или пароль"},
        status_code=401,
    )


@auth_router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


# --- ADMIN ROUTES ---

router = APIRouter(prefix="/admin", tags=["Admin Panel"])


@router.get("/", response_class=HTMLResponse)
def get_admin_panel(request: Request, db: Session = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    from app.services.external_vpn_service import ext_vpn_service
    settings = vpn_service.get_settings(db)
    subscriptions = ext_vpn_service.get_all_subscriptions(db)
    ext_configs_map = {
        sub.id: ext_vpn_service.get_configs_by_subscription(db, sub.id)
        for sub in subscriptions
    }
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "configs": vpn_service.get_all_configs(db),
        "settings": settings,
        "subscriptions": subscriptions,
        "ext_configs_map": ext_configs_map,
    })


@router.post("/update-settings")
def update_settings(
    request: Request,
    sub_name: str = Form(...),
    sub_description: str = Form(...),
    db: Session = Depends(get_db),
):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    vpn_service.update_settings(db, sub_name, sub_description)
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/add")
def add_config(
    request: Request,
    name: str = Form(...),
    raw_link: str = Form(...),
    db: Session = Depends(get_db),
):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    vpn_service.create_config(db, name=name, raw_link=raw_link)
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/edit/{config_id}")
def edit_config(
    request: Request,
    config_id: int,
    name: str = Form(...),
    raw_link: str = Form(...),
    db: Session = Depends(get_db),
):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    cfg = config_repo.get_by_id(db, config_id)
    if cfg:
        config_repo.update(db, config_id, name=name, raw_link=raw_link, is_active=cfg.is_active)
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/toggle/{config_id}")
def toggle_config(request: Request, config_id: int, db: Session = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    config_repo.toggle_active(db, config_id)
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/delete/{config_id}")
def delete_config(request: Request, config_id: int, db: Session = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    config_repo.delete(db, config_id)
    return RedirectResponse(url="/admin", status_code=303)


# --- EXTERNAL SUBSCRIPTIONS ---

@router.post("/external-subs/fetch")
def fetch_external_sub(
    request: Request,
    url: str = Form(...),
):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    from app.services.external_vpn_service import ext_vpn_service
    configs = ext_vpn_service.fetch_and_parse(url)
    return JSONResponse({"configs": configs})


@router.post("/external-subs/save")
def save_external_sub(
    request: Request,
    db: Session = Depends(get_db),
    sub_name: str = Form(...),
    sub_url: str = Form(...),
    names: list[str] = Form(...),
    raw_links: list[str] = Form(...),
):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    from app.services.external_vpn_service import ext_vpn_service
    selected = [{"name": n, "raw_link": r} for n, r in zip(names, raw_links)]
    ext_vpn_service.save_configs(db, url=sub_url, name=sub_name, selected=selected)
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/external-subs/{sub_id}/delete")
def delete_external_sub(request: Request, sub_id: int, db: Session = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    from app.services.external_vpn_service import ext_vpn_service
    ext_vpn_service.delete_subscription(db, sub_id)
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/external-configs/{config_id}/rename")
def rename_external_config(
    request: Request,
    config_id: int,
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    config_repo.rename(db, config_id, name)
    return RedirectResponse(url="/admin", status_code=303)
