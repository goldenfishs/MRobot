from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QSizePolicy
from PyQt5.QtCore import Qt
from qfluentwidgets import (TitleLabel, SubtitleLabel, BodyLabel, LineEdit, PushButton, 
                           ComboBox, CardWidget, FluentIcon, InfoBar, DoubleSpinBox, 
                           PushSettingCard, TabBar)
import math


class GearCalculator(QWidget):
    """齿轮参数计算器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GearCalculator")
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)
        
        # 标题
        title = SubtitleLabel("齿轮参数计算")
        layout.addWidget(title)
        
        # 说明
        desc = BodyLabel("输入任意已知参数，点击计算按钮自动计算其他参数")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # 参数输入区域
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # 齿轮1参数
        grid_layout.addWidget(BodyLabel("齿轮1 模数 (m):"), 0, 0)
        self.module1_spin = DoubleSpinBox()
        self.module1_spin.setRange(0, 100)
        self.module1_spin.setSingleStep(0.5)
        self.module1_spin.setDecimals(2)
        self.module1_spin.setSuffix(" mm")
        grid_layout.addWidget(self.module1_spin, 0, 1)
        
        grid_layout.addWidget(BodyLabel("齿轮1 齿数 (Z1):"), 1, 0)
        self.teeth1_spin = DoubleSpinBox()
        self.teeth1_spin.setRange(0, 500)
        self.teeth1_spin.setSingleStep(1)
        self.teeth1_spin.setDecimals(0)
        grid_layout.addWidget(self.teeth1_spin, 1, 1)
        
        grid_layout.addWidget(BodyLabel("齿轮1 分度圆直径 (d1):"), 2, 0)
        self.diameter1_spin = DoubleSpinBox()
        self.diameter1_spin.setRange(0, 1000)
        self.diameter1_spin.setSingleStep(1)
        self.diameter1_spin.setDecimals(2)
        self.diameter1_spin.setSuffix(" mm")
        grid_layout.addWidget(self.diameter1_spin, 2, 1)
        
        # 齿轮2参数
        grid_layout.addWidget(BodyLabel("齿轮2 齿数 (Z2):"), 0, 2)
        self.teeth2_spin = DoubleSpinBox()
        self.teeth2_spin.setRange(0, 500)
        self.teeth2_spin.setSingleStep(1)
        self.teeth2_spin.setDecimals(0)
        grid_layout.addWidget(self.teeth2_spin, 0, 3)
        
        grid_layout.addWidget(BodyLabel("齿轮2 分度圆直径 (d2):"), 1, 2)
        self.diameter2_spin = DoubleSpinBox()
        self.diameter2_spin.setRange(0, 1000)
        self.diameter2_spin.setSingleStep(1)
        self.diameter2_spin.setDecimals(2)
        self.diameter2_spin.setSuffix(" mm")
        grid_layout.addWidget(self.diameter2_spin, 1, 3)
        
        # 中心距
        grid_layout.addWidget(BodyLabel("中心距 (a):"), 2, 2)
        self.center_distance_spin = DoubleSpinBox()
        self.center_distance_spin.setRange(0, 2000)
        self.center_distance_spin.setSingleStep(1)
        self.center_distance_spin.setDecimals(2)
        self.center_distance_spin.setSuffix(" mm")
        grid_layout.addWidget(self.center_distance_spin, 2, 3)
        
        # 传动比
        grid_layout.addWidget(BodyLabel("传动比 (i):"), 3, 0)
        self.ratio_spin = DoubleSpinBox()
        self.ratio_spin.setRange(0, 100)
        self.ratio_spin.setSingleStep(0.1)
        self.ratio_spin.setDecimals(3)
        grid_layout.addWidget(self.ratio_spin, 3, 1)
        
        layout.addLayout(grid_layout)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self.calc_btn = PushButton(FluentIcon.PLAY, "计算")
        self.calc_btn.clicked.connect(self._calculate)
        self.clear_btn = PushButton(FluentIcon.DELETE, "清空")
        self.clear_btn.clicked.connect(self._clear)
        btn_layout.addWidget(self.calc_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 结果显示
        self.result_label = BodyLabel("")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
    
    def _calculate(self):
        """计算齿轮参数"""
        try:
            # 获取输入值
            m = self.module1_spin.value() if self.module1_spin.value() > 0 else None
            z1 = self.teeth1_spin.value() if self.teeth1_spin.value() > 0 else None
            d1 = self.diameter1_spin.value() if self.diameter1_spin.value() > 0 else None
            z2 = self.teeth2_spin.value() if self.teeth2_spin.value() > 0 else None
            d2 = self.diameter2_spin.value() if self.diameter2_spin.value() > 0 else None
            a = self.center_distance_spin.value() if self.center_distance_spin.value() > 0 else None
            i = self.ratio_spin.value() if self.ratio_spin.value() > 0 else None
            
            # 齿轮基本公式：d = m * z, a = (d1 + d2) / 2, i = z2 / z1
            
            # 尝试计算模数
            if m is None:
                if d1 and z1:
                    m = d1 / z1
                    self.module1_spin.setValue(m)
                elif d2 and z2:
                    m = d2 / z2
                    self.module1_spin.setValue(m)
            
            # 尝试计算齿轮1参数
            if z1 is None and d1 and m:
                z1 = round(d1 / m)
                self.teeth1_spin.setValue(z1)
            elif d1 is None and z1 and m:
                d1 = m * z1
                self.diameter1_spin.setValue(d1)
            
            # 尝试计算齿轮2参数
            if z2 is None and d2 and m:
                z2 = round(d2 / m)
                self.teeth2_spin.setValue(z2)
            elif d2 is None and z2 and m:
                d2 = m * z2
                self.diameter2_spin.setValue(d2)
            
            # 尝试计算传动比
            if i is None and z1 and z2:
                i = z2 / z1
                self.ratio_spin.setValue(i)
            
            # 尝试根据传动比计算齿数
            if i and z1 and z2 is None:
                z2 = round(z1 * i)
                self.teeth2_spin.setValue(z2)
                if m:
                    d2 = m * z2
                    self.diameter2_spin.setValue(d2)
            
            # 尝试计算中心距
            if a is None and d1 and d2:
                a = (d1 + d2) / 2
                self.center_distance_spin.setValue(a)
            
            # 尝试根据中心距计算参数
            if a and d1 and d2 is None:
                d2 = 2 * a - d1
                self.diameter2_spin.setValue(d2)
                if m:
                    z2 = round(d2 / m)
                    self.teeth2_spin.setValue(z2)
            
            self.result_label.setText("✓ 计算完成！请检查结果是否符合预期。")
            
        except Exception as e:
            InfoBar.error(
                title="计算错误",
                content=f"计算失败: {str(e)}",
                parent=self,
                duration=3000
            )
    
    def _clear(self):
        """清空所有输入"""
        self.module1_spin.setValue(0)
        self.teeth1_spin.setValue(0)
        self.diameter1_spin.setValue(0)
        self.teeth2_spin.setValue(0)
        self.diameter2_spin.setValue(0)
        self.center_distance_spin.setValue(0)
        self.ratio_spin.setValue(0)
        self.result_label.setText("")


class TimingBeltCalculator(QWidget):
    """同步带轮参数计算器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TimingBeltCalculator")
        
        # 常见同步带型号的节距（pitch）数据 (mm)
        self.belt_pitches = {
            "MXL": 2.032,
            "XL": 5.08,
            "L": 9.525,
            "H": 12.7,
            "XH": 22.225,
            "XXH": 31.75,
            "T2.5": 2.5,
            "T5": 5.0,
            "T10": 10.0,
            "T20": 20.0,
            "AT5": 5.0,
            "AT10": 10.0,
            "AT20": 20.0,
            "HTD 3M": 3.0,
            "HTD 5M": 5.0,
            "HTD 8M": 8.0,
            "HTD 14M": 14.0,
            "HTD 20M": 20.0,
            "GT2 2M": 2.0,
            "GT2 3M": 3.0,
            "GT2 5M": 5.0,
        }
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)
        
        # 标题
        title = SubtitleLabel("同步带轮参数计算")
        layout.addWidget(title)
        
        # 说明
        desc = BodyLabel("选择同步带型号，输入已知参数进行计算")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # 参数输入区域
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # 同步带型号
        grid_layout.addWidget(BodyLabel("同步带型号:"), 0, 0)
        self.belt_type_combo = ComboBox()
        self.belt_type_combo.addItems(list(self.belt_pitches.keys()))
        self.belt_type_combo.setCurrentText("GT2 2M")
        grid_layout.addWidget(self.belt_type_combo, 0, 1)
        
        grid_layout.addWidget(BodyLabel("节距 (pitch):"), 0, 2)
        self.pitch_spin = DoubleSpinBox()
        self.pitch_spin.setRange(0, 100)
        self.pitch_spin.setSingleStep(0.1)
        self.pitch_spin.setDecimals(3)
        self.pitch_spin.setSuffix(" mm")
        self.pitch_spin.setValue(2.0)
        self.pitch_spin.setEnabled(False)
        grid_layout.addWidget(self.pitch_spin, 0, 3)
        
        # 带轮1参数
        grid_layout.addWidget(BodyLabel("带轮1 齿数 (Z1):"), 1, 0)
        self.pulley1_teeth_spin = DoubleSpinBox()
        self.pulley1_teeth_spin.setRange(0, 500)
        self.pulley1_teeth_spin.setSingleStep(1)
        self.pulley1_teeth_spin.setDecimals(0)
        grid_layout.addWidget(self.pulley1_teeth_spin, 1, 1)
        
        grid_layout.addWidget(BodyLabel("带轮1 节圆直径 (PD1):"), 2, 0)
        self.pulley1_pd_spin = DoubleSpinBox()
        self.pulley1_pd_spin.setRange(0, 1000)
        self.pulley1_pd_spin.setSingleStep(1)
        self.pulley1_pd_spin.setDecimals(2)
        self.pulley1_pd_spin.setSuffix(" mm")
        grid_layout.addWidget(self.pulley1_pd_spin, 2, 1)
        
        # 带轮2参数
        grid_layout.addWidget(BodyLabel("带轮2 齿数 (Z2):"), 1, 2)
        self.pulley2_teeth_spin = DoubleSpinBox()
        self.pulley2_teeth_spin.setRange(0, 500)
        self.pulley2_teeth_spin.setSingleStep(1)
        self.pulley2_teeth_spin.setDecimals(0)
        grid_layout.addWidget(self.pulley2_teeth_spin, 1, 3)
        
        grid_layout.addWidget(BodyLabel("带轮2 节圆直径 (PD2):"), 2, 2)
        self.pulley2_pd_spin = DoubleSpinBox()
        self.pulley2_pd_spin.setRange(0, 1000)
        self.pulley2_pd_spin.setSingleStep(1)
        self.pulley2_pd_spin.setDecimals(2)
        self.pulley2_pd_spin.setSuffix(" mm")
        grid_layout.addWidget(self.pulley2_pd_spin, 2, 3)
        
        # 中心距和带长
        grid_layout.addWidget(BodyLabel("中心距 (C):"), 3, 0)
        self.center_distance_spin = DoubleSpinBox()
        self.center_distance_spin.setRange(0, 5000)
        self.center_distance_spin.setSingleStep(1)
        self.center_distance_spin.setDecimals(2)
        self.center_distance_spin.setSuffix(" mm")
        grid_layout.addWidget(self.center_distance_spin, 3, 1)
        
        grid_layout.addWidget(BodyLabel("带长 (L):"), 3, 2)
        self.belt_length_spin = DoubleSpinBox()
        self.belt_length_spin.setRange(0, 10000)
        self.belt_length_spin.setSingleStep(1)
        self.belt_length_spin.setDecimals(2)
        self.belt_length_spin.setSuffix(" mm")
        grid_layout.addWidget(self.belt_length_spin, 3, 3)
        
        # 带齿数和传动比
        grid_layout.addWidget(BodyLabel("带齿数 (Tb):"), 4, 0)
        self.belt_teeth_spin = DoubleSpinBox()
        self.belt_teeth_spin.setRange(0, 5000)
        self.belt_teeth_spin.setSingleStep(1)
        self.belt_teeth_spin.setDecimals(0)
        grid_layout.addWidget(self.belt_teeth_spin, 4, 1)
        
        grid_layout.addWidget(BodyLabel("传动比 (i):"), 4, 2)
        self.ratio_spin = DoubleSpinBox()
        self.ratio_spin.setRange(0, 100)
        self.ratio_spin.setSingleStep(0.1)
        self.ratio_spin.setDecimals(3)
        grid_layout.addWidget(self.ratio_spin, 4, 3)
        
        layout.addLayout(grid_layout)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self.calc_btn = PushButton(FluentIcon.PLAY, "计算")
        self.calc_btn.clicked.connect(self._calculate)
        self.clear_btn = PushButton(FluentIcon.DELETE, "清空")
        self.clear_btn.clicked.connect(self._clear)
        btn_layout.addWidget(self.calc_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 结果显示
        self.result_label = BodyLabel("")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
        
        # 连接信号
        self.belt_type_combo.currentTextChanged.connect(self._on_belt_type_changed)
    
    def _on_belt_type_changed(self, text):
        """同步带型号改变时更新节距"""
        pitch = self.belt_pitches.get(text, 2.0)
        self.pitch_spin.setValue(pitch)
    
    def _calculate(self):
        """计算同步带参数"""
        try:
            # 获取输入值
            pitch = self.pitch_spin.value()
            z1 = self.pulley1_teeth_spin.value() if self.pulley1_teeth_spin.value() > 0 else None
            pd1 = self.pulley1_pd_spin.value() if self.pulley1_pd_spin.value() > 0 else None
            z2 = self.pulley2_teeth_spin.value() if self.pulley2_teeth_spin.value() > 0 else None
            pd2 = self.pulley2_pd_spin.value() if self.pulley2_pd_spin.value() > 0 else None
            c = self.center_distance_spin.value() if self.center_distance_spin.value() > 0 else None
            l = self.belt_length_spin.value() if self.belt_length_spin.value() > 0 else None
            tb = self.belt_teeth_spin.value() if self.belt_teeth_spin.value() > 0 else None
            i = self.ratio_spin.value() if self.ratio_spin.value() > 0 else None
            
            # 同步带公式：
            # PD = (Z * pitch) / π
            # L = 2C + π(PD1 + PD2)/2 + (PD2 - PD1)²/(4C)
            # Tb = L / pitch
            
            # 计算节圆直径
            if pd1 is None and z1:
                pd1 = (z1 * pitch) / math.pi
                self.pulley1_pd_spin.setValue(pd1)
            elif z1 is None and pd1:
                z1 = round((pd1 * math.pi) / pitch)
                self.pulley1_teeth_spin.setValue(z1)
            
            if pd2 is None and z2:
                pd2 = (z2 * pitch) / math.pi
                self.pulley2_pd_spin.setValue(pd2)
            elif z2 is None and pd2:
                z2 = round((pd2 * math.pi) / pitch)
                self.pulley2_teeth_spin.setValue(z2)
            
            # 计算传动比
            if i is None and z1 and z2:
                i = z2 / z1
                self.ratio_spin.setValue(i)
            elif i and z1 and z2 is None:
                z2 = round(z1 * i)
                self.pulley2_teeth_spin.setValue(z2)
                pd2 = (z2 * pitch) / math.pi
                self.pulley2_pd_spin.setValue(pd2)
            
            # 计算带长
            if l is None and c and pd1 and pd2:
                l = 2 * c + math.pi * (pd1 + pd2) / 2 + (pd2 - pd1) ** 2 / (4 * c)
                self.belt_length_spin.setValue(l)
            
            # 计算带齿数
            if tb is None and l:
                tb = round(l / pitch)
                self.belt_teeth_spin.setValue(tb)
            elif l is None and tb:
                l = tb * pitch
                self.belt_length_spin.setValue(l)
            
            # 根据带长和节圆直径计算中心距（近似）
            if c is None and l and pd1 and pd2:
                # 使用近似公式求解
                b = math.pi * (pd1 + pd2) / 2
                a_term = (pd2 - pd1) ** 2 / 4
                # 2C + b + a_term/C = L
                # 求解二次方程: 2C² + bC + a_term - LC = 0
                # 2C² + (b-L)C + a_term = 0
                A = 2
                B = b - l
                C_term = a_term
                discriminant = B**2 - 4*A*C_term
                if discriminant >= 0:
                    c = (-B + math.sqrt(discriminant)) / (2*A)
                    self.center_distance_spin.setValue(c)
            
            self.result_label.setText("✓ 计算完成！请检查结果是否符合预期。\n提示：带长计算为理论值，实际选型请参考标准带长。")
            
        except Exception as e:
            InfoBar.error(
                title="计算错误",
                content=f"计算失败: {str(e)}",
                parent=self,
                duration=3000
            )
    
    def _clear(self):
        """清空所有输入"""
        self.pulley1_teeth_spin.setValue(0)
        self.pulley1_pd_spin.setValue(0)
        self.pulley2_teeth_spin.setValue(0)
        self.pulley2_pd_spin.setValue(0)
        self.center_distance_spin.setValue(0)
        self.belt_length_spin.setValue(0)
        self.belt_teeth_spin.setValue(0)
        self.ratio_spin.setValue(0)
        self.result_label.setText("")


class MechDesignInterface(QWidget):
    """机械设计计算界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MechDesignInterface")
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(10, 0, 10, 10)
        
        # 顶部标签栏
        self.tabBar = TabBar(self)
        self.tabBar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.tabBar)
        
        self.stackedWidget = QStackedWidget(self)
        layout.addWidget(self.stackedWidget)
        
        # 主页面
        self.mainPage = QWidget(self)
        mainLayout = QVBoxLayout(self.mainPage)
        mainLayout.setAlignment(Qt.AlignTop)
        mainLayout.setContentsMargins(20, 20, 20, 20)
        mainLayout.setSpacing(15)
        
        # 页面标题
        title = SubtitleLabel("机械设计计算工具")
        mainLayout.addWidget(title)
        
        # 页面说明
        desc = BodyLabel("选择需要的计算工具")
        desc.setWordWrap(True)
        mainLayout.addWidget(desc)
        
        # 齿轮计算器卡片
        self.gearCard = PushSettingCard(
            text="▶ 启动",
            icon=FluentIcon.UNIT,
            title="齿轮参数计算",
            content="计算齿轮模数、齿数、分度圆直径、中心距、传动比等参数"
        )
        self.gearCard.clicked.connect(self.open_gear_tab)
        mainLayout.addWidget(self.gearCard)
        
        # 同步带计算器卡片
        self.beltCard = PushSettingCard(
            text="▶ 启动",
            icon=FluentIcon.SYNC,
            title="同步带轮参数计算",
            content="计算同步带轮齿数、节圆直径、中心距、带长等参数"
        )
        self.beltCard.clicked.connect(self.open_belt_tab)
        mainLayout.addWidget(self.beltCard)
        
        mainLayout.addStretch()
        
        # 添加主页面到堆叠窗口
        self.addSubInterface(self.mainPage, "mainPage", "机械设计")
        
        # 信号连接
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.tabBar.tabCloseRequested.connect(self.onCloseTab)
    
    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.tabBar.addTab(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )
    
    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.tabBar.setCurrentTab(widget.objectName())
    
    def onCloseTab(self, index: int):
        item = self.tabBar.tabItem(index)
        widget = self.findChild(QWidget, item.routeKey())
        # 禁止关闭主页
        if widget.objectName() == "mainPage":
            return
        self.stackedWidget.removeWidget(widget)
        self.tabBar.removeTab(index)
        widget.deleteLater()
    
    def open_gear_tab(self):
        # 检查是否已存在标签页，避免重复添加
        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if widget.objectName() == "gearPage":
                self.stackedWidget.setCurrentWidget(widget)
                self.tabBar.setCurrentTab("gearPage")
                return
        gear_page = GearCalculator(self)
        self.addSubInterface(gear_page, "gearPage", "齿轮计算")
        self.stackedWidget.setCurrentWidget(gear_page)
        self.tabBar.setCurrentTab("gearPage")
    
    def open_belt_tab(self):
        # 检查是否已存在标签页，避免重复添加
        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if widget.objectName() == "beltPage":
                self.stackedWidget.setCurrentWidget(widget)
                self.tabBar.setCurrentTab("beltPage")
                return
        belt_page = TimingBeltCalculator(self)
        self.addSubInterface(belt_page, "beltPage", "同步带计算")
        self.stackedWidget.setCurrentWidget(belt_page)
        self.tabBar.setCurrentTab("beltPage")
