import threading
import queue
import json
import time
from typing import Any
from datetime import datetime


import psutil


from Modules.Base import ModuleBase, MonitorBase
from Modules.System import SysClock


class Logger(ModuleBase):  # 日志记录器
    MODULE_IDENTIFIER = "Logger"  # 定义模块标识符

    def __init__(
        self,
        log_queue: queue.Queue,  # 日志队列
        running_event: threading.Event,  # 持续运行事件
        end_event: threading.Event,  # 线程结束事件
        sys_clock: SysClock,  # 系统时钟，来自 System.py 中的 SysClock 类
        module_registry: dict[str, dict | Any],  # 模块注册表
        sleep_time: float = 4.0,  # 休眠时间，默认4秒
    ):
        super().__init__()

        self.log_queue = log_queue  # 日志队列
        self.running_event = running_event  # 持续运行事件
        self.end_event = end_event  # 线程结束事件
        self.sys_clock = sys_clock  # 系统时钟
        self.module_registry = module_registry  # 模块注册表
        self.sleep_time = sleep_time  # 休眠时间，默认12秒
        self.logs_collected = []  # 日志收集列表

    def perform_task(self):  # 实现抽象方法
        self.collect_logs()  # 收集日志

    def collect_logs(self):  # 收集日志
        vote_for_flush = {}  # 初始化投票收集器

        for monitor in self.module_registry["Monitor"].values():  # 收集投票
            vote_for_flush.update(monitor.can_get_and_flush_buffer())

        reject_collect = any(vote == "Disagree" for vote in vote_for_flush.values())
        all_skip_collect = all(vote == "Skip" for vote in vote_for_flush.values())

        if not reject_collect and not all_skip_collect:
            self.logs_collected += sum(
                (
                    monitor.get_and_flush_buffer()
                    for monitor in self.module_registry["Monitor"].values()
                    if vote_for_flush[monitor.MODULE_IDENTIFIER] == "Agree"
                ),
                [],
            )  # 使用列表推导式获取所有同意的日志，并使用sum函数合并列表

            logs_sorted = self.sort_logs_by_timestamp(
                self.logs_collected
            )  # 按时间戳排序

            for log in logs_sorted:  # 打印日志，监控用
                print(log)

            with open("logs.json", "a", encoding="utf-8") as file:  # 保存日志
                json.dump(logs_sorted, file, ensure_ascii=False, indent=4)  # 日志写入

            self.logs_collected.clear()  # 清空日志列表

    def sort_logs_by_timestamp(self, logs):  # 将获取的日志按照时间排序
        return sorted(
            logs,
            key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S.%f"),
        )  # 返回排序完成的日志


class ProcessMonitor(MonitorBase):  # 示例进程监控器
    MODULE_IDENTIFIER = "Process"  # 定义模块标识符

    def __init__(
        self,
        running_event: threading.Event,  # 持续运行事件
        end_event: threading.Event,  # 线程结束事件
        sys_clock: SysClock,  # 系统时钟，来自 System.py 中的 SysClock 类
        module_registry: dict[str, dict | Any],  # 模块注册表
        uid: str,
        sleep_time: float = 1.0,  # 休眠时间
    ):
        super().__init__()
        self.running_event = running_event
        self.end_event = end_event
        self.sys_clock = sys_clock
        self.module_registry = module_registry
        self.sleep_time = sleep_time
        self.uid = uid

        self.verify_consts_and_params()  # 验证常量和参数

        self.history_pids = set()  # 历史进程ID集合，pid也可以作为key
        self.history_processes = {}  # 历史进程集合，可通过key访问进程信息

    def perform_monitor_task(self):  # 实现抽象方法
        current_pids = set(psutil.pids())  # 当前进程ID集合
        new_pids = current_pids - self.history_pids  # 新启动的进程ID集合
        ended_pids = self.history_pids - current_pids  # 结束的进程ID集合
        self.history_pids = current_pids  # 更新历史进程ID集合
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        for pid in new_pids:  # 遍历新启动的进程
            try:
                process = psutil.Process(pid)  # 获取进程对象
                process_name = process.name()  # 进程名称
                create_time = round(process.create_time(), 3)  # 进程创建时间，保留三位小数
                self.history_processes[pid] = {
                    "process_name": process_name,
                    "create_time": create_time,
                }  # 记录进程信息
                self.add_log_to_buffer(
                    {
                        "pid": pid,
                        "process_name": process_name,
                        "event": "create",
                        "create_time": create_time,
                    },
                    timestamp,
                )  # 记录日志
            except psutil.NoSuchProcess as e:
                self.add_log_to_buffer(
                    {
                        "pid": pid,
                        "event": "error",
                        "error_msg": str(e),
                    },
                    timestamp,
                )  # 记录错误日志

        for pid in ended_pids:  # 遍历结束的进程
            try:
                process_info = self.history_processes.pop(pid)  # 拿出进程信息
                process_name = process_info["process_name"]  # 进程名称
                runtime = round(
                    time.time() - process_info["create_time"], 3
                )  # 进程运行时间，保留三位小数
                self.add_log_to_buffer(
                    {
                        "pid": pid,
                        "process_name": process_name,
                        "event": "kill",
                        "runtime": runtime,
                    },
                    timestamp,
                )  # 记录日志
            except KeyError as e:
                self.add_log_to_buffer(
                    {
                        "pid": pid,
                        "event": "error",
                        "error_msg": str(e),
                    },
                    timestamp,
                )  # 记录错误日志


