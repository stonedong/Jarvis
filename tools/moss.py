from conversation_manager import ConversationManager
from coordinator import Coordinator
from default_tool_executor import DefaultToolExecutor
from llm_thinking_engine import LLMThinkingEngine
from utils import logger


class Moss:
    """MOSS，莫斯，一个基于LLM的智能体，能够执行复杂任务"""
    def execute(self, task: str) -> str:
        """
        执行莫斯任务
        :param task: 任务描述 类型为字符串，描述需要莫斯完成的任务
        """
        logger.info(f"莫斯收到任务: {task}")
        # 创建思考引擎实例
        thinking_engine = LLMThinkingEngine(system_prompt_file="moss_system_prompt.txt")
        # 创建工具执行器实例
        tool_executor = DefaultToolExecutor(tools_package_path="tools")
        # 创建会话管理器
        conversation_manager = ConversationManager(max_history_length=20)
        # 创建协调器实例，并传入会话管理器
        coordinator = Coordinator(
            thinking_engine,
            tool_executor,
            conversation_manager=conversation_manager
        )
        response = coordinator.start_interaction(
                task,
                use_conversation_manager=True
            )
        logger.info(f"莫斯完成了任务: {response}")
        return "SUCCESS"