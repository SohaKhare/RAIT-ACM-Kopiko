from fastapi import FastAPI, Form, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import json

import requests
from routes import health, groundwater, mandi, location
from twilio.rest import Client

from config import settings
from routes import health
from services import GeminiConversationService

app = FastAPI(title="Backend API")

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

@app.post("/webhook")
async def whatsapp_webhook(request: Request, From: str = Form(...)):
    user_phone = From
    
    form_data = await request.form()
    user_message = form_data.get("Body", "").strip()
    
    # ----------------------------------------------------------------
    # 🎙️ AUDIO PROCESSING VIA GEMINI
    # ----------------------------------------------------------------
    if "MediaUrl0" in form_data and "audio" in form_data.get("MediaContentType0", ""):
        audio_url = form_data["MediaUrl0"]

        audio_response = requests.get(audio_url, auth=(settings.ACCOUNT_SID, settings.AUTH_TOKEN))
        audio_response.raise_for_status()

        prompt = (
            "Analyze the audio file. If the user speaks in Hindi or any regional language, "
            "translate their meaning directly into the closest English command phrase. "
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
    
    if user_message_lower in ["hi", "hello", "start", "menu"]:
        twilio_client.messages.create(
            from_="whatsapp:+14155238886",
            to=user_phone,
            content_sid=settings.BUTTONS_CONTENT_SID,
            content_variables=json.dumps({})
        )
        return Response(status_code=200)
        
    elif user_message_lower == "english":
        twilio_client.messages.create(from_="whatsapp:+14155238886", to=user_phone, body="Language set to English! Please provide your PIN code.")
        return Response(status_code=200)
        
    elif user_message in ["हिंदी", "Hindi"] or user_message_lower == "hindi":
        twilio_client.messages.create(from_="whatsapp:+14155238886", to=user_phone, body="भाषा हिंदी सेट की गई है! कृपया अपना पिन कोड दर्ज करें।")
        return Response(status_code=200)
        
    elif "421001" in user_message_lower:
        twilio_client.messages.create(
            from_="whatsapp:+14155238886",
            to=user_phone,
            body="📍 Region: Kalyan Belt\n⚠️ Status: CRITICAL\n💡 Advice: Switch Paddy -> Maize."
        )
        return Response(status_code=200)
        
    else:
        twilio_client.messages.create(
            from_="whatsapp:+14155238886",
            to=user_phone,
            body=f"Processed content: '{user_message}'. Try typing or saying *start* or *421001*!"
        )
        return Response(status_code=200)
    

