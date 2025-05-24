import sys
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox,
    QLabel, QTableWidget, QTableWidgetItem, QFileDialog, QTextEdit,
    QComboBox, QMessageBox, QHeaderView
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PolyFitApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MRobot 多项式拟合工具")
        self.resize(1440, 1280)
        self.setFont(QFont("微软雅黑", 11))
        self.center()

        self.data_x = []
        self.data_y = []
        self.last_coeffs = None
        self.last_xmin = None
        self.last_xmax = None

        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)
        main_layout.addLayout(left_layout, 0)
        main_layout.addLayout(right_layout, 1)

        # 数据输入区
        self.table = QTableWidget(0, 2)
        self.table.setFont(QFont("Consolas", 11))
        self.table.setHorizontalHeaderLabels(["x", "y"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        left_layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.add_row_btn = QPushButton("添加数据")
        self.add_row_btn.setStyleSheet("color: #333;")
        self.add_row_btn.clicked.connect(self.add_point_row)
        btn_row.addWidget(self.add_row_btn)

        self.del_row_btn = QPushButton("删除选中行")
        self.del_row_btn.setStyleSheet("color: #333;")
        self.del_row_btn.clicked.connect(self.delete_selected_rows)
        btn_row.addWidget(self.del_row_btn)
        left_layout.addLayout(btn_row)

        # 导入导出按钮区
        file_btn_row = QHBoxLayout()
        self.import_btn = QPushButton("导入Excel文件")
        self.import_btn.setStyleSheet("font-weight: bold; color: #333;")
        self.import_btn.clicked.connect(self.load_excel)
        file_btn_row.addWidget(self.import_btn)

        self.export_btn = QPushButton("导出Excel文件")
        self.export_btn.setStyleSheet("font-weight: bold; color: #333;")
        self.export_btn.clicked.connect(self.export_excel_and_plot)
        file_btn_row.addWidget(self.export_btn)
        left_layout.addLayout(file_btn_row)

        # 拟合参数区
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("多项式阶数:"))
        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 10)
        self.order_spin.setValue(2)
        param_layout.addWidget(self.order_spin)
        left_layout.addLayout(param_layout)

        self.fit_btn = QPushButton("拟合并显示")
        self.fit_btn.setStyleSheet("font-weight: bold; color: #333;")
        self.fit_btn.clicked.connect(self.fit_and_plot)
        left_layout.addWidget(self.fit_btn)

        # 输出区
        self.output = QTextEdit()
        self.output.setReadOnly(False)
        self.output.setFont(QFont("Consolas", 10))
        self.output.setMaximumHeight(150)
        left_layout.addWidget(self.output)

        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("输出代码格式:"))
        self.code_type = QComboBox()
        self.code_type.addItems(["C", "C++", "Python"])
        code_layout.addWidget(self.code_type)
        self.gen_code_btn = QPushButton("生成函数代码")
        self.gen_code_btn.setStyleSheet("color: #333;")
        self.gen_code_btn.clicked.connect(self.generate_code)
        code_layout.addWidget(self.gen_code_btn)
        left_layout.addLayout(code_layout)

        # 拟合曲线区
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def add_point_row(self, x_val="", y_val=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(x_val)))
        self.table.setItem(row, 1, QTableWidgetItem(str(y_val)))

    def delete_selected_rows(self):
        selected = self.table.selectionModel().selectedRows()
        for idx in sorted(selected, reverse=True):
            self.table.removeRow(idx.row())

    def load_excel(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)")
        if file:
            try:
                data = pd.read_excel(file, usecols=[0, 1])
                new_x = data.iloc[:, 0].values.tolist()
                new_y = data.iloc[:, 1].values.tolist()
                for x, y in zip(new_x, new_y):
                    self.add_point_row(x, y)
                QMessageBox.information(self, "成功", "数据导入成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取Excel失败: {e}")

    def export_excel_and_plot(self):
        file, _ = QFileDialog.getSaveFileName(self, "导出Excel文件", "", "Excel Files (*.xlsx *.xls)")
        if file:
            x_list, y_list = [], []
            for row in range(self.table.rowCount()):
                try:
                    x = float(self.table.item(row, 0).text())
                    y = float(self.table.item(row, 1).text())
                    x_list.append(x)
                    y_list.append(y)
                except Exception:
                    continue
            if not x_list or not y_list:
                QMessageBox.warning(self, "导出失败", "没有可导出的数据！")
                return
            df = pd.DataFrame({'x': x_list, 'y': y_list})
            try:
                df.to_excel(file, index=False)
                # 导出同名png图像
                png_file = file
                if png_file.lower().endswith('.xlsx') or png_file.lower().endswith('.xls'):
                    png_file = png_file.rsplit('.', 1)[0] + '.png'
                else:
                    png_file = png_file + '.png'
                self.figure.savefig(png_file, dpi=150, bbox_inches='tight')
                QMessageBox.information(self, "导出成功", f"数据已成功导出到Excel文件！\n图像已导出为：{png_file}")
            except Exception as e:
                QMessageBox.critical(self, "导出错误", f"导出Excel或图像失败: {e}")

    def get_manual_points(self):
        x_list, y_list = [], []
        for row in range(self.table.rowCount()):
            try:
                x = float(self.table.item(row, 0).text())
                y = float(self.table.item(row, 1).text())
                x_list.append(x)
                y_list.append(y)
            except Exception:
                continue
        return x_list, y_list

    def fit_and_plot(self):
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
        matplotlib.rcParams['axes.unicode_minus'] = False
        matplotlib.rcParams['font.size'] = 14
        self.data_x, self.data_y = self.get_manual_points()
        try:
            order = int(self.order_spin.value())
        except ValueError:
            QMessageBox.warning(self, "输入错误", "阶数必须为整数！")
            return
        n_points = len(self.data_x)
        if n_points < order + 1:
            QMessageBox.warning(self, "数据不足", "数据点数量不足以拟合该阶多项式！")
            return
        x = np.array(self.data_x, dtype=np.float64)
        y = np.array(self.data_y, dtype=np.float64)
        x_min, x_max = x.min(), x.max()
        if x_max - x_min == 0:
            QMessageBox.warning(self, "数据错误", "所有x值都相同，无法拟合！")
            return
        try:
            coeffs = np.polyfit(x, y, order)
        except Exception as e:
            QMessageBox.critical(self, "拟合错误", f"多项式拟合失败：{e}")
            return
        poly = np.poly1d(coeffs)
        expr = "y = " + " + ".join([f"{c:.6g}*x^{order-i}" for i, c in enumerate(coeffs)])
        self.output.setPlainText(f"{expr}\n")
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.scatter(x, y, color='red', label='数据点')
        x_fit = np.linspace(x_min, x_max, 200)
        y_fit = poly(x_fit)
        ax.plot(x_fit, y_fit, label='拟合曲线')
        ax.legend()
        self.canvas.draw()
        self.last_coeffs = coeffs
        self.last_xmin = x_min
        self.last_xmax = x_max

    def generate_code(self):
        if self.last_coeffs is None:
            QMessageBox.warning(self, "未拟合", "请先拟合数据！")
            return
        coeffs = self.last_coeffs
        code_type = self.code_type.currentText()
        if code_type == "C":
            code = self.create_c_function(coeffs)
        elif code_type == "C++":
            code = self.create_cpp_function(coeffs)
        else:
            code = self.create_py_function(coeffs)
        self.output.setPlainText(code)

    def create_c_function(self, coeffs):
        lines = ["#include <math.h>", "double polynomial(double x) {", "    return "]
        n = len(coeffs)
        terms = []
        for i, c in enumerate(coeffs):
            exp = n - i - 1
            if exp == 0:
                terms.append(f"{c:.8g}")
            elif exp == 1:
                terms.append(f"{c:.8g}*x")
            else:
                terms.append(f"{c:.8g}*pow(x,{exp})")
        lines[-1] += " + ".join(terms) + ";"
        lines.append("}")
        return "\n".join(lines)

    def create_cpp_function(self, coeffs):
        lines = ["#include <cmath>", "double polynomial(double x) {", "    return "]
        n = len(coeffs)
        terms = []
        for i, c in enumerate(coeffs):
            exp = n - i - 1
            if exp == 0:
                terms.append(f"{c:.8g}")
            elif exp == 1:
                terms.append(f"{c:.8g}*x")
            else:
                terms.append(f"{c:.8g}*pow(x,{exp})")
        lines[-1] += " + ".join(terms) + ";"
        lines.append("}")
        return "\n".join(lines)

    def create_py_function(self, coeffs):
        n = len(coeffs)
        lines = ["def polynomial(x):", "    return "]
        terms = []
        for i, c in enumerate(coeffs):
            exp = n - i - 1
            if exp == 0:
                terms.append(f"{c:.8g}")
            elif exp == 1:
                terms.append(f"{c:.8g}*x")
            else:
                terms.append(f"{c:.8g}*x**{exp}")
        lines[-1] += " + ".join(terms)
        return "\n".join(lines)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PolyFitApp()
    win.show()
    sys.exit(app.exec_())