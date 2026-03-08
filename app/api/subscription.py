# app/api/subscription.py
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.vpn_service import vpn_service

# Создаем роутер. Эндпоинт будет доступен по адресу /sub
router = APIRouter(prefix="/sub", tags=["Subscription"])

@router.get("/")
def get_subscription(db: Session = Depends(get_db)):
    """
    Эндпоинт для приложения Happ.
    Возвращает список серверов в формате Base64.
    """
    sub_data = vpn_service.generate_subscription(db)
    
    # Приложения-клиенты ожидают получить обычный текст (text/plain), а не JSON!
    return Response(content=sub_data, media_type="text/plain")