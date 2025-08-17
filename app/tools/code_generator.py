import os
import yaml
import shutil
from typing import Dict, List, Tuple
import sys
import os
class CodeGenerator:
    """通用代码生成器"""
    
    @staticmethod
    def load_template(template_path: str) -> str:
        """加载代码模板"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"加载模板失败: {template_path}, 错误: {e}")
            return ""
    
    @staticmethod
    def replace_auto_generated(content: str, marker: str, replacement: str) -> str:
        """替换自动生成的代码标记"""
        marker_line = f"/* {marker} */"
        if marker_line in content:
            return content.replace(marker_line, replacement)
        return content
    
    @staticmethod
    def save_file(content: str, file_path: str) -> bool:
        """保存文件"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"保存文件失败: {file_path}, 错误: {e}")
            return False
    
    @staticmethod
    def load_config(config_path: str) -> Dict:
        """加载配置文件"""
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"加载配置失败: {config_path}, 错误: {e}")
        return {}
    
    @staticmethod
    def save_config(config: Dict, config_path: str) -> bool:
        """保存配置文件"""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {config_path}, 错误: {e}")
            return False
    
    @staticmethod
    def get_template_dir():
        """获取模板目录路径，兼容打包环境"""
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            base_path = sys._MEIPASS
            template_dir = os.path.join(base_path, "assets", "User_code", "bsp")
        else:
            # 开发环境
            current_dir = os.path.dirname(os.path.abspath(__file__))
            while os.path.basename(current_dir) != 'MRobot' and current_dir != '/':
                current_dir = os.path.dirname(current_dir)
            template_dir = os.path.join(current_dir, "assets", "User_code", "bsp")
        
        print(f"模板目录路径: {template_dir}")
        if not os.path.exists(template_dir):
            print(f"警告：模板目录不存在: {template_dir}")
        
        return template_dir
    
    @staticmethod
    def get_assets_dir(sub_path=""):
        """获取assets目录路径，兼容打包环境
        Args:
            sub_path: 子路径，如 "User_code/component" 或 "User_code/device"
        Returns:
            str: 完整的assets路径
        """
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            base_path = sys._MEIPASS
            assets_dir = os.path.join(base_path, "assets")
        else:
            # 开发环境
            current_dir = os.path.dirname(os.path.abspath(__file__))
            while os.path.basename(current_dir) != 'MRobot' and current_dir != '/':
                current_dir = os.path.dirname(current_dir)
            assets_dir = os.path.join(current_dir, "assets")
        
        if sub_path:
            full_path = os.path.join(assets_dir, sub_path)
        else:
            full_path = assets_dir
            
        if not os.path.exists(full_path):
            print(f"警告：资源目录不存在: {full_path}")
        
        return full_path