class FocusWinMonitor(MonitorBase):  # 示例焦点窗口监控器
    MODULE_IDENTIFIER = "FocusWin"  # 定义模块标识符

    def __init__(
        self,
        running_event: threading.Event,  # 持续运行事件
        end_event: threading.Event,  # 线程结束事件
        sys_clock: SysClock,  # 系统时钟，来自 System.py 中的 SysClock 类
        module_registry: dict[str, dict | Any],  # 模块注册表
        uid: str,
        sleep_time: float = 100.0,  # 休眠时间
    ):
        super().__init__()
        self.running_event = running_event
        self.end_event = end_event
        self.sys_clock = sys_clock
        self.module_registry = module_registry
        self.sleep_time = sleep_time
        self.uid = uid
        self.verify_consts_and_params()  # 验证常量和参数

    def perform_monitor_task(self):  # 实现抽象方法
        self.add_log_to_buffer({"details": "FocusWin monitor task performed"})


class MouseMonitor(MonitorBase):  # 示例鼠标监控器
    MODULE_IDENTIFIER = "Mouse"  # 定义模块标识符

    def __init__(
        self,
        running_event: threading.Event,  # 持续运行事件
        end_event: threading.Event,  # 线程结束事件
        sys_clock: SysClock,  # 系统时钟，来自 System.py 中的 SysClock 类
        module_registry: dict[str, dict | Any],  # 模块注册表
        uid: str,
        sleep_time: float = 100.0,  # 休眠时间
    ):
        super().__init__()
        self.running_event = running_event
        self.end_event = end_event
        self.sys_clock = sys_clock
        self.module_registry = module_registry
        self.sleep_time = sleep_time
        self.uid = uid
        self.verify_consts_and_params()  # 验证常量和参数

    def perform_monitor_task(self):  # 实现抽象方法
        self.add_log_to_buffer({"details": "Mouse monitor task performed"})
        self.module_registry["Monitor"][
            "ProcessMonitor"
        ].trigger()  # 立即触发 Process 监控器
        self.module_registry["Monitor"][
            "FocusWinMonitor"
        ].trigger()  # 立即触发 FocusWin 监控器


class KeyboardMonitor(MonitorBase):  # 示例键盘监控器
    MODULE_IDENTIFIER = "Keyboard"  # 定义模块标识符

    def __init__(
        self,
        running_event: threading.Event,  # 持续运行事件
        end_event: threading.Event,  # 线程结束事件
        sys_clock: SysClock,  # 系统时钟，来自 System.py 中的 SysClock 类
        module_registry: dict[str, dict | Any],  # 模块注册表
        uid: str,
        sleep_time: float = 1.0,  # 休眠时间
    ):
        super().__init__()
        self.running_event = running_event
        self.end_event = end_event
        self.sys_clock = sys_clock
        self.module_registry = module_registry
        self.sleep_time = sleep_time
        self.uid = uid
        self.verify_consts_and_params()  # 验证常量和参数

    def perform_monitor_task(self):  # 实现抽象方法
        self.add_log_to_buffer({"details": "Keyboard monitor task performed"})
        self.module_registry["Monitor"][
            "ProcessMonitor"
        ].trigger()  # 立即触发 Process 监控器
        self.module_registry["Monitor"][
            "FocusWinMonitor"
        ].trigger()  # 立即触发 FocusWin 监控器


class ClipboardMonitor(MonitorBase):  # 示例剪贴板监控器
    MODULE_IDENTIFIER = "Clipboard"  # 定义模块标识符

    def __init__(
        self,
        running_event: threading.Event,  # 持续运行事件
        end_event: threading.Event,  # 线程结束事件
        sys_clock: SysClock,  # 系统时钟，来自 System.py 中的 SysClock 类
        module_registry: dict[str, dict | Any],  # 模块注册表
        uid: str,
        sleep_time: float = 1.0,  # 休眠时间
    ):
        super().__init__()
        self.running_event = running_event
        self.end_event = end_event
        self.sys_clock = sys_clock
        self.module_registry = module_registry
        self.sleep_time = sleep_time
        self.uid = uid
        self.verify_consts_and_params()  # 验证常量和参数

    def perform_monitor_task(self):  # 实现抽象方法
        self.add_log_to_buffer({"details": "Clipboard monitor task performed"})
