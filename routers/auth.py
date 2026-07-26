from fastapi import APIRouter, HTTPException, status
from models.schemas import LoginRequest, LoginResponse, ForgotPasswordRequest, RegisterRequest, ResetPasswordRequest
import database as db
import logging
import hashlib
import secrets
import time
from services.email_service import send_reset_password_email

logger = logging.getLogger("auth_router")
router = APIRouter(prefix="/api/auth", tags=["Auth"])

# In-memory store for reset tokens for simplicity
reset_tokens_store = {} 

def get_password_hash(password: str) -> str:
    # Using built-in SHA-256 to avoid needing 'passlib' or 'bcrypt' via pip
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

@router.post("/register")
async def register(request: RegisterRequest):
    existing_user = await db.get_user(request.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = get_password_hash(request.password)
    user_dict = {
        "email": request.email,
        "password": hashed_password,
        "role": request.role
    }
    
    await db.save_user(user_dict)
    return {"message": "User registered successfully"}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    logger.info(f"Login attempt for email: {request.email}")
    
    user = await db.get_user(request.email)
    
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
        
    # Generate a simple secure token using built-in secrets to avoid needing 'PyJWT' via pip
    access_token = secrets.token_urlsafe(32)
    
    return LoginResponse(
        token=access_token,
        role=user["role"],
        message="Login successful"
    )

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    logger.info(f"Forgot password attempt for email: {request.email}")
    
    user = await db.get_user(request.email)
    if not user:
        return {"message": "If that email exists in our system, a password reset link has been sent to it."}
        
    # Generate a secure reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Store token with expiration (15 mins)
    reset_tokens_store[reset_token] = {
        "email": user["email"],
        "expires": time.time() + 900
    }
    
    # Send actual email
    email_sent = send_reset_password_email(user["email"], reset_token)
    
    if not email_sent:
        logger.error(f"Failed to dispatch email for {request.email}. Check SMTP config.")
        
    return {"message": "If that email exists in our system, a password reset link has been sent to it."}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    token_data = reset_tokens_store.get(request.token)
    
    if not token_data or time.time() > token_data["expires"]:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
            
    email = token_data["email"]
        
    user = await db.get_user(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    hashed_password = get_password_hash(request.new_password)
    await db.update_password(email, hashed_password)
    
    # Clean up token
    del reset_tokens_store[request.token]
        
    return {"message": "Password has been successfully reset. You can now log in."}
