from fastapi import FastAPI, Form, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import json

import requests
from routes import health, groundwater, mandi, location
from services.groundwater import get_groundwater_data
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from config import settings
from routes import health
from services import GeminiConversationService
from sarvamai import SarvamAI

app = FastAPI(title="Backend API")

# In-memory session storage (use a database like Supabase/Redis for production)
user_sessions = {}

def standardize_location(text: str) -> str:
    """Uses Gemini to translate/standardize Indian location names to English."""
    # If the text is already simple ASCII/English, we might skip but calling Gemini ensures 
    # spelling matches expected formats (e.g. 'Maharashtra' instead of 'maharashtr').
    try:
        prompt = (
            f"Convert this Indian location name to its standard English spelling: '{text}'. "
            "Return ONLY the English name, nothing else."
        )
        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite", # Using a fast model for text translation
            contents=[prompt]
        )
        standardized = response.text.strip()
        print(f"🌍 Standardized '{text}' -> '{standardized}'")
        return standardized
    except Exception as e:
        print(f"Standardization error: {e}")
        return text # Fallback to original

# Language Translation Map for UI Prompts
TRANSLATIONS = {
    "English": {
        "ask_state": "Please enter your *State* (e.g., Andhra Pradesh):",
        "ask_district": "Got it: {}. Now, please enter your *District*:",
        "ask_village": "District: {}. Finally, please enter your *Village* (type 'none' if unsure):",
        "searching": "Searching data for {}, {}...",
        "not_found": "Sorry, I couldn't find data for {}, {}. Type *start* to try again."
    },
    "Hindi": {
        "ask_state": "कृपया अपना *राज्य* दर्ज करें (उदा. उत्तर प्रदेश):",
        "ask_district": "ठीक है: {}। अब, अपना *जिला* दर्ज करें:",
        "ask_village": "जिला: {}। अंत में, अपना *गांव* दर्ज करें (पता न होने पर 'none' लिखें):",
        "searching": "{}, {} के लिए डेटा खोजा जा रहा है...",
        "not_found": "क्षमा करें, मुझे {}, {} के लिए डेटा नहीं मिला। फिर से प्रयास करने के लिए *start* लिखें।"
    },
    "Marathi": {
        "ask_state": "कृपया तुमचे *राज्य* प्रविष्ट करा (उदा. महाराष्ट्र):",
        "ask_district": "समजले: {}। आता, तुमचा *जिल्हा* प्रविष्ट करा:",
        "ask_village": "जिल्हा: {}। शेवटी, तुमचे *गाव* प्रविष्ट करा (माहित नसल्यास 'none' लिहा):",
        "searching": "{}, {} साठी डेटा शोधत आहे...",
        "not_found": "क्षमस्व, मला {}, {} साठी डेटा सापडला नाही. पुन्हा प्रयत्न करण्यासाठी *start* लिहा।"
    },
    "Urdu": {
        "ask_state": "براہ کرم اپنی *ریاست* درج کریں (مثلاً اتر پردیش):",
        "ask_district": "ٹھیک ہے: {}۔ اب اپنا *ضلع* درج کریں:",
        "ask_village": "ضلع: {}۔ آخر میں، اپنا *گاؤں* درج کریں (اگر معلوم نہ ہو تو 'none' لکھیں):",
        "searching": "{}، {} کے لیے ڈیٹا تلاش کیا جا رہا ہے...",
        "not_found": "معذرت، مجھے {}، {} کے لیے ڈیٹا نہیں ملا۔ دوبارہ کوشش کرنے کے لیے *start* ٹائپ کریں۔"
    },
    "Tamil": {
        "ask_state": "உங்கள் *மாநிலத்தை* உள்ளிடவும் (எ.கா., தமிழ்நாடு):",
        "ask_district": "புரிந்தது: {}। இப்போது, உங்கள் *மாவட்டத்தை* உள்ளிடவும்:",
        "ask_village": "மாவட்டம்: {}। இறுதியாக, உங்கள் *கிராமத்தை* உள்ளிடவும் (தெரியவில்லை என்றால் 'none' என தட்டச்சு செய்யவும்):",
        "searching": "{}, {} க்கான தரவைத் தேடுகிறது...",
        "not_found": "மன்னிக்கவும், {}, {} க்கான தரவைக் கண்டறிய முடியவில்லை. மீண்டும் முயல *start* என தட்டச்சு செய்யவும்."
    }
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(groundwater.router)
app.include_router(mandi.router)
app.include_router(location.router)
twilio_client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)
gemini_service = GeminiConversationService()
sarvam_client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)

