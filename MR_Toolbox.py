import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QSizePolicy, QFrame
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

class ToolboxUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MRobot 工具箱")
        self.setMinimumSize(900, 600)
        self.init_ui()

    def init_ui(self):
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 左半区
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setSpacing(20)

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(180, 80)
        logo_pixmap.fill(Qt.transparent)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setText("MRobot")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFont(QFont("Arial", 28, QFont.Bold))
        logo_label.setStyleSheet("color: #3498db;")
        logo_label.setFixedHeight(100)
        left_layout.addWidget(logo_label)

        # 按钮区
        self.buttons = []
        button_names = ["功能一", "功能二", "功能三", "功能四"]
        for idx, name in enumerate(button_names):
            btn = QPushButton(name)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2980b9; color: white;
                    border-radius: 8px; font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #3498db;
                }
            """)
            btn.clicked.connect(lambda checked, i=idx: self.switch_function(i))
            self.buttons.append(btn)
            left_layout.addWidget(btn)

        left_layout.addStretch(1)

        # 文本输出框
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setFixedHeight(80)
        self.output_box.setStyleSheet("background: #f4f6f7; border-radius: 6px;")
        left_layout.addWidget(self.output_box)

        left_frame.setMaximumWidth(240)
        main_layout.addWidget(left_frame)

        # 右半区
        self.stack = QStackedWidget()
        for i in range(len(button_names)):
            page = QLabel(f"这里是 {button_names[i]} 的功能界面")
            page.setAlignment(Qt.AlignCenter)
            page.setFont(QFont("微软雅黑", 20))
            self.stack.addWidget(page)
        main_layout.addWidget(self.stack)

        # 默认输出
        self.output_box.append("欢迎使用 MRobot 工具箱！请选择左侧功能。")

    def switch_function(self, idx):
        self.stack.setCurrentIndex(idx)
        self.output_box.append(f"已切换到功能：{self.buttons[idx].text()}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ToolboxUI()
    win.show()
    sys.exit(app.exec_())