from fastapi import APIRouter, HTTPException, status
from models.schemas import LoginRequest, LoginResponse
import logging

logger = logging.getLogger("auth_router")
router = APIRouter(prefix="/api/auth", tags=["Auth"])

# Mock User Database
MOCK_USERS = {
    "citizen@india.gov.in": {
        "password": "password123",
        "role": "citizen"
    },
    "lawyer@india.gov.in": {
        "password": "password123",
        "role": "lawyer"
    },
    "admin@india.gov.in": {
        "password": "password123",
        "role": "admin"
    }
}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    logger.info(f"Login attempt for email: {request.email}")
    
    user = MOCK_USERS.get(request.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
        
    if user["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
        
    # In a real app, generate a JWT token here
    token = f"mock-jwt-token-{request.email}"
    
    return LoginResponse(
        token=token,
        role=user["role"],
        message="Login successful"
    )
