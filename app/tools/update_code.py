import os
import sys
import requests
import zipfile
import io
import shutil
import tempfile
import time

def update_code(parent=None, info_callback=None, error_callback=None):
    url = "http://gitea.qutrobot.top/robofish/MRobot/archive/User_code.zip"
    
    # 导入 CodeGenerator 以使用统一的路径获取逻辑
    try:
        from app.tools.code_generator import CodeGenerator
        # 直接使用 CodeGenerator 的路径获取方法，确保路径一致
        assets_dir = CodeGenerator.get_assets_dir("")
        print(f"更新代码：使用 CodeGenerator 路径: {assets_dir}")
    except Exception as e:
        print(f"无法导入 CodeGenerator，使用后备路径逻辑: {e}")
        # 后备方案：使用与CodeGenerator.get_assets_dir相同的逻辑确定assets目录
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            if hasattr(sys, '_MEIPASS'):
                base_path = getattr(sys, '_MEIPASS')
                assets_dir = os.path.join(base_path, "assets")
                print(f"更新代码：使用PyInstaller临时目录: {assets_dir}")
            else:
                # 使用可执行文件所在目录
                exe_dir = os.path.dirname(sys.executable)
                assets_dir = os.path.join(exe_dir, "assets")
                print(f"更新代码：打包环境，使用路径: {assets_dir}")
            
            # 如果不存在，尝试工作目录
            if not os.path.exists(assets_dir):
                cwd_assets = os.path.join(os.getcwd(), "assets")
                if os.path.exists(cwd_assets):
                    assets_dir = cwd_assets
                    print(f"更新代码：使用工作目录: {assets_dir}")
        else:
            # 开发环境
            current_dir = os.path.dirname(os.path.abspath(__file__))
            while current_dir != os.path.dirname(current_dir):
                if os.path.basename(current_dir) == 'MRobot':
                    break
                parent_dir = os.path.dirname(current_dir)
                if parent_dir == current_dir:
                    break
                current_dir = parent_dir
            assets_dir = os.path.join(current_dir, "assets")
            print(f"更新代码：开发环境，使用路径: {assets_dir}")
    
    local_dir = os.path.join(assets_dir, "User_code")
    print(f"更新代码：最终目标目录: {local_dir}")
    
    try:
        # 下载远程代码库
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        
        # 创建临时目录进行操作
        with tempfile.TemporaryDirectory() as temp_dir:
            # 解压到临时目录
            z = zipfile.ZipFile(io.BytesIO(resp.content))
            extract_path = os.path.join(temp_dir, "extracted")
            z.extractall(extract_path)
            
            # 获取解压后的根目录
            extracted_items = os.listdir(extract_path)
            if not extracted_items:
                raise Exception("下载的压缩包为空")
            
            source_root = os.path.join(extract_path, extracted_items[0])
            
            # 确保本地目录的父目录存在
            parent_dir = os.path.dirname(local_dir)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # 创建备份（如果原目录存在）
            backup_dir = None
            if os.path.exists(local_dir):
                backup_dir = f"{local_dir}_backup_{int(time.time())}"
                try:
                    shutil.move(local_dir, backup_dir)
                except Exception as e:
                    # 如果移动失败，尝试强制删除
                    shutil.rmtree(local_dir, ignore_errors=True)
            
            try:
                # 复制新文件到目标位置
                shutil.copytree(source_root, local_dir)
                
                # 验证复制是否成功
                if not os.path.exists(local_dir):
                    raise Exception("复制失败，目标目录不存在")
                
                # 设置正确的文件权限，确保文件可以被正常访问和修改
                for root, dirs, files in os.walk(local_dir):
                    # 设置目录权限为755 (rwxr-xr-x)
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        try:
                            os.chmod(dir_path, 0o755)
                        except:
                            pass
                    
                    # 设置文件权限为644 (rw-r--r--)
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        try:
                            os.chmod(file_path, 0o644)
                        except:
                            pass
                
                # 删除备份目录（更新成功）
                if backup_dir and os.path.exists(backup_dir):
                    shutil.rmtree(backup_dir, ignore_errors=True)
                
                # 清除 CodeGenerator 的缓存，确保后续读取更新后的文件
                try:
                    from app.tools.code_generator import CodeGenerator
                    CodeGenerator._assets_dir_cache = None
                    CodeGenerator._assets_dir_initialized = False
                    CodeGenerator._template_dir_logged = False
                    print("已清除 CodeGenerator 缓存")
                except Exception as e:
                    print(f"清除缓存失败（可忽略）: {e}")
                
                if info_callback:
                    info_callback(parent)
                return True
                
            except Exception as copy_error:
                # 恢复备份
                if backup_dir and os.path.exists(backup_dir):
                    if os.path.exists(local_dir):
                        shutil.rmtree(local_dir, ignore_errors=True)
                    try:
                        shutil.move(backup_dir, local_dir)
                    except:
                        pass
                raise copy_error
                
    except Exception as e:
        if error_callback:
            error_callback(parent, str(e))
        return False