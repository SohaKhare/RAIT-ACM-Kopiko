from services.llm import process_audio_message, process_text_message


def handle_text_message(
    message_text: str, 
    language: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    state: str | None = None,
    district: str | None = None,
) -> dict:
    return process_text_message(
        message_text=message_text, 
        language=language,
        lat=lat,
        lng=lng,
        state=state,
        district=district,
    )


def handle_audio_message(
    audio_bytes: bytes,
    mime_type: str,
    filename: str,
    language: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    state: str | None = None,
    district: str | None = None,
) -> dict:
    return process_audio_message(
        audio_bytes=audio_bytes,
        mime_type=mime_type,
        filename=filename,
        language=language,
        lat=lat,
        lng=lng,
        state=state,
        district=district,
    )
