from typing import Any, Dict, List, Optional
import importlib
from loguru import logger

from scheduler.scheduler import scheduler


class SchedulerTool:
    """调度器工具：用于添加、移除、列出和管理定时任务。

    使用示例:
      - 添加任务:
          execute(action='add', func_path='my_module:my_func', trigger='interval', trigger_args={'seconds':30}, job_id='job1')
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
        func_path: Optional[str] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """执行调度操作。

        Args:
            action: 操作类型: 'add'|'remove'|'list'|'start'|'shutdown'
            job_id: 任务 id（删除或指定 id 时使用；添加时可选）
            trigger: APScheduler trigger 类型: 'date'|'interval'|'cron'
            trigger_args: 传递给 trigger 的参数（例如 {'seconds':10} 或 {'hour':'12'})
            func_path: 要调度的可调用路径，格式 'module:callable' 或 'module.callable'
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
                if not func_path:
                    raise ValueError("添加任务需要参数 'func_path'，格式 'module:callable' 或 'module.callable'")

                if ":" in func_path:
                    module_name, func_name = func_path.split(":", 1)
                elif "." in func_path:
                    module_name, func_name = func_path.rsplit(".", 1)
                else:
                    raise ValueError("无法解析 func_path: 请使用 'module:callable' 或 'module.callable' 格式")
                module_name = "tools." + module_name
                module = importlib.import_module(module_name)
                func = getattr(module, func_name)

                job = scheduler.add_job(
                    func,
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

        except Exception as e:
            logger.exception("SchedulerTool 执行失败")
            return {"error": str(e)}
