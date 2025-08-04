import os
import yaml
import shutil
from typing import Dict, List, Tuple

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
        """获取模板文件目录"""
        # 从当前文件向上找到 MRobot 目录，然后定位到模板目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 向上找到 MRobot 根目录
        while os.path.basename(current_dir) != 'MRobot' and current_dir != '/':
            current_dir = os.path.dirname(current_dir)
        
        if os.path.basename(current_dir) == 'MRobot':
            return os.path.join(current_dir, "assets/User_code/bsp")
        else:
            # 如果找不到，使用相对路径作为备选
            return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets/User_code/bsp")