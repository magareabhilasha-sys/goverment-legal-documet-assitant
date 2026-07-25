import io
import math
import logging
from PyPDF2 import PdfReader
from app.services.gemini_service import generate_embedding
import app.database as db

logger = logging.getLogger("rag_service")

# Session-based Document Vector Store
# Session ID -> { "filename": str, "chunks": List[{ "text": str, "embedding": List[float] }] }
_document_store = {}

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculates cosine similarity between two 768-dim float vectors"""
    if len(v1) != len(v2) or not v1 or not v2:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

async def add_document(session_id: str, file_bytes: bytes, filename: str) -> dict:
    """Extracts text from PDF, splits into chunks, computes embeddings, and stores in session RAG index"""
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        
        full_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text += f"\n--- Page {i+1} ---\n" + text

        if not full_text.trim() if hasattr(full_text, 'trim') else not full_text.strip():
            return {"success": False, "error": "No readable text found in PDF"}

        # Chunk text into ~500 character paragraphs with overlapping context
        paragraphs = [p.strip() for p in full_text.split('\n') if p.strip()]
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            if len(current_chunk) + len(p) < 600:
                current_chunk += " " + p
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = p
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Generate embeddings for each chunk
        chunk_objects = []
        for text_chunk in chunks:
            emb = await generate_embedding(text_chunk)
            chunk_objects.append({
                "text": text_chunk,
                "embedding": emb
            })

        _document_store[session_id] = {
            "filename": filename,
            "chunks": chunk_objects
        }

        # Track analytic
        await db.increment_analytic("documents_uploaded")

        logger.info(f"Indexed {len(chunk_objects)} chunks for PDF '{filename}' in session {session_id}")
        return {
            "success": True,
            "filename": filename,
            "chunks": len(chunk_objects),
            "message": f"Successfully indexed '{filename}' into RAG context"
        }

    except Exception as e:
        logger.error(f"Error parsing PDF document: {e}")
        return {"success": False, "error": str(e)}

def has_document(session_id: str) -> bool:
    return session_id in _document_store and len(_document_store[session_id]["chunks"]) > 0

def clear_session_documents(session_id: str):
    if session_id in _document_store:
        del _document_store[session_id]

async def get_rag_context(session_id: str, query: str, top_k: int = 3) -> str:
    """Retrieves top-k most relevant text chunks matching the user query"""
    if not has_document(session_id):
        return ""

    query_emb = await generate_embedding(query)
    doc = _document_store[session_id]
    chunks = doc["chunks"]

    # Calculate similarities
    scored_chunks = []
    for c in chunks:
        sim = cosine_similarity(query_emb, c["embedding"])
        scored_chunks.append((sim, c["text"]))

    # Sort descending
    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    # Pick top k
    top_chunks = scored_chunks[:top_k]
    context_text = "\n\n".join([chunk[1] for chunk in top_chunks if chunk[0] > 0.05])

    return context_text
