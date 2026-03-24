# app/repository/vpn_repository.py
from sqlalchemy.orm import Session
from app.domain.models import Config, SubscriptionSettings


class ConfigRepository:
    def get_all(self, db: Session) -> list[Config]:
        return db.query(Config).all()

    def get_manual(self, db: Session) -> list[Config]:
        """Configs added manually (no external subscription)."""
        return db.query(Config).filter(Config.subscription_id.is_(None)).all()

    def get_by_subscription(self, db: Session, sub_id: int) -> list[Config]:
        return db.query(Config).filter(Config.subscription_id == sub_id).all()

    def get_active(self, db: Session) -> list[Config]:
        return db.query(Config).filter(Config.is_active == True).all()

    def get_by_id(self, db: Session, config_id: int) -> Config | None:
        return db.query(Config).filter(Config.id == config_id).first()

    def create(self, db: Session, name: str, raw_link: str, subscription_id: int | None = None) -> Config:
        cfg = Config(name=name, raw_link=raw_link, subscription_id=subscription_id)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
        return cfg

    def create_many(self, db: Session, items: list[dict], subscription_id: int) -> int:
        configs = [
            Config(name=item["name"], raw_link=item["raw_link"], subscription_id=subscription_id)
            for item in items
        ]
        db.add_all(configs)
        db.commit()
        return len(configs)

    def update(self, db: Session, config_id: int, name: str, raw_link: str, is_active: bool) -> Config | None:
        cfg = self.get_by_id(db, config_id)
        if cfg:
            cfg.name = name
            cfg.raw_link = raw_link
            cfg.is_active = is_active
            db.commit()
            db.refresh(cfg)
        return cfg

    def toggle_active(self, db: Session, config_id: int) -> bool:
        cfg = self.get_by_id(db, config_id)
        if cfg:
            cfg.is_active = not cfg.is_active
            db.commit()
            return cfg.is_active
        return False

    def rename(self, db: Session, config_id: int, name: str):
        cfg = self.get_by_id(db, config_id)
        if cfg:
            cfg.name = name
            db.commit()

    def delete(self, db: Session, config_id: int):
        cfg = self.get_by_id(db, config_id)
        if cfg:
            db.delete(cfg)
            db.commit()

    def get_settings(self, db: Session) -> SubscriptionSettings:
        settings = db.query(SubscriptionSettings).first()
        if not settings:
            settings = SubscriptionSettings(id=1)
            db.add(settings)
            db.commit()
        return settings

    def update_settings(self, db: Session, name: str, desc: str) -> SubscriptionSettings:
        settings = self.get_settings(db)
        settings.sub_name = name
        settings.sub_description = desc
        db.commit()
        return settings


config_repo = ConfigRepository()
