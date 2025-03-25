import threading
import queue
import time
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime


class MonitorBase(threading.Thread, ABC):
    """监控线程基类"""

    DEFAULT_SLEEP_TIME: Optional[int] = None
    MONITOR_TYPE: Optional[str] = None

    def __init__(
        self,
        log_queue: queue.Queue,
        running_event: threading.Event,
        end_event: threading.Event,
        uid: str,
        module_controller: "ModuleController",
        sys_clock: "SysClock",
    ):
        super().__init__()
        if self.DEFAULT_SLEEP_TIME is None:
            raise NotImplementedError("DEFAULT_SLEEP_TIME is not defined")

        if self.MONITOR_TYPE is None:
            raise NotImplementedError("MONITOR_TYPE is not defined")

        self.log_queue = log_queue  # 日志队列
        self.running_event = running_event  # 允许运行事件
        self.end_event = end_event  # 线程结束事件
        self.ready_to_flush_event = threading.Event()  # 日志缓冲区就绪事件
        self.trigger_event = threading.Event()  # 立即行动事件

        self.monitor_type = self.MONITOR_TYPE  # 监控类型唯一标识符
        self._base_sleep_time = self.DEFAULT_SLEEP_TIME  # 保持原有sleep_time定义
        self.module_controller = module_controller  # 模块控制器对象
        self.buffer_queue = queue.Queue()  # Queue作为日志缓冲区，解决多线程问题
        self.uid = uid  # 用户唯一标识符
        self.sys_clock = sys_clock  # 系统时钟对象
        self.daemon = True  # 守护线程

    def _dynamic_wait(self, start_time: float) -> None:
        """动态等待逻辑"""
        while not self.end_event.is_set():
            # elapsed = time.monotonic() - start_time
            elapsed = self.sys_clock.get_time() - start_time
            remaining = self._base_sleep_time - elapsed

            # 优先响应触发事件
            if self.trigger_event.wait(max(remaining, 0)):
                self.trigger_event.clear()
                time.sleep(0.001)  # 略微错开时间，方便记录日志产生顺序
                break

            if remaining <= 0:
                break

    def run(self) -> None:
        """主监控循环"""
        while not self.end_event.is_set():
            self.running_event.wait()
            if self.end_event.is_set():  # 及时结束事件
                break
            # start_time = time.monotonic()
            start_time = self.sys_clock.get_time()
            try:
                self.monitor_task()
            except Exception as e:
                self._add_log_error(str(e))

            self._dynamic_wait(start_time)

    def _add_log(self, log_details: Dict[str, Any]) -> None:
        """统一日志格式"""
        log = {
            "uid": self.uid,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "monitor_type": self.monitor_type,
            "details": log_details,
        }
        # self.buffer_queue.put(json.dumps(log))
        self.buffer_queue.put(log)
        # log_entry = self.buffer_queue.get()
        # print(log_entry)

    def _add_log_error(self, error_msg: str) -> None:
        """记录错误日志"""
        self._log(
            {
                "event": {"type": "system", "action": "error"},
                "message": error_msg,
            }
        )

    def can_flush(self) -> bool:
        """检查是否可以立即执行日志缓冲区"""
        # print(f"{self.monitor_type}: can_flush: {not self.buffer_queue.empty()}")
        return not self.buffer_queue.empty()  # 使用empty()方法检查队列是否为空

    def flush_buffer(self) -> List[Dict[str, Any]]:
        """取出并清空缓冲区"""
        logs = []
        while not self.buffer_queue.empty():
            logs.append(self.buffer_queue.get())
        self.buffer_queue.task_done()
        return logs

    def trigger(self):
        """外部触发立即执行"""
        self.trigger_event.set()

    @abstractmethod
    def monitor_task(self) -> None:
        """具体监控任务（由子类实现）"""
        raise NotImplementedError("monitor_task() is not implemented")


class ProcessMonitor(MonitorBase):
    DEFAULT_SLEEP_TIME = 4
    MONITOR_TYPE = "process"

    def monitor_task(self) -> None:
        self._add_log(
            {
                "event": "start",
                "pid": "1234",
                "process_name": "test.exe",
                "running_time": "1234",
                "foreground_time": "567",
            }
        )


class FocusWinMonitor(MonitorBase):
    DEFAULT_SLEEP_TIME = 1
    MONITOR_TYPE = "window"

    def monitor_task(self) -> None:
        self._add_log(
            {
                "event": "focus_change",
                "pid": "1234",
                "process_name": "test.exe",
                "win_size": "1280x720",
                "win_title": "test.exe",
            }
        )


class MouseClickMonitor(MonitorBase):
    DEFAULT_SLEEP_TIME = 0.1
    MONITOR_TYPE = "mouse"

    def monitor_task(self) -> None:
        self._add_log(
            {
                "event": "click",
                "pid": "1234",
                "process_name": "test.exe",
                "win_size": "1280x720",
                "win_title": "test.exe",
                "coordinate": "100,200",
            }
        )
        # 触发窗口监控立即执行
        module_controller = self.module_controller
        for win_monitor in module_controller.get_monitors("window"):
            win_monitor.trigger()


