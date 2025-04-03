import threading
import queue
import json
from typing import List, Any
from datetime import datetime


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
        sleep_time: float = 12.0,  # 休眠时间，默认12秒
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
        all_monitors_ready = all(
            monitor.can_get_and_flush_buffer()
            for monitor in self.module_registry["Monitor"].values()
        )  # 通过模块注册表中的监视器注册表检查模块状态

        if all_monitors_ready:  # 所有模块都可以获取日志
            for monitor in self.module_registry["Monitor"].values():  # 逐个获取日志
                self.logs_collected += monitor.get_and_flush_buffer()  # 获取日志

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


class ProcessMonitor(MonitorBase):  # 进程监控器
    MODULE_IDENTIFIER = "Process"  # 定义模块标识符

    def __init__(
        self,
        running_event: threading.Event,  # 持续运行事件
        end_event: threading.Event,  # 线程结束事件
        sys_clock: SysClock,  # 系统时钟，来自 System.py 中的 SysClock 类
        module_registry: dict[str, dict | Any],  # 模块注册表
        uid: str,
        sleep_time: float = 5.0,  # 休眠时间
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
        self.add_log_to_buffer({"details": "Process monitor task performed"})


class FocusWinMonitor(MonitorBase):  # 焦点窗口监控器
    MODULE_IDENTIFIER = "FocusWin"  # 定义模块标识符

    def __init__(
        self,
        running_event: threading.Event,  # 持续运行事件
        end_event: threading.Event,  # 线程结束事件
        sys_clock: SysClock,  # 系统时钟，来自 System.py 中的 SysClock 类
        module_registry: dict[str, dict | Any],  # 模块注册表
        uid: str,
        sleep_time: float = 5.0,  # 休眠时间
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


class MouseMonitor(MonitorBase):  # 鼠标监控器
    MODULE_IDENTIFIER = "Mouse"  # 定义模块标识符

    def __init__(
        self,
        running_event: threading.Event,  # 持续运行事件
        end_event: threading.Event,  # 线程结束事件
        sys_clock: SysClock,  # 系统时钟，来自 System.py 中的 SysClock 类
        module_registry: dict[str, dict | Any],  # 模块注册表
        uid: str,
        sleep_time: float = 2.0,  # 休眠时间
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


class KeyboardMonitor(MonitorBase):  # 键盘监控器
    MODULE_IDENTIFIER = "Keyboard"  # 定义模块标识符

    def __init__(
        self,
        running_event: threading.Event,  # 持续运行事件
        end_event: threading.Event,  # 线程结束事件
        sys_clock: SysClock,  # 系统时钟，来自 System.py 中的 SysClock 类
        module_registry: dict[str, dict | Any],  # 模块注册表
        uid: str,
        sleep_time: float = 2.0,  # 休眠时间
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


class ClipboardMonitor(MonitorBase):  # 剪贴板监控器
    MODULE_IDENTIFIER = "Clipboard"  # 定义模块标识符

    def __init__(
        self,
        running_event: threading.Event,  # 持续运行事件
        end_event: threading.Event,  # 线程结束事件
        sys_clock: SysClock,  # 系统时钟，来自 System.py 中的 SysClock 类
        module_registry: dict[str, dict | Any],  # 模块注册表
        uid: str,
        sleep_time: float = 2.0,  # 休眠时间
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
