import logging
from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
import database as db
import services.gemini_service as gemini
import services.rag_service as rag

logger = logging.getLogger("chat_router")
router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    message = request.message
    language = request.language
    
    system_instruction = (
        "You are an expert AI Legal & Government Assistant, AND a highly capable general AI (like ChatGPT). "
        "You can answer questions about ANY topic, general knowledge, science, programming, etc., just like a standard AI assistant. "
        "When helping citizens with legal or government queries, use very simple language and break down jargon. "
        f"Always answer in the selected language: {language}. "
        "Be empathetic, clear, and direct. "
        "If a user asks about eligibility for a scheme, give step-by-step instructions. "
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

@router.post("/general", response_model=ChatResponse)
async def chat_general_endpoint(request: ChatRequest):
    session_id = request.session_id + "_general"
    message = request.message
    language = request.language
    
    system_instruction = (
        "You are a helpful, versatile AI assistant. "
        "Your goal is to answer any question the user has to the best of your ability, "
        "acting like a general-purpose conversational agent (like ChatGPT). "
        f"Always answer in the selected language: {language}. "
        "Be friendly, clear, and informative."
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
        system_instruction=system_instruction,
        is_general=True
    )
    
    await db.save_chat_message(
        session_id=session_id,
        sender="assistant",
        text=reply,
        voice=False
    )
    
    return ChatResponse(
        reply=reply,
        is_rag=False,
        language=language
    )

@router.get("/history/{session_id}")
async def get_history(session_id: str):
    history = await db.get_chat_history(session_id)
    return {
        "session_id": session_id,
        "history": history,
        "document_loaded": rag.has_document(session_id)
    }

@router.delete("/history/{session_id}")
async def delete_history(session_id: str):
    await db.clear_chat_history(session_id)
    rag.clear_session_documents(session_id)
    return {"status": "success", "message": f"Chat history and document vector index cleared for session: {session_id}"}
