# app/domain/schemas.py
from pydantic import BaseModel

class VpnConfigBase(BaseModel):
    name: str
    config_url: str
    is_active: bool = True

class VpnConfigCreate(VpnConfigBase):
    pass

class VpnConfigUpdate(VpnConfigBase):
    pass

class VpnConfigResponse(VpnConfigBase):
    id: int

    class Config:
        from_attributes = True