"""
协调器模块 - 智能助理的主流程控制中心
"""

from enum import Enum
from typing import Optional, Any, List, Dict
from dataclasses import dataclass
from abc import ABC, abstractmethod

from utils.logger import logger
from conversation_manager import ConversationManager, MessageRole


class ActionType(Enum):
    """动作类型枚举"""
    DIRECT_REPLY = "direct_reply"          # 直接回复用户
    CALL_TOOL = "call_tool"                # 调用工具
    ASK_USER = "ask_user"                  # 询问用户
    DELEGATE = "delegate"                  # 委托给子系统


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


@dataclass
class Thought:
    """协调器的思考结果"""
    action_type: ActionType
    action_content: Any  # 可能是回复文本、ToolCall、问题等
    confidence: float
    reasoning: str


class ToolExecutor(ABC):
    """工具执行器抽象基类"""
    
    @abstractmethod
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用"""
        pass

    @abstractmethod
    def get_all_tools_info(self) -> Dict[str, Any]:
        """获取所有工具的信息"""
        pass

class ThinkingEngine(ABC):
    """思考引擎抽象基类"""
    
    @abstractmethod
    def think(self, context: "InteractionContext") -> Thought:
        """基于当前上下文进行思考"""
        pass


@dataclass
class InteractionContext:
    """交互上下文"""
    user_input: str
    conversation_history: List[Dict[str, str]]
    tool_results: List[ToolResult]
    thought_chain: List[Thought]
    max_iterations: int = 5
    conversation_manager: Optional['ConversationManager'] = None
    all_tool_info: Dict[str, Any] = None
    
    @property
    def current_iteration(self) -> int:
        """当前迭代次数"""
        return len(self.thought_chain)
    
    @property
    def has_reached_max_iterations(self) -> bool:
        """是否达到最大迭代次数"""
        return self.current_iteration >= self.max_iterations
    
    def add_thought(self, thought: Thought) -> None:
        """添加思考结果"""
        self.thought_chain.append(thought)
    
    def add_tool_result(self, result: ToolResult) -> None:
        """添加工具执行结果"""
        self.tool_results.append(result)


class Coordinator:
    """协调器 - 主流程控制"""
    
    def __init__(
        self,
        thinking_engine: ThinkingEngine,
        tool_executor: ToolExecutor,
        max_iterations: int = 5,
        conversation_manager: Optional[ConversationManager] = None
    ):
        self.thinking_engine = thinking_engine
        self.tool_executor = tool_executor
        self.max_iterations = max_iterations
        # 使用传入的管理器，或创建新的
        self.conversation_manager = conversation_manager or ConversationManager()
    
    def start_interaction(
        self,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        use_conversation_manager: bool = True
    ) -> str:
        """
        开始一次交互循环

        Args:
            user_input: 用户输入的自然语言文本
            history: 对话历史（如果为None则使用conversation_manager中的历史）
            use_conversation_manager: 是否使用会话管理器维护连续对话

        Returns:
            最终的回复文本
        """
        # 如果启用会话管理器，添加用户消息到历史
        if use_conversation_manager:
            self.conversation_manager.add_user_message(user_input)
        
        # 如果没有提供历史，使用conversation_manager的历史
        if history is None and use_conversation_manager:
            history = self.conversation_manager.get_conversation_history()
        
        # 初始化交互上下文
        context = InteractionContext(
            user_input=user_input,
            conversation_history=history or [],
            tool_results=[],
            thought_chain=[],
            max_iterations=self.max_iterations,
            conversation_manager=self.conversation_manager if use_conversation_manager else None,
            all_tool_info=self.tool_executor.get_all_tools_info() if hasattr(self.tool_executor, "get_all_tools_info") else None
        )
        
        # 主循环
        while not context.has_reached_max_iterations:
            # 1. 协调器思考
            thought = self.thinking_engine.think(context)
            context.add_thought(thought)
            
            # 2. 根据思考结果执行动作
            if thought.action_type == ActionType.DIRECT_REPLY:
                # 直接回复
                return self._finalize_response(thought.action_content, context, use_conversation_manager)
            
            elif thought.action_type == ActionType.CALL_TOOL:
                # 调用工具
                tool_call: ToolCall = thought.action_content
                result = self.tool_executor.execute(tool_call)
                context.add_tool_result(result)
                
                if not result.success:
                    # 工具调用失败，生成错误回复
                    return self._finalize_response(
                        f"执行工具 {result.tool_name} 失败: {result.error}",
                        context,
                        use_conversation_manager
                    )
                # 继续循环，将工具结果作为新的输入
                continue
            
            elif thought.action_type == ActionType.ASK_USER:
                # 询问用户
                return self._finalize_response(thought.action_content, context, use_conversation_manager)
            
            elif thought.action_type == ActionType.DELEGATE:
                # 委托给子系统
                return self._finalize_response(thought.action_content, context, use_conversation_manager)
        
        # 达到最大迭代次数，返回最后的思考结果
        return self._finalize_response(
            "处理请求时超过最大迭代次数，请简化您的问题后重试。",
            context,
            use_conversation_manager
        )
    
    def _finalize_response(
        self,
        response: str,
        context: InteractionContext,
        use_conversation_manager: bool = True
    ) -> str:
        """Finalize response"""
        # If using conversation manager, add assistant message to history
        if use_conversation_manager and context.conversation_manager:
            context.conversation_manager.add_assistant_message(
                response,
                metadata={
                    "action_type": str(context.thought_chain[-1].action_type) if context.thought_chain else None,
                    "tool_results": [
                        {"tool": r.tool_name, "success": r.success}
                        for r in context.tool_results
                    ]
                }
            )
            # Update conversation context
            if context.thought_chain:
                context.conversation_manager.update_context(
                    tool_results=[
                        {
                            "tool_name": r.tool_name,
                            "success": r.success,
                            "result": str(r.result)[:200]
                        }
                        for r in context.tool_results
                    ],
                    assistant_action=str(context.thought_chain[-1].action_type),
                    user_intent=context.user_input[:100]
                )
        
        # logger.info(f"Final response: {response}")
        return response


class SimpleThinkingEngine(ThinkingEngine):
    """Simple thinking engine implementation (example)"""
    
    def think(self, context: InteractionContext) -> Thought:
        """
        Simple decision logic example
        """
        # If no previous thoughts, this is the first time
        if not context.thought_chain:
            # Example: simple heuristic rules
            if "weather" in context.user_input:
                return Thought(
                    action_type=ActionType.CALL_TOOL,
                    action_content=ToolCall(
                        tool_name="weather",
                        parameters={"query": context.user_input},
                        reason="User is asking about weather"
                    ),
                    confidence=0.9,
                    reasoning="User input contains 'weather' keyword, should call weather tool"
                )
            else:
                return Thought(
                    action_type=ActionType.DIRECT_REPLY,
                    action_content=f"I received your request: {context.user_input}",
                    confidence=0.8,
                    reasoning="Cannot determine specific need, confirming first"
                )
        
        # If there are tool results, continue thinking based on them
        if context.tool_results:
            last_result = context.tool_results[-1]
            return Thought(
                action_type=ActionType.DIRECT_REPLY,
                action_content=f"Tool execution complete, result: {last_result.result}",
                confidence=0.9,
                reasoning="Generate reply based on tool result"
            )
        
        return Thought(
            action_type=ActionType.DIRECT_REPLY,
            action_content="Processing complete",
            confidence=0.5,
            reasoning="Default reply"
        )


class SimpleToolExecutor(ToolExecutor):
    """简单的工具执行器实现（示例）"""
    
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用"""
        try:
            if tool_call.tool_name == "weather":
                # 模拟天气工具
                result = f"获取了 {tool_call.parameters.get('query')} 的天气信息"
                return ToolResult(
                    tool_name=tool_call.tool_name,
                    success=True,
                    result=result
                )
            else:
                return ToolResult(
                    tool_name=tool_call.tool_name,
                    success=False,
                    result=None,
                    error=f"未知工具: {tool_call.tool_name}"
                )
        except Exception as e:
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=False,
                result=None,
                error=str(e)
            )


# 使用示例
if __name__ == "__main__":
    # 创建协调器
    thinking_engine = SimpleThinkingEngine()
    tool_executor = SimpleToolExecutor()
    coordinator = Coordinator(thinking_engine, tool_executor)
    
    # 进行交互
    response = coordinator.start_interaction("今天天气怎么样？")
    print(f"回复: {response}")
    
    response2 = coordinator.start_interaction("你好")
    print(f"回复: {response2}")