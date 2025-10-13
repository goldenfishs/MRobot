#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication
from app.tools.fluent_design_update import FluentUpdateDialog

def test_ui():
    app = QApplication(sys.argv)
    
    try:
        dialog = FluentUpdateDialog("1.0.2")
        print("FluentUpdateDialog created successfully")
        dialog.show()
        app.exec_()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ui()