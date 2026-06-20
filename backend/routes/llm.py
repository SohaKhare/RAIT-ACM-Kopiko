import json
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from controllers.llm import handle_audio_message, handle_text_message


router = APIRouter(prefix="/llm", tags=["LLM"])


class TextMessageRequest(BaseModel):
    message_text: str
    language: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    state: Optional[str] = None
    district: Optional[str] = None
    farmer_context: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None


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
        farmer_context=request.farmer_context,
        conversation_history=request.conversation_history,
    )
    print("LLM text response generated.")
    return result


@router.post("/audio")
async def llm_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(default=None),
    lat: Optional[float] = Form(default=None),
    lng: Optional[float] = Form(default=None),
    state: Optional[str] = Form(default=None),
    district: Optional[str] = Form(default=None),
    context: Optional[str] = Form(default=None),  # JSON-serialized FarmerContext
    history: Optional[str] = Form(default=None),  # JSON-serialized list of previous turns
):
    print("\n--- LLM Audio Request ---")
    print(f"Filename: {file.filename}")
    print(f"Content type: {file.content_type}")
    print(f"Language: {language or 'auto'}")

    # Parse JSON-serialized inputs from Form Data
    farmer_context_dict = None
    if context:
        try:
            farmer_context_dict = json.loads(context)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for 'context' field.")

    conversation_history_list = None
    if history:
        try:
            conversation_history_list = json.loads(history)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for 'history' field.")

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
        farmer_context=farmer_context_dict,
        conversation_history=conversation_history_list,
    )
    print("LLM audio response generated.")
    return result
