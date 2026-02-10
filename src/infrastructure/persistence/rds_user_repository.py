from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ...domain.entities.user import User
from ...domain.ports.user_repository import UserRepository
from .models import UserModel

class RDSUserRepository(UserRepository):
    """
    Implementation of User Repository using SQLAlchemy (works with RDS).
    
    WHY: Handles persistence logic for Users.
    """
    
    def __init__(self, db: Session):
        self.db = db

    async def save(self, user: User) -> User:
        # Check if user exists
        existing_user = self.db.query(UserModel).filter(UserModel.user_id == str(user.user_id)).first()
        
        if existing_user:
            # Update existing
            existing_user.email = user.email
            existing_user.password_hash = user.password_hash
            existing_user.full_name = user.full_name
            existing_user.role = user.role
            existing_user.is_active = user.is_active
            self.db.commit()
            self.db.refresh(existing_user)
            return self._to_domain(existing_user)
        else:
            # Create new
            db_user = UserModel(
                user_id=str(user.user_id),
                email=user.email,
                password_hash=user.password_hash,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at
            )
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return self._to_domain(db_user)

    async def get_by_email(self, email: str) -> Optional[User]:
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if db_user:
            return self._to_domain(db_user)
        return None

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        db_user = self.db.query(UserModel).filter(UserModel.user_id == str(user_id)).first()
        if db_user:
            return self._to_domain(db_user)
        return None

    def _to_domain(self, model: UserModel) -> User:
        return User(
            user_id=UUID(model.user_id),
            email=model.email,
            password_hash=model.password_hash,
            full_name=model.full_name,
            role=model.role,
            is_active=model.is_active,
            created_at=model.created_at
        )
