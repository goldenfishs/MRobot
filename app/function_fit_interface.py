from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QFileDialog, QLabel
from PyQt5.QtCore import Qt
from qfluentwidgets import TitleLabel, BodyLabel
import pandas as pd
import io

class FunctionFitInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("functionFitInterface")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        # 左侧：数据输入区
        left_layout = QVBoxLayout()
        left_layout.setSpacing(16)

        left_layout.addWidget(TitleLabel("数据输入/导入"))
        self.dataEdit = QTextEdit()
        self.dataEdit.setPlaceholderText("输入数据，每行格式：x,y")
        left_layout.addWidget(self.dataEdit)

        btn_layout = QHBoxLayout()
        import_btn = QPushButton("导入 Excel")
        import_btn.clicked.connect(self.import_excel)
        export_btn = QPushButton("导出 Excel")
        export_btn.clicked.connect(self.export_excel)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(export_btn)
        left_layout.addLayout(btn_layout)

        fit_btn = QPushButton("拟合并绘图")
        fit_btn.clicked.connect(self.fit_and_plot)
        left_layout.addWidget(fit_btn)

        main_layout.addLayout(left_layout, 1)

        # 右侧：图像展示区
        right_layout = QVBoxLayout()
        right_layout.setSpacing(16)
        right_layout.addWidget(TitleLabel("函数拟合图像"))

        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas, stretch=1)

        self.resultLabel = BodyLabel("")
        right_layout.addWidget(self.resultLabel)

        main_layout.addLayout(right_layout, 2)

    def import_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入 Excel", "", "Excel Files (*.xlsx *.xls)")
        if path:
            df = pd.read_excel(path)
            text = "\n".join(f"{row[0]},{row[1]}" for row in df.values)
            self.dataEdit.setText(text)

    def export_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 Excel", "", "Excel Files (*.xlsx)")
        if path:
            data = self.parse_data()
            if data is not None:
                df = pd.DataFrame(data, columns=["x", "y"])
                df.to_excel(path, index=False)

    def parse_data(self):
        lines = self.dataEdit.toPlainText().strip().split('\n')
        data = []
        for line in lines:
            try:
                x, y = map(float, line.split(','))
                data.append([x, y])
            except Exception:
                continue
        return data if data else None

    def fit_and_plot(self):
        data = self.parse_data()
        if not data:
            self.resultLabel.setText("数据格式错误或为空")
            return
        import numpy as np
        import matplotlib.pyplot as plt

        x = np.array([d[0] for d in data])
        y = np.array([d[1] for d in data])
        # 简单线性拟合
        coeffs = np.polyfit(x, y, 1)
        y_fit = np.polyval(coeffs, x)
        self.ax.clear()
        self.ax.scatter(x, y, label="原始数据")
        self.ax.plot(x, y_fit, color='r', label=f"拟合: y={coeffs[0]:.3f}x+{coeffs[1]:.3f}")
        self.ax.legend()
        self.canvas.draw()
        self.resultLabel.setText(f"拟合公式: y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}")