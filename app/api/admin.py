import secrets
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.vpn_service import vpn_service
from app.domain.schemas import VpnConfigCreate, VpnConfigUpdate

# --- НАСТРОЙКА АВТОРИЗАЦИИ ---
security = HTTPBasic()

# ЗАДАЙ СВОЙ ЛОГИН И ПАРОЛЬ ЗДЕСЬ (позже можно вынести в .env файл)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "supersecretpassword123"

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """Проверяет логин и пароль"""
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- ДОБАВЛЯЕМ ЗАЩИТУ КО ВСЕМУ РОУТЕРУ ---
# Параметр dependencies=[Depends(get_current_username)] закроет все пути, начинающиеся с /admin
router = APIRouter(
    prefix="/admin", 
    tags=["Admin Panel"],
    dependencies=[Depends(get_current_username)] 
)

# Подключаем папку с HTML шаблонами
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def get_admin_panel(request: Request, db: Session = Depends(get_db)):
    """Отображает главную страницу админки"""
    configs = vpn_service.get_all_configs(db)
    # Передаем список configs в HTML шаблон
    return templates.TemplateResponse("admin.html", {"request": request, "configs": configs})

@router.post("/add")
def add_config(
    name: str = Form(...), 
    config_url: str = Form(...), 
    db: Session = Depends(get_db)
):
    """Обрабатывает форму добавления нового конфига"""
    new_config = VpnConfigCreate(name=name, config_url=config_url, is_active=True)
    vpn_service.create_config(db, new_config)
    # Возвращаемся обратно на страницу админки
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/toggle/{config_id}")
def toggle_config(config_id: int, db: Session = Depends(get_db)):
    """Включает или выключает конфиг в подписке"""
    config = vpn_service.get_config(db, config_id)
    if config:
        # Меняем статус на противоположный
        update_data = VpnConfigUpdate(
            name=config.name, 
            config_url=config.config_url, 
            is_active=not config.is_active
        )
        vpn_service.update_config(db, config_id, update_data)
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/delete/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    """Удаляет конфиг из БД"""
    vpn_service.delete_config(db, config_id)
    return RedirectResponse(url="/admin", status_code=303)