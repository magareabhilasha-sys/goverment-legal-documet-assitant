import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
from config import MONGODB_URL, DATABASE_NAME, DEFAULT_SCHEMES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

db_client = None
db = None
MOCK_MODE = False

# In-Memory stores for Mock fallback mode
_mock_store = {
    "chats": [],
    "schemes": list(DEFAULT_SCHEMES),
    "documents": {},
    "scam_logs": [],
    "analytics": {
        "chat_requests": 0,
        "scam_checks": 0,
        "scam_warnings_triggered": 0,
        "documents_uploaded": 0
    }
}

async def init_db():
    global db_client, db, MOCK_MODE
    try:
        logger.info(f"Connecting to MongoDB at {MONGODB_URL}...")
        # Set 3 second timeout for quick fallback checks
        db_client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=3000)
        # Verify connection by running admin command
        await db_client.admin.command('ping')
        db = db_client[DATABASE_NAME]
        logger.info("Successfully connected to MongoDB!")
        MOCK_MODE = False
        
        # Initialize default schemes if collection is empty
        schemes_count = await db.schemes.count_documents({})
        if schemes_count == 0:
            logger.info("Initializing schemes collection with default records...")
            await db.schemes.insert_many(DEFAULT_SCHEMES)
            
    except OperationFailure as e:
        if e.code == 13: # Unauthorized
            logger.warning("MongoDB requires authentication but no credentials were provided. Falling back to In-Memory storage mode! (Set MONGODB_URL in .env to connect)")
        else:
            logger.warning(f"MongoDB operation failed: {e}. Falling back to In-Memory storage mode!")
        MOCK_MODE = True
        db = None
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
        logger.warning(f"MongoDB connection failed: {e}. Falling back to In-Memory storage mode!")
        MOCK_MODE = True
        db = None

async def get_db():
    if MOCK_MODE:
        return None
    return db

async def save_chat_message(session_id: str, sender: str, text: str, voice: bool = False, original_text: str = None):
    await increment_analytic("chat_requests")
    
    message = {
        "session_id": session_id,
        "sender": sender,
        "text": text,
        "voice": voice,
        "original_text": original_text,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    if MOCK_MODE or db is None:
        _mock_store["chats"].append(message)
    else:
        await db.chats.insert_one(message)
    return message

async def get_chat_history(session_id: str):
    if MOCK_MODE or db is None:
        return [m for m in _mock_store["chats"] if m["session_id"] == session_id]
    else:
        cursor = db.chats.find({"session_id": session_id}).sort("timestamp", 1)
        history = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            history.append(doc)
        return history

async def clear_chat_history(session_id: str):
    if MOCK_MODE or db is None:
        _mock_store["chats"] = [m for m in _mock_store["chats"] if m["session_id"] != session_id]
    else:
        await db.chats.delete_many({"session_id": session_id})

async def add_scheme(scheme: dict):
    if MOCK_MODE or db is None:
        _mock_store["schemes"] = [s for s in _mock_store["schemes"] if s["id"] != scheme["id"]]
        _mock_store["schemes"].append(scheme)
    else:
        await db.schemes.replace_one({"id": scheme["id"]}, scheme, upsert=True)
    return scheme

async def search_schemes(query: str = None, category: str = None):
    if MOCK_MODE or db is None:
        results = _mock_store["schemes"]
        if category and category != "All":
            results = [s for s in results if s["category"].lower() == category.lower()]
        if query:
            q = query.lower()
            results = [s for s in results if q in s["name"].lower() or q in s["description"].lower() or q in s["eligibility"].lower()]
        return results
    else:
        filter_query = {}
        if category and category != "All":
            filter_query["category"] = {"$regex": f"^{category}$", "$options": "i"}
        if query:
            filter_query["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"eligibility": {"$regex": query, "$options": "i"}}
            ]
        cursor = db.schemes.find(filter_query)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

async def save_scam_log(text: str, result: dict):
    await increment_analytic("scam_checks")
    if result.get("is_scam", False):
        await increment_analytic("scam_warnings_triggered")
        
    log_entry = {
        "text": text,
        "result": result,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    if MOCK_MODE or db is None:
        _mock_store["scam_logs"].append(log_entry)
    else:
        await db.scam_logs.insert_one(log_entry)
    return log_entry

async def increment_analytic(metric_name: str):
    if MOCK_MODE or db is None:
        if metric_name in _mock_store["analytics"]:
            _mock_store["analytics"][metric_name] += 1
    else:
        await db.analytics.update_one(
            {"metric": metric_name},
            {"$inc": {"value": 1}},
            upsert=True
        )

async def get_analytics():
    if MOCK_MODE or db is None:
        return _mock_store["analytics"]
    else:
        metrics = ["chat_requests", "scam_checks", "scam_warnings_triggered", "documents_uploaded"]
        result = {}
        for m in metrics:
            doc = await db.analytics.find_one({"metric": m})
            result[m] = doc["value"] if doc else 0
        return result
