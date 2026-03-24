# app/services/vpn_service.py
import base64

from sqlalchemy.orm import Session
from app.repository.vpn_repository import config_repo


class VpnService:
    def get_settings(self, db: Session):
        return config_repo.get_settings(db)

    def update_settings(self, db: Session, name: str, desc: str):
        return config_repo.update_settings(db, name, desc)

    def get_all_configs(self, db: Session):
        return config_repo.get_manual(db)

    def get_config(self, db: Session, config_id: int):
        return config_repo.get_by_id(db, config_id)

    def create_config(self, db: Session, name: str, raw_link: str):
        return config_repo.create(db, name=name, raw_link=raw_link)

    def update_config(self, db: Session, config_id: int, name: str, raw_link: str, is_active: bool):
        return config_repo.update(db, config_id, name=name, raw_link=raw_link, is_active=is_active)

    def delete_config(self, db: Session, config_id: int):
        config_repo.delete(db, config_id)

    def generate_subscription(self, db: Session) -> str:
        """Base64-encoded list of all active VPN links for Happ/V2Ray/Xray clients."""
        active = config_repo.get_active(db)
        plain_text = "\n".join(c.raw_link for c in active)
        return base64.b64encode(plain_text.encode("utf-8")).decode("utf-8")


vpn_service = VpnService()
