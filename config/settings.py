from pydantic_settings import BaseSettings
from pydantic import Field
from config.env_loader import load_env

# 先加载 ENV & .env
load_env()

class Settings(BaseSettings):
    # 环境
    ENV: str = Field("dev")
    DEBUG: bool = Field(True)

    # 日志
    LOG_LEVEL: str = Field("LOG_LEVEL")
    LOG_FILE_PATH: str = Field("logs")
    LOG_TYPE: str = Field("console")

    # LLM配置
    LLM_API_KEY: str = Field("LLM_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局唯一配置实例
settings = Settings()