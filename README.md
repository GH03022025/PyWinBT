# PyWinBT - PC行为分析监控系统框架

## 项目简介
PyWinBT是一个基于Python的多线程PC行为分析监控系统框架，用于收集和分析用户计算机操作行为数据。系统采用模块化设计，支持多种监控类型，包括进程、窗口焦点、鼠标、键盘和剪贴板活动。

## 功能特点
- **多线程架构**：高效并发执行多个监控任务
- **模块化设计**：易于扩展新的监控模块
- **精确计时**：毫秒级系统时钟同步
- **多种监控类型**：
  - 进程活动监控
  - 焦点窗口跟踪
  - 鼠标操作记录
  - 键盘输入监控
  - 剪贴板内容追踪
- **日志系统**：结构化日志存储为JSON格式
- **优雅关闭**：支持安全终止所有监控线程

## 系统架构
系统采用模块注册表(module_registry)统一管理所有模块，核心组件包括：

```
SysManager (主控制器)
├── module_registry (模块注册表)
│   ├── SysClock (系统时钟)
│   ├── Logger (日志记录器)
│   └── Monitor (监控器分类)
│       ├── ProcessMonitor (进程监控)
│       ├── FocusWinMonitor (焦点窗口监控)
│       ├── MouseMonitor (鼠标监控)
│       ├── KeyboardMonitor (键盘监控)
│       └── ClipboardMonitor (剪贴板监控)
├── running_event (运行控制事件)
└── end_event (结束控制事件)
```

module_registry是核心字典结构，用于：
- 注册和访问所有系统模块
- 提供模块间的通信桥梁
- 支持递归操作所有模块

## 安装要求
- Python 3.7+
- 依赖库：暂无

## 使用说明
1. 克隆项目仓库
2. 安装依赖：暂无
3. 运行主程序：`python main.py`
4. 系统启动后，按提示操作：
   - 输入`y`继续监控
   - 输入`n`安全关闭系统
5. 日志文件将保存在`logs.json`中

## 模块说明
### 1. SysManager
系统主控制器，负责初始化和协调所有监控模块。

### 2. SysClock
系统时钟，提供精确的时间同步服务。

### 3. Logger
日志记录器，收集、排序和保存各监控模块的日志数据。

### 4. 监控模块
所有监控模块继承自`MonitorBase`基类：
- **ProcessMonitor**：监控系统进程活动
- **FocusWinMonitor**：跟踪焦点窗口变化
- **MouseMonitor**：记录鼠标点击和移动
- **KeyboardMonitor**：捕获键盘输入
- **ClipboardMonitor**：监控剪贴板内容变化

## 开发指南
### 添加新监控模块规范

#### 1. 模块基本要求
- 必须继承`MonitorBase`基类
- 必须定义`MODULE_IDENTIFIER`类变量作为唯一标识
- 必须实现`perform_monitor_task()`方法

#### 2. 必须实现的接口
```python
class CustomMonitor(MonitorBase):
    MODULE_IDENTIFIER = "CustomMonitor"  # 必须定义
    
    def __init__(self, running_event, end_event, sys_clock, module_registry, uid):
        super().__init__()
        # 初始化代码
        
    def perform_monitor_task(self):
        """核心监控逻辑"""
        # 必须实现
        self.add_log_to_buffer({
            "details": {...}  # 监控数据
        })
```

#### 3. 注册流程
1. 在`SysManager.__init__()`中添加监控器到注册表：
```python
monitor_registry = {
    "CustomMonitor": CustomMonitor
    # 其他监控器...
}
```

#### 4. 配置参数规范
- `sleep_time`: 监控间隔(秒)
- `uid`: 用户唯一标识
- 其他自定义参数需通过`__init__`传入

#### 5. 日志格式要求
```json
{
  "uid": "1000",
  "timestamp": "YYYY-MM-DD HH:MM:SS.ffffff",
  "monitor_type": "CustomMonitor",
  "details": {
    // 自定义监控数据
  }
}
```

#### 6. 测试建议
- 单元测试需覆盖：
  - 监控数据采集
  - 异常处理
  - 线程安全
- 集成测试需验证：
  - 模块注册流程
  - 与其他模块的交互
  - 日志格式一致性

#### 完整示例
```python
class MouseMonitor(MonitorBase):  # 示例鼠标监控器
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
        self.module_registry["Monitor"]["Process"].trigger()  # 立即触发 FocusWin 监控器
        self.module_registry["Monitor"]["FocusWin"].trigger()  # 立即触发 FocusWin 监控器
```

### 扩展系统功能
1. 创建新类继承`ModuleBase`
2. 实现`perform_task()`方法
3. 在`SysManager`中注册新模块

## 示例日志
```json
{
  "uid": "1000",
  "timestamp": "2023-01-01 12:00:00.123456",
  "monitor_type": "Keyboard",
  "details": {
    "key": "A",
    "action": "press"
  }
}
```
