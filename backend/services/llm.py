from services.gemini_audio import GeminiConversationService, FarmerContext

gemini_service = GeminiConversationService()


def process_text_message(
    message_text: str, 
    language: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    state: str | None = None,
    district: str | None = None,
    farmer_context: dict | None = None,
    conversation_history: list | None = None,
) -> dict:
    context_obj = FarmerContext(**farmer_context) if farmer_context else FarmerContext()
    
    # Pre-fill location if passed from geocoding/GPS and not already set
    if not context_obj.state_name and state:
        context_obj.state_name = state
    if not context_obj.district_name and district:
        context_obj.district_name = district
    if not context_obj.preferred_language and language:
        context_obj.preferred_language = language

    location_ctx = f" Farmer Location: {district or 'Unknown District'}, {state or 'Unknown State'} (Lat: {lat}, Lng: {lng})." if lat and lng else ""
    prompt = (
        f"Preferred response language: {language or 'auto'}. "
        f"Respond conversationally to the farmer's message.{location_ctx} "
        "Keep the response concise and practical."
    )
    result = gemini_service.run_text_turn(
        message_text=f"{prompt}\n\nFarmer message: {message_text}",
        conversation_history=conversation_history,
        farmer_context=context_obj
    )
    return {
        "reply_text": result.reply_text,
        "detected_language": result.detected_language,
        "missing_fields": result.missing_fields,
        "updated_context": result.updated_context.model_dump() if result.updated_context else {},
        "tool_calls": [tc.model_dump() for tc in result.tool_calls] if result.tool_calls else [],
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
    farmer_context: dict | None = None,
    conversation_history: list | None = None,
) -> dict:
    context_obj = FarmerContext(**farmer_context) if farmer_context else FarmerContext()
    
    # Pre-fill location if passed from geocoding/GPS and not already set
    if not context_obj.state_name and state:
        context_obj.state_name = state
    if not context_obj.district_name and district:
        context_obj.district_name = district
    if not context_obj.preferred_language and language:
        context_obj.preferred_language = language

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
        conversation_history=conversation_history,
        farmer_context=context_obj
    )
    return {
        "reply_text": result.reply_text,
        "detected_language": result.detected_language,
        "missing_fields": result.missing_fields,
        "updated_context": result.updated_context.model_dump() if result.updated_context else {},
        "tool_calls": [tc.model_dump() for tc in result.tool_calls] if result.tool_calls else [],
    }
