# PC操作行为分析

#### 介绍
专注于行为数据分析的项目，提供Win系统计算机操作行为识别、跟踪及分析工具，适用于安全监控、用户行为研究等领域。

#### 软件架构
操作行为收集软件由Python语言编写，主要包括以下模块：

- 数据采集模块：采集操作行为数据，包括鼠标、键盘、屏幕、剪贴板、进程、窗口等信息。
    1. 模块类型：
        1) 鼠标跟踪模块：采集鼠标移动、点击、滚轮等信息。
        2) 键盘跟踪模块：采集键盘按键等信息。
        3) 剪贴板跟踪模块：采集剪贴板内容。
        4) 进程跟踪模块：采集进程创建、结束等信息。
        5) 窗口跟踪模块：采集窗口创建、关闭、切换等信息。
    2. 每个模块均在独立线程中运行。
        1) 不同线程通过事件通知机制进行通信。
    3. 日志生成：
        1) 定期生成。
        2) 暂存于各个监控模块的日志缓冲区。
        3) 等待日志收集模块定期收集，收集后清空缓冲区。
    4. 监控触发：
        1) 以固定间隔时间循环触发。
        2) 模块间存在连携触发关系，如鼠标点击触发窗口跟踪。

- 日志收集模块：定期从数据采集模块获取数据并将数据存储到日志文件中。
    1. 日志文件格式为JSON格式，暂时存储在本地磁盘。
    2. 日志收集流程：
        1) 定期从各个监控模块的日志缓冲区获取数据。
            1) 先向所有监控模块询问是否能够收集日志。
            2) 若所有监控模块都可以收集日志，则将数据从各个监控模块的日志缓冲区获取，并将数据合并后存储到日志文件中。
        2) 若有监控模块不能收集日志，将该模块进行标记，等待一段时间后重新尝试。
            1) 当被标记的模块变为可收集状态时，立即通知日志收集模块重新尝试。
        3) 将数据存储到日志文件中。

- 系统时钟模块：主线程处于非暂停状态时，时钟走字。其他模块通过从系统时钟获取的时间协调工作。
        
- 系统协调模块：集中管控各个模块的运行，确保各模块之间数据交换及运行时状态同步。
    1. 其他模块均在系统协调模块中实例化。
    2. 控制系统运行的线程事件均在系统协调模块中进行定义与管理。