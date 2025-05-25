import sys
import os
import numpy as np
import pandas as pd
import requests
import webbrowser
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QSizePolicy, QFrame, QGraphicsDropShadowEffect,
    QSpinBox, QTableWidget, QTableWidgetItem, QFileDialog, QComboBox, QMessageBox, QHeaderView,
    QGroupBox, QGridLayout, QLineEdit, QTextBrowser, QCheckBox
)
from PyQt5.QtGui import QPixmap, QFont, QIcon, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QTimer, QPointF, pyqtSlot
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView  # 新增
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import QThread
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage


def resource_path(relative_path):
    """兼容PyInstaller打包后资源路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --------- 主页 ---------
class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(32)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fbfd, stop:1 #eaf6fb);
                border-radius: 18px;
            }
        """)

        # 欢迎标题
        title = QLabel("欢迎来到 MRobot 工具箱！")
        title.setFont(QFont("微软雅黑", 26, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2980b9; letter-spacing: 3px;")
        layout.addWidget(title)
        # 设置高度
        title.setFixedHeight(120)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #d6eaf8; background: #d6eaf8; min-height: 2px;")
        layout.addWidget(line)

        # 介绍内容
        desc = QLabel(
            "🤖 本工具箱由青岛理工大学（QUT）机器人战队开发，\n"
            "涵盖沧溟（Robocon）与MOVE（Robomaster）两支队伍。\n\n"
            "集成了常用小工具与助手功能，持续更新中ing！\n"
            "👉 可通过左侧选择不同模块，助力更高效的机器人开发，\n"
            "节约开发时间，减少繁琐操作。\n\n"
            "欢迎反馈建议，共同完善工具箱！"
        )
        desc.setFont(QFont("微软雅黑", 16))
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #34495e;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 作者&版本信息
        info = QLabel(
            "<b>作者：</b> QUT RMer & RCer &nbsp;&nbsp;|&nbsp;&nbsp; "
            "<b>版本：</b> 0.0.2 &nbsp;&nbsp;|&nbsp;&nbsp; "
            "<b>联系方式：</b> QQ群 : 857466609"
        )
        info.setFont(QFont("微软雅黑", 14))
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #7f8c8d; margin-top: 24px;")
        info.setFixedHeight(100)  # 修改为固定高度
        layout.addWidget(info)

        # 页脚
        footer = QLabel("© 2025 MRobot. 保留所有权利。")
        footer.setFont(QFont("微软雅黑", 12))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #b2bec3; margin-top: 18px;")
        footer.setFixedHeight(100)  # 修改为固定高度
        layout.addWidget(footer)

# --------- 功能一：多项式拟合工具页面 ---------
class PolyFitApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("微软雅黑", 15))
        self.data_x = []
        self.data_y = []
        self.last_coeffs = None
        self.last_xmin = None
        self.last_xmax = None

        # 统一背景和边框
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eaf6fb, stop:1 #d6eaf8);
                border-radius: 16px;
                border: 1px solid #d6eaf8;
            }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(18)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(18)
        main_layout.addLayout(left_layout, 0)
        main_layout.addLayout(right_layout, 1)

        # 标题
        title = QLabel("曲线拟合工具")
        # title.setFont(QFont("微软雅黑", 2, QFont.Bold))
        # 设置文字大小  
        title.setFont(QFont("微软雅黑", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2980b9; letter-spacing: 2px;")
        left_layout.addWidget(title)

        # 数据表
        self.table = QTableWidget(0, 2)
        self.table.setFont(QFont("Consolas", 16))
        self.table.setHorizontalHeaderLabels(["x", "y"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #f8fbfd;
                border-radius: 10px;
                border: 1px solid #d6eaf8;
                font-size: 16px;
            }
            QHeaderView::section {
                background-color: #eaf6fb;
                color: #2980b9;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #d6eaf8;
                height: 36px;
            }
        """)
        self.table.setMinimumHeight(200)  # 设置最小高度
        left_layout.addWidget(self.table, stretch=1)  # 让表格尽量撑大

        # 添加/删除行
        btn_row = QHBoxLayout()
        self.add_row_btn = QPushButton("添加数据")
        self.add_row_btn.setFont(QFont("微软雅黑", 20, QFont.Bold))
        self.add_row_btn.setMinimumHeight(44)
        self.add_row_btn.clicked.connect(self.add_point_row)
        self.del_row_btn = QPushButton("删除选中行")
        self.del_row_btn.setFont(QFont("微软雅黑", 20, QFont.Bold))
        self.del_row_btn.setMinimumHeight(44)
        self.del_row_btn.clicked.connect(self.delete_selected_rows)
        for btn in [self.add_row_btn, self.del_row_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #eaf6fb, stop:1 #d6eaf8);
                    color: #2980b9;
                    border-radius: 20px;
                    font-size: 20px;
                    font-weight: 600;
                    padding: 10px 0;
                    border: 1px solid #d6eaf8;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f8fffe, stop:1 #cfe7fa);
                    color: #1a6fae;
                    border: 1.5px solid #b5d0ea;
                }
                QPushButton:pressed {
                    background: #e3f0fa;
                    color: #2471a3;
                    border: 1.5px solid #a4cbe3;
                }
            """)
        btn_row.addWidget(self.add_row_btn)
        btn_row.addWidget(self.del_row_btn)
        left_layout.addLayout(btn_row)

        # 导入/导出
        file_btn_row = QHBoxLayout()
        self.import_btn = QPushButton("导入Excel文件")
        self.import_btn.setFont(QFont("微软雅黑", 18, QFont.Bold))
        self.import_btn.setMinimumHeight(44)
        self.import_btn.clicked.connect(self.load_excel)
        self.export_btn = QPushButton("导出Excel文件")
        self.export_btn.setFont(QFont("微软雅黑", 18, QFont.Bold))
        self.export_btn.setMinimumHeight(44)
        self.export_btn.clicked.connect(self.export_excel_and_plot)
        for btn in [self.import_btn, self.export_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #eaf6fb, stop:1 #d6eaf8);
                    color: #2980b9;
                    border-radius: 20px;
                    font-size: 20px;
                    font-weight: 600;
                    padding: 10px 0;
                    border: 1px solid #d6eaf8;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f8fffe, stop:1 #cfe7fa);
                    color: #1a6fae;
                    border: 1.5px solid #b5d0ea;
                }
                QPushButton:pressed {
                    background: #e3f0fa;
                    color: #2471a3;
                    border: 1.5px solid #a4cbe3;
                }
            """)
        file_btn_row.addWidget(self.import_btn)
        file_btn_row.addWidget(self.export_btn)
        left_layout.addLayout(file_btn_row)

        # 阶数选择
        param_layout = QHBoxLayout()
        label_order = QLabel("多项式阶数:")
        # 文字居中
        label_order.setAlignment(Qt.AlignCenter)
        # 文字加粗
        label_order.setStyleSheet("color: #2980b9;")
        param_layout.addWidget(label_order)
        self.order_spin = QSpinBox()
        self.order_spin.setFont(QFont("微软雅黑", 18))
        self.order_spin.setRange(1, 10)
        self.order_spin.setValue(2)
        self.order_spin.setStyleSheet("""
            QSpinBox {
                background: #f8fbfd;
                border-radius: 10px;
                border: 1px solid #d6eaf8;
                font-size: 18px;
                padding: 4px 12px;
            }
        """)
        param_layout.addWidget(self.order_spin)
        left_layout.addLayout(param_layout)

        # 拟合按钮
        self.fit_btn = QPushButton("拟合并显示")
        self.fit_btn.setFont(QFont("微软雅黑", 20, QFont.Bold))
        self.fit_btn.setMinimumHeight(48)
        self.fit_btn.clicked.connect(self.fit_and_plot)
        self.fit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eaf6fb, stop:1 #d6eaf8);
                color: #2980b9;
                border-radius: 20px;
                font-size: 22px;
                font-weight: 600;
                padding: 12px 0;
                border: 1px solid #d6eaf8;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fffe, stop:1 #cfe7fa);
                color: #1a6fae;
                border: 1.5px solid #b5d0ea;
            }
            QPushButton:pressed {
                background: #e3f0fa;
                color: #2471a3;
                border: 1.5px solid #a4cbe3;
            }
        """)
        left_layout.addWidget(self.fit_btn)
        # 输出区
        self.output = QTextEdit()
        self.output.setReadOnly(False)
        self.output.setFont(QFont("Consolas", 16))
        self.output.setMaximumHeight(160)
        self.output.setStyleSheet("""
            QTextEdit {
                background: #f4f6f7;
                border-radius: 8px;
                border: 1px solid #d6eaf8;
                font-size: 16px;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        # self.table.setFixedHeight(400)  # 设置表格高度为260像素
        left_layout.addWidget(self.output)
        # 代码生成
        code_layout = QHBoxLayout()
        label_code = QLabel("输出代码格式:")
        # label_code.setFont(QFont("微软雅黑", 18, QFont.Bold))
        label_code.setStyleSheet("color: #2980b9;")
        code_layout.addWidget(label_code)
        self.code_type = QComboBox()
        self.code_type.setFont(QFont("微软雅黑", 18))
        self.code_type.addItems(["C", "C++", "Python"])
        self.code_type.setStyleSheet("""
            QComboBox {
                background: #f8fbfd;
                border-radius: 10px;
                border: 1px solid #d6eaf8;
                font-size: 18px;
                padding: 4px 12px;
            }
        """)
        code_layout.addWidget(self.code_type)
        self.gen_code_btn = QPushButton("生成代码")
        self.gen_code_btn.setFont(QFont("微软雅黑", 18, QFont.Bold))
        self.gen_code_btn.setMinimumHeight(44)
        self.gen_code_btn.clicked.connect(self.generate_code)
        self.gen_code_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eaf6fb, stop:1 #d6eaf8);
                color: #2980b9;
                border-radius: 20px;
                font-size: 20px;
                font-weight: 600;
                padding: 10px 0;
                border: 1px solid #d6eaf8;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fffe, stop:1 #cfe7fa);
                color: #1a6fae;
                border: 1.5px solid #b5d0ea;
            }
            QPushButton:pressed {
                background: #e3f0fa;
                color: #2471a3;
                border: 1.5px solid #a4cbe3;
            }
        """)
        code_layout.addWidget(self.gen_code_btn)
        left_layout.addLayout(code_layout)


        # 曲线区加圆角和阴影
        curve_frame = QFrame()
        curve_frame.setStyleSheet("""
            QFrame {
                background: #fff;
                border-radius: 16px;
                border: 1px solid #d6eaf8;
            }
        """)
        curve_shadow = QGraphicsDropShadowEffect(self)
        curve_shadow.setBlurRadius(24)
        curve_shadow.setOffset(0, 4)
        curve_shadow.setColor(Qt.gray)
        curve_frame.setGraphicsEffect(curve_shadow)
        curve_layout = QVBoxLayout(curve_frame)
        curve_layout.setContentsMargins(10, 10, 10, 10)
        self.figure = Figure(figsize=(6, 5))
        self.canvas = FigureCanvas(self.figure)
        curve_layout.addWidget(self.canvas)
        right_layout.addWidget(curve_frame)

        # 默认显示空坐标系
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        # ax.set_title("拟合结果", fontsize=22, fontweight='bold')
        ax.set_xlabel("x", fontsize=18)
        ax.set_ylabel("y", fontsize=18)
        ax.tick_params(labelsize=15)
        # ax.set_title("拟合结果", fontsize=22, fontweight='bold')  # 中文标题
        self.canvas.draw()
        
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
        # ax.set_title("拟合结果", fontsize=22, fontweight='bold')
        ax.set_xlabel("x", fontsize=18)
        ax.set_ylabel("y", fontsize=18)
        ax.scatter(x, y, color='red', label='Data')
        x_fit = np.linspace(x_min, x_max, 200)
        y_fit = poly(x_fit)
        ax.plot(x_fit, y_fit, label='Fit Curve')
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

# --------- 功能二：下载 ---------
class DownloadPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("微软雅黑", 15))
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eaf6fb, stop:1 #d6eaf8);
                border-radius: 18px;
                border: 1px solid #d6eaf8;
            }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 60, 60, 60)
        main_layout.setSpacing(32)

        # 标题
        title = QLabel("常用工具下载")
        title.setFont(QFont("微软雅黑", 26, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2980b9; letter-spacing: 3px; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #d6eaf8; background: #d6eaf8; min-height: 2px;")
        main_layout.addWidget(line)

        # # 说明
        # desc = QLabel("点击下方按钮可直接跳转到常用工具或开发软件的官方下载页面：")
        # desc.setFont(QFont("微软雅黑", 17))
        # desc.setAlignment(Qt.AlignCenter)
        # desc.setStyleSheet("color: #34495e; margin-bottom: 18px;")
        # main_layout.addWidget(desc)

        spacer = QFrame()
        spacer.setFixedHeight(4)  # 可根据需要调整间隔高度
        spacer.setStyleSheet("background: transparent; border: none;")
        main_layout.addWidget(spacer)

        # 小工具类
        tools_tools = [
            ("Geek Uninstaller", "https://geekuninstaller.com/download", "🧹"),
            ("Neat Download Manager", "https://www.neatdownloadmanager.com/index.php/en/", "⬇️"),
            ("Everything", "https://www.voidtools.com/zh-cn/downloads/", "🔍"),
            ("Bandizip", "https://www.bandisoft.com/bandizip/", "🗜️"),
            ("PotPlayer", "https://potplayer.daum.net/", "🎬"),
            ("Typora", "https://typora.io/", "📝"),
            ("Git", "https://git-scm.com/download/win", "🟥"),
            ("Python", "https://www.python.org/downloads/", "🐍"),
        ]
        tools_group = QGroupBox("常用小工具")
        tools_group.setFont(QFont("微软雅黑", 14, QFont.Bold))
        tools_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #b5d0ea;
                border-radius: 12px;
                margin-top: 16px;
                background: #f8fbfd;
                color: #2471a3;
                padding: 10px 0 0 0;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 18px;
                top: -10px;
                background: transparent;
                padding: 0 8px;
            }
        """)
        tools_layout = QGridLayout()
        tools_layout.setSpacing(18)
        tools_layout.setContentsMargins(24, 24, 24, 24)
        for idx, (name, url, icon) in enumerate(tools_tools):
            btn = QPushButton(f"{icon}  {name}")
            btn.setFont(QFont("微软雅黑", 16, QFont.Bold))
            btn.setMinimumHeight(60)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #eaf6fb, stop:1 #d6eaf8);
                    color: #2471a3;
                    border-radius: 14px;
                    font-size: 16px;
                    font-weight: 600;
                    padding: 8px 0;
                    border: 1.5px solid #d6eaf8;
                    letter-spacing: 1px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f8fffe, stop:1 #cfe7fa);
                    color: #1a6fae;
                    border: 2px solid #b5d0ea;
                }
                QPushButton:pressed {
                    background: #e3f0fa;
                    color: #2471a3;
                    border: 2px solid #a4cbe3;
                }
            """)
            btn.clicked.connect(lambda checked, link=url: webbrowser.open(link))
            row, col = divmod(idx, 4)
            tools_layout.addWidget(btn, row, col)
        tools_group.setLayout(tools_layout)
        main_layout.addWidget(tools_group)
        spacer = QFrame()
        spacer.setFixedHeight(4)  # 可根据需要调整间隔高度
        spacer.setStyleSheet("background: transparent; border: none;")
        main_layout.addWidget(spacer)

        # 开发/设计软件类
        dev_tools = [
            ("STM32CubeMX", "https://www.st.com/zh/development-tools/stm32cubemx.html", "🟦"),
            ("Keil MDK", "https://www.keil.com/download/product/", "🟩"),
            ("Visual Studio Code", "https://code.visualstudio.com/", "🟦"),
            ("CLion", "https://www.jetbrains.com/clion/download/", "🟧"),
            ("MATLAB", "https://www.mathworks.com/downloads/", "🟨"),
            ("SolidWorks", "https://www.solidworks.com/sw/support/downloads.htm", "🟫"),
            ("Altium Designer", "https://www.altium.com/zh/altium-designer/downloads", "🟪"),
            ("原神", "https://download-porter.hoyoverse.com/download-porter/2025/03/27/GenshinImpact_install_202503072011.exe?trace_key=GenshinImpact_install_ua_679d0b4e9b10", "🟫"),
        ]
        dev_group = QGroupBox("开发/设计软件")
        dev_group.setFont(QFont("微软雅黑", 14, QFont.Bold))
        dev_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #b5d0ea;
                border-radius: 12px;
                margin-top: 16px;
                background: #f8fbfd;
                color: #2471a3;
                padding: 10px 0 0 0;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 18px;
                top: -10px;
                background: transparent;
                padding: 0 8px;
            }
        """)
        dev_layout = QGridLayout()
        dev_layout.setSpacing(18)
        dev_layout.setContentsMargins(24, 24, 24, 24)
        for idx, (name, url, icon) in enumerate(dev_tools):
            btn = QPushButton(f"{icon}  {name}")
            btn.setFont(QFont("微软雅黑", 16, QFont.Bold))
            btn.setMinimumHeight(60)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #eaf6fb, stop:1 #d6eaf8);
                    color: #2471a3;
                    border-radius: 14px;
                    font-size: 16px;
                    font-weight: 600;
                    padding: 8px 0;
                    border: 1.5px solid #d6eaf8;
                    letter-spacing: 1px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f8fffe, stop:1 #cfe7fa);
                    color: #1a6fae;
                    border: 2px solid #b5d0ea;
                }
                QPushButton:pressed {
                    background: #e3f0fa;
                    color: #2471a3;
                    border: 2px solid #a4cbe3;
                }
            """)
            btn.clicked.connect(lambda checked, link=url: webbrowser.open(link))
            row, col = divmod(idx, 4)
            dev_layout.addWidget(btn, row, col)
        dev_group.setLayout(dev_layout)
        main_layout.addWidget(dev_group)

        main_layout.addStretch(1)

        # 页脚
        footer = QLabel("如有问题或建议，欢迎反馈至QQ群：857466609")
        footer.setFont(QFont("微软雅黑", 13))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #b2bec3; margin-top: 18px;")
        main_layout.addWidget(footer)

