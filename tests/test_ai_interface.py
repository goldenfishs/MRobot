from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt5.QtWidgets import QApplication

from app.ai_interface import ChatMessageWidget, render_assistant_markdown


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance() or QApplication([])
    return application


def test_assistant_markdown_renders_headings_lists_and_code(qapp: QApplication) -> None:
    source = """### 配置步骤

- 检查时钟
- 检查 GPIO

```c
int main(void) { return 0; }
```
"""
    rendered = render_assistant_markdown(source)
    assert "<h3" in rendered
    assert "<ul" in rendered
    assert "<pre" in rendered
    assert "int main" in rendered
    assert "font-weight: 700" in rendered


def test_chat_widget_keeps_user_text_plain_and_assistant_text_rich(qapp: QApplication) -> None:
    user = ChatMessageWidget("user", "### 不是标题")
    assistant = ChatMessageWidget("assistant", "### 是标题")
    assert "<h3" not in user.content.text()
    assert "<h3" in assistant.content.text()
