from pydantic_settings import BaseSettings
from pydantic import Field
from config.env_loader import load_env

# 先加载 ENV & .env
load_env()

class Settings(BaseSettings):
    # 环境
    ENV: str = Field("dev")
    DEBUG: bool = Field(True)
    TIMEZONE: str = Field("Asia/Shanghai")

    # 日志
    LOG_LEVEL: str = Field("LOG_LEVEL")
    LOG_FILE_PATH: str = Field("logs")
    LOG_TYPE: str = Field("console")

    # LLM配置
    LLM_API_KEY: str = Field("LLM_API_KEY")

    # 调度器配置
    SCHEDULER_SQLITE_FILE: str = Field("./local/scheduler.db")

    # 邮件发送配置
    SMTP_HOST: str = Field("SMTP_HOST")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USER: str = Field("SMTP_USER")
    SMTP_PASSWORD: str = Field("SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(True, env="SMTP_USE_TLS")
    SMTP_FROM: str = Field("SMTP_FROM")
    IMAP_HOST: str = Field("IMAP_HOST")
    IMAP_PORT: int = Field(993, env="IMAP_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局唯一配置实例
settings = Settings()