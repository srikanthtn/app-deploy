from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from ...domain.entities.user import User
from ..dto.auth_requests import RegisterUserRequest, LoginRequest
from ..dto.auth_responses import TokenResponse, UserResponse
from ...infrastructure.security.hashing import Hasher
from ...infrastructure.security.jwt_token import create_access_token
from ...infrastructure.persistence.rds_user_repository import RDSUserRepository

class AuthUseCase:
    def __init__(self, user_repo: RDSUserRepository):
        self.user_repo = user_repo

    async def register(self, request: RegisterUserRequest) -> UserResponse:
        """Register a new user in RDS database"""
        try:
            # Check if user already exists
            existing_user = await self.user_repo.get_by_email(request.email)
            if existing_user:
                raise HTTPException(status_code=400, detail="User already registered")

            # Create new user entity
            user_id = uuid4()
            hashed_password = Hasher.get_password_hash(request.password)

            user = User(
                user_id=user_id,
                email=request.email,
                password_hash=hashed_password,
                full_name=request.full_name,
                role=request.role,
                created_at=datetime.utcnow(),
                is_active=True
            )

            # Save to database
            saved_user = await self.user_repo.save(user)

            # Return user response
            return UserResponse(
                user_id=str(saved_user.user_id),
                email=saved_user.email,
                full_name=saved_user.full_name,
                role=saved_user.role,
                is_active=saved_user.is_active
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Registration error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate user from RDS database and return token"""
        try:
            # Find user by email
            user = await self.user_repo.get_by_email(request.email)

            # Check if user exists and password is correct
            if not user or not Hasher.verify_password(request.password, user.password_hash):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Create access token
            token = create_access_token(data={"sub": str(user.user_id), "email": user.email})

            # Create user response
            user_response = UserResponse(
                user_id=str(user.user_id),
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active
            )

            # Return token response
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user=user_response
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Login error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
