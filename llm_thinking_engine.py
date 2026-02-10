from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import json
import os
from config.settings import settings
from openai import OpenAI

# 假设这些是从主流程定义中导入的
from coordinator import InteractionContext, ActionType
from coordinator import Thought, ToolCall


@dataclass
class LLMConfig:
    """LLM配置类"""
    api_key: Optional[str] = None
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "deepseek-v3.2"
    enable_thinking: bool = True
    temperature: float = 0.7
    max_tokens: int = 2048


class LLMThinkingEngine:
    """LLM驱动的思考引擎实现"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        初始化LLMThinkingEngine
        
        Args:
            config: LLM配置对象，如果为None则使用默认配置
        """
        self.config = config or LLMConfig()
        self._init_client()
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        api_key = self.config.api_key or settings.LLM_API_KEY
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.config.base_url,
        )
    
    def think(self, context: InteractionContext) -> Thought:
        """
        基于LLM进行思考，返回下一步的行动
        
        Args:
            context: 当前交互上下文
            
        Returns:
            Thought: 思考结果，包含行动类型和内容
        """
        # 构建适用于LLM的消息
        messages = self._build_messages(context)
        
        # 调用LLM进行思考
        thinking_content, response_content = self._call_llm(messages)
        
        # 解析LLM的响应
        thought = self._parse_llm_response(
            response_content, 
            thinking_content, 
            context
        )
        
        return thought
    
    def _build_messages(self, context: InteractionContext) -> list[Dict[str, str]]:
        """
        构建发送给LLM的消息

        Args:
            context: 交互上下文

        Returns:
            消息列表，包含系统提示、历史和当前输入
        """
        messages = []
        
        # 系统提示
        system_prompt = self._get_system_prompt()
        messages.append({"role": "system", "content": system_prompt})
        
        # 添加对话历史
        # 如果有完整的对话历史，直接使用
        if context.conversation_history:
            # 对话历史中可能包含之前的完整对话
            for msg in context.conversation_history:
                messages.append(msg)
        
        # 添加当前轮次之前的思考链中的交互
        for thought in context.thought_chain:
            # 添加上一个思考结果
            if thought.action_type == ActionType.CALL_TOOL:
                tool_call = thought.action_content
                messages.append({
                    "role": "assistant",
                    "content": f"我决定调用工具：{tool_call.tool_name}，参数为：{tool_call.parameters}，原因是：{tool_call.reason}"
                })
            else:
                messages.append({
                    "role": "assistant",
                    "content": f"我的回复是：{thought.action_content}"
                })
        
        # 添加工具结果（如果有）
        if context.tool_results:
            for tool_result in context.tool_results:
                if tool_result.success:
                    messages.append({
                        "role": "user",
                        "content": f"工具'{tool_result.tool_name}'执行成功，结果为：{tool_result.result}"
                    })
                else:
                    messages.append({
                        "role": "user",
                        "content": f"工具'{tool_result.tool_name}'执行失败，错误信息：{tool_result.error}"
                    })
        
        # 添加当前用户输入（如果这是第一次思考或需要继续思考）
        if not context.thought_chain or context.tool_results:
            # 如果没有历史或最后一个结果是工具结果，需要询问LLM下一步
            if context.tool_results:
                messages.append({
                    "role": "user",
                    "content": f"基于上述工具执行结果，请决定下一步的行动。原始用户请求是：{context.user_input}"
                })
            else:
                messages.append({
                    "role": "user",
                    "content": context.user_input
                })
        
        return messages
    
    def _get_system_prompt(self) -> str:
        """
        获取系统提示词
        
        Returns:
            系统提示词
        """
        prompt_path = os.path.join(
            os.path.dirname(__file__), 
            "prompts", 
            "system_prompt.txt"
        )
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            # 如果文件不存在，返回默认提示词
            return """你是一个智能助理的决策引擎。你需要分析用户的请求，并决定下一步的行动。

你有三种可能的行动：
1. DIRECT_REPLY：直接回复用户
2. CALL_TOOL：调用工具来完成任务
3. ASK_USER：询问用户以获取更多信息

请以JSON格式输出你的决策。"""
    
    def _call_llm(self, messages: list[Dict[str, str]]) -> tuple[str, str]:
        """
        调用LLM API
        
        Args:
            messages: 消息列表
            
        Returns:
            (thinking_content, response_content): 思考内容和响应内容
        """
        thinking_content = ""
        response_content = ""
        
        try:
            completion = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                extra_body={"enable_thinking": self.config.enable_thinking},
                stream=True
            )
            
            # 流式处理响应
            for chunk in completion:
                delta = chunk.choices[0].delta
                
                # 收集思考内容
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    thinking_content += delta.reasoning_content
                
                # 收集响应内容
                if hasattr(delta, "content") and delta.content:
                    response_content += delta.content
            
        except Exception as e:
            # 错误处理
            response_content = f"调用LLM时出错：{str(e)}"
        
        return thinking_content, response_content
    
    def _parse_llm_response(
        self, 
        response_content: str, 
        thinking_content: str,
        context: InteractionContext
    ) -> Thought:
        """
        解析LLM的响应并转换为Thought对象
        
        Args:
            response_content: LLM的响应内容
            thinking_content: LLM的思考内容
            context: 交互上下文
            
        Returns:
            Thought: 解析后的思考对象
        """
        try:
            # 尝试从响应中提取JSON
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                parsed = json.loads(json_str)
            else:
                # 如果没有JSON格式，使用默认回复
                parsed = {
                    "action_type": "DIRECT_REPLY",
                    "action_content": response_content,
                    "confidence": 0.5,
                    "reasoning": thinking_content or "无法完全理解请求"
                }
            
            # 转换action_type字符串为枚举
            action_type_str = parsed.get("action_type", "DIRECT_REPLY").upper()
            try:
                action_type = ActionType[action_type_str]
            except KeyError:
                action_type = ActionType.DIRECT_REPLY
            
            # 处理action_content
            action_content = parsed.get("action_content", "")
            
            # 如果是工具调用，将其转换为ToolCall对象
            if action_type == ActionType.CALL_TOOL and isinstance(action_content, dict):
                action_content = ToolCall(
                    tool_name=action_content.get("tool_name", ""),
                    parameters=action_content.get("parameters", {}),
                    reason=action_content.get("reason", "")
                )
            
            # 创建Thought对象
            thought = Thought(
                action_type=action_type,
                action_content=action_content,
                confidence=float(parsed.get("confidence", 0.5)),
                reasoning=parsed.get("reasoning", thinking_content)
            )
            
            return thought
            
        except Exception as e:
            # 解析失败时返回默认回复
            return Thought(
                action_type=ActionType.DIRECT_REPLY,
                action_content=f"处理请求时出错：{str(e)}，原始响应：{response_content}",
                confidence=0.3,
                reasoning=f"解析错误：{str(e)}"
            )
    
    def set_config(self, config: LLMConfig):
        """更新LLM配置"""
        self.config = config
        self._init_client()