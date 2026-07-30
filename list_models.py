import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY", "").strip()

try:
    from google import genai
    print(f"Initializing with API key: {api_key[:5]}...{api_key[-5:] if len(api_key)>10 else ''}")
    client = genai.Client(api_key=api_key)
    print("\nAvailable Models:")
    models = client.models.list()
    for m in models:
        # Check if generateContent is supported
        methods = getattr(m, 'supported_generation_methods', [])
        if methods and 'generateContent' in methods:
            print(f"- {m.name}")
    print("\nIf you see gemini-1.5-flash-latest, the update should work!")
except ImportError:
    print("google-genai SDK not installed.")
except Exception as e:
    print(f"Error: {e}")
