from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session

from ...application.dto.auth_requests import RegisterUserRequest, LoginRequest
from ...application.dto.auth_responses import TokenResponse, UserResponse
from ...application.use_cases.auth import AuthUseCase
from ...infrastructure.persistence.rds_user_repository import RDSUserRepository
from ..dependencies import get_db_session

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

def get_auth_use_case(db: Session = Depends(get_db_session)) -> AuthUseCase:
    """Dependency injection for AuthUseCase with database"""
    user_repo = RDSUserRepository(db)
    return AuthUseCase(user_repo)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: RegisterUserRequest,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case)
):
    """Register a new user"""
    return await auth_use_case.register(request)

@router.post("/signin", response_model=TokenResponse)
async def signin(
    request: LoginRequest,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case)
):
    """Authenticate user and return token"""
    return await auth_use_case.login(request)
