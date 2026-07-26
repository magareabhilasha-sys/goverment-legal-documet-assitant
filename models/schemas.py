from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    session_id: str
    message: str
    voice: Optional[bool] = False
    language: Optional[str] = "English"

class ChatResponse(BaseModel):
    reply: str
    is_rag: bool
    language: str

class SchemeCreate(BaseModel):
    id: str
    name: str
    category: str
    description: str
    eligibility: str
    benefits: str
    required_documents: List[str]

class ScamCheckRequest(BaseModel):
    text: str

class ScamCheckResponse(BaseModel):
    is_scam: bool
    confidence: float
    reason: str
    safety_steps: str

class ApiKeyUpdate(BaseModel):
    api_key: str

class LoginRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = "citizen"

class LoginResponse(BaseModel):
    token: str
    role: str
    message: str

class ForgotPasswordRequest(BaseModel):
    email: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = "citizen"

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
