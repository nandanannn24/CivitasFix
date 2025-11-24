import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Untuk SQLite, kita tidak perlu DATABASE_URL yang complex
    DATABASE_URL: str = "sqlite:///./civitasfix.db"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "civitasfix-secret-key-2024-upn-veteran-jatim")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

settings = Settings()