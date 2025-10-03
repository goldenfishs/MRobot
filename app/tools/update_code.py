import os
import requests
import zipfile
import io
import shutil
import tempfile
import time

def update_code(parent=None, info_callback=None, error_callback=None):
    url = "http://gitea.qutrobot.top/robofish/MRobot/archive/User_code.zip"
    local_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../assets/User_code")
    
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