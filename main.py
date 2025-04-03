from Modules.System import SysManager

def main():
    sys_manager = SysManager()  # 实例化系统管理器
    sys_manager.run_system()  # 启动监控系统

if __name__ == "__main__":
    main()