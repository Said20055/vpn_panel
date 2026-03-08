# app/domain/models.py
from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class VpnConfig(Base):
    __tablename__ = "vpn_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)        # Название (например, "🇩🇪 Germany VLESS")
    config_url = Column(String, unique=True) # Сама ссылка vless://..., vmess://...
    is_active = Column(Boolean, default=True)# Активен ли сервер