from services.gemini_audio import GeminiConversationService


gemini_service = GeminiConversationService()


def process_text_message(message_text: str, language: str | None = None) -> dict:
    prompt = (
        f"Preferred response language: {language or 'auto'}. "
        "Respond conversationally to the farmer's message. "
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
) -> dict:
    prompt = (
        f"Preferred response language: {language or 'auto'}. "
        "Understand the farmer's spoken message and reply conversationally. "
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
