# app/api/subscription.py
from urllib.parse import quote

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.vpn_service import vpn_service

router = APIRouter(prefix="/sub", tags=["Subscription"])


@router.get("/")
def get_subscription(db: Session = Depends(get_db)):
    """
    Endpoint для Happ/V2Ray/Xray клиентов.
    Возвращает Base64-список всех активных серверов с заголовками для Happ.
    """
    settings = vpn_service.get_settings(db)
    sub_data = vpn_service.generate_subscription(db)
    # HTTP headers must be latin-1; URL-encode any non-ASCII characters
    headers = {
        "profile-title": quote(settings.sub_name or "VPN", safe=" "),
        "support-url": quote(settings.sub_description or "", safe=":/?#[]@!$&'()*+,;=-._~%"),
        "profile-update-interval": "12",
        "content-type": "text/plain; charset=utf-8",
    }
    return Response(content=sub_data, media_type="text/plain", headers=headers)
