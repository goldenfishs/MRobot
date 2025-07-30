from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout, QFileDialog, QHeaderView
from qfluentwidgets import TitleLabel, BodyLabel, SubtitleLabel, StrongBodyLabel, HorizontalSeparator, PushButton, TreeWidget, InfoBar, FluentIcon, Dialog, FlowLayout, FluentWindow, MSFluentWindow, SplitFluentWindow

class Demo(SplitFluentWindow):

    def __init__(self):
        super().__init__()
        layout = FlowLayout(self, needAni=True)  # 启用动画
        self.resize(250, 300)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    sys.exit(app.exec_())