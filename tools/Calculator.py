class Calculator:
    """计算器工具"""
    def execute(self, a: int, b: int, operation: str) -> float:
        """执行计算操作"""
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("除数不能为0")
            return a / b
        else:
            raise ValueError(f"不支持的操作: {operation}")