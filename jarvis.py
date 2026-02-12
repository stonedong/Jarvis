from coordinator import Coordinator
from default_tool_executor import DefaultToolExecutor
from llm_thinking_engine import LLMThinkingEngine
from conversation_manager import ConversationManager
import os
from utils import logger
from scheduler import scheduler


def save_conversation(manager: ConversationManager, save_dir: str = "."):
    """保存对话历史到文件"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    filepath = os.path.join(save_dir, f"{manager.conversation_id}.json")
    manager.save_to_file(filepath)
    return filepath

def start_scheduler():
    """启动调度器"""
    scheduler.start()

def main():
    logger.info("启动智能助理...")

    # 启动调度器（如果需要定时任务功能）
    start_scheduler()

    # 创建思考引擎实例
    thinking_engine = LLMThinkingEngine()

    # 创建工具执行器实例
    tool_executor = DefaultToolExecutor(tools_package_path="tools")

    # 列出所有工具
    all_tools_info = tool_executor.get_all_tools_info()
    logger.info(f"所有工具信息: {all_tools_info}")
    
    # 创建会话管理器
    conversation_manager = ConversationManager(max_history_length=20)
    
    # 创建协调器实例，并传入会话管理器
    coordinator = Coordinator(
        thinking_engine,
        tool_executor,
        conversation_manager=conversation_manager
    )
    
    print("=" * 60)
    print("欢迎使用智能助理！支持连续对话功能")
    print("=" * 60)
    print("你好！我可以为你提供帮助。")
    print("命令说明：")
    print("  - 'exithistory'：保存对话历史并退出")
    print("  - 'loadhistory'：从文件加载对话历史")
    print("  - 'clearhistory'：清除对话历史")
    print("  - 'showhistory'：显示对话历史摘要")
    print("  - 'stats'：显示对话统计信息")
    print("  - '退出'：直接退出（不保存）")
    print("  - 'list': 列出所有定时任务")
    print("  - 'delete <job_id>': 删除指定定时任务")
    print("=" * 60)
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n你: ").strip()
            
            if not user_input:
                continue
            
            # 处理特殊命令
            if user_input == "退出":
                print("结束对话。")
                break
            
            elif user_input == "exithistory":
                # 保存对话历史并退出
                filepath = save_conversation(conversation_manager, "conversation_logs")
                print(f"对话历史已保存到: {filepath}")
                print("结束对话。")
                break
            
            elif user_input == "clearhistory":
                # 清除对话历史
                conversation_manager.clear_history()
                print("✓ 对话历史已清除")
                continue
            
            elif user_input == "showhistory":
                # 显示对话历史
                print("\n--- 对话历史摘要 ---")
                print(conversation_manager.get_conversation_summary())
                print("--- 结束 ---\n")
                continue
            
            elif user_input == "stats":
                # 显示对话统计
                stats = conversation_manager.get_statistics()
                print("\n--- 对话统计信息 ---")
                for key, value in stats.items():
                    print(f"{key}: {value}")
                print("--- 结束 ---\n")
                continue
            
            elif user_input == "loadhistory":
                # 加载对话历史
                print("请输入要加载的对话文件路径: ")
                filepath = input().strip()
                if os.path.exists(filepath):
                    conversation_manager = ConversationManager.load_from_file(filepath)
                    coordinator.conversation_manager = conversation_manager
                    print(f"✓ 对话历史已从 {filepath} 加载")
                else:
                    print(f"✗ 文件不存在: {filepath}")
                continue

            elif user_input == "list":
                # 列出所有定时任务
                jobs = scheduler.get_jobs()
                if not jobs:
                    print("没有定时任务。")
                else:
                    print("\n--- 定时任务列表 ---")
                    for job in jobs:
                        print(f"ID: {job.id}, 下一次运行时间: {job.next_run_time}, 触发器: {job.trigger}")
                    print("--- 结束 ---\n")
                continue

            elif user_input.startswith("delete "):
                # 删除指定定时任务
                job_id = user_input.split(" ", 1)[1].strip()
                try:
                    scheduler.remove_job(job_id)
                    print(f"✓ 定时任务 {job_id} 已删除")
                except Exception as e:
                    print(f"✗ 无法删除定时任务 {job_id}: {str(e)}")
                continue
            
            # 处理用户输入，使用连续对话模式
            print("系统: 正在处理...", end="", flush=True)
            response = coordinator.start_interaction(
                user_input,
                use_conversation_manager=True
            )
            print("\r系统: ", end="")
            print(response)
        
        except KeyboardInterrupt:
            print("\n\n检测到中断信号...")
            confirm = input("是否保存对话历史？(y/n): ").strip().lower()
            if confirm == 'y':
                filepath = save_conversation(conversation_manager, "conversation_logs")
                print(f"对话历史已保存到: {filepath}")
            print("结束对话。")
            break
        
        except Exception as e:
            print(f"发生错误: {str(e)}")
            print("请重试或输入其他命令")


if __name__ == "__main__":
    main()
