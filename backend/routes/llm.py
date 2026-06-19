from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

from controllers.llm import handle_audio_message, handle_text_message


router = APIRouter(prefix="/llm", tags=["LLM"])


class TextMessageRequest(BaseModel):
    message_text: str
    language: str | None = None
    lat: float | None = None
    lng: float | None = None
    state: str | None = None
    district: str | None = None


@router.post("/text")
async def llm_text(request: TextMessageRequest):
    print("\n--- LLM Text Request ---")
    print(f"Language: {request.language or 'auto'}")
    print(f"Message: {request.message_text!r}")
    result = handle_text_message(
        message_text=request.message_text,
        language=request.language,
        lat=request.lat,
        lng=request.lng,
        state=request.state,
        district=request.district,
    )
    print("LLM text response generated.")
    return result


@router.post("/audio")
async def llm_audio(
    file: UploadFile = File(...),
    language: str | None = Form(default=None),
    lat: float | None = Form(default=None),
    lng: float | None = Form(default=None),
    state: str | None = Form(default=None),
    district: str | None = Form(default=None),
):
    print("\n--- LLM Audio Request ---")
    print(f"Filename: {file.filename}")
    print(f"Content type: {file.content_type}")
    print(f"Language: {language or 'auto'}")

    audio_bytes = await file.read()
    print(f"Audio bytes received: {len(audio_bytes)}")

    result = handle_audio_message(
        audio_bytes=audio_bytes,
        mime_type=file.content_type or "audio/webm",
        filename=file.filename or "farmer-audio.webm",
        language=language,
        lat=lat,
        lng=lng,
        state=state,
        district=district,
    )
    print("LLM audio response generated.")
    return result
