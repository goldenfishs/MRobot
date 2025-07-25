from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from qfluentwidgets import TextEdit, LineEdit, PushButton, TitleLabel, SubtitleLabel, FluentIcon, InfoBar, InfoBarPosition
import requests
import json

class AIWorker(QThread):
    response_signal = pyqtSignal(str)
    done_signal = pyqtSignal()
    error_signal = pyqtSignal(str)  # 新增

    def __init__(self, prompt, parent=None):
        super().__init__(parent)
        self.prompt = prompt

    def run(self):
        url = "http://154.37.215.220:11434/api/generate"
        payload = {
            "model": "qwen3:0.6b",
            "prompt": self.prompt
        }
        try:
            response = requests.post(url, json=payload, stream=True, timeout=60)
            got_response = False
            for line in response.iter_lines():
                if line:
                    got_response = True
                    try:
                        data = json.loads(line.decode('utf-8'))
                        self.response_signal.emit(data.get("response", ""))
                        if data.get("done", False):
                            self.done_signal.emit()
                            break
                    except Exception:
                        continue
            if not got_response:
                self.error_signal.emit("服务器繁忙，请稍后再试。")
                self.done_signal.emit()
        except requests.ConnectionError:
            self.error_signal.emit("网络连接失败，请检查网络设置。")
            self.done_signal.emit()
        except Exception as e:
            self.error_signal.emit(f"[错误]: {str(e)}")
            self.done_signal.emit()


class AIInterface(QWidget):
    MAX_HISTORY = 20  # 新增最大对话条数

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aiPage")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        self.title = SubtitleLabel("MRobot AI小助手", self)
        self.title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title)

        self.chat_display = TextEdit(self)
        self.chat_display.setReadOnly(True)

        self.layout.addWidget(self.chat_display, stretch=1)

        input_layout = QHBoxLayout()
        self.input_box = LineEdit(self)
        self.input_box.setPlaceholderText("请输入你的问题...")
        input_layout.addWidget(self.input_box, stretch=1)

        # self.send_btn = PushButton("发送", self)
        self.send_btn = PushButton("发送", icon=FluentIcon.SEND, parent=self)

        self.send_btn.setFixedWidth(80)
        input_layout.addWidget(self.send_btn)

        self.layout.addLayout(input_layout)

        self.send_btn.clicked.connect(self.send_message)
        self.input_box.returnPressed.connect(self.send_message)

        self.worker = None
        self.is_waiting = False
        self.history = []
        self.chat_display.setText(
            "<b>MRobot:</b> 欢迎使用MRobot AI小助手!"
        )

    def send_message(self):
        if self.is_waiting:
            return
        prompt = self.input_box.text().strip()
        if not prompt:
            return
        if len(prompt) > 1000:
            InfoBar.warning(
                title='警告',
                content="每条发送内容不能超过1000字，请精简后再发送。",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=-1,
                parent=self
            )
            return
        if len(self.history) >= self.MAX_HISTORY:
            InfoBar.warning(
                title='警告',
                content="对话条数已达上限，请清理历史或重新开始。",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=-1,
                parent=self
            )
            return
        self.append_chat("你", prompt)
        self.input_box.clear()
        self.append_chat("MRobot", "", new_line=False)
        self.is_waiting = True

        # 只在首次对话时加入身份提示
        if not self.history:
            system_prompt = (
                "你是MRobot，是QUT青岛理工大学机器人战队的AI机器人。"
                "请以此身份与用户进行交流。"
            )
        else:
            system_prompt = ""

        self.history.append({"role": "user", "content": prompt})
        context = system_prompt + "\n" if system_prompt else ""
        for msg in self.history:
            if msg["role"] == "user":
                context += f"你: {msg['content']}\n"
            else:
                context += f"AI: {msg['content']}\n"

        self.worker = AIWorker(context)
        self.worker.response_signal.connect(self.stream_response)
        self.worker.done_signal.connect(self.finish_response)
        self.worker.error_signal.connect(self.show_error)  # 新增
        self.worker.start()


    def append_chat(self, sender, message, new_line=True):
        if new_line:
            self.chat_display.append(f"<b>{sender}:</b> {message}")
        else:
            self.chat_display.append(f"<b>{sender}:</b> ")
        self.chat_display.moveCursor(self.chat_display.textCursor().End)
        # 新增：保存AI回复到历史
        if sender == "AI" and message:
            self.history.append({"role": "ai", "content": message})

    def stream_response(self, text):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.chat_display.setTextCursor(cursor)
        # 新增：流式保存AI回复
        if self.history and self.history[-1]["role"] == "ai":
            self.history[-1]["content"] += text
        elif text:
            self.history.append({"role": "ai", "content": text})

    def finish_response(self):
        self.chat_display.append("")  # 换行
        self.is_waiting = False
    
    def show_error(self, msg):  # 新增
        InfoBar.error(
            title='失败',
            content=msg,
            orient=Qt.Vertical,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=self
        )
        self.is_waiting = False
