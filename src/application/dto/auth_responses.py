from pydantic import BaseModel, Field
from uuid import UUID
from typing import Union

class UserResponse(BaseModel):
    user_id: Union[str, UUID] = Field(..., description="User ID")
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
