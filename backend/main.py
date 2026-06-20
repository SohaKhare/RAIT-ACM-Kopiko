import json

import requests
from fastapi import FastAPI, Form, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sarvamai import SarvamAI
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from config import settings
from routes import groundwater, health, llm, location, mandi, weather, aggregator, mandi_predict
from services import GeminiConversationService
from services.groundwater import get_groundwater_data


def create_app() -> FastAPI:
    app = FastAPI(title="Backend API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(groundwater.router)
    app.include_router(mandi.router)
    app.include_router(mandi_predict.router)
    app.include_router(location.router)
    app.include_router(llm.router)
    app.include_router(weather.router)
    app.include_router(aggregator.router)
    return app


app = create_app()

twilio_client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)
gemini_service = GeminiConversationService()
sarvam_client = (
    SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
    if settings.SARVAM_API_KEY
    else None
)

# In-memory session storage. Replace with Redis or DB for production.
user_sessions: dict[str, dict[str, str]] = {}

TRANSLATIONS = {
    "English": {
        "ask_state": "Please enter your *State* (e.g., Andhra Pradesh):",
        "ask_district": "Got it: {}. Now, please enter your *District*:",
        "ask_village": "District: {}. Finally, please enter your *Village* (type 'none' if unsure):",
        "searching": "Searching data for {}, {}...",
        "not_found": "Sorry, I couldn't find data for {}, {}. Type *start* to try again.",
    },
    "Hindi": {
        "ask_state": "कृपया अपना *राज्य* दर्ज करें (उदा. उत्तर प्रदेश):",
        "ask_district": "ठीक है: {}। अब, अपना *जिला* दर्ज करें:",
        "ask_village": "जिला: {}। अंत में, अपना *गांव* दर्ज करें (पता न होने पर 'none' लिखें):",
        "searching": "{}, {} के लिए डेटा खोजा जा रहा है...",
        "not_found": "क्षमा करें, मुझे {}, {} के लिए डेटा नहीं मिला। फिर से प्रयास करने के लिए *start* लिखें।",
    },
    "Marathi": {
        "ask_state": "कृपया तुमचे *राज्य* प्रविष्ट करा (उदा. महाराष्ट्र):",
        "ask_district": "समजले: {}। आता, तुमचा *जिल्हा* प्रविष्ट करा:",
        "ask_village": "जिल्हा: {}। शेवटी, तुमचे *गाव* प्रविष्ट करा (माहित नसल्यास 'none' लिहा):",
        "searching": "{}, {} साठी डेटा शोधत आहे...",
        "not_found": "क्षमस्व, मला {}, {} साठी डेटा सापडला नाही. पुन्हा प्रयत्न करण्यासाठी *start* लिहा।",
    },
    "Urdu": {
        "ask_state": "براہ کرم اپنی *ریاست* درج کریں (مثلاً اتر پردیش):",
        "ask_district": "ٹھیک ہے: {}۔ اب اپنا *ضلع* درج کریں:",
        "ask_village": "ضلع: {}۔ آخر میں، اپنا *گاؤں* درج کریں (اگر معلوم نہ ہو تو 'none' لکھیں):",
        "searching": "{}، {} کے لیے ڈیٹا تلاش کیا جا رہا ہے...",
        "not_found": "معذرت، مجھے {}، {} کے لیے ڈیٹا نہیں ملا۔ دوبارہ کوشش کرنے کے لیے *start* ٹائپ کریں۔",
    },
    "Tamil": {
        "ask_state": "உங்கள் *மாநிலத்தை* உள்ளிடவும் (எ.கா., தமிழ்நாடு):",
        "ask_district": "புரிந்தது: {}। இப்போது, உங்கள் *மாவட்டத்தை* உள்ளிடவும்:",
        "ask_village": "மாவட்டம்: {}। இறுதியாக, உங்கள் *கிராமத்தை* உள்ளிடவும் (தெரியவில்லை என்றால் 'none' என தட்டச்சு செய்யவும்):",
        "searching": "{}, {} க்கான தரவைத் தேடுகிறது...",
        "not_found": "மன்னிக்கவும், {}, {} க்கான தரவைக் கண்டறிய முடியவில்லை. மீண்டும் முயல *start* என தட்டச்சு செய்யவும்.",
    },
}

