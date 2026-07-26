import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database as db

# Import routers
from routers import health, chat, documents, schemes, scams, analytics, settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(
    title="AI Legal & Government Assistant API",
    description="Modular Backend service for multilingual legal analysis, scheme searching, form guidance, and scam checks.",
    version="2.0.0"
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

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(schemes.router)
app.include_router(scams.router)
app.include_router(analytics.router)
app.include_router(settings.router)
