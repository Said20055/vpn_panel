# app/domain/models.py
from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class VpnConfig(Base):
    __tablename__ = "vpn_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)        # Название (например, "🇩🇪 Germany VLESS")
    config_url = Column(String, unique=True) # Сама ссылка vless://..., vmess://...
    is_active = Column(Boolean, default=True)# Активен ли сервер

class SubscriptionSettings(Base):
    __tablename__ = "subscription_settings"
    id = Column(Integer, primary_key=True, default=1)
    sub_name = Column(String, default="Мой VPN")
    sub_description = Column(String, default="https://t.me/your_channel")