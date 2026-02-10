import sys
import os
from loguru import logger
from config.settings import settings

# 移除默认的 handler（否则重复输出）
logger.remove()

if "console" in settings.LOG_TYPE:
    # ======== 控制台输出 ========
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            "| <level>{level: <8}</level> "
            "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
            "- <level>{message}</level>",
    )

if "file" in settings.LOG_TYPE:
    # 日志目录
    LOG_DIR = settings.LOG_FILE_PATH
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # ======== 文件输出（按天切割）========
    logger.add(
        f"{LOG_DIR}/app_{{time:YYYY-MM-DD}}.log",
        rotation="00:00",        # 每天 0 点切割
        retention="7 days",      # 保存 7 天
        encoding="utf-8",
        level=settings.LOG_LEVEL,
        enqueue=True,            # 多线程安全
        compression="zip",       # 自动压缩旧日志
    )

__all__ = ["logger"]