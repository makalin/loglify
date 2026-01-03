from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Telegram
    telegram_token: str
    telegram_chat_id: Optional[str] = None
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    
    # Database
    database_url: str = "sqlite:///./loglify.db"
    
    # GitHub
    github_token: Optional[str] = None
    github_username: Optional[str] = None
    github_repos: Optional[str] = None
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # AI Review
    enable_daily_review: bool = True
    review_time: str = "22:00"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

