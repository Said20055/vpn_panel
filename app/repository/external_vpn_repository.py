# app/repository/external_vpn_repository.py
from sqlalchemy.orm import Session
from app.domain.models import ExternalSubscription


class ExternalSubscriptionRepository:
    def create(self, db: Session, name: str, url: str) -> ExternalSubscription:
        sub = ExternalSubscription(name=name, url=url)
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    def get_all(self, db: Session) -> list[ExternalSubscription]:
        return db.query(ExternalSubscription).all()

    def get_by_id(self, db: Session, sub_id: int) -> ExternalSubscription | None:
        return db.query(ExternalSubscription).filter(ExternalSubscription.id == sub_id).first()

    def delete(self, db: Session, sub_id: int):
        sub = self.get_by_id(db, sub_id)
        if sub:
            db.delete(sub)
            db.commit()


ext_sub_repo = ExternalSubscriptionRepository()
