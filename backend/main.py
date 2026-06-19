from fastapi import FastAPI, Form, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from routes import health, groundwater
from twilio.rest import Client
from config import settings
import json
import os
import requests
from google import genai

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
twilio_client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

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
        
        # 1. Download the voice note file from Twilio
        audio_response = requests.get(audio_url, auth=(settings.ACCOUNT_SID, settings.AUTH_TOKEN))
        temp_audio_filename = "incoming_voice.ogg"
        with open(temp_audio_filename, "wb") as f:
            f.write(audio_response.content)
            
        # 2. Upload the file binary to Gemini using the files API
        uploaded_audio = gemini_client.files.upload(file=temp_audio_filename)
        
        # 3. Ask Gemini to transcribe what the farmer said (Handles English/Hindi accents perfectly)
        prompt = (
            "Analyze the audio file. If the user speaks in Hindi or any regional language, "
            "translate their meaning directly into the closest English command phrase. "
            "For example: 'Shuru karo' or 'शुरू करो' should be returned as 'start'. "
            "If they speak a number like 'four two one zero zero one', return '421001'. "
            "Return ONLY the plain English text or number, with no punctuation or extra words."
        )
        gemini_response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=[uploaded_audio, prompt]
        )
        
        user_message = gemini_response.text.strip()
        print(f"🎙️ Gemini Voice Transcript: '{user_message}'")
        
        # Cleanup file from Gemini cloud storage to keep things tidy
        gemini_client.files.delete(name=uploaded_audio.name)
    
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
    


