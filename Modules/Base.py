import threading
import queue
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime


class ModuleBase(threading.Thread, ABC):  # 功能性模块基类
    MODULE_IDENTIFIER: Optional[str] = None  # 必须定义模块标识符

    def __init__(self):
        super().__init__()

        self.trigger_event = threading.Event()  # 该事件被设置后模块立即执行主循环
        self.daemon = True  # 开启守护线程

    def verify_consts_and_params(self) -> None:  # 验证常量和参数
        if self.sleep_time is None:  # 必须定义休眠时间
            raise NotImplementedError("sleep_time must be provided")

        if self.MODULE_IDENTIFIER is None:  # 必须规定模块标识符
            raise NotImplementedError("MODULE_IDENTIFIER must be provided")

        if self.running_event is None:  # 必须提供运行事件
            raise NotImplementedError("running_event must be provided")

        if self.end_event is None:  # 必须提供结束事件
            raise NotImplementedError("end_event must be provided")

        if self.sys_clock is None:  # 必须提供系统时钟
            raise NotImplementedError("sys_clock must be provided")

        if self.module_registry is None:  # 必须提供模块注册表
            raise NotImplementedError("module_registry must be provided")

    def run(self) -> None:  # 主循环
        while not self.end_event.is_set():  # 线程未结束
            self.running_event.wait()  # 且允许持续运行

            if self.end_event.is_set():  # 立即响应线程结束
                break

            start_time = self.sys_clock.get_time()  # 记录本次循环开始时间

            try:
                self.perform_task()  # 尝试执行模块任务
            except Exception as e:
                self.handle_task_failure(str(e))  # 处理任务异常

            self.__dynamic_sleep(start_time)  # 动态休眠，需传入本轮循环开始时间

    def __dynamic_sleep(self, start_time: float) -> None:  # 动态休眠
        while not self.end_event.is_set():  # 响应线程结束
            elapsed = self.sys_clock.get_time() - start_time  # 计算已休眠时间
            remaining = self.sleep_time - elapsed  # 计算剩余休眠时间

            if self.trigger_event.wait(max(remaining, 0)):  # 响应外部触发
                self.trigger_event.clear()
                break

            if remaining <= 0:  # 正常休眠结束
                break

    def trigger(self) -> None:  # 外部触发
        self.trigger_event.set()  # 设置立即触发事件

    @abstractmethod
    def perform_task(self) -> None:  # 模块任务，子类必须实现
        raise NotImplementedError("perform_task() is not implemented")

    def handle_task_failure(self, error_msg: str) -> None:  # 处理任务异常，可以覆写
        print(f"Module: {self.MODULE_IDENTIFIER} failed: {error_msg}")


class MonitorBase(ModuleBase):  # 监控器基类
    def __init__(self):
        super().__init__()
        self.buffer_queue = queue.Queue()  # Queue作为日志缓冲区，解决多线程问题
        self.ready_to_flush_event = threading.Event()  # 日志缓冲区就绪事件

    def verify_consts_and_params(self):
        super().verify_consts_and_params()
        if self.uid is None:  # 必须定义唯一标识符
            raise NotImplementedError("uid must be provided")

    def add_log_to_buffer(self, log_details: Dict[str, Any]) -> None:
        log = {
            "uid": self.uid,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "monitor_type": self.MODULE_IDENTIFIER,
            "details": log_details,
        }
        self.buffer_queue.put(log)  # 将日志添加进缓冲队列

    def can_get_and_flush_buffer(self) -> bool:  # 检查是否可以取出并清空缓存
        return True

    def get_and_flush_buffer(self) -> List[Dict[str, Any]]:  # 取出并清空缓存
        logs = []  # 用列表暂存
        while not self.buffer_queue.empty():
            logs.append(self.buffer_queue.get())  # 一条一条取出
        self.buffer_queue.task_done()
        return logs

    def perform_task(self) -> None:  # 实现抽象方法
        self.perform_monitor_task()  # 两层抽象，方便之后拓展

    @abstractmethod
    def perform_monitor_task(self) -> None:  # 监控器任务子类必须实现
        raise NotImplementedError("perform_monitor_task() is not implemented")