# --------- 功能三：串口助手 ---------
class SerialAssistant(QWidget):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("微软雅黑", 15))
        self.ser = None
        self.timer = None
        self.recv_buffer = b""
        self.plot_data = {}
        self.curve_colors = ["#e74c3c", "#2980b9", "#27ae60", "#f1c40f", "#8e44ad", "#16a085"]
        self.data_types = ["float", "int16", "uint16", "int8", "uint8"]
        self.data_type = "float"
        self.data_count = 2
        self.sample_idx = 0
    
        # 新增：HEX模式复选框
        self.hex_send_chk = QCheckBox("HEX发送")
        self.hex_recv_chk = QCheckBox("HEX接收")
        self.hex_send_chk.setFont(QFont("微软雅黑", 12))
        self.hex_recv_chk.setFont(QFont("微软雅黑", 12))
        self.hex_send_chk.setChecked(False)
        self.hex_recv_chk.setChecked(False)
    
        # 主体布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(28)
    
        # 左侧面板
        left_panel = QVBoxLayout()
        left_panel.setSpacing(20)
        left_panel.setContentsMargins(0, 0, 0, 0)
    
        # 串口配置区
        config_group = QGroupBox("串口配置")
        config_group.setFont(QFont("微软雅黑", 14, QFont.Bold))
        config_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #b5d0ea;
                border-radius: 12px;
                margin-top: 12px;
                background: #f8fbfd;
                color: #2471a3;
                padding: 8px 0 0 0;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 16px;
                top: -8px;
                background: transparent;
                padding: 0 8px;
            }
        """)
        config_layout = QGridLayout()
        config_layout.setSpacing(12)
        config_layout.setContentsMargins(16, 16, 16, 16)
        config_layout.addWidget(QLabel("串口号:"), 0, 0)
        self.port_box = QComboBox()
        self.port_box.setMinimumWidth(120)
        self.refresh_ports()
        config_layout.addWidget(self.port_box, 0, 1)
        config_layout.addWidget(QLabel("波特率:"), 1, 0)
        self.baud_box = QComboBox()
        self.baud_box.addItems(["9600", "115200", "57600", "38400", "19200", "4800"])
        self.baud_box.setCurrentText("115200")
        config_layout.addWidget(self.baud_box, 1, 1)
        self.refresh_btn = QPushButton("刷新串口")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.refresh_btn.setStyleSheet(self._btn_style())
        config_layout.addWidget(self.refresh_btn, 2, 0)
        self.open_btn = QPushButton("打开串口")
        self.open_btn.setCheckable(True)
        self.open_btn.clicked.connect(self.toggle_serial)
        self.open_btn.setStyleSheet(self._btn_style("#27ae60"))
        config_layout.addWidget(self.open_btn, 2, 1)
        config_group.setLayout(config_layout)
        left_panel.addWidget(config_group)
    
        # 数据协议配置区
        proto_group = QGroupBox("数据协议配置")
        proto_group.setFont(QFont("微软雅黑", 14, QFont.Bold))
        proto_group.setStyleSheet(config_group.styleSheet())
        proto_layout = QHBoxLayout()
        proto_layout.setSpacing(18)
        proto_layout.setContentsMargins(16, 16, 16, 16)
        proto_layout.addWidget(QLabel("数据数量:"))
        self.data_count_spin = QSpinBox()
        self.data_count_spin.setRange(1, 16)
        self.data_count_spin.setValue(self.data_count)
        self.data_count_spin.setFixedWidth(80)
        self.data_count_spin.valueChanged.connect(self.apply_proto_config)
        proto_layout.addWidget(self.data_count_spin)
        proto_layout.addSpacing(18)
        proto_layout.addWidget(QLabel("数据类型:"))
        self.data_type_box = QComboBox()
        self.data_type_box.addItems(self.data_types)
        self.data_type_box.setCurrentText(self.data_type)
        self.data_type_box.setFixedWidth(100)
        self.data_type_box.currentTextChanged.connect(self.apply_proto_config)
        proto_layout.addWidget(self.data_type_box)
        # proto_layout.addStretch(1)
        proto_group.setLayout(proto_layout)
        left_panel.addWidget(proto_group)
    
        # 发送数据区美化
        send_group = QGroupBox("发送数据")
        send_group.setFont(QFont("微软雅黑", 14, QFont.Bold))
        send_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #b5d0ea;
                border-radius: 12px;
                margin-top: 12px;
                background: #f8fbfd;
                color: #2471a3;
                padding: 8px 0 0 0;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 16px;
                top: -8px;
                background: transparent;
                padding: 0 8px;
            }
        """)
        send_layout = QVBoxLayout()
        send_layout.setSpacing(16)
        send_layout.setContentsMargins(18, 18, 18, 18)
    
        # 输入框（多行）
        self.send_edit = QTextEdit()
        self.send_edit.setFont(QFont("Consolas", 18))
        self.send_edit.setPlaceholderText("输入要发送的数据，可多行（支持HEX/文本）...")
        self.send_edit.setMinimumHeight(140)
        self.send_edit.setMaximumHeight(220)
        self.send_edit.setStyleSheet("""
            QTextEdit {
                background: #f8fbfd;
                border-radius: 12px;
                border: 2px solid #d6eaf8;
                font-size: 18px;
                padding: 14px 20px;
            }
        """)
        send_layout.addWidget(self.send_edit)
    
        # HEX复选框和按钮行
        row1 = QHBoxLayout()
        row1.setSpacing(24)
        self.hex_send_chk.setStyleSheet("""
            QCheckBox {
                color: #2471a3;
                font-size: 15px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
            }
            QCheckBox::indicator:checked {
                background-color: #2980b9;
                border: 1.5px solid #2980b9;
            }
            QCheckBox::indicator:unchecked {
                background-color: #fff;
                border: 1.5px solid #b5d0ea;
            }
        """)
        self.hex_recv_chk.setStyleSheet(self.hex_send_chk.styleSheet())
        row1.addWidget(self.hex_send_chk)
        row1.addWidget(self.hex_recv_chk)
        row1.addStretch(1)
        send_layout.addLayout(row1)
    
        # 发送和持续发送按钮+频率（优化为“每秒发送次数”）
        row2 = QHBoxLayout()
        row2.setSpacing(18)
        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_data)
        self.send_btn.setFont(QFont("微软雅黑", 16, QFont.Bold))
        self.send_btn.setFixedHeight(44)
        self.send_btn.setFixedWidth(120)
        self.send_btn.setStyleSheet(self._btn_style("#2980b9"))
        row2.addWidget(self.send_btn)
    
        self.cont_send_btn = QPushButton("持续发送")
        self.cont_send_btn.setCheckable(True)
        self.cont_send_btn.setFont(QFont("微软雅黑", 15))
        self.cont_send_btn.setFixedHeight(44)
        self.cont_send_btn.setFixedWidth(120)
        self.cont_send_btn.setStyleSheet(self._btn_style("#f1c40f"))
        self.cont_send_btn.clicked.connect(self.toggle_cont_send)
        row2.addWidget(self.cont_send_btn)
    
        freq_label = QLabel("   每秒发送次数:")
        freq_label.setFont(QFont("微软雅黑", 8))
        freq_label.setFixedWidth(180)
        #文本居中
        # freq_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row2.addWidget(freq_label)
    
        self.freq_input = QSpinBox()
        self.freq_input.setRange(1, 1000)
        self.freq_input.setValue(5)
        self.freq_input.setFont(QFont("Consolas", 14))
        self.freq_input.setFixedWidth(100)
        self.freq_input.setStyleSheet("""
            QSpinBox {
                background: #f8fbfd;
                border-radius: 8px;
                border: 1px solid #d6eaf8;
                font-size: 15px;
                padding: 2px 8px;
            }
        """)
        row2.addWidget(self.freq_input)
    
        # freq_unit = QLabel("次/秒")
        # freq_unit.setFont(QFont("微软雅黑", 13))
        # freq_unit.setFixedWidth(40)
        # row2.addWidget(freq_unit)
        row2.addStretch(1)
        send_layout.addLayout(row2)
    
        self.cont_send_timer = QTimer(self)
        self.cont_send_timer.timeout.connect(self.send_data)
    
        send_group.setLayout(send_layout)
        left_panel.addWidget(send_group, stretch=1)  # 让发送区弹性填充
    
        # 使用说明始终在最下方
        usage_group = QGroupBox("使用说明")
        usage_group.setFont(QFont("微软雅黑", 13, QFont.Bold))
        usage_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #b5d0ea;
                border-radius: 10px;
                margin-top: 10px;
                background: #f8fbfd;
                color: #2471a3;
                padding: 6px 0 0 0;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 10px;
                top: -8px;
                background: transparent;
                padding: 0 6px;
            }
        """)
        usage_layout = QVBoxLayout()
        usage_label = QLabel(
            "1. 在“数据协议配置”中选择数据数量和数据类型。\n"
            "2. 下位机发送格式：\n"
            "   0x55 + 数据数量(1字节) + 数据 + 校验和(1字节)\n"
            "   校验和为包头到最后一个数据字节的累加和的低8位。\n"
            "3. 每包数据自动绘制曲线，X轴为采样点（或时间），Y轴为各通道数据。\n"
        )
        usage_label.setWordWrap(True)
        usage_label.setFont(QFont("微软雅黑", 9))
        usage_layout.addWidget(usage_label)
        usage_group.setLayout(usage_layout)
        left_panel.addWidget(usage_group)
    
        # 清空按钮紧贴使用说明
        self.clear_btn = QPushButton("清空接收和曲线")
        self.clear_btn.clicked.connect(self.clear_all)
        self.clear_btn.setStyleSheet(self._btn_style("#e74c3c"))
        self.clear_btn.setFixedHeight(38)
        left_panel.addWidget(self.clear_btn)
    
        main_layout.addLayout(left_panel, 0)
    
        # 右侧面板
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)
    
        # 接收区
        recv_group = QGroupBox("串口接收区")
        recv_group.setFont(QFont("微软雅黑", 14, QFont.Bold))
        recv_group.setStyleSheet(config_group.styleSheet())
        recv_layout = QVBoxLayout()
        self.recv_box = QTextEdit()
        self.recv_box.setFont(QFont("Consolas", 13))
        self.recv_box.setReadOnly(True)
        self.recv_box.setMinimumHeight(120)
        self.recv_box.setStyleSheet("""
            QTextEdit {
                background: #f8fbfd;
                border-radius: 10px;
                border: 1px solid #d6eaf8;
                font-size: 15px;
                color: #2c3e50;
                padding: 8px;
            }
        """)
        recv_layout.addWidget(self.recv_box)
        recv_group.setLayout(recv_layout)
        right_panel.addWidget(recv_group)
    
        # 曲线绘图区
        plot_frame = QFrame()
        plot_frame.setStyleSheet("""
            QFrame {
                background: #fff;
                border-radius: 16px;
                border: 1px solid #d6eaf8;
            }
        """)
        plot_shadow = QGraphicsDropShadowEffect(self)
        plot_shadow.setBlurRadius(18)
        plot_shadow.setOffset(0, 4)
        plot_shadow.setColor(Qt.gray)
        plot_frame.setGraphicsEffect(plot_shadow)
        plot_layout2 = QVBoxLayout(plot_frame)
        plot_layout2.setContentsMargins(10, 10, 10, 10)
        self.figure = Figure(figsize=(7, 4))
        self.canvas = FigureCanvas(self.figure)
        plot_layout2.addWidget(self.canvas)
        right_panel.addWidget(plot_frame, 2)
    
        main_layout.addLayout(right_panel, 1)
    
        # 定时器接收
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_serial)
    
        # 新增：正弦波测试定时器
        self.sine_timer = QTimer(self)
        self.sine_timer.timeout.connect(self.send_sine_data)
        self.sine_phase = 0
        # 默认配置
        self.apply_proto_config()
    
    def parse_hex_string(self, s):
        """支持 0x11 0x22 33 44 格式转bytes"""
        s = s.strip().replace(',', ' ').replace(';', ' ')
        parts = s.split()
        result = []
        for part in parts:
            if part.startswith('0x') or part.startswith('0X'):
                try:
                    result.append(int(part, 16))
                except Exception:
                    pass
            else:
                try:
                    result.append(int(part, 16))
                except Exception:
                    pass
        return bytes(result)

    def send_data(self):
        if self.ser and self.ser.is_open:
            data = self.send_edit.text()
            try:
                if self.hex_send_chk.isChecked():
                    # 支持 0x11 0x22 33 44 格式
                    data_bytes = self.parse_hex_string(data)
                    if not data_bytes:
                        self.recv_box.append("HEX格式错误，未发送。")
                        return
                    self.ser.write(data_bytes)
                    self.recv_box.append(f"发送(HEX): {' '.join(['%02X'%b for b in data_bytes])}")
                else:
                    self.ser.write(data.encode('utf-8'))
                    self.recv_box.append(f"发送: {data}")
            except Exception as e:
                self.recv_box.append(f"发送失败: {e}")
        else:
            self.recv_box.append("串口未打开，无法发送。")

    def toggle_cont_send(self):
        if self.cont_send_btn.isChecked():
            try:
                interval = int(self.freq_box.currentText())
            except Exception:
                interval = 200
            self.cont_send_timer.start(interval)
            self.cont_send_btn.setText("停止发送")
        else:
            self.cont_send_timer.stop()
            self.cont_send_btn.setText("持续发送")

    def simulate_data(self):
        """模拟一包数据并自动解析绘图"""
        import struct
        import random
        # 构造协议包
        head = 0x55
        count = self.data_count
        dtype = self.data_type
        # 随机生成数据
        if dtype == "float":
            vals = [random.uniform(-10, 10) for _ in range(count)]
            data_bytes = struct.pack(f"<{count}f", *vals)
        elif dtype == "int16":
            vals = [random.randint(-30000, 30000) for _ in range(count)]
            data_bytes = struct.pack(f"<{count}h", *vals)
        elif dtype == "uint16":
            vals = [random.randint(0, 65535) for _ in range(count)]
            data_bytes = struct.pack(f"<{count}H", *vals)
        elif dtype == "int8":
            vals = [random.randint(-128, 127) for _ in range(count)]
            data_bytes = struct.pack(f"<{count}b", *vals)
        elif dtype == "uint8":
            vals = [random.randint(0, 255) for _ in range(count)]
            data_bytes = struct.pack(f"<{count}B", *vals)
        else:
            vals = [0] * count
            data_bytes = b"\x00" * (count * self._type_size())
        # 拼包
        pkt = bytes([head, count]) + data_bytes
        checksum = sum(pkt) & 0xFF
        pkt += bytes([checksum])
        # 加入接收缓冲区并解析
        self.recv_buffer += pkt
        self.parse_and_plot_bin()

    def _btn_style(self, color="#2980b9"):
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eaf6fb, stop:1 #d6eaf8);
                color: {color};
                border-radius: 14px;
                font-size: 16px;
                font-weight: 600;
                padding: 8px 0;
                border: 1.5px solid #d6eaf8;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fffe, stop:1 #cfe7fa);
                color: #1a6fae;
                border: 2px solid #b5d0ea;
            }}
            QPushButton:pressed {{
                background: #e3f0fa;
                color: {color};
                border: 2px solid #a4cbe3;
            }}
        """

    def apply_proto_config(self):
        self.data_count = self.data_count_spin.value()
        self.data_type = self.data_type_box.currentText()
        self.plot_data = {i: [[], []] for i in range(self.data_count)}
        self.sample_idx = 0
        self.update_plot()

    def refresh_ports(self):
        self.port_box.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_box.addItem(port.device)
        if self.port_box.count() == 0:
            self.port_box.addItem("无可用串口")

    def toggle_serial(self):
        if self.open_btn.isChecked():
            port = self.port_box.currentText()
            baud = int(self.baud_box.currentText())
            try:
                self.ser = serial.Serial(port, baud, timeout=0.1)
                self.open_btn.setText("关闭串口")
                self.recv_box.append(f"已打开串口 {port} @ {baud}bps")
                self.timer.start(50)
            except Exception as e:
                self.recv_box.append(f"打开串口失败: {e}")
                self.open_btn.setChecked(False)
        else:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.open_btn.setText("打开串口")
            self.recv_box.append("串口已关闭")
            self.timer.stop()

    def send_multi_data(self):
        if self.ser and self.ser.is_open:
            text = self.send_edit.text()
            lines = text.split(";")
            for line in lines:
                if line.strip():
                    try:
                        if self.hex_send_chk.isChecked():
                            data_bytes = self.parse_hex_string(line.strip())
                            self.ser.write(data_bytes)
                            self.recv_box.append(f"发送(HEX): {' '.join(['%02X'%b for b in data_bytes])}")
                        else:
                            self.ser.write(line.strip().encode('utf-8'))
                            self.recv_box.append(f"发送: {line.strip()}")
                    except Exception as e:
                        self.recv_box.append(f"发送失败: {e}")
        else:
            self.recv_box.append("串口未打开，无法发送。")

    def read_serial(self):
        if self.ser and self.ser.is_open:
            try:
                data = self.ser.read_all()
                if data:
                    if self.hex_recv_chk.isChecked():
                        self.recv_box.append(f"接收(HEX): {data.hex(' ').upper()}")
                    else:
                        try:
                            self.recv_box.append(f"接收: {data.decode('utf-8', errors='replace')}")
                        except Exception:
                            self.recv_box.append(f"接收(HEX): {data.hex(' ').upper()}")
                    self.recv_buffer += data
                    self.parse_and_plot_bin()
            except Exception as e:
                self.recv_box.append(f"接收失败: {e}")

    def toggle_sine_test(self):
        if self.test_btn.isChecked():
            self.test_btn.setText("停止测试")
            self.sine_phase = 0
            self.sine_timer.start(80)  # 80ms周期
        else:
            self.test_btn.setText("测试正弦波(持续)")
            self.sine_timer.stop()

    def send_sine_data(self):
        import struct, math
        head = 0x55
        count = self.data_count
        dtype = self.data_type
        t = self.sine_phase
        vals = []
        for i in range(count):
            # 多通道不同相位
            val = math.sin(t / 10.0 + i * math.pi / 4) * 10
            if dtype == "float":
                vals.append(float(val))
            elif dtype == "int16":
                vals.append(int(val * 1000))
            elif dtype == "uint16":
                vals.append(int(val * 1000 + 20000))
            elif dtype == "int8":
                vals.append(int(val * 10))
            elif dtype == "uint8":
                vals.append(int(val * 10 + 100))
        # 打包
        if dtype == "float":
            data_bytes = struct.pack(f"<{count}f", *vals)
        elif dtype == "int16":
            data_bytes = struct.pack(f"<{count}h", *vals)
        elif dtype == "uint16":
            data_bytes = struct.pack(f"<{count}H", *vals)
        elif dtype == "int8":
            data_bytes = struct.pack(f"<{count}b", *vals)
        elif dtype == "uint8":
            data_bytes = struct.pack(f"<{count}B", *vals)
        else:
            data_bytes = b"\x00" * (count * self._type_size())
        pkt = bytes([head, count]) + data_bytes
        checksum = sum(pkt) & 0xFF
        pkt += bytes([checksum])
        # 直接走接收流程模拟
        self.recv_buffer += pkt
        self.parse_and_plot_bin()
        # 在接收区实时显示理论值
        self.recv_box.append(f"理论: {['%.3f'%v for v in vals]}")
        self.sine_phase += 1

    def parse_and_plot_bin(self):
        # 协议：0x55 + 数据数量(1B) + 数据 + 校验(1B)
        min_len = 1 + 1 + self.data_count * self._type_size() + 1
        while len(self.recv_buffer) >= min_len:
            idx = self.recv_buffer.find(b'\x55')
            if idx == -1:
                self.recv_buffer = b""
                break
            if idx > 0:
                self.recv_buffer = self.recv_buffer[idx:]
            if len(self.recv_buffer) < min_len:
                break
            # 检查数量
            count = self.recv_buffer[1]
            if count != self.data_count:
                self.recv_buffer = self.recv_buffer[2:]
                continue
            data_bytes = self.recv_buffer[2:2+count*self._type_size()]
            checksum = self.recv_buffer[2+count*self._type_size()]
            calc_sum = (sum(self.recv_buffer[:2+count*self._type_size()])) & 0xFF
            if checksum != calc_sum:
                self.recv_box.append("校验和错误，丢弃包")
                self.recv_buffer = self.recv_buffer[1:]
                continue
            # 解析数据
            values = self._unpack_data(data_bytes, count)
            self.recv_box.append(f"接收: {values}")
            for i, v in enumerate(values):
                self.plot_data[i][0].append(self.sample_idx)
                self.plot_data[i][1].append(v)
                if len(self.plot_data[i][0]) > 200:
                    self.plot_data[i][0].pop(0)
                    self.plot_data[i][1].pop(0)
            self.sample_idx += 1
            self.recv_buffer = self.recv_buffer[min_len:]
            self.update_plot()

    def _type_size(self):
        if self.data_type == "float":
            return 4
        elif self.data_type in ("int16", "uint16"):
            return 2
        elif self.data_type in ("int8", "uint8"):
            return 1
        return 4

    def _unpack_data(self, data_bytes, count):
        import struct
        fmt = {
            "float": f"<{count}f",
            "int16": f"<{count}h",
            "uint16": f"<{count}H",
            "int8": f"<{count}b",
            "uint8": f"<{count}B"
        }[self.data_type]
        try:
            return struct.unpack(fmt, data_bytes)
        except Exception:
            return [0] * count

    def update_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_xlabel("Sample", fontsize=14)
        ax.set_ylabel("Value", fontsize=14)
        has_curve = False
        for idx in range(self.data_count):
            color = self.curve_colors[idx % len(self.curve_colors)]
            x_list, y_list = self.plot_data.get(idx, ([], []))
            if x_list and y_list:
                ax.plot(x_list, y_list, label=f"CH{idx+1}", color=color, linewidth=2)
                has_curve = True
        if has_curve:
            ax.legend()
        ax.grid(True, linestyle="--", alpha=0.5)
        self.canvas.draw()

    def clear_all(self):
        self.recv_box.clear()
        self.plot_data = {i: [[], []] for i in range(self.data_count)}
        self.sample_idx = 0
        self.update_plot()

