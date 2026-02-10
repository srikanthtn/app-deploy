from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from ..entities.user import User

class UserRepository(ABC):
    """
    Port for User Persistence.
    
    WHY: Abstract interface to decouple domain from database.
    """
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Save a new user or update existing one"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Find user by ID"""
        pass
