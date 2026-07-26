import asyncio
import sys
from database import init_db, save_chat_message, get_chat_history, search_schemes, save_scam_log, get_analytics
from services.gemini_service import generate_chat_response, detect_scam

async def test_all():
    print("--- Starting Backend & MongoDB Integration Tests ---")
    
    # 1. Test database setup
    print("\n[Test 1] Initializing Database (MongoDB with in-memory fallback)...")
    await init_db()
    
    # 2. Test chat message persistence
    print("\n[Test 2] Saving mock chat message...")
    sess_id = "test-session-123"
    await save_chat_message(sess_id, "user", "Hello! Tell me about PM-Kisan.")
    await save_chat_message(sess_id, "assistant", "PM-Kisan gives ₹6000/year to farmers.")
    
    history = await get_chat_history(sess_id)
    print(f"Chat history count retrieved: {len(history)}")
    assert len(history) == 2, "Chat history saving failed"
    print("Chat history works correctly.")
    
    # 3. Test Scheme searching
    print("\n[Test 3] Searching schemes list...")
    schemes = await search_schemes(query="kisan")
    print(f"Found schemes for 'kisan': {len(schemes)}")
    for s in schemes:
        print(f" - {s['name']} ({s['category']})")
    assert len(schemes) > 0, "Default schemes not loaded"
    
    # 4. Test Scam Protection simulation/LLM
    print("\n[Test 4] Testing Scam check on message...")
    spam_msg = "Congratulations! You won ₹1 Crore in PM Kisan Lottery. Click bit.ly/fake-kisan and share OTP to claim!"
    result = await detect_scam(spam_msg)
    print(f"Text checked: {spam_msg}")
    print(f"Scam Check Result: is_scam={result['is_scam']}, confidence={result['confidence']}")
    print(f"Reason: {result['reason']}")
    assert result['is_scam'] is True, "Scam engine did not flag obvious fraud words"
    
    await save_scam_log(spam_msg, result)
    
    # 5. Get Analytics
    print("\n[Test 5] Fetching analytics...")
    stats = await get_analytics()
    print(f"Analytics stats: {stats}")
    
    print("\n--- All Backend & MongoDB Tests Passed! ---")

if __name__ == "__main__":
    asyncio.run(test_all())
