from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime
from .database import Base

class UserModel(Base):
    """
    SQLAlchemy Model for Users table.
    
    WHY: Maps Python objects to SQL table rows.
    """
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True) # Storing UUID as string
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
