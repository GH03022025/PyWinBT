import threading
import queue
import time
from typing import Callable


class SysClock(threading.Thread):  # 系统时钟，精度1毫秒
    def __init__(self, running_event: threading.Event, end_event: threading.Event):
        super().__init__()
        self.running_event = running_event  # 持续运行事件
        self.end_event = end_event  # 线程结束事件
        self.time: float = 0.0  # 当前时间
        self.lock = threading.Lock()  # 线程锁
        self.start_time: float = time.monotonic()  # 初始化时设置 start_time
        self.daemon = True  # 开启守护线程

    def run(self) -> None:
        while not self.end_event.is_set():  # 线程未结束
            if self.running_event.is_set():  # 允许持续运行
                current_time = time.monotonic()  # 获取当前时间
                with self.lock:  # 线程锁，保证安全
                    self.time += current_time - self.start_time  # 累计时间
                    self.start_time = current_time  # 更新 start_time
            else:
                self.start_time = time.monotonic()  # 重置 start_time

            time.sleep(0.001)  # 精度1毫秒

    def get_time(self) -> float:  # 外部调用，获取当前时间
        with self.lock:
            return self.time


class SysManager:  # 系统管理器
    def __init__(self, uid: str = "1000"):
        from Modules.Functions import (
            Logger,
            ProcessMonitor,
            FocusWinMonitor,
            MouseMonitor,
            KeyboardMonitor,
            ClipboardMonitor,
        )  # 导入各个模块，防止循环导入

        self.uid = uid  # 用户唯一标识符
        self.log_queue = queue.Queue()
        self.running_event = threading.Event()
        self.end_event = threading.Event()

        self.module_registry = {}  # 所有模块注册表

        self.sys_clock = SysClock(self.running_event, self.end_event)
        self.module_registry["SysClock"] = self.sys_clock  # 注册系统时钟

        monitor_registry = {
            "ProcessMonitor": ProcessMonitor,
            "FocusWinMonitor": FocusWinMonitor,
            "MouseMonitor": MouseMonitor,
            "KeyboardMonitor": KeyboardMonitor,
            "ClipboardMonitor": ClipboardMonitor,
        }  # 初始化监控器注册表

        for monitor_key, monitor_instance in monitor_registry.items():
            monitor_registry[monitor_key] = monitor_instance(
                self.running_event,
                self.end_event,
                self.sys_clock,
                self.module_registry,
                self.uid,
            )  # 实例化各个监控器

        self.module_registry["Monitor"] = monitor_registry  # 在模块注册表中注册监控器

        self.logger = Logger(
            self.log_queue,
            self.running_event,
            self.end_event,
            self.sys_clock,
            self.module_registry,
        )  # 实例化日志模块

        self.module_registry["Logger"] = self.logger  # 注册日志模块

        self.running_event.set()

        self.sleep_time = 3.0  # 休眠时间

    def operate_modules_in_module_registry(
        self,
        module_registry: dict,
        method: Callable,  # 传入模块注册表和待执行函数
    ) -> None:  # 递归启动模块
        for item in module_registry.values():  # 遍历模块注册表
            if isinstance(item, dict):  # 若为子注册表，则递归
                self.operate_modules_in_module_registry(item, method)
            else:  # 若为模块实例，则执行传入函数
                method(item)  # 对模块实例执行传入函数

    def run_system(self) -> None:  # 启动监控系统
        self.operate_modules_in_module_registry(
            self.module_registry, lambda x: x.start()
        )  # 启动所有模块

        try:
            while not self.end_event.is_set():  # 持续运行
                time.sleep(self.sleep_time)  # 休眠一定时间，暂时用来模拟因外部状况中断
                self.running_event.clear()  # 暂时停止运行

                choice = input(
                    f"\n监控系统已运行{self.sleep_time}秒，是否继续？(y继续/n结束/其他延后): "
                ).lower()
                if choice == "n":  # 结束
                    self.shutdown()
                    break
                elif choice == "y":  # 继续
                    self.running_event.set()
                else:  # 延后
                    pass
        except (KeyboardInterrupt, EOFError):
            self.shutdown()

    def shutdown(self) -> None:  # 安全关闭系统
        self.end_event.set()
        self.running_event.set()  # 唤醒等待线程

        print("\n正在关闭，等待日志处理完毕...")
        self.log_queue.join()  # 等待日志处理完成

        self.operate_modules_in_module_registry(
            self.module_registry, lambda x: x.join(timeout=1.0)
        )  # 等待所有模块结束

        print("监控系统已安全关闭")
