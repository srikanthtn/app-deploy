from pydantic import BaseModel, EmailStr

class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"  # Optional with default

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
