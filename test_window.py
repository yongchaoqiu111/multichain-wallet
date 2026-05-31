import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("测试窗口")
window.setGeometry(100, 100, 400, 300)
label = QLabel("如果看到这个窗口，说明PyQt6正常工作", window)
label.setGeometry(50, 50, 300, 30)
window.show()
print("窗口已显示")
sys.exit(app.exec())
