from services.gemini_audio import GeminiConversationService


gemini_service = GeminiConversationService()


def process_text_message(
    message_text: str, 
    language: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    state: str | None = None,
    district: str | None = None,
) -> dict:
    location_ctx = f" Farmer Location: {district or 'Unknown District'}, {state or 'Unknown State'} (Lat: {lat}, Lng: {lng})." if lat and lng else ""
    prompt = (
        f"Preferred response language: {language or 'auto'}. "
        f"Respond conversationally to the farmer's message.{location_ctx} "
        "Keep the response concise and practical."
    )
    result = gemini_service.run_text_turn(
        message_text=f"{prompt}\n\nFarmer message: {message_text}",
    )
    return {
        "reply_text": result.reply_text,
        "detected_language": result.detected_language,
        "missing_fields": result.missing_fields,
    }


def process_audio_message(
    audio_bytes: bytes,
    mime_type: str,
    filename: str,
    language: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    state: str | None = None,
    district: str | None = None,
) -> dict:
    location_ctx = f" Farmer Location: {district or 'Unknown District'}, {state or 'Unknown State'} (Lat: {lat}, Lng: {lng})." if lat and lng else ""
    prompt = (
        f"Preferred response language: {language or 'auto'}. "
        f"Understand the farmer's spoken message and reply conversationally.{location_ctx} "
        "Keep the response concise and practical."
    )
    result = gemini_service.run_audio_turn(
        audio_bytes=audio_bytes,
        mime_type=mime_type,
        filename=filename,
        prompt=prompt,
    )
    return {
        "reply_text": result.reply_text,
        "detected_language": result.detected_language,
        "missing_fields": result.missing_fields,
    }
