from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from qfluentwidgets import TitleLabel, BodyLabel

class CodeGenerateInterface(QWidget):
    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        self.setObjectName("CodeGenerateInterface")
        self.project_path = project_path

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)

        title = TitleLabel("代码生成页面")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = BodyLabel(f"当前工程路径: {self.project_path}")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)