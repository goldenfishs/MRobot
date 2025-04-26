import tkinter as tk
import os
import threading
import shutil
import re
from git import Repo

# 配置常量
REPO_DIR = "MRobot_repo"
REPO_URL = "http://gitea.qutrobot.top/robofish/MRobot.git"

class MRobotApp:
    def __init__(self):
        self.ioc_data = None
        self.add_gitignore_var = None  # 延迟初始化
        self.header_file_vars = {}

    # 克隆仓库
    def clone_repo(self):
        try:
            if os.path.exists(REPO_DIR):
                shutil.rmtree(REPO_DIR)
            print(f"正在克隆仓库到 {REPO_DIR}...")
            Repo.clone_from(REPO_URL, REPO_DIR)
            print("仓库克隆成功！")
        except Exception as e:
            print(f"克隆仓库时出错: {e}")

    # 删除克隆的仓库
    def delete_repo(self):
        try:
            if os.path.exists(REPO_DIR):
                shutil.rmtree(REPO_DIR)
                print(f"已删除克隆的仓库目录: {REPO_DIR}")
        except Exception as e:
            print(f"删除仓库目录时出错: {e}")

    # 复制文件
    def copy_file_from_repo(self, src_path, dest_path):
        try:
            # 修复路径拼接问题，确保 src_path 不重复包含 REPO_DIR
            if src_path.startswith(REPO_DIR):
                full_src_path = src_path
            else:
                full_src_path = os.path.join(REPO_DIR, src_path.lstrip(os.sep))

            # 检查源文件是否存在
            if not os.path.exists(full_src_path):
                print(f"文件 {full_src_path} 不存在！（检查路径或仓库内容）")
                return

            # 检查目标路径是否有效
            if not dest_path or not dest_path.strip():
                print("目标路径为空或无效，无法复制文件！")
                return

            # 创建目标目录（如果不存在）
            dest_dir = os.path.dirname(dest_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            # 执行文件复制
            shutil.copy(full_src_path, dest_path)
            print(f"文件已从 {full_src_path} 复制到 {dest_path}")
        except Exception as e:
            print(f"复制文件时出错: {e}")

    # 查找并读取 .ioc 文件
    def find_and_read_ioc_file(self):
        try:
            for file in os.listdir("."):
                if file.endswith(".ioc"):
                    print(f"找到 .ioc 文件: {file}")
                    with open(file, "r", encoding="utf-8") as f:
                        return f.read()
            print("未找到 .ioc 文件！")
        except Exception as e:
            print(f"读取 .ioc 文件时出错: {e}")
        return None

    # 检查是否启用了 FreeRTOS
    def check_freertos_enabled(self, ioc_data):
        try:
            return bool(re.search(r"Mcu\.IP\d+=FREERTOS", ioc_data))
        except Exception as e:
            print(f"检查 FreeRTOS 配置时出错: {e}")
            return False

    # 生成操作
    def generate_action(self):
        def task():
            # 检查并创建目录
            self.create_directories()
    
            if self.add_gitignore_var.get():
                self.copy_file_from_repo(".gitignore", ".gitignore")
            if self.ioc_data and self.check_freertos_enabled(self.ioc_data):
                self.copy_file_from_repo("src/freertos.c", os.path.join("Core", "Src", "freertos.c"))
    
            # 定义需要处理的文件夹
            folders = ["bsp", "component", "device", "module"]
    
            for folder in folders:
                folder_dir = os.path.join(REPO_DIR, "User", folder)
                for file_name, var in self.header_file_vars.items():
                    if var.get():
                        # 复制 .h 文件
                        h_file_src = os.path.join(folder_dir, f"{file_name}.h")
                        h_file_dest = os.path.join("User", folder, f"{file_name}.h")
                        self.copy_file_from_repo(h_file_src, h_file_dest)
    
                        # 复制同名 .c 文件（如果存在）
                        c_file_src = os.path.join(folder_dir, f"{file_name}.c")
                        c_file_dest = os.path.join("User", folder, f"{file_name}.c")
                        if os.path.exists(c_file_src):
                            self.copy_file_from_repo(c_file_src, c_file_dest)
    
        threading.Thread(target=task).start()

    # 创建必要的目录
    def create_directories(self):
        try:
            directories = [
                "User/bsp",
                "User/component",
                "User/device",
                "User/module",
            ]
            # 根据是否启用 FreeRTOS 决定是否创建 User/task
            if self.ioc_data and self.check_freertos_enabled(self.ioc_data):
                directories.append("User/task")

            for directory in directories:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    print(f"已创建目录: {directory}")
                else:
                    print(f"目录已存在: {directory}")
        except Exception as e:
            print(f"创建目录时出错: {e}")

    # 更新 FreeRTOS 状态标签
    def update_freertos_status(self, label):
        if self.ioc_data:
            status = "已启用" if self.check_freertos_enabled(self.ioc_data) else "未启用"
        else:
            status = "未检测到 .ioc 文件"
        label.config(text=f"FreeRTOS 状态: {status}")

    # 初始化
    def initialize(self):
        print("初始化中，正在克隆仓库...")
        self.clone_repo()
        self.ioc_data = self.find_and_read_ioc_file()
        print("初始化完成，启动主窗口...")
        self.show_main_window()

    # 显示主窗口
    def show_main_window(self):
        root = tk.Tk()
        root.title("MRobot自动生成脚本")
        root.geometry("700x700")  # 调整窗口大小
    
        # 初始化 BooleanVar
        self.add_gitignore_var = tk.BooleanVar(value=True)
    
        # 添加标题
        title_label = tk.Label(root, text="MRobot 自动生成脚本", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
    
        # 添加复选框
        gitignore_frame = tk.Frame(root)
        gitignore_frame.pack(pady=10)
        tk.Checkbutton(gitignore_frame, text="添加 .gitignore", variable=self.add_gitignore_var).pack(anchor="w")
    
        # 添加 FreeRTOS 状态标签
        freertos_status_label = tk.Label(root, text="FreeRTOS 状态: 检测中...", font=("Arial", 12))
        freertos_status_label.pack(pady=10)
        self.update_freertos_status(freertos_status_label)
    
        # 显示 .h 文件复选框
        header_files_frame = tk.LabelFrame(root, text="模块文件选择", padx=10, pady=10, font=("Arial", 10, "bold"))
        header_files_frame.pack(pady=10, fill="both", expand=True)
        self.header_files_frame = header_files_frame
        self.update_header_files()
    
        # 添加生成按钮
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)
        generate_button = tk.Button(button_frame, text="一键自动生成MR架构", command=self.generate_action, bg="green", fg="white", font=("Arial", 12, "bold"))
        generate_button.pack()
    
        # 在程序关闭时清理
        root.protocol("WM_DELETE_WINDOW", lambda: self.on_closing(root))
        root.mainloop()

    # 更新文件夹显示
    def update_folder_display(self):
        for widget in self.folder_frame.winfo_children():
            widget.destroy()
    
        folders = ["User/bsp", "User/component", "User/device", "User/module"]
        # if self.ioc_data and self.check_freertos_enabled(self.ioc_data):
        #     folders.append("User/task")
    
        for folder in folders:
            # 去掉 "User/" 前缀
            display_name = folder.replace("User/", "")
            tk.Label(self.folder_frame, text=display_name).pack()

    # 更新 .h 文件复选框
    def update_header_files(self):
        for widget in self.header_files_frame.winfo_children():
            widget.destroy()

        # 定义需要处理的文件夹
        folders = ["bsp", "component", "device", "module"]

        for folder in folders:
            folder_dir = os.path.join(REPO_DIR, "User", folder)
            if os.path.exists(folder_dir):
                # 创建每个模块的分组框
                module_frame = tk.LabelFrame(self.header_files_frame, text=folder.capitalize(), padx=10, pady=10, font=("Arial", 10, "bold"))
                module_frame.pack(fill="x", pady=5)

                # 创建一个横向布局的容器
                row_frame = tk.Frame(module_frame)
                row_frame.pack(fill="x", pady=5)

                for file in os.listdir(folder_dir):
                    if file.endswith(".h"):
                        file_name_without_extension = os.path.splitext(file)[0]  # 去掉 .h 后缀
                        var = tk.BooleanVar(value=False)
                        self.header_file_vars[file_name_without_extension] = var
                        # 显示复选框，横向排列
                        tk.Checkbutton(
                            row_frame,
                            text=file_name_without_extension,
                            variable=var
                        ).pack(side="left", padx=5, pady=5)
    # 生成操作
    def generate_action(self):
        def task():
            # 检查并创建目录
            self.create_directories()
    
            if self.add_gitignore_var.get():
                self.copy_file_from_repo(".gitignore", ".gitignore")
            if self.ioc_data and self.check_freertos_enabled(self.ioc_data):
                self.copy_file_from_repo("src/freertos.c", os.path.join("Core", "Src", "freertos.c"))
    
            # 定义需要处理的文件夹
            folders = ["bsp", "component", "device", "module"]
    
            # 遍历每个文件夹，复制选中的 .h 和 .c 文件
            for folder in folders:
                folder_dir = os.path.join(REPO_DIR, "User", folder)
                if not os.path.exists(folder_dir):
                    continue  # 如果文件夹不存在，跳过
    
                for file_name in os.listdir(folder_dir):
                    file_base, file_ext = os.path.splitext(file_name)
                    if file_ext not in [".h", ".c"]:
                        continue  # 只处理 .h 和 .c 文件
    
                    # 检查是否选中了对应的文件
                    if file_base in self.header_file_vars and self.header_file_vars[file_base].get():
                        src_path = os.path.join(folder_dir, file_name)
                        dest_path = os.path.join("User", folder, file_name)
                        self.copy_file_from_repo(src_path, dest_path)
    
        threading.Thread(target=task).start()
    # 程序关闭时清理
    def on_closing(self, root):
        self.delete_repo()
        root.destroy()

# 程序入口
if __name__ == "__main__":
    app = MRobotApp()
    app.initialize()