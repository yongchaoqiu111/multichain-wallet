import sys
print("Python version:", sys.version)

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow
    print("PyQt6 导入成功")
    
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("钱包工具测试")
    window.setGeometry(200, 200, 500, 400)
    window.show()
    
    print("窗口已创建，即将显示...")
    result = app.exec()
    print(f"程序退出，代码: {result}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
