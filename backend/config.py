from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    ACCOUNT_SID: str = ""
    AUTH_TOKEN: str = ""
    BUTTONS_CONTENT_SID: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GEMINI_MODEL: str = "gemma-4-31b-it"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4174",
        "http://127.0.0.1:4174",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
