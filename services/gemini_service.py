import os
import json
import logging
import random
import re
from config import GEMINI_API_KEY

logger = logging.getLogger("gemini_service")

# Safe import for google.genai
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False
    logger.info("google.genai package not found in Python environment. Using Mock Intelligence mode.")

# Initialize Gemini SDK if API key is provided and SDK is installed
api_key = (GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")).strip()
client = None

if api_key and GENAI_AVAILABLE:
    logger.info("Initializing Gemini API with provided key.")
    try:
        client = genai.Client(api_key=api_key)
        has_gemini = True
    except Exception as e:
        logger.warning(f"Failed to configure Gemini API: {e}")
        has_gemini = False
else:
    has_gemini = False
    if not GENAI_AVAILABLE:
        logger.info("Gemini SDK not installed. Running in Mock simulation mode.")
    else:
        logger.info("No Gemini API key found. Running in Mock LLM simulation mode.")

def update_api_key(new_key: str):
    """Dynamic key configuration from frontend/settings."""
    new_key = new_key.strip() if new_key else ""
    if new_key and GENAI_AVAILABLE:
        api_key = new_key
        try:
            client = genai.Client(api_key=new_key)
            has_gemini = True
            logger.info("Gemini API key updated dynamically.")
        except Exception as e:
            logger.error(f"Error configuring Gemini with key: {e}")
            has_gemini = False
    else:
        has_gemini = False
        client = None
        logger.warning("Gemini API key cleared or SDK missing. Switched to Mock mode.")

async def generate_embedding(text: str) -> list[float]:
    """Generates a text embedding vector"""
    if not text:
        return [0.0] * 768
        
    if has_gemini and GENAI_AVAILABLE and client:
        try:
            result = client.models.embed_content(
                model="text-embedding-004",
                contents=text,
                config=types.EmbedContentConfig(task_type="retrieval_document")
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}. Returning mock vector.")
            
    random.seed(hash(text))
    return [random.uniform(-0.1, 0.1) for _ in range(768)]

FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemma-4-31b-it",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]


async def generate_chat_response(prompt: str, chat_history: list = None, system_instruction: str = None, is_general: bool = False):
    chat_history = chat_history or []
    
    if has_gemini and GENAI_AVAILABLE and client:
        try:
            config_args = {"temperature": 0.7}
            if system_instruction:
                config_args["system_instruction"] = system_instruction
                
            contents = []
            for msg in chat_history:
                contents.append({
                    "role": "user" if msg["sender"] == "user" else "model",
                    "parts": [{"text": msg["text"]}]
                })
            contents.append({"role": "user", "parts": [{"text": prompt}]})
            
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=contents,
                config=types.GenerateContentConfig(**config_args)
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini SDK Error: {e}")
            if "401" in str(e) or "403" in str(e):
                logger.warning("Gemini API key rejected. Falling back to free public AI...")
                try:
                    import urllib.request
                    import json
                    fallback_msgs = [{"role": "system", "content": system_instruction or "You are a helpful AI assistant."}]
                    for msg in chat_history:
                        fallback_msgs.append({"role": "user" if msg["sender"] == "user" else "assistant", "content": msg["text"]})
                    fallback_msgs.append({"role": "user", "content": prompt})
                    
                    req = urllib.request.Request(
                        "https://text.pollinations.ai/", 
                        data=json.dumps({"messages": fallback_msgs}).encode('utf-8'),
                        headers={
                            'Content-Type': 'application/json',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                    )
                    with urllib.request.urlopen(req, timeout=60) as res:
                        return res.read().decode('utf-8')
                except Exception as fallback_err:
                    logger.error(f"Fallback AI also failed: {fallback_err}")
                    if "pm-kisan" in prompt.lower() or "kisan" in prompt.lower():
                        return "The PM-KISAN scheme provides ₹6,000 per year in three equal installments to small and marginal farmers. Required documents: Aadhaar card, land records, and bank account details."
                    elif "pmsym" in prompt.lower() or "pension" in prompt.lower():
                        return "The PM-SYM scheme is a voluntary pension scheme for unorganized workers aged 18-40. It provides a ₹3,000 monthly pension after age 60."
                    else:
                        return f"Based on your query '{prompt}', I can assist you with information regarding various government schemes like PM-KISAN, PM-SYM, or PM Awas Yojana. Please upload a document or ask about a specific scheme!"
                        
            return f"⚠️ **Server Error**: Failed to connect to Google API. {str(e)}"
            
    prompt_lower = prompt.lower()
    
    is_hindi = any(re.search(rf"\b{word}\b", prompt_lower, re.UNICODE) for word in ["नमस्ते", "है", "क्या", "कहाँ", "योजना", "दस्तावेज"])
    is_marathi = any(re.search(rf"\b{word}\b", prompt_lower, re.UNICODE) for word in ["नमस्कार", "आहे", "कुठे", "माहिती", "कागदपत्रे"])
    
    if "pm-kisan" in prompt_lower or "pm kisan" in prompt_lower or "किसान" in prompt_lower:
        if is_hindi:
            return "पीएम-किसान (PM-KISAN) योजना के तहत सीमांत किसानों को प्रति वर्ष ₹6,000 की वित्तीय सहायता दी जाती है। यह राशि ₹2,000 की तीन किश्तों में दी जाती है। इसके लिए आधार कार्ड, बैंक खाता और भूमि रिकॉर्ड दस्तावेज़ आवश्यक हैं।"
        elif is_marathi:
            return "पीएम-किसान (PM-KISAN) योजनेअंतर्गत अल्पभूधारक शेतकऱ्यांना दरवर्षी ₹६,००० चे आर्थिक सहाय्य दिले जाते. ही रक्कम ₹२,००० च्या तीन हप्त्यांमध्ये दिली जाते. यासाठी आधार कार्ड, बँक खाते आणि जमिनीचे कागदपत्रे आवश्यक आहेत।"
        return "The PM-KISAN scheme provides ₹6,000 per year in three equal installments of ₹2,000 to small and marginal landholding farmers. Required documents: Aadhaar card, land records, bank account, and mobile number."
        
    if "pmsym" in prompt_lower or "pension" in prompt_lower or "पेंशन" in prompt_lower:
        if is_hindi:
            return "प्रधानमंत्री श्रम योगी मान-धन (PM-SYM) योजना असंगठित क्षेत्र के श्रमिकों (18-40 वर्ष) के लिए एक पेंशन योजना है। 60 वर्ष की आयु के बाद ₹3,000 मासिक पेंशन मिलती है।"
        elif is_marathi:
            return "पंतप्रधान श्रम योगी मान-धन (PM-SYM) योजना असंघटित क्षेत्रातील कामगारांसाठी (१८-४० वर्षे) पेन्शन योजना आहे. वयाच्या ६० वर्षांनंतर ₹३,००० मासिक पेन्शन मिळते."
        return "The PM-SYM scheme is a voluntary pension scheme for unorganized workers aged 18-40 with income under ₹15,000. Provides ₹3,000 monthly pension after age 60."

    if "post-matric" in prompt_lower or "post matric" in prompt_lower or "scholarship" in prompt_lower or "छात्रवृत्ति" in prompt_lower or "शिष्यवृत्ती" in prompt_lower:
        if is_hindi:
            return "पोस्ट मैट्रिक छात्रवृत्ति (Post Matric Scholarship) योजना अनुसूचित जाति (SC), अनुसूचित जनजाति (ST), और अन्य पिछड़े वर्गों (OBC) के छात्रों को उच्च शिक्षा प्राप्त करने के लिए वित्तीय सहायता प्रदान करती है। आवश्यक दस्तावेज़: आधार कार्ड, आय प्रमाण पत्र, जाति प्रमाण पत्र, मार्कशीट, फीस रसीद और बैंक पासबुक।"
        elif is_marathi:
            return "पोस्ट मॅट्रिक शिष्यवृत्ती (Post Matric Scholarship) योजना अनुसूचित जाती (SC), जमाती (ST) आणि इतर मागासवर्गीय (OBC) विद्यार्थ्यांना उच्च शिक्षणासाठी आर्थिक मदत देते. आवश्यक कागदपत्रे: आधार कार्ड, उत्पन्नाचा दाखला, जातीचा दाखला, गुणपत्रिका, फी पावती आणि बँक पासबुक."
        return "The Post Matric Scholarship Scheme provides financial assistance to students belonging to Scheduled Castes (SC), Scheduled Tribes (ST), and other backward classes (OBC) to pursue higher education. Required documents: Aadhaar Card, Income Certificate, Caste Certificate, Mark sheets, Fee Receipt, and Bank Passbook."

    is_greeting = bool(re.search(r'\b(hello|hi|hey|नमस्ते|नमस्कार)\b', prompt_lower, re.UNICODE))

    if is_general:
        if is_greeting:
            return "Hello! I am a general AI assistant. How can I help you today? (Note: API Key missing, running in Mock Mode)"
        return f"You asked: '{prompt}'. As a general AI assistant running in mock mode without an API key, I acknowledge your question! Please configure the Gemini API Key to get a real response."

    if is_greeting:
        if is_hindi:
            return "नमस्ते! मैं आपका एआई कानूनी और सरकारी योजना सहायक हूँ। मैं आपकी किस प्रकार सहायता कर सकता हूँ? आप दस्तावेज़ अपलोड कर सकते हैं या किसी भी योजना के बारे में पूछ सकते हैं।"
        elif is_marathi:
            return "नमस्कार! मी तुमचा एआय कायदेशीर आणि शासकीय योजना सहाय्यक आहे. मी तुम्हाला कशी मदत करू शकतो? तुम्ही कागदपत्रे अपलोड करू शकता किंवा योजनेबद्दल विचारू शकता."
        return "Hello! I am your AI Legal and Government Scheme Assistant. How can I help you today? You can search schemes, upload documents for RAG QA, or check messages for scams!"

    if is_hindi:
        return f"आपके प्रश्न '{prompt}' के आधार पर, यह एक सरकारी सेवा या योजना से संबंधित प्रतीत होता है। असली AI उत्तर के लिए कृपया सेटिंग्स में अपना Gemini API Key दर्ज करें।"
    elif is_marathi:
        return f"तुमच्या '{prompt}' या प्रश्नावरून, हे शासकीय योजना किंवा कायद्याशी संबंधित दिसते. खऱ्या AI उत्तरासाठी कृपया सेटिंग्जमध्ये तुमचा Gemini API Key टाका."
    return f"You asked: '{prompt}'. To get a real, ChatGPT-like AI answer for ANY topic, please enter a valid Gemini API Key in the Settings (gear icon) menu!"

async def detect_scam(text: str) -> dict:
    """Uses Gemini to detect if text/link is a scam and returns structured results."""
    system_prompt = (
        "You are an expert Cybersecurity Scam Detection and Red-Flag warning agent. "
        "Analyze the provided text, link, or message. "
        "Determine if it is a scam (phishing, fraudulent government scheme, fake agent, unofficial link, fake lottery/prizes, urgent request for sensitive details). "
        "Provide a JSON response with the exact keys: 'is_scam' (bool), 'confidence' (float 0-1), 'reason' (string), and 'safety_steps' (string)."
    )
    
    if has_gemini and GENAI_AVAILABLE and client:
        last_error = None
        for model_name in FALLBACK_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[system_prompt, f"Analyze this message: {text}"],
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                parsed = json.loads(response.text)
                return {
                    "is_scam": bool(parsed.get("is_scam", False)),
                    "confidence": float(parsed.get("confidence", 0.0)),
                    "reason": str(parsed.get("reason", "Unknown")),
                    "safety_steps": str(parsed.get("safety_steps", "Do not share personal details."))
                }
            except Exception as e:
                logger.warning(f"Scam detection model {model_name} failed: {e}")
                last_error = e
                
        logger.error(f"Gemini scam detection all models failed: {last_error}. Falling back to rules engine.")
            
    text_lower = text.lower()
    
    scam_keywords = ["lottery", "prize", "won", "crore", "lakh", "gift card", "otp", "password", 
                     "bank account", "instant approval", "guaranteed money", "fake agent", "middleman",
                     "bit.ly", "tinyurl.com", "click here", "urgently", "limited time", "free cash"]
    
    matched_words = [word for word in scam_keywords if word in text_lower]
    
    has_url = "http" in text_lower or ".com" in text_lower or ".in" in text_lower
    has_gov = ".gov.in" in text_lower or "nic.in" in text_lower
    
    is_scam = False
    confidence = 0.0
    reason = "This message seems safe, but always verify details through official channels."
    safety_steps = "Always visit official government portals ending in '.gov.in' and never share OTPs or personal credentials."
    
    if len(matched_words) >= 2 or (has_url and not has_gov and ("kisan" in text_lower or "yojana" in text_lower or "free" in text_lower)):
        is_scam = True
        confidence = round(0.7 + (len(matched_words) * 0.05 if len(matched_words) < 6 else 0.2), 2)
        reason = f"Detected suspicious keywords {matched_words} and unofficial link structures. Scammers often use unofficial domains mimicking official schemes to steal bank details or personal info."
        safety_steps = (
            "1. DO NOT click the link or share any personal/financial details.\n"
            "2. Cross-check the scheme on the official portal (ending with .gov.in).\n"
            "3. Remember that government schemes NEVER request fees or OTPs via SMS or WhatsApp."
        )
    elif "otp" in text_lower or ("bank" in text_lower and ("urgent" in text_lower or "verify" in text_lower)):
        is_scam = True
        confidence = 0.85
        reason = "Message requests urgent bank details verification or sharing an OTP. No legitimate government official will ask for sensitive data via message."
        safety_steps = "1. Never share OTPs, PINs, or account numbers with anyone.\n2. Contact your bank directly through their official helpline."
        
    return {
        "is_scam": is_scam,
        "confidence": confidence,
        "reason": reason,
        "safety_steps": safety_steps
    }