# --------- 功能四：MRobot架构生成 ---------
class GenerateMRobotCode(QWidget):
    repo_ready_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFont(QFont("微软雅黑", 15))
        self.setStyleSheet("""
            QWidget {
                background: #f8fbfd;
                border-radius: 16px;
                padding: 20px;
            }
        """)
        # 变量初始化
        self.repo_dir = "MRobot_repo"
        self.repo_url = "http://gitea.qutrobot.top/robofish/MRobot.git"
        self.header_file_vars = {}
        self.task_vars = []
        self.ioc_data = None
        self.add_gitignore = False
        self.auto_configure = False
        self.repo_ready = False  # 标志：仓库是否已准备好
        self.init_ui()
        self.repo_ready_signal.connect(self.on_repo_ready)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.repo_ready:
            self.log("首次进入，正在克隆MRobot仓库...")
            self.clone_repo_and_refresh()

    def clone_repo_and_refresh(self):
        import threading
        def do_clone():
            self.clone_repo()
            self.repo_ready = True
            self.ioc_data = self.find_and_read_ioc_file()
            self.repo_ready_signal.emit()
        threading.Thread(target=do_clone).start()

    @pyqtSlot()
    def on_repo_ready(self):
        self.update_freertos_status()
        self.update_header_files()
        self.update_task_ui()
        self.log("仓库准备完成！")

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(32, 32, 32, 32)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eaf6fb, stop:1 #d6eaf8);
                border-radius: 16px;
            }
        """)

        # 顶部标题区
        title = QLabel("MRobot 架构生成工具")
        title.setFont(QFont("微软雅黑", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2980b9; letter-spacing: 2px; margin-bottom: 2px;")
        main_layout.addWidget(title)

        desc = QLabel("快速生成 MRobot 项目代码，自动管理模块、任务与环境配置。")
        desc.setFont(QFont("微软雅黑", 13))
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #34495e; margin-bottom: 8px;")
        main_layout.addWidget(desc)

        # 状态与选项区
        status_opt_row = QHBoxLayout()
        status_opt_row.setSpacing(24)

        # 状态区
        status_col = QVBoxLayout()
        self.freertos_status_label = QLabel("FreeRTOS 状态: 检测中...")
        self.freertos_status_label.setFont(QFont("微软雅黑", 12))
        self.freertos_status_label.setStyleSheet("color: #2471a3;")
        status_col.addWidget(self.freertos_status_label)
        status_col.addStretch(1)
        status_opt_row.addLayout(status_col, 1)

        # 选项区
        option_col = QVBoxLayout()
        self.gitignore_chk = QCheckBox("生成 .gitignore")
        self.gitignore_chk.setFont(QFont("微软雅黑", 12))
        self.gitignore_chk.stateChanged.connect(lambda x: setattr(self, "add_gitignore", x == Qt.Checked))
        option_col.addWidget(self.gitignore_chk)
        self.auto_env_chk = QCheckBox("自动环境配置")
        self.auto_env_chk.setFont(QFont("微软雅黑", 12))
        self.auto_env_chk.stateChanged.connect(lambda x: setattr(self, "auto_configure", x == Qt.Checked))
        option_col.addWidget(self.auto_env_chk)
        option_col.addStretch(1)
        status_opt_row.addLayout(option_col, 1)

        status_opt_row.addStretch(2)
        main_layout.addLayout(status_opt_row)

        # 主体分区：左侧模块选择，右侧任务管理
        body_layout = QHBoxLayout()
        body_layout.setSpacing(24)

        # 左侧：模块文件选择
        left_col = QVBoxLayout()
        self.header_group = QGroupBox("模块文件选择")
        self.header_group.setFont(QFont("微软雅黑", 15, QFont.Bold))
        self.header_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #b5d0ea;
                border-radius: 12px;
                margin-top: 8px;
                background: #f8fbfd;
                color: #2471a3;
                padding: 10px 0 0 0;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 18px;
                top: -10px;
                background: transparent;
                padding: 0 8px;
            }
        """)
        self.header_layout = QVBoxLayout(self.header_group)
        self.header_layout.setSpacing(8)
        left_col.addWidget(self.header_group)
        left_col.addStretch(1)
        body_layout.addLayout(left_col, 2)

        # 右侧：任务管理
        right_col = QVBoxLayout()
        self.task_group = QGroupBox("任务管理 (FreeRTOS)")
        self.task_group.setFont(QFont("微软雅黑", 15, QFont.Bold))
        self.task_group.setStyleSheet(self.header_group.styleSheet())
        self.task_layout = QVBoxLayout(self.task_group)
        self.task_layout.setSpacing(8)
        right_col.addWidget(self.task_group)
        right_col.addStretch(1)
        body_layout.addLayout(right_col, 2)

        main_layout.addLayout(body_layout)

        # 生成按钮区
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.generate_btn = QPushButton("一键生成 MRobot 代码")
        self.generate_btn.setFont(QFont("微软雅黑", 18, QFont.Bold))
        self.generate_btn.setMinimumHeight(48)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eaf6fb, stop:1 #d6eaf8);
                color: #2980b9;
                border-radius: 20px;
                font-size: 20px;
                font-weight: 600;
                padding: 12px 0;
                border: 1px solid #d6eaf8;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fffe, stop:1 #cfe7fa);
                color: #1a6fae;
                border: 1.5px solid #b5d0ea;
            }
            QPushButton:pressed {
                background: #e3f0fa;
                color: #2471a3;
                border: 1.5px solid #a4cbe3;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_action)
        btn_row.addWidget(self.generate_btn)
        btn_row.addStretch(1)
        main_layout.addLayout(btn_row)

        # 日志输出区
        self.msg_box = QTextEdit()
        self.msg_box.setReadOnly(True)
        self.msg_box.setFont(QFont("Consolas", 13))
        self.msg_box.setMaximumHeight(100)
        self.msg_box.setStyleSheet("""
            QTextEdit {
                background: #f4f6f7;
                border-radius: 8px;
                border: 1px solid #d6eaf8;
                font-size: 15px;
                color: #2c3e50;
                padding: 8px;
            }
        """)
        main_layout.addWidget(self.msg_box)

        # 页脚
        footer = QLabel("如遇问题请反馈至 QUT 机器人战队")
        footer.setFont(QFont("微软雅黑", 11))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #b2bec3; margin-top: 6px;")
        main_layout.addWidget(footer)

        # 初始化内容
        self.update_header_files()
        self.update_task_ui()

        # ...其余方法保持不变...

    def log(self, msg):
        self.msg_box.append(msg)

    def clone_repo(self):
        import shutil
        from git import Repo
        if os.path.exists(self.repo_dir):
            shutil.rmtree(self.repo_dir)
        try:
            self.log("正在克隆仓库...")
            Repo.clone_from(self.repo_url, self.repo_dir, multi_options=["--depth=1"])
            self.log("仓库克隆成功！")
        except Exception as e:
            self.log(f"克隆仓库失败: {e}")

    def find_and_read_ioc_file(self):
        for file in os.listdir("."):
            if file.endswith(".ioc"):
                with open(file, "r", encoding="utf-8") as f:
                    return f.read()
        self.log("未找到 .ioc 文件！")
        return None

    def check_freertos_enabled(self):
        import re
        if not self.ioc_data:
            return False
        return bool(re.search(r"Mcu\.IP\d+=FREERTOS", self.ioc_data))

    def update_freertos_status(self):
        if self.ioc_data:
            status = "已启用" if self.check_freertos_enabled() else "未启用"
        else:
            status = "未检测到 .ioc 文件"
        self.freertos_status_label.setText(f"FreeRTOS 状态: {status}")

    def update_header_files(self):
        for i in reversed(range(self.header_layout.count())):
            widget = self.header_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        if not self.repo_ready or not os.path.exists(self.repo_dir):
            return
        from collections import defaultdict
        import csv
        folders = ["bsp", "component", "device", "module"]
        dependencies = defaultdict(list)
        for folder in folders:
            folder_dir = os.path.join(self.repo_dir, "User", folder)
            dep_file = os.path.join(folder_dir, "dependencies.csv")
            if os.path.exists(dep_file):
                with open(dep_file, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) == 2:
                            dependencies[row[0]].append(row[1])
        for folder in folders:
            folder_dir = os.path.join(self.repo_dir, "User", folder)
            if os.path.exists(folder_dir):
                group = QGroupBox(folder)
                g_layout = QHBoxLayout(group)
                for file in os.listdir(folder_dir):
                    file_base, file_ext = os.path.splitext(file)
                    if file_ext == ".h" and file_base != folder:
                        var = QCheckBox(file_base)
                        var.stateChanged.connect(lambda x, fb=file_base: self.handle_dependencies(fb, dependencies))
                        self.header_file_vars[file_base] = var
                        g_layout.addWidget(var)
                self.header_layout.addWidget(group)

    def handle_dependencies(self, file_base, dependencies):
        if file_base in self.header_file_vars and self.header_file_vars[file_base].isChecked():
            for dep in dependencies.get(file_base, []):
                dep_base = os.path.basename(dep)
                if dep_base in self.header_file_vars:
                    self.header_file_vars[dep_base].setChecked(True)

    def update_task_ui(self):
        for i in reversed(range(self.task_layout.count())):
            widget = self.task_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        if not self.repo_ready or not self.check_freertos_enabled():
            self.task_group.setVisible(False)
            return
        self.task_group.setVisible(True)
        for i, (task_var, freq_var) in enumerate(self.task_vars):
            row = QHBoxLayout()
            name_edit = QLineEdit(task_var)
            freq_spin = QSpinBox()
            freq_spin.setRange(1, 1000)
            freq_spin.setValue(freq_var)
            del_btn = QPushButton("删除")
            del_btn.clicked.connect(lambda _, idx=i: self.remove_task(idx))
            row.addWidget(name_edit)
            row.addWidget(QLabel("频率:"))
            row.addWidget(freq_spin)
            row.addWidget(del_btn)
            container = QWidget()
            container.setLayout(row)
            self.task_layout.addWidget(container)
        add_btn = QPushButton("添加任务")
        add_btn.clicked.connect(self.add_task)
        self.task_layout.addWidget(add_btn)

    def add_task(self):
        self.task_vars.append([f"Task_{len(self.task_vars)+1}", 100])
        self.update_task_ui()

    def remove_task(self, idx):
        if 0 <= idx < len(self.task_vars):
            self.task_vars.pop(idx)
            self.update_task_ui()

    def copy_file_from_repo(self, src_path, dest_path):
        import shutil
        if src_path.startswith(self.repo_dir):
            full_src_path = src_path
        else:
            full_src_path = os.path.join(self.repo_dir, src_path.lstrip(os.sep))
        if not os.path.exists(full_src_path):
            self.log(f"文件 {full_src_path} 不存在！")
            return
        dest_dir = os.path.dirname(dest_path)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        shutil.copy(full_src_path, dest_path)
        self.log(f"已复制 {full_src_path} 到 {dest_path}")

    def generate_action(self):
        import threading
        def task():
            self.create_directories()
            if self.add_gitignore:
                self.copy_file_from_repo(".gitignore", ".gitignore")
            if self.ioc_data and self.check_freertos_enabled():
                self.copy_file_from_repo("src/freertos.c", os.path.join("Core", "Src", "freertos.c"))
            folders = ["bsp", "component", "device", "module"]
            for folder in folders:
                folder_dir = os.path.join(self.repo_dir, "User", folder)
                if not os.path.exists(folder_dir):
                    continue
                for file_name in os.listdir(folder_dir):
                    file_base, file_ext = os.path.splitext(file_name)
                    if file_ext not in [".h", ".c"]:
                        continue
                    if file_base == folder:
                        src_path = os.path.join(folder_dir, file_name)
                        dest_path = os.path.join("User", folder, file_name)
                        self.copy_file_from_repo(src_path, dest_path)
                        continue
                    if file_base in self.header_file_vars and self.header_file_vars[file_base].isChecked():
                        src_path = os.path.join(folder_dir, file_name)
                        dest_path = os.path.join("User", folder, file_name)
                        self.copy_file_from_repo(src_path, dest_path)
            if self.ioc_data and self.check_freertos_enabled():
                self.modify_user_task_file()
                self.generate_user_task_header()
                self.generate_init_file()
                self.generate_task_files()
            self.log("生成完成！")
        threading.Thread(target=task).start()

    def create_directories(self):
        dirs = [
            "User/bsp",
            "User/component",
            "User/device",
            "User/module",
        ]
        if self.ioc_data and self.check_freertos_enabled():
            dirs.append("User/task")
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)
                self.log(f"已创建目录: {d}")

    def generate_task_files(self):
        try:
            import re
            template_file_path = os.path.join(self.repo_dir, "User", "task", "task.c.template")
            task_dir = os.path.join("User", "task")
            if not os.path.exists(template_file_path):
                self.log(f"模板文件 {template_file_path} 不存在，无法生成 task.c 文件！")
                return
            os.makedirs(task_dir, exist_ok=True)
            with open(template_file_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            for task in self.task_vars:
                if isinstance(task, (list, tuple)):
                    task_name = str(task[0])
                else:
                    task_name = str(task)
                task_file_path = os.path.join(task_dir, f"{task_name.lower()}.c")
                task_content = template_content.replace("{{task_name}}", task_name)
                task_content = task_content.replace("{{task_function}}", task_name)
                task_content = task_content.replace(
                    "{{task_frequency}}", f"TASK_FREQ_{task_name.upper()}"
                )
                task_content = task_content.replace("{{task_delay}}", f"TASK_INIT_DELAY_{task_name.upper()}")
                with open(task_file_path, "w", encoding="utf-8") as f2:
                    f2.write(task_content)
                self.log(f"已成功生成 {task_file_path} 文件！")
        except Exception as e:
            self.log(f"生成 task.c 文件时出错: {e}")

    def modify_user_task_file(self):
        try:
            import re
            template_file_path = os.path.join(self.repo_dir, "User", "task", "user_task.c.template")
            generated_task_file_path = os.path.join("User", "task", "user_task.c")
            if not os.path.exists(template_file_path):
                self.log(f"模板文件 {template_file_path} 不存在，无法生成 user_task.c 文件！")
                return
            os.makedirs(os.path.dirname(generated_task_file_path), exist_ok=True)
            with open(template_file_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            task_attr_definitions = "\n".join([
                f"""const osThreadAttr_t attr_{str(task[0]).lower()} = {{
    .name = "{str(task[0])}",
    .priority = osPriorityNormal,
    .stack_size = 128 * 4,
}};"""
                for task in self.task_vars
            ])
            task_content = template_content.replace("{{task_attr_definitions}}", task_attr_definitions)
            with open(generated_task_file_path, "w", encoding="utf-8") as f2:
                f2.write(task_content)
            self.log(f"已成功生成 {generated_task_file_path} 文件！")
        except Exception as e:
            self.log(f"修改 user_task.c 文件时出错: {e}")

    def generate_user_task_header(self):
        try:
            import re
            template_file_path = os.path.join(self.repo_dir, "User", "task", "user_task.h.template")
            header_file_path = os.path.join("User", "task", "user_task.h")
            if not os.path.exists(template_file_path):
                self.log(f"模板文件 {template_file_path} 不存在，无法生成 user_task.h 文件！")
                return
            os.makedirs(os.path.dirname(header_file_path), exist_ok=True)
            existing_msgq_content = ""
            if os.path.exists(header_file_path):
                with open(header_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"/\* USER MESSAGE BEGIN \*/\s*(.*?)\s*/\* USER MESSAGE END \*/", content, re.DOTALL)
                    if match:
                        existing_msgq_content = match.group(1).strip()
                        self.log("已存在的 msgq 区域内容已保留")
            with open(template_file_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            thread_definitions = "\n".join([f"        osThreadId_t {str(task[0]).lower()};" for task in self.task_vars])
            msgq_definitions = existing_msgq_content if existing_msgq_content else "        osMessageQueueId_t default_msgq;"
            freq_definitions = "\n".join([f"        float {str(task[0]).lower()};" for task in self.task_vars])
            last_up_time_definitions = "\n".join([f"        uint32_t {str(task[0]).lower()};" for task in self.task_vars])
            task_attr_declarations = "\n".join([f"extern const osThreadAttr_t attr_{str(task[0]).lower()};" for task in self.task_vars])
            task_function_declarations = "\n".join([f"void {str(task[0])}(void *argument);" for task in self.task_vars])
            task_frequency_definitions = "\n".join([
                f"#define TASK_FREQ_{str(task[0]).upper()} ({int(task[1])}u)"
                for task in self.task_vars
            ])
            task_init_delay_definitions = "\n".join([f"#define TASK_INIT_DELAY_{str(task[0]).upper()} (0u)" for task in self.task_vars])
            task_handle_definitions = "\n".join([f"    osThreadId_t {str(task[0]).lower()};" for task in self.task_vars])
            header_content = template_content.replace("{{thread_definitions}}", thread_definitions)
            header_content = header_content.replace("{{msgq_definitions}}", msgq_definitions)
            header_content = header_content.replace("{{freq_definitions}}", freq_definitions)
            header_content = header_content.replace("{{last_up_time_definitions}}", last_up_time_definitions)
            header_content = header_content.replace("{{task_attr_declarations}}", task_attr_declarations)
            header_content = header_content.replace("{{task_function_declarations}}", task_function_declarations)
            header_content = header_content.replace("{{task_frequency_definitions}}", task_frequency_definitions)
            header_content = header_content.replace("{{task_init_delay_definitions}}", task_init_delay_definitions)
            header_content = header_content.replace("{{task_handle_definitions}}", task_handle_definitions)
            if existing_msgq_content:
                header_content = re.sub(
                    r"/\* USER MESSAGE BEGIN \*/\s*.*?\s*/\* USER MESSAGE END \*/",
                    f"/* USER MESSAGE BEGIN */\n\n    {existing_msgq_content}\n\n    /* USER MESSAGE END */",
                    header_content,
                    flags=re.DOTALL
                )
            with open(header_file_path, "w", encoding="utf-8") as f2:
                f2.write(header_content)
            self.log(f"已成功生成 {header_file_path} 文件！")
        except Exception as e:
            self.log(f"生成 user_task.h 文件时出错: {e}")

    def generate_init_file(self):
        try:
            import re
            template_file_path = os.path.join(self.repo_dir, "User", "task", "init.c.template")
            generated_file_path = os.path.join("User", "task", "init.c")
            if not os.path.exists(template_file_path):
                self.log(f"模板文件 {template_file_path} 不存在，无法生成 init.c 文件！")
                return
            os.makedirs(os.path.dirname(generated_file_path), exist_ok=True)
            existing_msgq_content = ""
            if os.path.exists(generated_file_path):
                with open(generated_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"/\* USER MESSAGE BEGIN \*/\s*(.*?)\s*/\* USER MESSAGE END \*/", content, re.DOTALL)
                    if match:
                        existing_msgq_content = match.group(1).strip()
                        self.log("已存在的消息队列区域内容已保留")
            with open(template_file_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            thread_creation_code = "\n".join([
                f"  task_runtime.thread.{str(task[0]).lower()} = osThreadNew({str(task[0])}, NULL, &attr_{str(task[0]).lower()});"
                for task in self.task_vars
            ])
            init_content = template_content.replace("{{thread_creation_code}}", thread_creation_code)
            if existing_msgq_content:
                init_content = re.sub(
                    r"/\* USER MESSAGE BEGIN \*/\s*.*?\s*/\* USER MESSAGE END \*/",
                    f"/* USER MESSAGE BEGIN */\n  {existing_msgq_content}\n  /* USER MESSAGE END */",
                    init_content,
                    flags=re.DOTALL
                )
            with open(generated_file_path, "w", encoding="utf-8") as f2:
                f2.write(init_content)
            self.log(f"已成功生成 {generated_file_path} 文件！")
        except Exception as e:
            self.log(f"生成 init.c 文件时出错: {e}")

# --------- 功能五：零件库 ---------

class CustomWebView(QWebEngineView):
    def __init__(self, parent=None, popup_list=None):
        super().__init__(parent)
        self.popup_list = popup_list
        self._progress_dialog = None
        self.page().profile().downloadRequested.connect(self.handle_download)
        self.setStyleSheet("""
            QWebEngineView {
                border-radius: 12px;
                background: #f8fbfd;
                border: 1px solid #d6eaf8;
            }
        """)

    def handle_download(self, download_item):
        from PyQt5.QtWidgets import QFileDialog, QProgressDialog

        # 防止重复弹窗
        if hasattr(download_item, "_handled") and download_item._handled:
            return
        download_item._handled = True

        suggested = download_item.suggestedFileName()
        path, _ = QFileDialog.getSaveFileName(self, "保存文件", suggested)
        if not path:
            download_item.cancel()
            return

        download_item.setPath(path)
        download_item.accept()

        # 创建进度对话框
        self._progress_dialog = QProgressDialog(f"正在下载: {suggested}", "取消", 0, 100, self)
        self._progress_dialog.setWindowTitle("下载进度")
        self._progress_dialog.setWindowModality(Qt.WindowModal)
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setValue(0)
        self._progress_dialog.canceled.connect(download_item.cancel)
        self._progress_dialog.show()

        def on_progress(received, total):
            if total > 0:
                percent = int(received * 100 / total)
                self._progress_dialog.setValue(percent)
            else:
                self._progress_dialog.setValue(0)

        download_item.downloadProgress.connect(on_progress)

        def on_finished():
            self._progress_dialog.setValue(100)
            self._progress_dialog.close()
            if self.parent() and isinstance(self.parent(), CustomWebView):
                self.parent().close()
            elif self.popup_list and self in self.popup_list:
                self.close()
                self.popup_list.remove(self)

        download_item.finished.connect(on_finished)

    def createWindow(self, _type):
        popup = CustomWebView(popup_list=self.popup_list)
        popup.setAttribute(Qt.WA_DeleteOnClose)
        popup.setWindowTitle("下载")
        popup.resize(900, 600)
        popup.show()
        if self.popup_list is not None:
            self.popup_list.append(popup)
        return popup

class MachineryLibrary(QWidget):
    def __init__(self):
        super().__init__()
        self.popup_windows = []
        self.setFont(QFont("微软雅黑", 15))
        self.setStyleSheet("""
            QWidget {
                background: #f8fbfd;
                border-radius: 16px;
                padding: 20px;
            }
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(32, 32, 32, 32)

        # 标题区
        title = QLabel("MRobot 零件库")
        title.setFont(QFont("微软雅黑", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2980b9; letter-spacing: 2px; margin-bottom: 2px;")
        main_layout.addWidget(title)

        desc = QLabel("零件库账号：Engineer（无密码）")
        desc.setFont(QFont("微软雅黑", 13))
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #34495e; margin-bottom: 8px;")
        main_layout.addWidget(desc)

        # 加载提示
        self.loading_label = QLabel("正在加载零件库网页，请稍候...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setFont(QFont("微软雅黑", 14))
        self.loading_label.setStyleSheet("color: #888; margin-bottom: 8px;")
        main_layout.addWidget(self.loading_label)

        # 网页视图
        self.webview = CustomWebView(parent=self, popup_list=self.popup_windows)
        self.webview.setAttribute(Qt.WA_TranslucentBackground, True)
        self.webview.setMinimumHeight(480)
        self.webview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.webview.loadFinished.connect(self.on_webview_loaded)
        main_layout.addWidget(self.webview, stretch=10)

        # 刷新按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.refresh_btn = QPushButton("刷新零件库")
        self.refresh_btn.setFont(QFont("微软雅黑", 13, QFont.Bold))
        self.refresh_btn.setFixedWidth(140)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eaf6fb, stop:1 #d6eaf8);
                color: #2980b9;
                border-radius: 14px;
                font-size: 15px;
                font-weight: 600;
                padding: 8px 0;
                border: 1.5px solid #d6eaf8;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fffe, stop:1 #cfe7fa);
                color: #1a6fae;
                border: 2px solid #b5d0ea;
            }
            QPushButton:pressed {
                background: #e3f0fa;
                color: #2471a3;
                border: 2px solid #a4cbe3;
            }
        """)
        self.refresh_btn.clicked.connect(self.reload_webview)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addStretch(1)
        main_layout.addLayout(btn_row)

        # 自动加载网页
        QTimer.singleShot(200, lambda: self.webview.setUrl(QUrl("http://alist.qutrobot.top")))
        self.webview.show()

        # 定时刷新（可选，防止页面假死）
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(100)
        self.refresh_timer.timeout.connect(self.webview.update)
        self.refresh_timer.start()

    def reload_webview(self):
        self.loading_label.show()
        self.webview.setUrl(QUrl("http://alist.qutrobot.top"))

    def on_webview_loaded(self):
        self.loading_label.hide()

    def closeEvent(self, event):
        self.refresh_timer.stop()
        super().closeEvent(event)
# --------- 主工具箱UI ---------
class ToolboxUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MRobot 工具箱")
        self.resize(1920, 1080)
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eaf6fb, stop:1 #d6eaf8);
                border-radius: 16px;
            }
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 左侧导航
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.StyledPanel)
        left_frame.setStyleSheet("""
            QFrame {
                background: #f8fbfd;
                border-radius: 14px;
                border: 1px solid #d6eaf8;
            }
        """)
        left_shadow = QGraphicsDropShadowEffect(self)
        left_shadow.setBlurRadius(16)
        left_shadow.setOffset(0, 4)
        left_shadow.setColor(Qt.gray)
        left_frame.setGraphicsEffect(left_shadow)

        left_layout = QVBoxLayout(left_frame)
        left_layout.setSpacing(24)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_frame.setFixedWidth(260)
        main_layout.addWidget(left_frame)

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("mr_tool_img/MRobot.png"))
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(180, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("MRobot")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFont(QFont("Arial", 36, QFont.Bold))
        logo_label.setStyleSheet("color: #3498db;")
        logo_label.setFixedHeight(120)
        left_layout.addWidget(logo_label)

        # 按钮区
        self.button_names = ["主页", "曲线拟合", "Mini串口助手(BUG)", "MR架构配置(开发中)", "零件库", "软件指南"]
        self.buttons = []
        for idx, name in enumerate(self.button_names):
            btn = QPushButton(name)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(48)
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #eaf6fb, stop:1 #d6eaf8);
                    color: #2980b9;
                    border-radius: 20px;
                    font-size: 22px;
                    font-weight: 600;
                    padding: 14px 0;
                    border: 1px solid #d6eaf8;
                    letter-spacing: 2px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f8fffe, stop:1 #cfe7fa);
                    color: #1a6fae;
                    border: 1.5px solid #b5d0ea;
                }
                QPushButton:pressed {
                    background: #e3f0fa;
                    color: #2471a3;
                    border: 1.5px solid #a4cbe3;
                }
            """)
            btn.clicked.connect(lambda checked, i=idx: self.switch_function(i))
            self.buttons.append(btn)
            left_layout.addWidget(btn)

        left_layout.addStretch(1)

        # 文本输出框
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setFixedHeight(180)
        self.output_box.setStyleSheet("""
            QTextEdit {
                background: #f4f6f7;
                border-radius: 8px;
                border: 1px solid #d6eaf8;
                font-size: 16px;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        left_layout.addWidget(self.output_box)

        # 右侧功能区
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("""
            QStackedWidget {
                background: #fff;
                border-radius: 16px;
                border: 1px solid #d6eaf8;
            }
        """)
        right_shadow = QGraphicsDropShadowEffect(self)
        right_shadow.setBlurRadius(24)
        right_shadow.setOffset(0, 4)
        right_shadow.setColor(Qt.gray)
        self.stack.setGraphicsEffect(right_shadow)

        # 功能页面注册（后续扩展只需在这里添加页面类即可）
        self.page_widgets = {
            0: HomePage(),  # 主页
            1: PolyFitApp(),  # 多项式拟合
            2: SerialAssistant(),  # 串口助手
            3: GenerateMRobotCode(),  # MRobot架构生成
            4: MachineryLibrary(),  # 零件库
            5: DownloadPage(),  # 下载页面
        }
        for i in range(len(self.button_names)):
            self.stack.addWidget(self.page_widgets[i])
        main_layout.addWidget(self.stack)

        self.output_box.append("欢迎使用 MRobot 工具箱！请选择左侧功能。")



    def placeholder_page(self, text):
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("微软雅黑", 22, QFont.Bold))
        label.setStyleSheet("color: #2980b9;")
        layout.addStretch(1)
        layout.addWidget(label)
        layout.addStretch(1)
        return page

    def switch_function(self, idx):
        self.stack.setCurrentIndex(idx)
        self.output_box.append(f"已切换到功能：{self.button_names[idx]}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ToolboxUI()
    win.show()
    sys.exit(app.exec_())