from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class User:
    """User domain entity"""
    user_id: UUID
    email: str
    password_hash: str
    full_name: str
    role: str
    created_at: datetime
    is_active: bool = True
