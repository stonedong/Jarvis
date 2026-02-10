import os
from dotenv import load_dotenv

def load_env():
    """
    自动根据 ENV 加载对应的 .env 文件
    """
    base_file = ".env"
    prod_file = ".env.prod"
    test_file = ".env.test"

    # 先加载基础 .env
    if os.path.exists(base_file):
        load_dotenv(base_file)

    # 根据参数 ENV 再加载其他环境
    env = os.getenv("ENV", "dev")

    if env == "prod" and os.path.exists(prod_file):
        load_dotenv(prod_file, override=True)
    elif env == "test" and os.path.exists(test_file):
        load_dotenv(test_file, override=True)