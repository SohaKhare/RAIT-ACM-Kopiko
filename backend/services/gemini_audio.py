import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field

from config import settings


class FarmerContext(BaseModel):
    farmer_name: str | None = None
    phone_number: str | None = None
    preferred_language: str | None = None
    state_name: str | None = None
    district_name: str | None = None
    village_name: str | None = None
    pincode: str | None = None
    season: str | None = None
    land_area_acres: float | None = None
    irrigation_source: str | None = None
    current_crop: str | None = None
    candidate_crop: str | None = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class ToolCallRequest(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class ConversationTurnResult(BaseModel):
    reply_text: str
    detected_language: str | None = None
    updated_context: FarmerContext = Field(default_factory=FarmerContext)
    missing_fields: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCallRequest] = Field(default_factory=list)
    should_continue: bool = True


class GeminiConversationService:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.base_url = base_url or settings.GEMINI_BASE_URL
        self.model = model or settings.GEMINI_MODEL

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def run_text_turn(
        self,
        message_text: str,
        conversation_history: list[dict[str, Any]] | None = None,
        farmer_context: FarmerContext | None = None,
        tool_definitions: list[ToolDefinition] | None = None,
    ) -> ConversationTurnResult:
        user_message = {
            "role": "user",
            "content": [{"type": "text", "text": message_text}],
        }
        return self._run_turn(
            user_message=user_message,
            conversation_history=conversation_history,
            farmer_context=farmer_context,
            tool_definitions=tool_definitions,
        )

    def run_audio_turn(
        self,
        audio_bytes: bytes,
        mime_type: str,
        filename: str | None = None,
        prompt: str | None = None,
        conversation_history: list[dict[str, Any]] | None = None,
        farmer_context: FarmerContext | None = None,
        tool_definitions: list[ToolDefinition] | None = None,
    ) -> ConversationTurnResult:
        prepared_audio_bytes, audio_format = self._prepare_audio_for_gemini(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            filename=filename,
        )
        base64_audio = base64.b64encode(prepared_audio_bytes).decode("utf-8")

        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt or "Understand this farmer's audio message and respond naturally.",
                },
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": base64_audio,
                        "format": audio_format,
                    },
                },
            ],
        }
        return self._run_turn(
            user_message=user_message,
            conversation_history=conversation_history,
            farmer_context=farmer_context,
            tool_definitions=tool_definitions,
        )

    def build_tool_result_message(
        self,
        tool_call_id: str,
        tool_name: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": json.dumps(result, ensure_ascii=False),
        }

    def default_tool_definitions(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="get_groundwater_status",
                description=(
                    "Fetch district groundwater depth and category using state, district, and optional date range."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "state_name": {"type": "string"},
                        "district_name": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                    },
                    "required": ["state_name", "district_name"],
                },
            ),
            ToolDefinition(
                name="get_rainfall_forecast",
                description=(
                    "Fetch 7-day rainfall forecast using pincode or latitude and longitude."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "pincode": {"type": "string"},
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                    },
                },
            ),
            ToolDefinition(
                name="get_crop_economics",
                description=(
                    "Return water requirement, yield, MSP, and expected income for one or more kharif crops."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "crop_names": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "season": {"type": "string"},
                        "district_name": {"type": "string"},
                    },
                    "required": ["crop_names"],
                },
            ),
            ToolDefinition(
                name="compare_crop_options",
                description=(
                    "Compare current crop versus alternative crops on income, water use, and groundwater savings."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "current_crop": {"type": "string"},
                        "candidate_crops": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "district_name": {"type": "string"},
                        "state_name": {"type": "string"},
                        "land_area_acres": {"type": "number"},
                    },
                    "required": ["current_crop", "candidate_crops"],
                },
            ),
            ToolDefinition(
                name="get_mandi_crop_ranking",
                description=(
                    "Fetch the ranked list of Kharif crops for a state, showing predicted prices, MSP, profit gap %, and price risk/volatility."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "state_name": {"type": "string", "description": "The Indian state name, e.g. Maharashtra"}
                    },
                    "required": ["state_name"],
                },
            ),
            ToolDefinition(
                name="get_mandi_msp_comparison",
                description=(
                    "Compare predicted market price of a Kharif crop against its Minimum Support Price (MSP) in a given state."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "commodity": {"type": "string", "description": "Name of the Kharif crop, e.g. paddy, maize, cotton"},
                        "state_name": {"type": "string", "description": "State name, e.g. Maharashtra"}
                    },
                    "required": ["commodity", "state_name"],
                },
            ),
        ]

    def _run_turn(
        self,
        user_message: dict[str, Any],
        conversation_history: list[dict[str, Any]] | None,
        farmer_context: FarmerContext | None,
        tool_definitions: list[ToolDefinition] | None,
    ) -> ConversationTurnResult:
        current_context = farmer_context or FarmerContext()
        messages = [
            {"role": "system", "content": self._system_prompt(current_context)},
            *(conversation_history or []),
            user_message,
        ]

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self._build_tools(tool_definitions or self.default_tool_definitions()),
            tool_choice="auto",
        )

        message = completion.choices[0].message
        clean_reply_text = self._strip_context_update(message.content or "")
        tool_calls = self._extract_tool_calls(message.tool_calls or [])
        updated_context = self._merge_context_from_text(
            source_text=message.content or "",
            current_context=current_context,
        )
        missing_fields = self._missing_fields(updated_context)

        return ConversationTurnResult(
            reply_text=clean_reply_text,
            detected_language=self._detect_language(updated_context, current_context),
            updated_context=updated_context,
            missing_fields=missing_fields,
            tool_calls=tool_calls,
            should_continue=bool(tool_calls or missing_fields),
        )

    def _system_prompt(self, farmer_context: FarmerContext) -> str:
        return (
            "You are JalDhar's multilingual farm advisory assistant for Indian farmers. "
            "You speak simply, naturally, and respectfully in the farmer's language when possible. "
            "Your main conversational goals are to obtain the following 3 pieces of information:\n"
            "1. Location (State and District/Village) to fetch localized crop prices and rankings.\n"
            "2. Current Crop or Interested Crops they are considering growing.\n"
            "3. Irrigation source or land size (e.g. rainfed, well/borewell) to evaluate groundwater risks.\n"
            "Ask at most one question at a time to keep the conversation simple for the farmer. "
            "When data is needed, call tools instead of inventing values. "
            "Keep advice localized, brief, and practical. "
            "Always optimize for income per litre of water, not just gross yield. "
            "If a farmer grows paddy in a stressed groundwater district, explain the tradeoff clearly: "
            "water saved versus income impact.\n\n"
            "Known structured farmer context follows. Use it and update it implicitly in your reply:\n"
            f"{farmer_context.model_dump_json(indent=2)}\n"
            "At the end of every assistant reply, include a single line starting with "
            "'CONTEXT_UPDATE:' followed by compact JSON containing only context fields you are confident about."
        )

    @staticmethod
    def _build_tools(tool_definitions: list[ToolDefinition]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool_definition.name,
                    "description": tool_definition.description,
                    "parameters": tool_definition.parameters,
                },
            }
            for tool_definition in tool_definitions
        ]

    def _merge_context_from_text(
        self,
        source_text: str,
        current_context: FarmerContext,
    ) -> FarmerContext:
        marker = "CONTEXT_UPDATE:"
        if marker not in source_text:
            return current_context

        raw_json = source_text.split(marker, 1)[1].strip()
        raw_json = raw_json.splitlines()[0].strip()

        try:
            update_payload = json.loads(raw_json)
        except json.JSONDecodeError:
            return current_context

        merged = current_context.model_dump()
        for key, value in update_payload.items():
            if key in merged and value not in (None, "", []):
                merged[key] = value
        return FarmerContext(**merged)

    @staticmethod
    def _strip_context_update(source_text: str) -> str:
        marker = "CONTEXT_UPDATE:"
        if marker not in source_text:
            return source_text.strip()
        return source_text.split(marker, 1)[0].strip()

    @staticmethod
    def _detect_language(
        updated_context: FarmerContext,
        current_context: FarmerContext,
    ) -> str | None:
        return updated_context.preferred_language or current_context.preferred_language

    @staticmethod
    def _missing_fields(farmer_context: FarmerContext) -> list[str]:
        important_fields = [
            "preferred_language",
            "state_name",
            "district_name",
            "pincode",
            "season",
            "current_crop",
            "land_area_acres",
        ]
        return [
            field_name
            for field_name in important_fields
            if getattr(farmer_context, field_name) in (None, "")
        ]

    @staticmethod
    def _extract_tool_calls(tool_calls: list[Any]) -> list[ToolCallRequest]:
        extracted_calls: list[ToolCallRequest] = []
        for tool_call in tool_calls:
            arguments = tool_call.function.arguments
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            extracted_calls.append(
                ToolCallRequest(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=arguments,
                )
            )
        return extracted_calls

    @staticmethod
    def _resolve_audio_format(mime_type: str, filename: str | None = None) -> str:
        normalized_mime_type = mime_type.split(";", 1)[0].strip().lower()
        mime_map = {
            "audio/wav": "wav",
            "audio/x-wav": "wav",
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/webm": "webm",
            "audio/mp4": "mp4",
            "audio/x-m4a": "m4a",
            "audio/aac": "aac",
            "audio/ogg": "ogg",
            "audio/opus": "ogg",
        }

        if normalized_mime_type in mime_map:
            return mime_map[normalized_mime_type]

        if filename:
            extension = Path(filename).suffix.lower().lstrip(".")
            extension_map = {
                "wav": "wav",
                "mp3": "mp3",
                "webm": "webm",
                "mp4": "mp4",
                "m4a": "m4a",
                "aac": "aac",
                "ogg": "ogg",
                "opus": "ogg",
            }
            if extension in extension_map:
                return extension_map[extension]

        raise ValueError(f"Unsupported audio format for Gemini input: {mime_type}")

    def _prepare_audio_for_gemini(
        self,
        audio_bytes: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> tuple[bytes, str]:
        audio_format = self._resolve_audio_format(mime_type=mime_type, filename=filename)

        if audio_format in {"wav", "mp3"}:
            return audio_bytes, audio_format

        print(
            f"Converting frontend audio from {mime_type!r} to mp3 for Gemini compatibility."
        )
        converted_audio_bytes = self._convert_audio_with_ffmpeg(
            audio_bytes=audio_bytes,
            source_filename=filename or f"input.{audio_format}",
            target_extension="mp3",
        )
        print(f"Audio conversion complete. Converted bytes: {len(converted_audio_bytes)}")
        return converted_audio_bytes, "mp3"

    @staticmethod
    def _convert_audio_with_ffmpeg(
        audio_bytes: bytes,
        source_filename: str,
        target_extension: str,
    ) -> bytes:
        source_suffix = Path(source_filename).suffix or ".bin"
        source_file = tempfile.NamedTemporaryFile(delete=False, suffix=source_suffix)
        target_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{target_extension}")

        try:
            source_file.write(audio_bytes)
            source_file.flush()
            source_file.close()
            target_file.close()

            command = [
                "ffmpeg",
                "-y",
                "-i",
                source_file.name,
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-b:a",
                "32k",
                target_file.name,
            ]
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            with open(target_file.name, "rb") as converted_file:
                return converted_file.read()
        except subprocess.CalledProcessError as error:
            stderr_output = error.stderr.decode("utf-8", errors="ignore")
            raise ValueError(f"Audio conversion failed: {stderr_output}") from error
        finally:
            for temp_path in [source_file.name, target_file.name]:
                try:
                    os.remove(temp_path)
                except FileNotFoundError:
                    pass
