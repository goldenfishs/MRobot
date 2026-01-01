from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    BodyLabel, CheckBox, SubtitleLabel, PushButton, FluentIcon,
    InfoBar, InfoBarPosition, CardWidget, TitleLabel
)
from PyQt5.QtCore import Qt
from app.tools.code_generator import CodeGenerator
import os
import shutil
import csv


def get_module_page(module_type, subtype, project_path, parent=None):
    """获取模块配置页面"""
    return ModulePage(module_type, subtype, project_path, parent)


class ModulePage(QWidget):
    """单个模块配置页面"""
    
    def __init__(self, module_type, subtype, project_path, parent=None):
        super().__init__(parent)
        self.module_type = module_type
        self.subtype = subtype
        self.project_path = project_path
        
        # 获取模块路径
        module_dir = CodeGenerator.get_assets_dir("User_code/module")
        if subtype:
            self.module_path = os.path.join(module_dir, module_type, subtype)
            self.module_key = subtype
        else:
            self.module_path = os.path.join(module_dir, module_type)
            self.module_key = module_type
        
        # 加载描述
        self.descriptions = self._load_descriptions()
        
        self._init_ui()
        self._check_generated_status()
    
    def _load_descriptions(self):
        """从 describe.csv 加载模块描述"""
        descriptions = {}
        describe_path = os.path.join(
            CodeGenerator.get_assets_dir("User_code/module"),
            "describe.csv"
        )
        
        if os.path.exists(describe_path):
            try:
                with open(describe_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        module_name = row.get('module_name', '').strip()
                        description = row.get('description', '').strip()
                        if module_name and description:
                            descriptions[module_name] = description
            except Exception as e:
                print(f"读取模块描述失败: {e}")
        
        return descriptions
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(48, 48, 48, 48)
        
        # 标题
        if self.subtype:
            title_text = f"{self.module_type} / {self.subtype}"
        else:
            title_text = self.module_type
        
        title = TitleLabel(title_text)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 描述
        desc_text = self.descriptions.get(self.module_key, "模块功能说明")
        desc = BodyLabel(desc_text)
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)
        
        layout.addSpacing(24)
        
        # 文件列表卡片
        files_card = CardWidget()
        files_layout = QVBoxLayout(files_card)
        files_layout.setContentsMargins(16, 16, 16, 16)
        
        files_title = SubtitleLabel("包含文件")
        files_layout.addWidget(files_title)
        
        files = self._get_module_files()
        if files:
            for file in files:
                file_label = BodyLabel(f"• {file}")
                files_layout.addWidget(file_label)
        else:
            files_layout.addWidget(BodyLabel("未找到文件"))
        
        layout.addWidget(files_card)
        
        # 状态显示
        self.status_label = BodyLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addSpacing(24)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.generate_btn = PushButton(FluentIcon.SAVE, "生成模块代码")
        self.generate_btn.clicked.connect(self._generate_code)
        btn_layout.addWidget(self.generate_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
    
    def _get_module_files(self):
        """获取模块文件列表"""
        files = []
        try:
            if os.path.exists(self.module_path):
                for item in os.listdir(self.module_path):
                    if item.endswith(('.c', '.h')):
                        files.append(item)
        except Exception as e:
            print(f"读取模块文件失败: {e}")
        
        return sorted(files)
    
    def _check_generated_status(self):
        """检查模块是否已生成"""
        if self.subtype:
            dst_dir = os.path.join(self.project_path, "User/module", self.module_type, self.subtype)
        else:
            dst_dir = os.path.join(self.project_path, "User/module", self.module_type)
        
        if os.path.exists(dst_dir):
            has_code = any(
                f.endswith(('.c', '.h'))
                for f in os.listdir(dst_dir)
                if os.path.isfile(os.path.join(dst_dir, f))
            )
            if has_code:
                self.status_label.setText("✓ 模块已生成")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.generate_btn.setEnabled(False)
                return
        
        self.status_label.setText("○ 模块未生成")
        self.status_label.setStyleSheet("color: orange;")
    
    def _generate_code(self):
        """生成模块代码"""
        try:
            # 首先生成 config（如果不存在）
            self._generate_config()
            
            # 目标目录
            if self.subtype:
                dst_dir = os.path.join(self.project_path, "User/module", self.module_type, self.subtype)
            else:
                dst_dir = os.path.join(self.project_path, "User/module", self.module_type)
            
            # 检查是否已存在
            if os.path.exists(dst_dir):
                has_code = any(
                    f.endswith(('.c', '.h'))
                    for f in os.listdir(dst_dir)
                    if os.path.isfile(os.path.join(dst_dir, f))
                )
                if has_code:
                    InfoBar.warning(
                        title="已存在",
                        content="模块代码已存在，不会覆盖",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    return
            
            # 创建目录
            os.makedirs(dst_dir, exist_ok=True)
            
            # 复制所有文件
            file_count = 0
            for item in os.listdir(self.module_path):
                src_file = os.path.join(self.module_path, item)
                dst_file = os.path.join(dst_dir, item)
                
                if os.path.isfile(src_file):
                    if os.path.exists(dst_file):
                        continue
                    shutil.copy2(src_file, dst_file)
                    file_count += 1
                    print(f"生成文件: {dst_file}")
            
            if file_count > 0:
                InfoBar.success(
                    title="生成成功",
                    content=f"已生成 {file_count} 个文件",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self._check_generated_status()
            else:
                InfoBar.warning(
                    title="无需生成",
                    content="所有文件已存在",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            
        except Exception as e:
            print(f"生成模块失败: {e}")
            InfoBar.error(
                title="生成失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def _generate_config(self):
        """生成 config 文件（如果不存在）"""
        config_dir = os.path.join(self.project_path, "User/module")
        config_c = os.path.join(config_dir, "config.c")
        config_h = os.path.join(config_dir, "config.h")
        
        os.makedirs(config_dir, exist_ok=True)
        
        template_dir = CodeGenerator.get_assets_dir("User_code/module")
        template_c = os.path.join(template_dir, "config.c")
        template_h = os.path.join(template_dir, "config.h")
        
        if not os.path.exists(config_c) and os.path.exists(template_c):
            shutil.copy2(template_c, config_c)
            print(f"生成 config.c")
        
        if not os.path.exists(config_h) and os.path.exists(template_h):
            shutil.copy2(template_h, config_h)
            print(f"生成 config.h")
