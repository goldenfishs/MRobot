import tkinter as tk
from tkinter import ttk
import sys
import os
import threading
import shutil
import re
from git import Repo
from collections import defaultdict
import csv

# 配置常量
REPO_DIR = "MRobot_repo"
REPO_URL = "http://gitea.qutrobot.top/robofish/MRobot.git"

class MRobotApp:
    def __init__(self):
        self.ioc_data = None
        self.add_gitignore_var = None  # 延迟初始化
        self.header_file_vars = {}
        self.task_vars = []  # 用于存储任务的变量

    # 初始化
    def initialize(self):
        print("初始化中，正在克隆仓库...")
        self.clone_repo()
        self.ioc_data = self.find_and_read_ioc_file()
        print("初始化完成，启动主窗口...")
        self.show_main_window()

    # 克隆仓库
    def clone_repo(self):
        try:
            if os.path.exists(REPO_DIR):
                shutil.rmtree(REPO_DIR)
            print(f"正在克隆仓库到 {REPO_DIR}（仅克隆当前文件内容）...")
            Repo.clone_from(REPO_URL, REPO_DIR, multi_options=["--depth=1"])
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
    
            # 遍历每个文件夹，复制选中的 .h 和 .c 文件
            for folder in folders:
                folder_dir = os.path.join(REPO_DIR, "User", folder)
                if not os.path.exists(folder_dir):
                    continue  # 如果文件夹不存在，跳过
    
                for file_name in os.listdir(folder_dir):
                    file_base, file_ext = os.path.splitext(file_name)
                    if file_ext not in [".h", ".c"]:
                        continue  # 只处理 .h 和 .c 文件
    
                    # 强制复制与文件夹同名的文件
                    if file_base == folder:
                        src_path = os.path.join(folder_dir, file_name)
                        dest_path = os.path.join("User", folder, file_name)
                        self.copy_file_from_repo(src_path, dest_path)
                        continue  # 跳过后续检查，直接复制
    
                    # 检查是否选中了对应的文件
                    if file_base in self.header_file_vars and self.header_file_vars[file_base].get():
                        src_path = os.path.join(folder_dir, file_name)
                        dest_path = os.path.join("User", folder, file_name)
                        self.copy_file_from_repo(src_path, dest_path)
    
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



    # 显示主窗口
    def show_main_window(self):
        root = tk.Tk()
        root.title("MRobot 自动生成脚本")
        root.geometry("800x600")  # 调整窗口大小以适应布局

        # 在窗口关闭时调用 on_closing 方法
        root.protocol("WM_DELETE_WINDOW", lambda: self.on_closing(root))

        # 初始化 BooleanVar
        self.add_gitignore_var = tk.BooleanVar(value=True)

        # 创建主框架
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True)

        # 添加标题
        title_label = ttk.Label(main_frame, text="MRobot 自动生成脚本", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # 添加 FreeRTOS 状态标签
        freertos_status_label = ttk.Label(main_frame, text="FreeRTOS 状态: 检测中...", font=("Arial", 12))
        freertos_status_label.pack(pady=10)
        self.update_freertos_status(freertos_status_label)

        # 模块文件选择和任务管理框架
        module_task_frame = ttk.Frame(main_frame)
        module_task_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 模块文件选择框
        header_files_frame = ttk.LabelFrame(module_task_frame, text="模块文件选择", padding=(10, 10))
        header_files_frame.pack(side="left", fill="both", expand=True, padx=5)
        self.header_files_frame = header_files_frame
        self.update_header_files()

        if self.ioc_data and self.check_freertos_enabled(self.ioc_data):
            task_frame = ttk.LabelFrame(module_task_frame, text="任务管理", padding=(10, 10))
            task_frame.pack(side="left", fill="both", expand=True, padx=5)
            self.task_frame = task_frame
            self.update_task_ui()

        # 添加消息框和生成按钮在同一行
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=10, side="bottom")

        # 消息框
        self.message_box = tk.Text(bottom_frame, wrap="word", state="disabled", height=5, width=60)
        self.message_box.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # 生成按钮和 .gitignore 选项
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(side="right", padx=10)

        # 添加 .gitignore 复选框
        ttk.Checkbutton(button_frame, text="添加 .gitignore", variable=self.add_gitignore_var).pack(side="top", pady=5)

        # 添加生成按钮
        generate_button = ttk.Button(button_frame, text="一键生成MRobot代码", command=self.generate_action)
        generate_button.pack(side="top", pady=5)

        # 重定向输出到消息框
        self.redirect_output()

        # 打印欢迎信息
        print("欢迎使用 MRobot 自动生成脚本！")
        print("请根据需要选择模块文件和任务。")
        print("点击“一键生成MRobot代码”按钮开始生成。")

        # 启动 Tkinter 主事件循环
        root.mainloop()




    def redirect_output(self):
        """
        重定向标准输出到消息框
        """
        class TextRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget

            def write(self, message):
                self.text_widget.config(state="normal")
                self.text_widget.insert("end", message)
                self.text_widget.see("end")
                self.text_widget.config(state="disabled")

            def flush(self):
                pass

        sys.stdout = TextRedirector(self.message_box)
        sys.stderr = TextRedirector(self.message_box)

    # 修改 update_task_ui 方法
    def update_task_ui(self):
        # 检查是否有已存在的任务文件
        task_dir = os.path.join("User", "task")
        if os.path.exists(task_dir):
            for file_name in os.listdir(task_dir):
                file_base, file_ext = os.path.splitext(file_name)
                if file_ext == ".c" and file_base not in ["init", "user_task"] and file_base not in [task_var.get() for task_var, _ in self.task_vars]:
                    frequency = 100  # 默认频率
                    user_task_header_path = os.path.join("User", "task", "user_task.h")
                    if os.path.exists(user_task_header_path):
                        try:
                            with open(user_task_header_path, "r", encoding="utf-8") as f:
                                content = f.read()
                                pattern = rf"#define\s+TASK_FREQ_{file_base.upper()}\s*\((\d+)[uU]?\)"
                                match = re.search(pattern, content)
                                if match:
                                    frequency = int(match.group(1))
                                    print(f"从 user_task.h 文件中读取到任务 {file_base} 的频率: {frequency}")
                        except Exception as e:
                            print(f"读取 user_task.h 文件时出错: {e}")

                    new_task_var = tk.StringVar(value=file_base)
                    self.task_vars.append((new_task_var, tk.IntVar(value=frequency)))

        # 清空任务框架中的所有子组件
        for widget in self.task_frame.winfo_children():
            widget.destroy()


        # 设置任务管理框的固定宽度
        self.task_frame.config(width=400)

        # 显示任务列表
        for i, (task_var, freq_var) in enumerate(self.task_vars):
            task_row = ttk.Frame(self.task_frame, width=400)
            task_row.pack(fill="x", pady=5)

            ttk.Entry(task_row, textvariable=task_var, width=20).pack(side="left", padx=5)
            ttk.Label(task_row, text="频率:").pack(side="left", padx=5)
            ttk.Spinbox(task_row, from_=1, to=1000, textvariable=freq_var, width=5).pack(side="left", padx=5)
            ttk.Button(task_row, text="删除", command=lambda idx=i: self.remove_task(idx)).pack(side="left", padx=5)

        # 添加新任务按钮
        add_task_button = ttk.Button(self.task_frame, text="添加任务", command=self.add_task)
        add_task_button.pack(pady=10)


    # 修改 add_task 方法
    def add_task(self):
        new_task_var = tk.StringVar(value=f"Task_{len(self.task_vars) + 1}")
        new_freq_var = tk.IntVar(value=100)  # 默认频率为 100
        self.task_vars.append((new_task_var, new_freq_var))
        self.update_task_ui()
    
    # 修改 remove_task 方法
    def remove_task(self, idx):
        del self.task_vars[idx]
        self.update_task_ui()
    
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

        folders = ["bsp", "component", "device", "module"]
        dependencies = defaultdict(list)

        for folder in folders:
            folder_dir = os.path.join(REPO_DIR, "User", folder)
            if os.path.exists(folder_dir):
                dependencies_file = os.path.join(folder_dir, "dependencies.csv")
                if os.path.exists(dependencies_file):
                    with open(dependencies_file, "r", encoding="utf-8") as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if len(row) == 2:
                                dependencies[row[0]].append(row[1])

        # 创建复选框
        for folder in folders:
            folder_dir = os.path.join(REPO_DIR, "User", folder)
            if os.path.exists(folder_dir):
                module_frame = ttk.LabelFrame(self.header_files_frame, text=folder.capitalize(), padding=(10, 10))
                module_frame.pack(fill="x", pady=5)

                row, col = 0, 0
                for file in os.listdir(folder_dir):
                    file_base, file_ext = os.path.splitext(file)
                    if file_ext == ".h" and file_base != folder:
                        var = tk.BooleanVar(value=False)
                        self.header_file_vars[file_base] = var

                        checkbox = ttk.Checkbutton(
                            module_frame,
                            text=file_base,
                            variable=var,
                            command=lambda fb=file_base: self.handle_dependencies(fb, dependencies)
                        )
                        checkbox.grid(row=row, column=col, padx=5, pady=5, sticky="w")
                        col += 1
                        if col >= 6:
                            col = 0
                            row += 1



    def handle_dependencies(self, file_base, dependencies):
        """
        根据依赖关系自动勾选相关模块
        """
        if file_base in self.header_file_vars and self.header_file_vars[file_base].get():
            # 如果当前模块被选中，自动勾选其依赖项
            for dependency in dependencies.get(file_base, []):
                dep_base = os.path.basename(dependency)
                if dep_base in self.header_file_vars:
                    self.header_file_vars[dep_base].set(True)

    # 在 MRobotApp 类中添加以下方法
    def generate_task_files(self):
        try:
            template_file_path = os.path.join(REPO_DIR, "User", "task", "task.c.template")
            task_dir = os.path.join("User", "task")
    
            if not os.path.exists(template_file_path):
                print(f"模板文件 {template_file_path} 不存在，无法生成 task.c 文件！")
                return
    
            os.makedirs(task_dir, exist_ok=True)
    
            with open(template_file_path, "r", encoding="utf-8") as f:
                template_content = f.read()
    
            # 为每个任务生成对应的 task.c 文件
            for task_var, _ in self.task_vars:  # 解包元组
                task_name = f"Task_{task_var.get()}"  # 添加前缀 Task_
                task_file_path = os.path.join(task_dir, f"{task_var.get().lower()}.c")  # 文件名保持原始小写
    
                # 替换模板中的占位符
                task_content = template_content.replace("{{task_name}}", task_name)
                task_content = task_content.replace("{{task_function}}", task_name)
                task_content = task_content.replace(
                    "{{task_frequency}}", f"TASK_FREQ_{task_var.get().upper()}"
                )  # 替换为 user_task.h 中的宏定义
                task_content = task_content.replace("{{task_delay}}", f"TASK_INIT_DELAY_{task_var.get().upper()}")
    
                with open(task_file_path, "w", encoding="utf-8") as f:
                    f.write(task_content)
    
                print(f"已成功生成 {task_file_path} 文件！")
        except Exception as e:
            print(f"生成 task.c 文件时出错: {e}")
    # 修改 user_task.c 文件
    def modify_user_task_file(self):
        try:
            template_file_path = os.path.join(REPO_DIR, "User", "task", "user_task.c.template")
            generated_task_file_path = os.path.join("User", "task", "user_task.c")
    
            if not os.path.exists(template_file_path):
                print(f"模板文件 {template_file_path} 不存在，无法生成 user_task.c 文件！")
                return
    
            os.makedirs(os.path.dirname(generated_task_file_path), exist_ok=True)
    
            with open(template_file_path, "r", encoding="utf-8") as f:
                template_content = f.read()
    
            # 生成任务属性定义
            task_attr_definitions = "\n".join([
                f"""const osThreadAttr_t attr_{task_var.get().lower()} = {{
        .name = "{task_var.get()}",
        .priority = osPriorityNormal,
        .stack_size = 128 * 4,
    }};"""
                for task_var, _ in self.task_vars  # 解包元组
            ])
    
            # 替换模板中的占位符
            task_content = template_content.replace("{{task_attr_definitions}}", task_attr_definitions)
    
            with open(generated_task_file_path, "w", encoding="utf-8") as f:
                f.write(task_content)
    
            print(f"已成功生成 {generated_task_file_path} 文件！")
        except Exception as e:
            print(f"修改 user_task.c 文件时出错: {e}")
    # ...existing code...
    
    def generate_user_task_header(self):
        try:
            template_file_path = os.path.join(REPO_DIR, "User", "task", "user_task.h.template")
            header_file_path = os.path.join("User", "task", "user_task.h")
    
            if not os.path.exists(template_file_path):
                print(f"模板文件 {template_file_path} 不存在，无法生成 user_task.h 文件！")
                return
    
            os.makedirs(os.path.dirname(header_file_path), exist_ok=True)
    
            # 如果 user_task.h 已存在，提取 /* USER MESSAGE BEGIN */ 和 /* USER MESSAGE END */ 区域内容
            existing_msgq_content = ""
            if os.path.exists(header_file_path):
                with open(header_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 提取 /* USER MESSAGE BEGIN */ 和 /* USER MESSAGE END */ 区域内容
                    match = re.search(r"/\* USER MESSAGE BEGIN \*/\s*(.*?)\s*/\* USER MESSAGE END \*/", content, re.DOTALL)
                    if match:
                        existing_msgq_content = match.group(1).strip()
                        print("已存在的 msgq 区域内容:")
                        print(existing_msgq_content)
    
            with open(template_file_path, "r", encoding="utf-8") as f:
                template_content = f.read()
    
            # 定义占位符内容
            thread_definitions = "\n".join([f"        osThreadId_t {task_var.get().lower()};" for task_var, _ in self.task_vars])
            msgq_definitions = existing_msgq_content if existing_msgq_content else "        osMessageQueueId_t default_msgq;"
            freq_definitions = "\n".join([f"        float {task_var.get().lower()};" for task_var, _ in self.task_vars])
            last_up_time_definitions = "\n".join([f"        uint32_t {task_var.get().lower()};" for task_var, _ in self.task_vars])
            task_attr_declarations = "\n".join([f"extern const osThreadAttr_t attr_{task_var.get().lower()};" for task_var, _ in self.task_vars])
            task_function_declarations = "\n".join([f"void Task_{task_var.get()}(void *argument);" for task_var, _ in self.task_vars])
            task_frequency_definitions = "\n".join([
                f"#define TASK_FREQ_{task_var.get().upper()} ({freq_var.get()}u)"
                for task_var, freq_var in self.task_vars
            ])
            task_init_delay_definitions = "\n".join([f"#define TASK_INIT_DELAY_{task_var.get().upper()} (0u)" for task_var, _ in self.task_vars])
            task_handle_definitions = "\n".join([f"    osThreadId_t {task_var.get().lower()};" for task_var, _ in self.task_vars])
    
            # 替换模板中的占位符
            header_content = template_content.replace("{{thread_definitions}}", thread_definitions)
            header_content = header_content.replace("{{msgq_definitions}}", msgq_definitions)
            header_content = header_content.replace("{{freq_definitions}}", freq_definitions)
            header_content = header_content.replace("{{last_up_time_definitions}}", last_up_time_definitions)
            header_content = header_content.replace("{{task_attr_declarations}}", task_attr_declarations)
            header_content = header_content.replace("{{task_function_declarations}}", task_function_declarations)
            header_content = header_content.replace("{{task_frequency_definitions}}", task_frequency_definitions)
            header_content = header_content.replace("{{task_init_delay_definitions}}", task_init_delay_definitions)
            header_content = header_content.replace("{{task_handle_definitions}}", task_handle_definitions)
    
            # 如果存在 /* USER MESSAGE BEGIN */ 区域内容，则保留
            if existing_msgq_content:
                header_content = re.sub(
                    r"/\* USER MESSAGE BEGIN \*/\s*.*?\s*/\* USER MESSAGE END \*/",
                    f"/* USER MESSAGE BEGIN */\n\n    {existing_msgq_content}\n\n    /* USER MESSAGE END */",
                    header_content,
                    flags=re.DOTALL
                )
    
            with open(header_file_path, "w", encoding="utf-8") as f:
                f.write(header_content)
    
            print(f"已成功生成 {header_file_path} 文件！")
        except Exception as e:
            print(f"生成 user_task.h 文件时出错: {e}")

    def generate_init_file(self):
        try:
            template_file_path = os.path.join(REPO_DIR, "User", "task", "init.c.template")
            generated_file_path = os.path.join("User", "task", "init.c")
    
            if not os.path.exists(template_file_path):
                print(f"模板文件 {template_file_path} 不存在，无法生成 init.c 文件！")
                return
    
            os.makedirs(os.path.dirname(generated_file_path), exist_ok=True)
    
            # 如果 init.c 已存在，提取 /* USER MESSAGE BEGIN */ 和 /* USER MESSAGE END */ 区域内容
            existing_msgq_content = ""
            if os.path.exists(generated_file_path):
                with open(generated_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 提取 /* USER MESSAGE BEGIN */ 和 /* USER MESSAGE END */ 区域内容
                    match = re.search(r"/\* USER MESSAGE BEGIN \*/\s*(.*?)\s*/\* USER MESSAGE END \*/", content, re.DOTALL)
                    if match:
                        existing_msgq_content = match.group(1).strip()
                        print("已存在的消息队列区域内容:")
                        print(existing_msgq_content)
    
            with open(template_file_path, "r", encoding="utf-8") as f:
                template_content = f.read()
    
            # 生成任务创建代码
            thread_creation_code = "\n".join([
                f"  task_runtime.thread.{task_var.get().lower()} = osThreadNew(Task_{task_var.get()}, NULL, &attr_{task_var.get().lower()});"
                for task_var, _ in self.task_vars  # 解包元组
            ])
    
            # 替换模板中的占位符
            init_content = template_content.replace("{{thread_creation_code}}", thread_creation_code)
    
            # 如果存在 /* USER MESSAGE BEGIN */ 区域内容，则保留
            if existing_msgq_content:
                init_content = re.sub(
                    r"/\* USER MESSAGE BEGIN \*/\s*.*?\s*/\* USER MESSAGE END \*/",
                    f"/* USER MESSAGE BEGIN */\n  {existing_msgq_content}\n  /* USER MESSAGE END */",
                    init_content,
                    flags=re.DOTALL
                )
    
            with open(generated_file_path, "w", encoding="utf-8") as f:
                f.write(init_content)
    
            print(f"已成功生成 {generated_file_path} 文件！")
        except Exception as e:
            print(f"生成 init.c 文件时出错: {e}")

    # 修改 generate_action 方法
    
    def generate_action(self):
        def task():
            # 检查并创建目录（与 FreeRTOS 状态无关的模块始终创建）
            self.create_directories()
    
            # 复制 .gitignore 文件
            if self.add_gitignore_var.get():
                self.copy_file_from_repo(".gitignore", ".gitignore")
    
            # 如果启用了 FreeRTOS，复制相关文件
            if self.ioc_data and self.check_freertos_enabled(self.ioc_data):
                self.copy_file_from_repo("src/freertos.c", os.path.join("Core", "Src", "freertos.c"))
    
            # 定义需要处理的文件夹（与 FreeRTOS 状态无关）
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
    
                    # 强制复制与文件夹同名的文件
                    if file_base == folder:
                        src_path = os.path.join(folder_dir, file_name)
                        dest_path = os.path.join("User", folder, file_name)
                        self.copy_file_from_repo(src_path, dest_path)
                        print(f"强制复制与文件夹同名的文件: {file_name}")
                        continue  # 跳过后续检查，直接复制
    
                    # 检查是否选中了对应的文件
                    if file_base in self.header_file_vars and self.header_file_vars[file_base].get():
                        src_path = os.path.join(folder_dir, file_name)
                        dest_path = os.path.join("User", folder, file_name)
                        self.copy_file_from_repo(src_path, dest_path)
    
            # 如果启用了 FreeRTOS，执行任务相关的生成逻辑
            if self.ioc_data and self.check_freertos_enabled(self.ioc_data):
                # 修改 user_task.c 文件
                self.modify_user_task_file()
    
                # 生成 user_task.h 文件
                self.generate_user_task_header()
    
                # 生成 init.c 文件
                self.generate_init_file()
    
                # 生成 task.c 文件
                self.generate_task_files()
    
        threading.Thread(target=task).start()


    # 程序关闭时清理
    def on_closing(self, root):
        self.delete_repo()
        root.destroy()


# 程序入口
if __name__ == "__main__":
    app = MRobotApp()
    app.initialize()