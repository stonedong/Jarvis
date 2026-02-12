from utils import logger


class Calculator:
    """计算器工具"""
    def execute(self, a: int, b: int, operation: str) -> str:
        """
        执行计算操作
        :param a: 第一个数字
        :param b: 第二个数字
        :param operation: 操作类型，支持 'add'、'subtract'、'multiply'、'divide'
        :return: 计算结果
        """
        result = None
        try:
            if operation == "add":
                logger.info(f"执行加法: {a} + {b}")
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    raise ValueError("除数不能为0")
                result = a / b
            else:
                raise ValueError(f"不支持的操作: {operation}")
            logger.info(f"计算结果: {result}")
        except Exception as e:
            result = f"计算出错: {str(e)}"
            logger.error(f"计算出错: {e}")
        return result