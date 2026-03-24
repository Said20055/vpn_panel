# app/domain/schemas.py
# Schemas are kept for potential future API use.
# Currently the admin routes use the repository/service layer directly.
from pydantic import BaseModel


class ConfigBase(BaseModel):
    name: str
    raw_link: str
    is_active: bool = True


class ConfigCreate(ConfigBase):
    subscription_id: int | None = None


class ConfigUpdate(BaseModel):
    name: str
    raw_link: str
    is_active: bool


class ConfigResponse(ConfigBase):
    id: int
    subscription_id: int | None = None

    model_config = {"from_attributes": True}
