from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from loguru import logger
from config.settings import settings

def create_scheduler():
    # ---------- 1. 根据配置决定 JobStore ----------
    # 尝试读取数据库配置，如果全部存在且非空，则使用 PostgreSQL
    db_host = getattr(settings, 'DB_HOST', None)
    db_user = getattr(settings, 'DB_USER', None)
    db_pass = getattr(settings, 'DB_PASS', None)
    db_port = getattr(settings, 'DB_PORT', None)
    db_name = getattr(settings, 'DB_NAME', None)

    if all([db_host, db_user, db_pass, db_port, db_name]):
        # PostgreSQL 持久化
        db_url = (
            f"postgresql+psycopg://{db_user}:{db_pass}"
            f"@{db_host}:{db_port}/{db_name}"
        )
        job_stores = {
            "default": SQLAlchemyJobStore(url=db_url)
        }
        logger.info("Scheduler job store: PostgreSQL")
    else:
        # 后备方案：SQLite 文件持久化
        # 可从 settings 中自定义路径，默认放在当前目录
        sqlite_file = getattr(settings, 'SCHEDULER_SQLITE_FILE', './scheduler_jobs.sqlite')
        # 确保数据库文件父目录存在
        import os
        db_dir = os.path.dirname(sqlite_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created directory for SQLite: {db_dir}")

        sqlite_url = f"sqlite:///{sqlite_file}"
        job_stores = {
            "default": SQLAlchemyJobStore(url=sqlite_url)
        }
        logger.info(f"Scheduler job store: SQLite file ({sqlite_file})")

    # ---------- 2. 执行器配置 ----------
    executors = {
        "default": ThreadPoolExecutor(10),
        "processpool": ProcessPoolExecutor(2)
    }

    # ---------- 3. 作业默认行为 ----------
    job_defaults = {
        "coalesce": False,      # 不合并重叠执行
        "max_instances": 3      # 最大并发实例数
    }

    # ---------- 4. 创建调度器 ----------
    scheduler = BackgroundScheduler(
        jobstores=job_stores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=settings.TIMEZONE,
    )

    return scheduler


# 全局调度器实例
scheduler = create_scheduler()