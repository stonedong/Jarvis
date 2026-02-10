"""
Conversation Management Module
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """单条消息对象"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式（用于LLM API）"""
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class ConversationContext:
    """对话上下文 - 保持跨轮对话的状态信息"""
    last_tool_results: List[Dict[str, Any]] = field(default_factory=list)
    last_user_intent: Optional[str] = None
    last_assistant_action: Optional[str] = None
    context_summary: Optional[str] = None
    
    def update(
        self,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        user_intent: Optional[str] = None,
        assistant_action: Optional[str] = None,
        context_summary: Optional[str] = None
    ):
        """更新上下文信息"""
        if tool_results is not None:
            self.last_tool_results = tool_results
        if user_intent is not None:
            self.last_user_intent = user_intent
        if assistant_action is not None:
            self.last_assistant_action = assistant_action
        if context_summary is not None:
            self.context_summary = context_summary


class ConversationManager:
    """对话管理器 - 管理完整的对话历史和上下文"""
    
    def __init__(self, max_history_length: int = 20):
        """
        初始化会话管理器
        
        Args:
            max_history_length: 保留的最大历史消息数
        """
        self.messages: List[Message] = []
        self.context = ConversationContext()
        self.max_history_length = max_history_length
        self.conversation_id = self._generate_conversation_id()
        self.start_time = datetime.now()
        
        # logger.info(f"New conversation session: {self.conversation_id}")
    
    def _generate_conversation_id(self) -> str:
        """生成会话ID"""
        return f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        添加消息到对话历史
        
        Args:
            role: 消息角色
            content: 消息内容
            metadata: 消息元数据
            
        Returns:
            添加的消息对象
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        
        # if超过最大长度，移除最早的消息（保留最近的对话）
        if len(self.messages) > self.max_history_length:
            removed = self.messages.pop(0)
            # logger.debug(f"Removed early message: {removed.role.value}")
        
        # logger.debug(f"Added message [{message.role.value}]: {content[:50]}...")
        return message
    
    def add_user_message(self, content: str) -> Message:
        """添加用户消息"""
        return self.add_message(MessageRole.USER, content)
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """添加助手消息"""
        return self.add_message(MessageRole.ASSISTANT, content, metadata)
    
    def add_system_message(self, content: str) -> Message:
        """添加系统消息"""
        return self.add_message(MessageRole.SYSTEM, content)
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        获取对话历史（格式化为LLM API所需的格式）
        
        Returns:
            消息列表，每条消息包含role和content
        """
        return [msg.to_dict() for msg in self.messages]
    
    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """
        获取最近的N条消息
        
        Args:
            count: 消息数量
            
        Returns:
            最近的消息列表
        """
        return self.messages[-count:] if self.messages else []
    
    def get_conversation_summary(self) -> str:
        """
        获取对话摘要（简化后的对话历史）
        
        Returns:
            对话摘要字符串
        """
        if not self.messages:
            return "尚无对话记录"
        
        summary_parts = []
        for msg in self.get_recent_messages(10):
            role = "用户" if msg.role == MessageRole.USER else "助手"
            summary_parts.append(f"[{role}] {msg.content[:80]}")
        
        return "\n".join(summary_parts)
    
    def clear_history(self):
        """Clear all conversation history"""
        self.messages.clear()
        self.context = ConversationContext()
        # logger.info(f"Cleared conversation history: {self.conversation_id}")
    
    def update_context(
        self,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        user_intent: Optional[str] = None,
        assistant_action: Optional[str] = None,
        context_summary: Optional[str] = None
    ):
        """
        更新对话上下文
        
        Args:
            tool_results: 工具执行结果
            user_intent: 用户意图
            assistant_action: 助手动作
            context_summary: 上下文摘要
        """
        self.context.update(
            tool_results=tool_results,
            user_intent=user_intent,
            assistant_action=assistant_action,
            context_summary=context_summary
        )
        # logger.debug("Update conversation context")
    
    def get_context_for_llm(self) -> Dict[str, Any]:
        """
        获取用于LLM的完整上下文信息
        
        Returns:
            包含历史和上下文的字典
        """
        return {
            "conversation_history": self.get_conversation_history(),
            "recent_context": {
                "last_tool_results": self.context.last_tool_results,
                "last_user_intent": self.context.last_user_intent,
                "last_assistant_action": self.context.last_assistant_action,
            },
            "conversation_summary": self.context.context_summary
        }
    
    def save_to_file(self, filepath: str) -> None:
        """
        将对话历史保存到文件
        
        Args:
            filepath: 保存文件的路径
        """
        try:
            data = {
                "conversation_id": self.conversation_id,
                "start_time": self.start_time.isoformat(),
                "messages": [
                    {
                        "role": msg.role.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata
                    }
                    for msg in self.messages
                ],
                "context": {
                    "last_tool_results": self.context.last_tool_results,
                    "last_user_intent": self.context.last_user_intent,
                    "last_assistant_action": self.context.last_assistant_action,
                    "context_summary": self.context.context_summary
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # logger.info(f"Conversation history saved: {filepath}")
        except Exception as e:
            # logger.error(f"Failed to save conversation history: {str(e)}")
            pass
    
    @staticmethod
    def load_from_file(filepath: str) -> "ConversationManager":
        """
        从文件加载对话历史
        
        Args:
            filepath: 加载文件的路径
            
        Returns:
            ConversationManager实例
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            manager = ConversationManager()
            manager.conversation_id = data["conversation_id"]
            manager.start_time = datetime.fromisoformat(data["start_time"])
            
            for msg_data in data["messages"]:
                msg = Message(
                    role=MessageRole(msg_data["role"]),
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    metadata=msg_data.get("metadata", {})
                )
                manager.messages.append(msg)
            
            context_data = data.get("context", {})
            manager.context = ConversationContext(
                last_tool_results=context_data.get("last_tool_results", []),
                last_user_intent=context_data.get("last_user_intent"),
                last_assistant_action=context_data.get("last_assistant_action"),
                context_summary=context_data.get("context_summary")
            )
            
            # logger.info(f"Conversation history loaded: {filepath}")
            return manager
        except Exception as e:
            # logger.error(f"Failed to load conversation history: {str(e)}")
            return ConversationManager()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取对话统计信息
        
        Returns:
            统计信息字典
        """
        user_messages = [m for m in self.messages if m.role == MessageRole.USER]
        assistant_messages = [m for m in self.messages if m.role == MessageRole.ASSISTANT]
        
        return {
            "conversation_id": self.conversation_id,
            "total_messages": len(self.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "start_time": self.start_time.isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds()
        }
