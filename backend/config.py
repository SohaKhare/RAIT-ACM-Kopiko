from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    ACCOUNT_SID: str = ""
    AUTH_TOKEN: str = ""
    LIST_CONTENT_SID: str = ""    # Use this for 5+ languages
    SARVAM_API_KEY: str = ""      # Sarvam AI for multilingual results
    GEMINI_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"
    CORS_ORIGINS: list[str] = [
        "http://localhost:4000",
        "http://127.0.0.1:4000",
        "https://rait-acm-kopiko.vercel.app",
        "https://rait-acm-kopiko.vercel.app/",
        "100.106.76.121:4000",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
