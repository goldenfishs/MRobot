import os
import yaml
import shutil
from typing import Dict, List, Tuple, Optional
import sys
import re
import csv
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
            dir_path = os.path.dirname(file_path)
            if dir_path:  # 只有当目录路径不为空时才创建
                os.makedirs(dir_path, exist_ok=True)
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
                
                # 优先使用可执行文件所在目录（支持更新后的文件）
                exe_dir = os.path.dirname(sys.executable)
                exe_assets = os.path.join(exe_dir, "assets")
                
                # 如果exe目录下不存在assets，但_MEIPASS中有，则首次复制过去
                if not os.path.exists(exe_assets) and hasattr(sys, '_MEIPASS'):
                    base_path = getattr(sys, '_MEIPASS')
                    meipass_assets = os.path.join(base_path, "assets")
                    if os.path.exists(meipass_assets):
                        try:
                            import shutil
                            print(f"首次运行：从 {meipass_assets} 复制到 {exe_assets}")
                            shutil.copytree(meipass_assets, exe_assets)
                            print("初始资源复制成功")
                        except Exception as e:
                            print(f"复制初始资源失败: {e}")
                
                # 优先使用exe目录下的assets（这样可以读取更新后的文件）
                if os.path.exists(exe_assets):
                    assets_dir = exe_assets
                    print(f"使用可执行文件目录: {assets_dir}")
                # 后备方案：使用PyInstaller的临时解包目录
                elif hasattr(sys, '_MEIPASS'):
                    base_path = getattr(sys, '_MEIPASS')
                    assets_dir = os.path.join(base_path, "assets")
                    print(f"后备：使用PyInstaller临时目录: {assets_dir}")
                # 最后尝试工作目录
                else:
                    cwd_assets = os.path.join(os.getcwd(), "assets")
                    if os.path.exists(cwd_assets):
                        assets_dir = cwd_assets
                        print(f"从工作目录找到assets: {assets_dir}")
                    else:
                        assets_dir = exe_assets  # 即使不存在也使用exe目录，后续会创建
                        print(f"使用默认路径（将创建）: {assets_dir}")
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
    
    @staticmethod
    def preserve_all_user_regions(new_code: str, old_code: str) -> str:
        """保留用户定义的代码区域
        
        在新代码中保留旧代码中所有用户定义的区域。
        用户区域使用如下格式标记：
        /* USER REGION_NAME BEGIN */
        用户代码...
        /* USER REGION_NAME END */
        
        支持的格式示例：
        - /* USER REFEREE BEGIN */ ... /* USER REFEREE END */
        - /* USER CODE BEGIN */ ... /* USER CODE END */
        - /* USER CUSTOM_NAME BEGIN */ ... /* USER CUSTOM_NAME END */
        
        Args:
            new_code: 新的代码内容
            old_code: 旧的代码内容
            
        Returns:
            str: 保留了用户区域的新代码
        """
        if not old_code:
            return new_code
            
        # 更灵活的正则表达式，支持更多格式的用户区域标记
        # 匹配 /* USER 任意字符 BEGIN */ ... /* USER 相同字符 END */
        pattern = re.compile(
            r"/\*\s*USER\s+([A-Za-z0-9_\s]+?)\s+BEGIN\s*\*/(.*?)/\*\s*USER\s+\1\s+END\s*\*/",
            re.DOTALL | re.IGNORECASE
        )
        
        # 提取旧代码中的所有用户区域
        old_regions = {}
        for match in pattern.finditer(old_code):
            region_name = match.group(1).strip()
            region_content = match.group(2)
            old_regions[region_name.upper()] = region_content
        
        # 替换函数
        def repl(match):
            region_name = match.group(1).strip().upper()
            current_content = match.group(2)
            old_content = old_regions.get(region_name)
            
            if old_content is not None:
                # 直接替换中间的内容，保持原有的注释标记不变
                return match.group(0).replace(current_content, old_content)
            
            return match.group(0)
        
        # 应用替换
        result = pattern.sub(repl, new_code)
        
        # 调试信息：记录找到的用户区域
        if old_regions:
            print(f"保留了 {len(old_regions)} 个用户区域: {list(old_regions.keys())}")
        
        return result
    
    @staticmethod
    def save_with_preserve(file_path: str, new_code: str) -> bool:
        """保存文件并保留用户代码区域
        
        如果文件已存在，会先读取旧文件内容，保留其中的用户代码区域，
        然后将新代码与保留的用户区域合并后保存。
        
        Args:
            file_path: 文件路径
            new_code: 新的代码内容
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 如果文件已存在，先读取旧内容
            old_code = ""
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    old_code = f.read()
            
            # 保留用户区域
            final_code = CodeGenerator.preserve_all_user_regions(new_code, old_code)
            
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:  # 只有当目录路径不为空时才创建
                os.makedirs(dir_path, exist_ok=True)
            
            # 保存文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(final_code)
                
            return True
            
        except Exception as e:
            print(f"保存文件失败: {file_path}, 错误: {e}")
            return False
    
    @staticmethod
    def load_descriptions(csv_path: str) -> Dict[str, str]:
        """从CSV文件加载组件或设备的描述信息
        
        CSV格式：第一列为组件/设备名称，第二列为描述
        
        Args:
            csv_path: CSV文件路径
            
        Returns:
            Dict[str, str]: 名称到描述的映射字典
        """
        descriptions = {}
        if os.path.exists(csv_path):
            try:
                with open(csv_path, encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            key, desc = row[0].strip(), row[1].strip()
                            descriptions[key.lower()] = desc
            except Exception as e:
                print(f"加载描述文件失败: {csv_path}, 错误: {e}")
        return descriptions
    
    @staticmethod
    def load_dependencies(csv_path: str) -> Dict[str, List[str]]:
        """从CSV文件加载组件依赖关系
        
        CSV格式：第一列为组件名，后续列为依赖的组件
        
        Args:
            csv_path: CSV文件路径
            
        Returns:
            Dict[str, List[str]]: 组件名到依赖列表的映射字典
        """
        dependencies = {}
        if os.path.exists(csv_path):
            try:
                with open(csv_path, encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            component = row[0].strip()
                            deps = [dep.strip() for dep in row[1:] if dep.strip()]
                            dependencies[component] = deps
            except Exception as e:
                print(f"加载依赖文件失败: {csv_path}, 错误: {e}")
        return dependencies
    
    @staticmethod
    def load_device_config(config_path: str) -> Dict:
        """加载设备配置文件
        
        Args:
            config_path: YAML配置文件路径
            
        Returns:
            Dict: 配置数据字典
        """
        return CodeGenerator.load_config(config_path)
    
    @staticmethod
    def copy_dependency_file(src_path: str, dst_path: str) -> bool:
        """复制依赖文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            
        Returns:
            bool: 复制是否成功
        """
        try:
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)
            return True
        except Exception as e:
            print(f"复制文件失败: {src_path} -> {dst_path}, 错误: {e}")
            return False
    
    @staticmethod
    def generate_code_from_template(template_path: str, output_path: str, 
                                  replacements: Optional[Dict[str, str]] = None,
                                  preserve_user_code: bool = True) -> bool:
        """从模板生成代码文件
        
        Args:
            template_path: 模板文件路径
            output_path: 输出文件路径
            replacements: 要替换的标记字典，如 {'MARKER': 'replacement_content'}
            preserve_user_code: 是否保留用户代码区域
            
        Returns:
            bool: 生成是否成功
        """
        try:
            # 加载模板
            template_content = CodeGenerator.load_template(template_path)
            if not template_content:
                print(f"模板文件不存在或为空: {template_path}")
                return False
            
            # 执行替换
            if replacements:
                for marker, replacement in replacements.items():
                    template_content = CodeGenerator.replace_auto_generated(
                        template_content, marker, replacement
                    )
            
            # 保存文件
            if preserve_user_code:
                return CodeGenerator.save_with_preserve(output_path, template_content)
            else:
                return CodeGenerator.save_file(template_content, output_path)
                
        except Exception as e:
            print(f"从模板生成代码失败: {template_path} -> {output_path}, 错误: {e}")
            return False
    
    @staticmethod
    def read_file_content(file_path: str) -> Optional[str]:
        """读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件内容，如果失败返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取文件失败: {file_path}, 错误: {e}")
            return None
    
    @staticmethod
    def write_file_content(file_path: str, content: str) -> bool:
        """写入文件内容
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            bool: 写入是否成功
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入文件失败: {file_path}, 错误: {e}")
            return False
    
    @staticmethod
    def update_file_with_pattern(file_path: str, pattern: str, replacement: str, 
                               use_regex: bool = True) -> bool:
        """更新文件中匹配模式的内容
        
        Args:
            file_path: 文件路径
            pattern: 要匹配的模式
            replacement: 替换内容
            use_regex: 是否使用正则表达式
            
        Returns:
            bool: 更新是否成功
        """
        try:
            content = CodeGenerator.read_file_content(file_path)
            if content is None:
                return False
            
            if use_regex:
                import re
                updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            else:
                updated_content = content.replace(pattern, replacement)
            
            return CodeGenerator.write_file_content(file_path, updated_content)
            
        except Exception as e:
            print(f"更新文件失败: {file_path}, 错误: {e}")
            return False
    
    @staticmethod
    def replace_multiple_markers(content: str, replacements: Dict[str, str]) -> str:
        """批量替换内容中的多个标记
        
        Args:
            content: 要处理的内容
            replacements: 替换字典，如 {'MARKER1': 'content1', 'MARKER2': 'content2'}
            
        Returns:
            str: 替换后的内容
        """
        result = content
        for marker, replacement in replacements.items():
            result = CodeGenerator.replace_auto_generated(result, marker, replacement)
        return result
    
    @staticmethod
    def extract_user_regions(code: str) -> Dict[str, str]:
        """从代码中提取所有用户区域
        
        支持提取各种格式的用户区域：
        - /* USER REFEREE BEGIN */ ... /* USER REFEREE END */
        - /* USER CODE BEGIN */ ... /* USER CODE END */
        - /* USER CUSTOM_NAME BEGIN */ ... /* USER CUSTOM_NAME END */
        
        Args:
            code: 要提取的代码内容
            
        Returns:
            Dict[str, str]: 区域名称到区域内容的映射
        """
        if not code:
            return {}
            
        # 使用与preserve_all_user_regions相同的正则表达式
        pattern = re.compile(
            r"/\*\s*USER\s+([A-Za-z0-9_\s]+?)\s+BEGIN\s*\*/(.*?)/\*\s*USER\s+\1\s+END\s*\*/",
            re.DOTALL | re.IGNORECASE
        )
        
        regions = {}
        for match in pattern.finditer(code):
            region_name = match.group(1).strip().upper()
            region_content = match.group(2)
            regions[region_name] = region_content
        
        return regions
    
    @staticmethod
    def debug_user_regions(new_code: str, old_code: str, verbose: bool = False) -> Dict[str, Dict[str, str]]:
        """调试用户区域，显示新旧内容的对比
        
        Args:
            new_code: 新的代码内容
            old_code: 旧的代码内容
            verbose: 是否输出详细信息
            
        Returns:
            Dict: 包含所有用户区域信息的字典
        """
        if verbose:
            print("=== 用户区域调试信息 ===")
        
        new_regions = CodeGenerator.extract_user_regions(new_code)
        old_regions = CodeGenerator.extract_user_regions(old_code)
        
        all_region_names = set(new_regions.keys()) | set(old_regions.keys())
        
        result = {}
        
        for region_name in sorted(all_region_names):
            new_content = new_regions.get(region_name, "")
            old_content = old_regions.get(region_name, "")
            
            result[region_name] = {
                "new_content": new_content,
                "old_content": old_content,
                "will_preserve": bool(old_content),
                "exists_in_new": region_name in new_regions,
                "exists_in_old": region_name in old_regions
            }
            
            if verbose:
                status = "保留旧内容" if old_content else "使用新内容"
                print(f"\n区域: {region_name} ({status})")
                print(f"  新模板中存在: {'是' if region_name in new_regions else '否'}")
                print(f"  旧文件中存在: {'是' if region_name in old_regions else '否'}")
                
                if new_content.strip():
                    print(f"  新内容预览: {repr(new_content.strip()[:50])}...")
                if old_content.strip():
                    print(f"  旧内容预览: {repr(old_content.strip()[:50])}...")
        
        if verbose:
            print(f"\n总计: {len(all_region_names)} 个用户区域")
            preserve_count = sum(1 for info in result.values() if info["will_preserve"])
            print(f"将保留: {preserve_count} 个区域的旧内容")
        
        return result