# Language Mapping for Sarvam AI
SARVAM_LANG_MAP = {
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Marathi": "mr-IN",
    "Tamil": "ta-IN",
    "Urdu": "ur-PK" # Urdu is usually ur-PK or ur-IN depending on support
}

@app.post("/webhook")
async def whatsapp_webhook(request: Request, From: str = Form(...), To: str = Form(...)):
    user_phone = From
    bot_phone = To # Dynamic Bot Phone from Request
    
    form_data = await request.form()
    user_message = form_data.get("Body", "").strip()
    user_message_lower = user_message.lower()
    
    print(f"📩 Incoming from {user_phone} to {bot_phone}: '{user_message}'")
    
    # ----------------------------------------------------------------
    # 🎙️ AUDIO PROCESSING VIA GEMINI
    # ----------------------------------------------------------------
    if "MediaUrl0" in form_data and "audio" in form_data.get("MediaContentType0", ""):
        audio_url = form_data["MediaUrl0"]

        audio_response = requests.get(audio_url, auth=(settings.ACCOUNT_SID, settings.AUTH_TOKEN))
        audio_response.raise_for_status()

        prompt = (
            "Analyze the audio file. If the user speaks in Hindi or any regional language, "
            "translate their meaning directly into the closest English equivalent or command. "
            "For example: 'Shuru karo' or 'शुरू करो' should be returned as 'start'. "
            "If they speak a number like 'four two one zero zero one', return '421001'. "
            "Return ONLY the plain English text or number, with no punctuation, no markdown, "
            "and no extra words. Do not ask follow-up questions."
        )

        audio_turn = gemini_service.run_audio_turn(
            audio_bytes=audio_response.content,
            mime_type=form_data.get("MediaContentType0", "audio/ogg"),
            filename="incoming_voice.ogg",
            prompt=prompt,
        )

        user_message = audio_turn.reply_text.strip()
        print(f"🎙️ Gemini Voice Transcript: '{user_message}'")
    
    # ----------------------------------------------------------------
    # 📲 ROUTING AND CONVERSATION LOGIC
    # ----------------------------------------------------------------
    user_message_lower = user_message.lower()
    
    # Initialize session if not exists
    if user_phone not in user_sessions:
        user_sessions[user_phone] = {"state": "START", "lang": "English"}
        
    session = user_sessions[user_phone]
    lang = session.get("lang", "English")
    t = TRANSLATIONS.get(lang, TRANSLATIONS["English"])
    
    twiml = MessagingResponse()

    # Global Reset Command
    if user_message_lower in ["hi", "hello", "start", "menu", "reset", "restart", "clear"]:
        print(f"🔄 Resetting session for {user_phone}")
        session.clear() 
        session["state"] = "AWAITING_LANGUAGE"
        session["lang"] = "English"
        
        twiml.message("Welcome to Kopiko! 🌾\nPlease select a language from the menu.\n(If the menu doesn't appear, you can type: English, Hindi, Marathi, Urdu, or Tamil)")
        
        try:
            content_sid = settings.LIST_CONTENT_SID or settings.BUTTONS_CONTENT_SID
            if content_sid:
                twilio_client.messages.create(
                    from_=bot_phone,
                    to=user_phone,
                    content_sid=content_sid
                )
                print(f"✅ Attempted Language List/Buttons via REST ({content_sid})")
        except Exception as e:
            print(f"❌ REST Content Template Error: {e}")
            
        return Response(content=str(twiml), media_type="text/xml")

    # Flexible Language Detection (can be triggered anytime if in START or AWAITING_LANG)
    if session["state"] in ["START", "AWAITING_LANGUAGE"]:
        selected_lang = None
        if "english" in user_message_lower: selected_lang = "English"
        elif "hindi" in user_message_lower or "हिंदी" in user_message: selected_lang = "Hindi"
        elif "marathi" in user_message_lower or "मराठी" in user_message: selected_lang = "Marathi"
        elif "urdu" in user_message_lower or "اردو" in user_message: selected_lang = "Urdu"
        elif "tamil" in user_message_lower or "தமிழ்" in user_message: selected_lang = "Tamil"
        
        if selected_lang:
            session["lang"] = selected_lang
            session["state"] = "AWAITING_STATE"
            t = TRANSLATIONS[selected_lang]
            twiml.message(t["ask_state"])
            print(f"✅ Language set to {selected_lang}. Moving to AWAITING_STATE.")
            return Response(content=str(twiml), media_type="text/xml")
        
        # If we were specifically waiting for language and didn't get it
        if session["state"] == "AWAITING_LANGUAGE":
            twiml.message("Please select a valid language (English, Hindi, Marathi, Urdu, Tamil) or click the menu.")
            return Response(content=str(twiml), media_type="text/xml")
    
    if session["state"] == "AWAITING_STATE":
        standardized_state = standardize_location(user_message)
        session["state_val"] = standardized_state
        session["state"] = "AWAITING_DISTRICT"
        twiml.message(t["ask_district"].format(user_message))
        return Response(content=str(twiml), media_type="text/xml")
        
    elif session["state"] == "AWAITING_DISTRICT":
        standardized_district = standardize_location(user_message)
        session["district_val"] = standardized_district
        session["state"] = "AWAITING_VILLAGE"
        twiml.message(t["ask_village"].format(user_message))
        return Response(content=str(twiml), media_type="text/xml")
        
    elif session["state"] == "AWAITING_VILLAGE":
        standardized_village = standardize_location(user_message)
        village = standardized_village
        state = session.get("state_val")
        district = session.get("district_val")
        
        # Reset state but keep language
        session["state"] = "START"
        
        place = village if village.lower() != "none" else district
        
        # Combine everything into ONE message to save Twilio credits
        try:
            res = get_groundwater_data(state, place)
            if res["statusCode"] == 200 and res["data"]:
                data = res["data"][0]
                latest_reading = data.get("latestReading") or data.get("dataValue", "N/A")
                well_depth = data.get("wellDepth", "N/A")
                station = data.get("stationName", "N/A")
                
                body = (
                    f"✅ Data for {place}, {state}:\n"
                    f"📍 Station: {station}\n"
                    f"📏 Well Depth: {well_depth}m\n"
                    f"💧 Latest Reading: {latest_reading}m\n\n"
                    "Type *start* to check another location!"
                )

                # Use Sarvam AI to translate the result to the user's selected language
                if lang != "English":
                    try:
                        target_code = SARVAM_LANG_MAP.get(lang, "hi-IN")
                        sarvam_response = sarvam_client.text.translate(
                            input=body,
                            source_language_code="en-IN",
                            target_language_code=target_code,
                            mode="formal",
                            model="mayura:v1"
                        )
                        body = sarvam_response.translated_text
                        print(f"✨ Sarvam Translated ({lang}): {body}")
                    except Exception as sarvam_err:
                        print(f"❌ Sarvam AI Error: {sarvam_err}")
            else:
                body = t["not_found"].format(place, state)
        except Exception as e:
            print(f"Error fetching data: {e}")
            body = "Oops! Something went wrong. Please try again later."
            
        twiml.message(body)
        return Response(content=str(twiml), media_type="text/xml")
        
    elif "421001" in user_message_lower:
        twiml.message("📍 Region: Kalyan Belt\n⚠️ Status: CRITICAL\n💡 Advice: Switch Paddy -> Maize.")
        return Response(content=str(twiml), media_type="text/xml")
        
    else:
        twiml.message("Hi! Type *start* to begin the location-based query.")
        return Response(content=str(twiml), media_type="text/xml")
    


