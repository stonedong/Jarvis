from typing import Any, Dict, List, Optional
import importlib
from utils import logger

from scheduler import scheduler


class SchedulerTool:
    """调度器工具：用于添加、移除、列出和管理定时任务。

    使用示例:
      - 添加任务:
          execute(action='add', func='tool_name', trigger='interval', trigger_args={'seconds':30}, job_id='job1')
      - 列出任务:
          execute(action='list')
      - 删除任务:
          execute(action='remove', job_id='job1')
    """

    def execute(
        self,
        action: str,
        job_id: Optional[str] = None,
        trigger: str = "date",
        trigger_args: Optional[Dict[str, Any]] = None,
        func: Optional[str] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """执行调度操作。

        Args:
            action: 操作类型: 'add'|'remove'|'list'|'start'|'shutdown'
            job_id: 任务 id（删除或指定 id 时使用；添加时可选）
            trigger: APScheduler trigger 类型: 'date'|'interval'|'cron'
            trigger_args: 传递给 trigger 的参数（例如 {'seconds':10} 或 {'hour':'12'})
            func: 要调度的工具，从可用工具中指定，直接给出工具的名字
            args: 位置参数列表
            kwargs: 关键字参数字典

        Returns:
            操作结果说明或任务列表
        """

        trigger_args = trigger_args or {}
        args = args or []
        kwargs = kwargs or {}

        try:
            if action == "add":
                if not func:
                    raise ValueError("添加任务需要参数 'func'")


                module_name = "tools." + func
                module = importlib.import_module(module_name)
                # func = getattr(module, "execute")
                if hasattr(module, "execute"):
                    execute_func = getattr(module, "execute")
                else:
                    # assume class named after func (capitalized) with execute method
                    class_name = func.capitalize()
                    if hasattr(module, class_name):
                        cls = getattr(module, class_name)
                        instance = cls()
                        execute_func = instance.execute
                    else:
                        raise AttributeError(f"Module {module_name} has no execute function or class {class_name}")

                job = scheduler.add_job(
                    execute_func,
                    trigger,
                    args=args,
                    kwargs=kwargs,
                    id=job_id,
                    **trigger_args,
                )

                return {"job_id": job.id, "next_run_time": str(job.next_run_time)}

            elif action == "remove":
                if not job_id:
                    raise ValueError("删除任务需要指定 'job_id'")
                scheduler.remove_job(job_id)
                return {"removed": job_id}

            elif action == "list":
                jobs = scheduler.get_jobs()
                result = []
                for j in jobs:
                    result.append(
                        {
                            "id": j.id,
                            "next_run_time": str(j.next_run_time),
                            "trigger": str(j.trigger),
                        }
                    )
                return result

            elif action == "start":
                scheduler.start()
                return {"started": True}

            elif action == "shutdown":
                scheduler.shutdown(wait=False)
                return {"shutdown": True}

            else:
                raise ValueError(f"未知 action: {action}")

            logger.info(f"SchedulerTool 执行操作完成: {action}，参数: job_id={job_id}, trigger={trigger}, trigger_args={trigger_args}, func={func}, args={args}, kwargs={kwargs}")
        except Exception as e:
            logger.exception("SchedulerTool 执行失败")
            return {"error": str(e)}
