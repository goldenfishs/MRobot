#!/usr/bin/env python3
"""
财务界面UI测试脚本
验证 SegmentedWidget 和 TableWidget 是否正常工作
"""

import sys
from PyQt5.QtWidgets import QApplication
from app.finance_interface import FinanceInterface

def test_finance_ui():
    """测试财务界面 UI"""
    app = QApplication(sys.argv)
    
    # 创建财务界面
    finance_interface = FinanceInterface()
    
    # 验证组件存在
    assert hasattr(finance_interface, 'segmented_widget'), "SegmentedWidget 未创建"
    assert hasattr(finance_interface, 'stacked_widget'), "StackedWidget 未创建"
    assert hasattr(finance_interface, 'records_table'), "records_table 未创建"
    assert hasattr(finance_interface, 'query_result_table'), "query_result_table 未创建"
    
    # 验证 SegmentedWidget 项目数
    assert len(finance_interface.segmented_widget.items) == 3, "SegmentedWidget 应该有3个选项卡"
    
    # 验证表格列数
    assert finance_interface.records_table.columnCount() == 5, "records_table 应该有5列"
    assert finance_interface.query_result_table.columnCount() == 5, "query_result_table 应该有5列"
    
    # 验证标签切换功能
    finance_interface.segmented_widget.setCurrentItem("query")
    assert finance_interface.stacked_widget.currentIndex() == 1, "标签页切换失败"
    
    finance_interface.segmented_widget.setCurrentItem("export")
    assert finance_interface.stacked_widget.currentIndex() == 2, "标签页切换失败"
    
    print("✓ 所有 UI 组件验证通过")
    print("✓ SegmentedWidget 正常工作")
    print("✓ TableWidget 正常工作")
    print("✓ 标签页切换功能正常")
    
    return True

if __name__ == "__main__":
    try:
        if test_finance_ui():
            print("\n✅ 财务界面 UI 测试成功！")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
