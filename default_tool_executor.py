import inspect
import importlib
import sys
from pathlib import Path
from typing import Dict, Optional, Type, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections import defaultdict


@dataclass
class ToolCall:
    """工具调用请求"""
    tool_name: str
    parameters: Dict[str, Any]
    reason: str


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None


class ToolExecutor(ABC):
    """工具执行器抽象基类"""
    
    @abstractmethod
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用"""
        pass


class DefaultToolExecutor(ToolExecutor):
    """默认工具执行器实现"""
    
    def __init__(self, tools_package_path: str = "tools"):
        """
        初始化工具执行器
        
        Args:
            tools_package_path: tools包的路径（相对于项目根目录）
        """
        self.tools_package_path = tools_package_path
        self.tools: Dict[str, Any] = {}
        self._load_tools()
    
    def _load_tools(self) -> None:
        """动态加载tools包中的所有工具"""
        try:
            # 导入tools包
            tools_module = importlib.import_module(self.tools_package_path)
            
            # 获取tools包的路径
            if hasattr(tools_module, '__path__'):
                package_path = Path(tools_module.__path__[0])
            else:
                return
            
            # 遍历tools包中的所有Python文件
            for file_path in package_path.glob("*.py"):
                if file_path.name.startswith("_"):
                    continue
                
                module_name = file_path.stem
                try:
                    # 动态导入模块
                    module = importlib.import_module(
                        f"{self.tools_package_path}.{module_name}"
                    )
                    
                    # 查找模块中的工具类（假设命名规范：CamelCase）
                    for name, obj in inspect.getmembers(module):
                        # 跳过私有类和抽象类
                        if name.startswith("_"):
                            continue
                        
                        # 检查是否为类且可以实例化
                        if inspect.isclass(obj) and obj.__module__ == module.__name__:
                            try:
                                # 尝试实例化工具
                                tool_instance = obj()
                                tool_name = self._get_tool_name(name)
                                self.tools[tool_name] = tool_instance
                            except Exception as e:
                                print(f"警告: 无法实例化 {name}: {e}")
                
                except ImportError as e:
                    print(f"警告: 无法导入模块 {module_name}: {e}")
        
        except ImportError as e:
            print(f"警告: 无法导入tools包: {e}")
    
    def _get_tool_name(self, class_name: str) -> str:
        """
        将类名转换为工具名
        例如: GetWeather -> get_weather
        """
        result = []
        for i, char in enumerate(class_name):
            if i > 0 and char.isupper():
                result.append("_")
            result.append(char.lower())
        return "".join(result)
    
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """
        执行工具调用
        
        Args:
            tool_call: 工具调用请求
        
        Returns:
            工具执行结果
        """
        tool_name = tool_call.tool_name
        parameters = tool_call.parameters
        
        try:
            # 检查工具是否存在
            if tool_name not in self.tools:
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    result=None,
                    error=f"工具 '{tool_name}' 不存在。可用工具: {list(self.tools.keys())}"
                )
            
            tool = self.tools[tool_name]
            
            # 获取工具的execute方法
            if not hasattr(tool, "execute"):
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    result=None,
                    error=f"工具 '{tool_name}' 没有execute方法"
                )
            
            # 执行工具
            result = tool.execute(**parameters)
            
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                error=None
            )
        
        except TypeError as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"参数错误: {str(e)}"
            )
        
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"执行错误: {str(e)}"
            )
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有可用的工具及其信息
        
        Returns:
            工具信息字典
        """
        tools_info = {}
        for tool_name, tool in self.tools.items():
            if hasattr(tool, "execute"):
                sig = inspect.signature(tool.execute)
                tools_info[tool_name] = {
                    "class": tool.__class__.__name__,
                    "parameters": list(sig.parameters.keys()),
                    "docstring": tool.execute.__doc__ or ""
                }
        return tools_info