class KeyboardInputMonitor(MonitorBase):
    DEFAULT_SLEEP_TIME = 0.1
    MONITOR_TYPE = "keyboard"

    def monitor_task(self) -> None:
        self._add_log(
            {
                "event": "input",
                "pid": "1234",
                "process_name": "test.exe",
                "win_size": "1280x720",
                "win_title": "test.exe",
                "content": "hello world",
            }
        )


class Logger(threading.Thread):
    """日志记录器"""

    def __init__(
        self,
        log_queue: queue.Queue,
        running_event: threading.Event,
        end_event: threading.Event,
        monitors: List[MonitorBase],
        sys_clock: "SysClock",
        check_interval: float,
    ):
        super().__init__()
        self.log_queue = log_queue
        self.running_event = running_event
        self.end_event = end_event
        self.monitors = monitors
        self.sys_clock = sys_clock
        self.check_interval = check_interval
        self.daemon = True

    def run(self):
        collected = []
        """修改后的运行逻辑"""
        while not self.end_event.is_set():
            self.running_event.wait()
            if self.end_event.is_set():  # 及时结束事件
                break

            # 第一阶段：检查所有模块状态
            all_ready = all(monitor.can_flush() for monitor in self.monitors)

            if all_ready:
                # 第二阶段：原子性获取所有日志
                for monitor in self.monitors:
                    collected.extend(monitor.flush_buffer())
                collected_sorted = self.sort_by_timestamp(collected)
                for log in collected_sorted:
                    print(log)
                with open("logs.json", "w", encoding="utf-8") as file:
                    json.dump(collected_sorted, file, ensure_ascii=False, indent=4)
                # 第三阶段：清空缓冲区
                collected.clear()

            # 等待重试
            time.sleep(self.check_interval)

    def sort_by_timestamp(self, logs):
        return sorted(
            logs,
            key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S.%f"),
        )


class SysClock(threading.Thread):
    """系统时钟，精度为1毫秒"""

    def __init__(self, running_event: threading.Event, end_event: threading.Event):
        super().__init__()
        self.running_event = running_event
        self.end_event = end_event
        self.time = 0.0
        self.lock = threading.Lock()
        self.start_time = time.monotonic()  # 初始化时设置 start_time

    def run(self) -> None:
        while not self.end_event.is_set():
            if self.running_event.is_set():
                current_time = time.monotonic()
                with self.lock:
                    self.time += current_time - self.start_time
                    self.start_time = current_time  # 只有在系统运行时更新 start_time
            else:
                self.start_time = time.monotonic()  # 系统暂停时，更新 start_time 为当前时间，以便重新开始时不累加暂停时间
            time.sleep(0.001)

    def get_time(self) -> float:
        with self.lock:
            return self.time


class ModuleController:
    """模块管理器"""

    def __init__(self, uid: str = "1000"):
        self.log_queue = queue.Queue()
        self.running_event = threading.Event()
        self.end_event = threading.Event()

        self.sys_clock = SysClock(self.running_event, self.end_event)

        self.monitors = [
            cls(
                self.log_queue,
                self.running_event,
                self.end_event,
                uid,
                self,
                self.sys_clock,
            )
            for cls in [
                ProcessMonitor,
                FocusWinMonitor,
                MouseClickMonitor,
                KeyboardInputMonitor,
            ]
        ]

        self.logger = Logger(
            self.log_queue,
            self.running_event,
            self.end_event,
            self.monitors,
            self.sys_clock,
            12,
        )

        # self.logger = Logger(self.log_queue, self.end_event)
        self.running_event.set()

    def start(self) -> None:
        """启动监控系统"""
        for monitor in self.monitors:
            monitor.start()
        self.logger.start()
        self.sys_clock.start()

        try:
            while not self.end_event.is_set():
                time.sleep(24)
                self.running_event.clear()

                choice = input(
                    "\n系统监控已运行3秒，是否继续？(y继续/n结束/其他延后): "
                ).lower()
                if choice == "n":
                    self.shutdown()
                    break
                elif choice == "y":
                    self.running_event.set()
                else:
                    pass
        except (KeyboardInterrupt, EOFError):
            self.shutdown()

    def shutdown(self) -> None:
        """安全关闭系统"""
        self.end_event.set()
        self.running_event.set()  # 唤醒等待线程

        print("\n系统监控正在关闭...")
        self.log_queue.join()  # 等待日志处理完成

        for monitor in self.monitors:
            monitor.join(timeout=1)
        self.logger.join(timeout=1)
        self.sys_clock.join(timeout=1)
        print("系统监控已安全关闭")

    def get_monitors(self, monitor_type: str) -> list:
        return [m for m in self.monitors if m.monitor_type == monitor_type]


if __name__ == "__main__":
    monitor_system = ModuleController()
    monitor_system.start()
