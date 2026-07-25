import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

# Project Imports
from app.config import MONGODB_URL
import app.database as db
import app.services.gemini_service as gemini
import app.services.rag_service as rag

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(
    title="AI Legal & Government Assistant API",
    description="Backend service for multilingual legal analysis, scheme searching, form guidance, and scam warning checks with MongoDB integration.",
    version="1.1.0"
)

# Enable CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup DB initialization
@app.on_event("startup")
async def startup_event():
    await db.init_db()

# Request/Response Schemas
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

# Endpoints
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "database_mode": "mock_in_memory" if db.MOCK_MODE else "mongodb",
        "gemini_connected": gemini.has_gemini
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    message = request.message
    language = request.language
    
    system_instruction = (
        "You are an expert AI Legal & Government Assistant. "
        "Your goal is to help citizens, especially non-technical users, rural citizens, students, and senior citizens, "
        "understand legal documents, government policies, and applications in very simple language. "
        f"Always answer in the selected language: {language}. "
        "Be empathetic, clear, and direct. Break down legal jargon. "
        "If a user asks about eligibility, give step-by-step instructions. "
        "If you mention a website, suggest verifying it is an official '.gov.in' domain. "
        "If the user is asking about a scam or suspicious text, guide them to use our Scam Detection tool."
    )
    
    is_rag = False
    
    if rag.has_document(session_id):
        is_rag = True
        context = await rag.get_rag_context(session_id, message)
        if context:
            logger.info(f"Retrieved context size: {len(context)} for session: {session_id}")
            system_instruction += (
                "\n\nCONTEXT FROM UPLOADED DOCUMENT:\n"
                "The user has uploaded a document. Answer the user's question based ONLY on the context below. "
                "Do not assume or invent facts outside the text. If the answer is not in the text, politely state that it's not in the document.\n"
                "--------------------\n"
                f"{context}\n"
                "--------------------"
            )
            
    history = await db.get_chat_history(session_id)
    
    await db.save_chat_message(
        session_id=session_id,
        sender="user",
        text=message,
        voice=request.voice
    )
    
    reply = await gemini.generate_chat_response(
        prompt=message,
        chat_history=history,
        system_instruction=system_instruction
    )
    
    await db.save_chat_message(
        session_id=session_id,
        sender="assistant",
        text=reply,
        voice=False
    )
    
    return ChatResponse(
        reply=reply,
        is_rag=is_rag,
        language=language
    )

@app.post("/api/documents/upload")
async def upload_document(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")
        
    try:
        content = await file.read()
        result = await rag.add_document(session_id, content, file.filename)
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to parse PDF"))
        return result
    except Exception as e:
        logger.error(f"Error handling file upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history/{session_id}")
async def get_history(session_id: str):
    history = await db.get_chat_history(session_id)
    return {
        "session_id": session_id,
        "history": history,
        "document_loaded": rag.has_document(session_id)
    }

@app.delete("/api/chat/history/{session_id}")
async def delete_history(session_id: str):
    await db.clear_chat_history(session_id)
    rag.clear_session_documents(session_id)
    return {"status": "success", "message": f"Chat history and document vector index cleared for session: {session_id}"}

@app.get("/api/schemes")
async def get_schemes(query: Optional[str] = None, category: Optional[str] = None):
    results = await db.search_schemes(query=query, category=category)
    return results

@app.post("/api/schemes", status_code=201)
async def create_scheme(scheme: SchemeCreate):
    result = await db.add_scheme(scheme.dict())
    return {"status": "success", "scheme": result}

@app.post("/api/scams/check", response_model=ScamCheckResponse)
async def check_scam(request: ScamCheckRequest):
    result = await gemini.detect_scam(request.text)
    await db.save_scam_log(request.text, result)
    return ScamCheckResponse(**result)

@app.get("/api/analytics")
async def get_analytics_dashboard():
    stats = await db.get_analytics()
    return stats

@app.post("/api/settings/apikey")
async def change_api_key(payload: ApiKeyUpdate):
    gemini.update_api_key(payload.api_key)
    return {"status": "success", "gemini_connected": gemini.has_gemini}
