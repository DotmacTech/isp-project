from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- Base Attribute Schemas ---

class RadCheckBase(BaseModel):
    username: str
    attribute: str
    op: str = Field("==", max_length=2)
    value: str

class RadCheckCreate(RadCheckBase):
    pass

class RadCheckResponse(RadCheckBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class RadReplyBase(BaseModel):
    username: str
    attribute: str
    op: str = Field("=", max_length=2)
    value: str

class RadReplyCreate(RadReplyBase):
    pass

class RadReplyResponse(RadReplyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- User Schemas ---

class RadiusUserCreate(BaseModel):
    username: str
    password: Optional[str] = None
    rate_limit: Optional[str] = Field(None, description="Mikrotik-Rate-Limit, e.g., '2048k/10240k'")
    framed_ip_address: Optional[str] = None

class RadiusUserResponse(BaseModel):
    username: str
    check_attributes: List[RadCheckResponse]
    reply_attributes: List[RadReplyResponse]
    model_config = ConfigDict(from_attributes=True)

# --- Group Schemas ---

class RadGroupCheckBase(BaseModel):
    groupname: str
    attribute: str
    op: str = Field("==", max_length=2)
    value: str

class RadGroupCheckCreate(RadGroupCheckBase):
    pass

class RadGroupCheckResponse(RadGroupCheckBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class RadGroupReplyBase(BaseModel):
    groupname: str
    attribute: str
    op: str = Field("=", max_length=2)
    value: str

class RadGroupReplyCreate(RadGroupReplyBase):
    pass

class RadGroupReplyResponse(RadGroupReplyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class RadiusGroupResponse(BaseModel):
    groupname: str
    check_attributes: List[RadGroupCheckResponse]
    reply_attributes: List[RadGroupReplyResponse]
    model_config = ConfigDict(from_attributes=True)

# --- Schemas for Group Creation Body (without groupname) ---

class RadGroupCheckCreateBody(BaseModel):
    attribute: str
    op: str = Field("==", max_length=2)
    value: str

class RadGroupReplyCreateBody(BaseModel):
    attribute: str
    op: str = Field("=", max_length=2)
    value: str

# --- User-Group Association Schemas ---

class RadUserGroupBase(BaseModel):
    username: str
    groupname: str
    priority: int = 1

class RadUserGroupCreate(RadUserGroupBase):
    pass

class RadUserGroupResponse(RadUserGroupBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- NAS (Network Access Server) Schemas ---

class NasBase(BaseModel):
    nasname: str
    shortname: str
    type: str = 'other'
    ports: Optional[int] = None
    server: Optional[str] = None
    community: Optional[str] = None
    description: Optional[str] = None

class NasCreate(NasBase):
    secret: str

class NasUpdate(BaseModel):
    secret: Optional[str] = None
    nasname: Optional[str] = None
    shortname: Optional[str] = None
    type: Optional[str] = None
    ports: Optional[int] = None
    server: Optional[str] = None
    community: Optional[str] = None
    description: Optional[str] = None
class NasResponse(NasBase):
    id: int
    secret: str # Exposing secret in response for clarity in this context
    model_config = ConfigDict(from_attributes=True)

# --- Accounting & Post-Auth Log Schemas (Read-Only) ---

class RadAcctResponse(BaseModel):
    radacctid: int
    acctsessionid: str
    acctuniqueid: str
    username: Optional[str] = None
    nasipaddress: str
    acctstarttime: Optional[datetime] = None
    acctstoptime: Optional[datetime] = None
    acctsessiontime: Optional[int] = None
    acctinputoctets: Optional[int] = None
    acctoutputoctets: Optional[int] = None
    acctterminatecause: Optional[str] = None
    framedipaddress: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class RadPostAuthResponse(BaseModel):
    id: int
    username: str
    pass_: str = Field(..., alias='pass')
    reply: str
    authdate: datetime
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)