SARVAM_LANG_MAP = {
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Marathi": "mr-IN",
    "Tamil": "ta-IN",
    "Urdu": "ur-PK",
}


def standardize_location(text: str) -> str:
    if not text.strip():
        return text

    try:
        completion = gemini_service.client.chat.completions.create(
            model=settings.GEMINI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict location cleaner. Convert the input Indian location name into standard English spelling. "
                        "OUTPUT ONLY THE CLEANED WORD OR PLACE NAME. Never explain, never ask questions, never write sentences, and do not include conversational text."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
        standardized = (completion.choices[0].message.content or text).strip()
        
        # Guardrail: If Gemini hallucinates a long sentence, reject it and fall back to the raw text
        if len(standardized.split()) > 3:
            print(f"⚠️ Gemini leaked conversational text, falling back to raw: {text!r}")
            return text.strip()
            
        print(f"🌍 Standardized {text!r} -> {standardized!r}")
        return standardized
    except Exception as error:
        print(f"Standardization error: {error}")
        return text


def maybe_translate_with_sarvam(body: str, language: str) -> str:
    if language == "English" or not sarvam_client:
        return body

    try:
        target_code = SARVAM_LANG_MAP.get(language, "hi-IN")
        sarvam_response = sarvam_client.text.translate(
            input=body,
            source_language_code="en-IN",
            target_language_code=target_code,
            mode="formal",
            model="mayura:v1",
        )
        translated = sarvam_response.translated_text
        print(f"✨ Sarvam translated ({language}): {translated}")
        return translated
    except Exception as error:
        print(f"❌ Sarvam AI Error: {error}")
        return body


@app.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
):
    user_phone = From
    bot_phone = To
    form_data = await request.form()
    user_message = str(form_data.get("Body", "")).strip()
    media_url = form_data.get("MediaUrl0")
    media_content_type = str(form_data.get("MediaContentType0", ""))

    print("\n--- Incoming WhatsApp Webhook ---")
    print(f"From: {user_phone}")
    print(f"To bot number: {bot_phone}")
    print(f"Body: {user_message!r}")
    print(f"Has media: {'MediaUrl0' in form_data}")
    print(f"Media content type: {media_content_type or 'None'}")
    if media_url:
        print(f"Media URL present: {media_url}")

    if "MediaUrl0" in form_data and "audio" in media_content_type:
        print("Audio media detected. Downloading audio from Twilio...")
        if isinstance(media_url, str) and media_url.startswith("http"):
            print("Downloading remote Twilio audio bytes dynamically...")
            audio_response = requests.get(
                media_url,
                auth=(settings.ACCOUNT_SID, settings.AUTH_TOKEN),
            )
            audio_response = requests.get(
                str(media_url),
                auth=(settings.ACCOUNT_SID, settings.AUTH_TOKEN),
            )
            audio_response.raise_for_status()
            audio_payload = audio_response.content
            print(f"Audio download complete. Bytes received: {len(audio_payload)}")
        else:
            audio_payload = media_url

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
            mime_type=media_content_type or "audio/ogg",
            filename="incoming_voice.ogg",
            prompt=prompt,
        )
        user_message = audio_turn.reply_text.strip()
        print(f"🎙️ Gemini Voice Transcript: {user_message!r}")
    elif "MediaUrl0" in form_data:
        print("Media was attached, but it was not recognized as audio. Skipping transcription.")
    else:
        print("No media attached. Processing as text-only message.")

    user_message_lower = user_message.lower()
    print(f"Normalized user message: {user_message_lower!r}")

    if user_phone not in user_sessions:
        user_sessions[user_phone] = {"state": "START", "lang": "English"}

    session = user_sessions[user_phone]
    language = session.get("lang", "English")
    translations = TRANSLATIONS.get(language, TRANSLATIONS["English"])
    twiml = MessagingResponse()

    if user_message_lower in ["hi", "hello", "start", "menu", "reset", "restart", "clear"]:
        print(f"🔄 Resetting session for {user_phone}")
        session.clear()
        session["state"] = "AWAITING_LANGUAGE"
        session["lang"] = "English"

        twiml.message(
            "Welcome to Bhoomi! 🌾\nPlease select a language from the menu.\n"
            "(If the menu doesn't appear, you can type: English, Hindi, Marathi, Urdu, or Tamil)"
        )

        try:
            content_sid = settings.LIST_CONTENT_SID
            if content_sid:
                twilio_client.messages.create(
                    from_=bot_phone,
                    to=user_phone,
                    content_sid=content_sid,
                )
                print(f"✅ Attempted language list via REST ({content_sid})")
        except Exception as error:
            print(f"❌ REST Content Template Error: {error}")

        return Response(content=str(twiml), media_type="text/xml")

    if session["state"] in ["START", "AWAITING_LANGUAGE"]:
        selected_language = None
        if "english" in user_message_lower:
            selected_language = "English"
        elif "hindi" in user_message_lower or "हिंदी" in user_message:
            selected_language = "Hindi"
        elif "marathi" in user_message_lower or "मराठी" in user_message:
            selected_language = "Marathi"
        elif "urdu" in user_message_lower or "اردو" in user_message:
            selected_language = "Urdu"
        elif "tamil" in user_message_lower or "தமிழ்" in user_message:
            selected_language = "Tamil"

        if selected_language:
            session["lang"] = selected_language
            session["state"] = "AWAITING_STATE"
            translations = TRANSLATIONS[selected_language]
            twiml.message(translations["ask_state"])
            print(f"✅ Language set to {selected_language}. Moving to AWAITING_STATE.")
            return Response(content=str(twiml), media_type="text/xml")

        if session["state"] == "AWAITING_LANGUAGE":
            twiml.message(
                "Please select a valid language (English, Hindi, Marathi, Urdu, Tamil) or click the menu."
            )
            return Response(content=str(twiml), media_type="text/xml")

    if session["state"] == "AWAITING_STATE":
        standardized_state = standardize_location(user_message)
        session["state_val"] = standardized_state
        session["state"] = "AWAITING_DISTRICT"
        twiml.message(translations["ask_district"].format(user_message))
        return Response(content=str(twiml), media_type="text/xml")

    if session["state"] == "AWAITING_DISTRICT":
        standardized_district = standardize_location(user_message)
        session["district_val"] = standardized_district
        session["state"] = "AWAITING_VILLAGE"
        twiml.message(translations["ask_village"].format(user_message))
        return Response(content=str(twiml), media_type="text/xml")

    if session["state"] == "AWAITING_VILLAGE":
        standardized_village = standardize_location(user_message)
        village = standardized_village
        state = session.get("state_val", "")
        district = session.get("district_val", "")
        session["state"] = "START"

        cleaned_village = village.lower().replace(".", "").strip()
        if cleaned_village in ["none", "no", "nil", "koi nahi", "not sure"]:
            village = "none"
        place = village if village.lower() != "none" else district

        try:
            result = get_groundwater_data(state, place)
            if (result["statusCode"] != 200 or not result["data"]):
                if "mumbai" in place.lower():
                    print("⚠️ No direct data for Mumbai City. Redirecting to Mumbai Suburban...")
                    result = get_groundwater_data(state, "Mumbai Suburban")
            if result["statusCode"] == 200 and result["data"]:
                data = result["data"][0]
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
                body = maybe_translate_with_sarvam(body, language)
            else:
                body = translations["not_found"].format(place, state)
        except Exception as error:
            print(f"Error fetching groundwater data: {error}")
            body = "Oops! Something went wrong. Please try again later."

        twiml.message(body)
        return Response(content=str(twiml), media_type="text/xml")

    if "421001" in user_message_lower:
        twiml.message(
            "📍 Region: Kalyan Belt\n⚠️ Status: CRITICAL\n💡 Advice: Switch Paddy -> Maize."
        )
        return Response(content=str(twiml), media_type="text/xml")

    twiml.message("Hi! Type *start* to begin the location-based query.")
    return Response(content=str(twiml), media_type="text/xml")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=4001, reload=False)
