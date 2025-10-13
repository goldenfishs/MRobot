import os
import yaml
import shutil
from typing import Dict, List, Tuple
import sys
import os
class CodeGenerator:
    """通用代码生成器"""
    
    # 添加类级别的缓存
    _assets_dir_cache = None
    _assets_dir_initialized = False
    _template_dir_logged = False
    
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
        # 使用统一的get_assets_dir方法来获取路径
        template_dir = CodeGenerator.get_assets_dir("User_code/bsp")
        
        # 只在第一次或出现问题时打印日志
        if not hasattr(CodeGenerator, '_template_dir_logged'):
            print(f"模板目录路径: {template_dir}")
            CodeGenerator._template_dir_logged = True
            
        if template_dir and not os.path.exists(template_dir):
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
        # 使用缓存机制，避免重复计算和日志输出
        if not CodeGenerator._assets_dir_initialized:
            assets_dir = ""
            
            if getattr(sys, 'frozen', False):
                # 打包后的环境
                print("检测到打包环境")
                
                # 优先使用sys._MEIPASS（PyInstaller的临时解包目录）
                if hasattr(sys, '_MEIPASS'):
                    base_path = getattr(sys, '_MEIPASS')
                    assets_dir = os.path.join(base_path, "assets")
                    print(f"使用PyInstaller临时目录: {assets_dir}")
                else:
                    # 后备方案：使用可执行文件所在目录
                    exe_dir = os.path.dirname(sys.executable)
                    assets_dir = os.path.join(exe_dir, "assets")
                    print(f"使用可执行文件目录: {assets_dir}")
                
                # 如果都不存在，尝试其他可能的位置
                if not os.path.exists(assets_dir):
                    # 尝试从当前工作目录查找
                    cwd_assets = os.path.join(os.getcwd(), "assets")
                    if os.path.exists(cwd_assets):
                        assets_dir = cwd_assets
                        print(f"从工作目录找到assets: {assets_dir}")
                    else:
                        print(f"警告：无法找到assets目录，使用默认路径: {assets_dir}")
            else:
                # 开发环境
                current_dir = os.path.dirname(os.path.abspath(__file__))
                
                # 向上查找直到找到MRobot目录或到达根目录
                while current_dir != os.path.dirname(current_dir):  # 防止无限循环
                    if os.path.basename(current_dir) == 'MRobot':
                        break
                    parent = os.path.dirname(current_dir)
                    if parent == current_dir:  # 已到达根目录
                        break
                    current_dir = parent
                
                assets_dir = os.path.join(current_dir, "assets")
                print(f"开发环境：使用路径: {assets_dir}")
                
                # 如果找不到，尝试从当前工作目录
                if not os.path.exists(assets_dir):
                    cwd_assets = os.path.join(os.getcwd(), "assets")
                    if os.path.exists(cwd_assets):
                        assets_dir = cwd_assets
                        print(f"开发环境后备：使用工作目录: {assets_dir}")
            
            # 缓存基础assets目录
            CodeGenerator._assets_dir_cache = assets_dir
            CodeGenerator._assets_dir_initialized = True
        else:
            # 使用缓存的路径
            assets_dir = CodeGenerator._assets_dir_cache or ""
        
        # 构建完整路径
        if sub_path:
            full_path = os.path.join(assets_dir, sub_path)
        else:
            full_path = assets_dir
            
        # 规范化路径（处理路径分隔符）
        full_path = os.path.normpath(full_path)
        
        # 只在第一次访问某个路径时检查并警告
        safe_sub_path = sub_path.replace('/', '_').replace('\\', '_')
        warning_key = f"_warned_{safe_sub_path}"
        if full_path and not os.path.exists(full_path) and not hasattr(CodeGenerator, warning_key):
            print(f"警告：资源目录不存在: {full_path}")
            setattr(CodeGenerator, warning_key, True)
        
        return full_path