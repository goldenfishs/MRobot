import serial
import serial.tools.list_ports
import pyqtgraph as pg
import struct
import time
from datetime import datetime
from collections import deque
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QSizePolicy, QStackedWidget
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (
    FluentIcon, PushButton, ComboBox, TextEdit, LineEdit, CheckBox,
    SubtitleLabel, BodyLabel, HorizontalSeparator, PrimaryPushButton,
    isDarkTheme, qconfig, CardWidget, StrongBodyLabel, CaptionLabel
)

class SerialReadThread(QThread):
    data_received = pyqtSignal(str)
    raw_data_received = pyqtSignal(bytes)

    def __init__(self, ser, parent_widget=None):
        super().__init__()
        self.ser = ser
        self.parent_widget = parent_widget
        self._running = True
        self.buffer = bytearray()
        self.batch_size = 8192

    def run(self):
        while self._running: 
            if self.ser and self.ser.is_open:
                try:
                    if self.ser.in_waiting:
                        bytes_to_read = min(self.ser.in_waiting, self.batch_size)
                        raw_data = self.ser.read(bytes_to_read)
                        if raw_data:
                            self.buffer.extend(raw_data)
                            self.raw_data_received.emit(bytes(raw_data))
                            
                            # 检查显示设置
                            is_hex_receive = True
                            is_timestamp = True
                            if self.parent_widget:
                                if hasattr(self.parent_widget, 'hex_receive_checkbox'):
                                    is_hex_receive = self.parent_widget.hex_receive_checkbox.isChecked()
                                if hasattr(self.parent_widget, 'timestamp_checkbox'):
                                    is_timestamp = self.parent_widget.timestamp_checkbox.isChecked()
                            
                            # 格式化数据
                            if is_hex_receive:
                                display_data = ' '.join([f'{b:02X}' for b in raw_data])
                            else:
                                try:
                                    display_data = raw_data.decode('utf-8', errors='replace')
                                except:
                                    display_data = ' '.join([f'{b:02X}' for b in raw_data])
                            
                            if display_data:
                                if is_timestamp:
                                    timestamp = datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
                                    data_to_send = timestamp + display_data + '\n'
                                else:
                                    data_to_send = display_data + '\n'
                                self.data_received.emit(data_to_send)
                        
                except Exception as e:
                    print(f"串口读取错误: {e}")
            
            self.msleep(1)

    def stop(self):
        self._running = False
        self.wait()


class SerialTerminalInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("serialTerminalInterface")
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # 顶部：基本设置行（始终显示）
        basic_layout = QHBoxLayout()
        basic_layout.addWidget(BodyLabel("串口:"))
        self.port_combo = ComboBox()
        self.refresh_ports()
        basic_layout.addWidget(self.port_combo)
        self.refresh_btn = PushButton(FluentIcon.SYNC, "刷新")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        basic_layout.addWidget(self.refresh_btn)
        basic_layout.addWidget(BodyLabel("波特率:"))
        self.baud_combo = ComboBox()
        self.baud_combo.addItems(['115200', '9600', '57600', '38400', '19200', '4800'])
        self.baud_combo.setCurrentText('9600')
        basic_layout.addWidget(self.baud_combo)
        
        self.connect_btn = PrimaryPushButton("连接串口")
        self.connect_btn.clicked.connect(self.toggle_connection)
        basic_layout.addWidget(self.connect_btn)
        
        # 展开/折叠按钮
        self.expand_btn = PushButton(FluentIcon.DOWN, "高级设置")
        self.expand_btn.clicked.connect(self.toggle_advanced_settings)
        basic_layout.addWidget(self.expand_btn)
        basic_layout.addStretch()
        main_layout.addLayout(basic_layout)
        
        # 高级设置 - 默认隐藏
        self.advanced_widget = QWidget()
        self.advanced_widget.setVisible(False)
        advanced_main_layout = QVBoxLayout(self.advanced_widget)
        advanced_main_layout.setContentsMargins(0, 8, 0, 0)
        advanced_main_layout.setSpacing(8)
        
        # 详细设置行
        detail_layout = QHBoxLayout()
        detail_layout.addWidget(BodyLabel("数据位:"))
        self.data_bits_combo = ComboBox()
        self.data_bits_combo.addItems(['8', '7', '6', '5'])
        self.data_bits_combo.setCurrentText('8')
        detail_layout.addWidget(self.data_bits_combo)
        
        detail_layout.addWidget(BodyLabel("校验位:"))
        self.parity_combo = ComboBox()
        self.parity_combo.addItems(['None', 'Even', 'Odd', 'Mark', 'Space'])
        self.parity_combo.setCurrentText('None')
        detail_layout.addWidget(self.parity_combo)
        
        detail_layout.addWidget(BodyLabel("停止位:"))
        self.stop_bits_combo = ComboBox()
        self.stop_bits_combo.addItems(['1', '1.5', '2'])
        self.stop_bits_combo.setCurrentText('1')
        detail_layout.addWidget(self.stop_bits_combo)
        detail_layout.addStretch()
        advanced_main_layout.addLayout(detail_layout)
        
        main_layout.addWidget(self.advanced_widget)
        main_layout.addWidget(HorizontalSeparator())

        # 初始化状态变量
        self.ser = None
        self.read_thread = None
        self.is_chart_mode = False  # 默认使用文本模式
        self.is_paused = False

        # 中部：左侧快捷命令，右侧显示区
        center_hbox = QHBoxLayout()
        
        # 左侧：快捷命令区域
        preset_widget = QWidget()
        preset_widget.setFixedWidth(250)
        preset_vbox = QVBoxLayout(preset_widget)
        preset_vbox.addWidget(SubtitleLabel("快捷指令"))
        preset_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 预设命令配置
        self.preset_commands = [
            ("性能监视", "htop"),
            ("陀螺仪校准", "cali_gyro"),
            ("重启", "reset"),
        ]
        
        for label, cmd in self.preset_commands:
            btn = PushButton(FluentIcon.SEND, label)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.clicked.connect(lambda _, c=cmd: self.send_preset_command(c))
            preset_vbox.addWidget(btn)
        
        # 添加使用说明
        preset_vbox.addSpacing(16)
        preset_vbox.addWidget(HorizontalSeparator())
        preset_vbox.addSpacing(8)
        
        # 使用说明标题
        usage_title = SubtitleLabel("使用说明")
        usage_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preset_vbox.addWidget(usage_title)
        preset_vbox.addSpacing(8)
        
        # 使用说明内容
        usage_content = BodyLabel()
        usage_content.setText(
            "• 波形图显示：\n"
            "  发送格式化数据（逗号或空格分隔的数值）\n"
            "  如: 1.2, 3.4, 5.6\n"
            "  系统将自动识别数据通道并创建波形\n\n"
        )
        usage_content.setWordWrap(True)
        usage_content.setAlignment(Qt.AlignmentFlag.AlignLeft)
        preset_vbox.addWidget(usage_content)
        
        preset_vbox.addStretch()
        center_hbox.addWidget(preset_widget)
        
        # 右侧：显示区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 切换按钮区域
        switch_layout = QHBoxLayout()
        switch_layout.addWidget(BodyLabel("显示模式:"))
        self.mode_toggle_btn = PushButton("切换到波形图")
        self.mode_toggle_btn.clicked.connect(self.toggle_display_mode)
        switch_layout.addWidget(self.mode_toggle_btn)
        
        self.pause_btn = PushButton(FluentIcon.PAUSE, "暂停接收")
        self.pause_btn.clicked.connect(self.toggle_pause_receive)
        switch_layout.addWidget(self.pause_btn)
        
        self.clear_btn = PushButton(FluentIcon.DELETE, "清空")
        self.clear_btn.clicked.connect(self.clear_display)
        switch_layout.addWidget(self.clear_btn)
        
        self.hex_receive_checkbox = CheckBox("HEX接收  ")
        self.hex_receive_checkbox.setChecked(True)
        switch_layout.addWidget(self.hex_receive_checkbox)
        
        self.timestamp_checkbox = CheckBox("时间戳")
        self.timestamp_checkbox.setChecked(True)
        switch_layout.addWidget(self.timestamp_checkbox)
        
        switch_layout.addStretch()
        right_layout.addLayout(switch_layout)
        
        # 创建堆叠布局用于切换显示内容
        self.display_stack = QStackedWidget()
        
        # 原始数据显示页面
        self.text_edit = TextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMinimumWidth(400)
        self.display_stack.addWidget(self.text_edit)
        
        # 波形图显示页面
        self.setup_chart_widget()
        
        right_layout.addWidget(self.display_stack)
        center_hbox.addWidget(right_widget, 1)
        
        main_layout.addLayout(center_hbox, stretch=1)
        main_layout.addWidget(HorizontalSeparator())

        # 底部：输入区
        bottom_hbox = QHBoxLayout()
        self.input_line = LineEdit()
        self.input_line.setPlaceholderText("输入内容，回车发送")
        self.input_line.returnPressed.connect(self.send_data)
        bottom_hbox.addWidget(self.input_line, 4)
        send_btn = PushButton(FluentIcon.SEND, "发送")
        send_btn.clicked.connect(self.send_data)
        bottom_hbox.addWidget(send_btn, 1)
        
        self.hex_send_checkbox = CheckBox("HEX发送")
        self.hex_send_checkbox.setChecked(False)
        self.hex_send_checkbox.stateChanged.connect(self.update_input_placeholder)
        bottom_hbox.addWidget(self.hex_send_checkbox)
        
        bottom_hbox.addWidget(BodyLabel("末尾添加"))
        self.line_ending_combo = ComboBox()
        self.line_ending_combo.addItems(['\\n', '无', '\\r', '\\r\\n'])
        self.line_ending_combo.setCurrentText('\\n')
        bottom_hbox.addWidget(self.line_ending_combo)
        
        # 自动发送功能
        self.auto_send_checkbox = CheckBox("自动发送")
        self.auto_send_checkbox.setChecked(False)
        self.auto_send_checkbox.stateChanged.connect(self.toggle_auto_send)
        bottom_hbox.addWidget(self.auto_send_checkbox)
        
        bottom_hbox.addWidget(BodyLabel("间隔(ms):"))
        self.auto_send_interval = LineEdit()
        self.auto_send_interval.setPlaceholderText("1000")
        self.auto_send_interval.setText("1000")
        self.auto_send_interval.setMaximumWidth(80)
        bottom_hbox.addWidget(self.auto_send_interval)
        
        bottom_hbox.addStretch()
        main_layout.addLayout(bottom_hbox)

        # 数据解析相关
        self.data_buffer = bytearray()
        self.max_data_points = 5000
        self.data_history = {}  # 动态存储数据
        self.data_timestamps = deque(maxlen=self.max_data_points)
        self.data_channels = []  # 数据通道列表
        
        # 图表更新定时器
        self.chart_timer = QTimer()
        self.chart_timer.timeout.connect(self.update_charts)
        self.chart_timer.setInterval(50)
        
        # 自动发送定时器
        self.auto_send_timer = QTimer()
        self.auto_send_timer.timeout.connect(self.auto_send_data)
        
        # 监听主题变化
        qconfig.themeChangedFinished.connect(self.on_theme_changed)

    def setup_chart_widget(self):
        """设置波形图显示区域"""
        chart_container = QWidget()
        chart_main_layout = QHBoxLayout(chart_container)
        chart_main_layout.setContentsMargins(0, 0, 0, 0)
        chart_main_layout.setSpacing(8)
        
        # 左侧：波形图
        self.main_plot = pg.PlotWidget()
        self.apply_plot_style()
        self.main_plot.setTitle('实时数据波形图', size='14pt')
        self.main_plot.showGrid(x=True, y=True, alpha=0.3)
        self.main_plot.setLabel('left', '数值')
        self.main_plot.setLabel('bottom', '时间 (ms)')
        self.main_plot.setAntialiasing(True)
        self.main_plot.setMouseEnabled(x=True, y=True)
        self.main_plot.enableAutoRange()
        
        chart_main_layout.addWidget(self.main_plot, 3)
        
        # 右侧：实时数据显示面板
        self.setup_data_display_panel()
        chart_main_layout.addWidget(self.data_display_panel, 1)
        
        self.display_stack.addWidget(chart_container)
        self.display_stack.setCurrentIndex(0)  # 默认显示文本
        
        # 初始化曲线字典
        self.curves = {}
        
    def setup_data_display_panel(self):
        """设置实时数据显示面板"""
        self.data_display_panel = CardWidget()
        self.data_display_panel.setFixedWidth(200)
        
        panel_layout = QVBoxLayout(self.data_display_panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(12)
        
        title_label = SubtitleLabel("实时数据")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(title_label)
        
        panel_layout.addWidget(HorizontalSeparator())
        panel_layout.addSpacing(8)
        
        # 数据标签容器
        self.data_labels_container = QWidget()
        self.data_labels_layout = QVBoxLayout(self.data_labels_container)
        self.data_labels_layout.setContentsMargins(0, 0, 0, 0)
        self.data_labels_layout.setSpacing(8)
        panel_layout.addWidget(self.data_labels_container)
        
        self.data_labels = {}
        self.data_cards = {}
        
        panel_layout.addStretch()
        
    def get_theme_colors(self):
        """获取主题颜色"""
        colors = [
            '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b',
            '#6c5ce7', '#a29bfe', '#fd79a8', '#fdcb6e', '#e17055'
        ]
        return colors
        
    def apply_plot_style(self):
        """应用波形图样式"""
        is_dark = isDarkTheme()
        
        if is_dark:
            bg_color = '#2b2b2b'
            text_color = '#ffffff'
        else:
            bg_color = '#ffffff'
            text_color = '#333333'
        
        self.main_plot.setBackground(bg_color)
        
        try:
            axis_pen = pg.mkPen(color=text_color, width=1)
            self.main_plot.getAxis('left').setPen(axis_pen)
            self.main_plot.getAxis('bottom').setPen(axis_pen)
            self.main_plot.getAxis('left').setTextPen(text_color)
            self.main_plot.getAxis('bottom').setTextPen(text_color)
        except Exception as e:
            print(f"设置坐标轴样式错误: {e}")

    def on_theme_changed(self):
        """主题变化时更新样式"""
        if hasattr(self, 'main_plot'):
            self.apply_plot_style()
            
    def toggle_display_mode(self):
        """切换显示模式"""
        self.is_chart_mode = not self.is_chart_mode
        
        if self.is_chart_mode:
            self.display_stack.setCurrentIndex(1)
            self.mode_toggle_btn.setText("切换到原始数据")
            self.hex_receive_checkbox.setVisible(False)
            self.timestamp_checkbox.setVisible(False)
            if self.ser and self.ser.is_open:
                self.chart_timer.start()
        else:
            self.display_stack.setCurrentIndex(0)
            self.mode_toggle_btn.setText("切换到波形图")
            self.hex_receive_checkbox.setVisible(True)
            self.timestamp_checkbox.setVisible(True)
            self.chart_timer.stop()

    def toggle_pause_receive(self):
        """切换暂停/恢复"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.setIcon(FluentIcon.PLAY)
            self.pause_btn.setText("恢复接收")
        else:
            self.pause_btn.setIcon(FluentIcon.PAUSE)
            self.pause_btn.setText("暂停接收")

    def clear_display(self):
        """清空显示"""
        self.text_edit.clear()
        for key in self.data_history:
            self.data_history[key].clear()
        if hasattr(self, 'data_timestamps'):
            self.data_timestamps.clear()
        if hasattr(self, 'curves'):
            for curve in self.curves.values():
                curve.setData([], [])
        self.data_buffer.clear()

    def toggle_advanced_settings(self):
        """切换高级设置显示"""
        is_visible = self.advanced_widget.isVisible()
        self.advanced_widget.setVisible(not is_visible)
        
        if is_visible:
            self.expand_btn.setIcon(FluentIcon.DOWN)
            self.expand_btn.setText("高级设置")
        else:
            self.expand_btn.setIcon(FluentIcon.UP)
            self.expand_btn.setText("收起设置")

    def send_preset_command(self, cmd):
        """发送预设命令"""
        self.input_line.setText(cmd)
        self.send_data()

    def refresh_ports(self):
        """刷新串口列表"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def toggle_connection(self):
        """切换连接状态"""
        if self.ser and self.ser.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        """连接串口"""
        port = self.port_combo.currentText()
        baud = int(self.baud_combo.currentText())
        data_bits = int(self.data_bits_combo.currentText())
        
        parity_map = {
            'None': serial.PARITY_NONE,
            'Even': serial.PARITY_EVEN,
            'Odd': serial.PARITY_ODD,
            'Mark': serial.PARITY_MARK,
            'Space': serial.PARITY_SPACE
        }
        parity = parity_map[self.parity_combo.currentText()]
        
        stop_bits_map = {
            '1': serial.STOPBITS_ONE,
            '1.5': serial.STOPBITS_ONE_POINT_FIVE,
            '2': serial.STOPBITS_TWO
        }
        stop_bits = stop_bits_map[self.stop_bits_combo.currentText()]
        
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=data_bits,
                parity=parity,
                stopbits=stop_bits,
                timeout=0.1
            )
            
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            self.connect_btn.setText("断开连接")
            timestamp = datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
            self.text_edit.append(f"{timestamp}已连接到 {port} @ {baud}")
            
            self.read_thread = SerialReadThread(self.ser, self)
            self.read_thread.data_received.connect(self.display_data)
            self.read_thread.raw_data_received.connect(self.process_raw_data)
            self.read_thread.start()
            
            if self.is_chart_mode:
                self.chart_timer.start()
                
        except Exception as e:
            timestamp = datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
            self.text_edit.append(f"{timestamp}连接失败: {e}")

    def disconnect_serial(self):
        """断开串口"""
        self.chart_timer.stop()
        self.auto_send_timer.stop()  # 停止自动发送
        if self.read_thread:
            self.read_thread.stop()
            self.read_thread = None
        if self.ser:
            self.ser.close()
            self.ser = None
        self.connect_btn.setText("连接串口")
        timestamp = datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
        self.text_edit.append(f"{timestamp}已断开连接")

    def display_data(self, data):
        """显示接收数据"""
        if self.is_paused:
            return
            
        self.text_edit.moveCursor(QTextCursor.End)
        self.text_edit.insertPlainText(data)
        self.text_edit.moveCursor(QTextCursor.End)
        
        if len(self.text_edit.toPlainText()) > 10000:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor, 5000)
            cursor.removeSelectedText()
            self.text_edit.moveCursor(QTextCursor.End)

    def send_data(self):
        """发送数据"""
        if self.ser and self.ser.is_open:
            text = self.input_line.text()
            try:
                if self.hex_send_checkbox.isChecked():
                    hex_data = self.parse_hex_string(text)
                    if hex_data is not None:
                        self.ser.write(hex_data)
                        line_ending = self.get_line_ending()
                        if line_ending:
                            self.ser.write(line_ending.encode())
                        sent_hex = ' '.join([f'{b:02X}' for b in hex_data])
                        timestamp = datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
                        self.text_edit.append(f"{timestamp}发送: {sent_hex}")
                    else:
                        timestamp = datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
                        self.text_edit.append(f"{timestamp}HEX格式错误")
                else:
                    data_to_send = text
                    line_ending = self.get_line_ending()
                    if line_ending:
                        data_to_send += line_ending
                    self.ser.write(data_to_send.encode())
                    timestamp = datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
                    self.text_edit.append(f"{timestamp}发送: {text}")
            except Exception as e:
                timestamp = datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
                self.text_edit.append(f"{timestamp}发送失败: {e}")
            
            # 只有在非自动发送模式下才清空输入框
            if not self.auto_send_checkbox.isChecked():
                self.input_line.clear()

    def parse_hex_string(self, hex_str):
        """解析十六进制字符串"""
        try:
            hex_str = hex_str.replace(' ', '').replace('\t', '').upper()
            if len(hex_str) % 2 != 0:
                return None
            byte_data = bytearray()
            for i in range(0, len(hex_str), 2):
                byte_data.append(int(hex_str[i:i+2], 16))
            return bytes(byte_data)
        except ValueError:
            return None

    def get_line_ending(self):
        """获取行结束符"""
        ending_text = self.line_ending_combo.currentText()
        ending_map = {
            '无': '',
            '\\n': '\n',
            '\\r': '\r',
            '\\r\\n': '\r\n'
        }
        return ending_map.get(ending_text, '')

    def update_input_placeholder(self):
        """更新输入框提示"""
        if self.hex_send_checkbox.isChecked():
            self.input_line.setPlaceholderText("输入十六进制数据，如: AA 01 BB")
        else:
            self.input_line.setPlaceholderText("输入内容，回车发送")

    def process_raw_data(self, raw_data):
        """处理原始数据 - 自动解析数据结构"""
        if self.is_paused or not self.is_chart_mode:
            return
            
        self.data_buffer.extend(raw_data)
        
        # 尝试解析数据包格式
        self.auto_parse_data()
    
    def auto_parse_data(self):
        """自动解析数据格式"""
        # 简单示例：假设数据是以空格或逗号分隔的浮点数
        try:
            text_data = self.data_buffer.decode('utf-8', errors='ignore')
            lines = text_data.strip().split('\n')
            
            for line in lines:
                if not line.strip():
                    continue
                    
                # 尝试解析为数值
                values = []
                for separator in [',', ' ', '\t', ';']:
                    try:
                        parts = [p.strip() for p in line.split(separator) if p.strip()]
                        values = [float(p) for p in parts]
                        if values:
                            break
                    except:
                        continue
                
                if values:
                    # 动态创建数据通道
                    num_channels = len(values)
                    if len(self.data_channels) != num_channels:
                        self.create_data_channels(num_channels)
                    
                    # 存储数据
                    current_time = time.time() * 1000
                    self.data_timestamps.append(current_time)
                    
                    for i, value in enumerate(values):
                        channel_name = f'CH{i+1}'
                        if channel_name in self.data_history:
                            self.data_history[channel_name].append(value)
            
            self.data_buffer.clear()
            
        except Exception as e:
            print(f"数据解析错误: {e}")
    
    def create_data_channels(self, num_channels):
        """创建数据通道"""
        # 清除旧的
        self.data_channels.clear()
        self.data_history.clear()
        self.curves.clear()
        if hasattr(self, 'main_plot'):
            self.main_plot.clear()
        
        # 创建新的
        colors = self.get_theme_colors()
        for i in range(num_channels):
            channel_name = f'CH{i+1}'
            self.data_channels.append(channel_name)
            self.data_history[channel_name] = deque(maxlen=self.max_data_points)
            
            # 创建曲线
            color = colors[i % len(colors)]
            pen = pg.mkPen(color=color, width=2)
            curve = self.main_plot.plot(pen=pen, name=channel_name)
            self.curves[channel_name] = curve
            
            # 创建数据显示卡片
            self.create_data_card(channel_name, color)
        
        # 添加图例
        if hasattr(self, 'main_plot'):
            self.main_plot.addLegend()
    
    def create_data_card(self, channel_name, color):
        """创建数据显示卡片"""
        data_card = QWidget()
        data_card.setObjectName(f"dataCard_{channel_name}")
        card_layout = QVBoxLayout(data_card)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(2)
        
        name_label = CaptionLabel(channel_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(name_label)
        
        value_label = StrongBodyLabel("--")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        value_label.setObjectName(f"valueLabel_{channel_name}")
        self.data_labels[channel_name] = value_label
        card_layout.addWidget(value_label)
        
        self.apply_data_card_style(data_card, color)
        self.data_cards[channel_name] = data_card
        
        self.data_labels_layout.addWidget(data_card)
    
    def apply_data_card_style(self, card_widget, accent_color):
        """应用数据卡片样式"""
        is_dark = isDarkTheme()
        
        if is_dark:
            bg_color = "rgba(45, 45, 45, 0.8)"
        else:
            bg_color = "rgba(255, 255, 255, 0.9)"
        
        card_style = f"""
        QWidget[objectName^="dataCard"] {{
            background-color: {bg_color};
            border: 2px solid {accent_color};
            border-radius: 6px;
            margin: 2px;
        }}
        """
        card_widget.setStyleSheet(card_style)

    def update_charts(self):
        """更新波形图"""
        try:
            current_time = time.time() * 1000
            
            for channel_name, data in self.data_history.items():
                if len(data) > 0 and channel_name in self.curves:
                    timestamps = list(self.data_timestamps)
                    y_data = list(data)
                    
                    if len(timestamps) >= len(y_data):
                        used_timestamps = timestamps[-len(y_data):]
                    else:
                        used_timestamps = timestamps.copy()
                        for i in range(len(y_data) - len(timestamps)):
                            if used_timestamps:
                                estimated_time = used_timestamps[-1] + 1
                            else:
                                estimated_time = current_time - (len(y_data) - i - 1)
                            used_timestamps.append(estimated_time)
                    
                    x_data = [t - current_time for t in used_timestamps]
                    self.curves[channel_name].setData(x_data, y_data, _callSync='off')
                    
                    # 更新数据标签
                    if channel_name in self.data_labels:
                        latest_value = data[-1]
                        self.data_labels[channel_name].setText(f"{latest_value:.2f}")
                        
        except Exception as e:
            print(f"图表更新错误: {e}")
    
    def toggle_auto_send(self, state):
        """切换自动发送"""
        if state == Qt.CheckState.Checked:
            try:
                interval = int(self.auto_send_interval.text())
                if interval < 10:
                    interval = 10  # 最小间隔10ms
                self.auto_send_timer.setInterval(interval)
                self.auto_send_timer.start()
                timestamp = datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
                self.text_edit.append(f"{timestamp}自动发送已启动，间隔: {interval}ms")
            except ValueError:
                self.auto_send_checkbox.setChecked(False)
                timestamp = datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
                self.text_edit.append(f"{timestamp}间隔时间格式错误")
        else:
            self.auto_send_timer.stop()
            timestamp = datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
            self.text_edit.append(f"{timestamp}自动发送已停止")
    
    def auto_send_data(self):
        """自动发送数据"""
        if self.ser and self.ser.is_open:
            self.send_data()