# app/services/vpn_service.py
import base64

from sqlalchemy.orm import Session
from app.repository.vpn_repository import vpn_repo
from app.domain.schemas import VpnConfigCreate, VpnConfigUpdate

class VpnService:
    def get_all_configs(self, db: Session):
        return vpn_repo.get_all(db)

    def get_active_configs(self, db: Session):
        return vpn_repo.get_active(db)

    def get_config(self, db: Session, config_id: int):
        return vpn_repo.get_by_id(db, config_id)

    def create_config(self, db: Session, config: VpnConfigCreate):
        # Здесь можно добавить логику проверки: начинается ли ссылка с vless://, trojan:// и т.д.
        return vpn_repo.create(db, config)

    def update_config(self, db: Session, config_id: int, config_data: VpnConfigUpdate):
        return vpn_repo.update(db, config_id, config_data)

    def delete_config(self, db: Session, config_id: int):
        return vpn_repo.delete(db, config_id)
    
    def generate_subscription(self, db: Session) -> str:
        """
        Генерирует Base64 строку со списком всех активных конфигураций
        специально для клиентов типа Happ, V2Ray, Xray.
        """
        active_configs = self.get_active_configs(db)
        
        # Собираем все ссылки (config_url) в один список
        urls = [config.config_url for config in active_configs]
        
        # Объединяем их через перенос строки
        plain_text = "\n".join(urls)
        
        # Кодируем в Base64
        encoded_bytes = base64.b64encode(plain_text.encode("utf-8"))
        return encoded_bytes.decode("utf-8")


vpn_service = VpnService()