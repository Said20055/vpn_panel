# app/repository/vpn_repository.py
from sqlalchemy.orm import Session
from app.domain.models import VpnConfig
from app.domain.schemas import VpnConfigCreate, VpnConfigUpdate

class VpnRepository:
    def get_all(self, db: Session):
        """Получить все конфигурации (и активные, и неактивные)"""
        return db.query(VpnConfig).all()

    def get_active(self, db: Session):
        """Получить только активные конфигурации для подписки"""
        return db.query(VpnConfig).filter(VpnConfig.is_active == True).all()

    def get_by_id(self, db: Session, config_id: int):
        """Получить конфигурацию по ID"""
        return db.query(VpnConfig).filter(VpnConfig.id == config_id).first()

    def create(self, db: Session, config: VpnConfigCreate):
        """Добавить новый конфиг"""
        # Используем model_dump() (в pydantic v2) для перевода схемы в словарь
        db_config = VpnConfig(**config.model_dump())
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config

    def update(self, db: Session, config_id: int, config_data: VpnConfigUpdate):
        """Обновить существующий конфиг"""
        db_config = self.get_by_id(db, config_id)
        if db_config:
            for key, value in config_data.model_dump().items():
                setattr(db_config, key, value)
            db.commit()
            db.refresh(db_config)
        return db_config

    def delete(self, db: Session, config_id: int):
        """Удалить конфиг"""
        db_config = self.get_by_id(db, config_id)
        if db_config:
            db.delete(db_config)
            db.commit()
        return db_config

# Создаем экземпляр репозитория для импорта в другие файлы
vpn_repo = VpnRepository()