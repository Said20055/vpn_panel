# app/domain/models.py
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class SubscriptionSettings(Base):
    __tablename__ = "subscription_settings"
    id = Column(Integer, primary_key=True, default=1)
    sub_name = Column(String, default="Мой VPN")
    sub_description = Column(String, default="https://t.me/your_channel")


class ExternalSubscription(Base):
    __tablename__ = "external_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    configs = relationship("Config", back_populates="subscription", cascade="all, delete-orphan")


class Config(Base):
    __tablename__ = "configs"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String, nullable=False)
    raw_link        = Column(String, nullable=False)
    is_active       = Column(Boolean, default=True)
    subscription_id = Column(Integer, ForeignKey("external_subscriptions.id"), nullable=True)
    subscription    = relationship("ExternalSubscription", back_populates="configs")
