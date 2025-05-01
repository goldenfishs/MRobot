import os
import xml.etree.ElementTree as ET

# Keil 项目文件路径
KEIL_PROJECT_FILE = "C:\Mac\Home\Desktop\MR_test\MDK-ARM\MR_test.uvprojx"  # 替换为你的 Keil 项目文件路径
USER_DIR = "User"  # User 目录路径

def add_groups_and_files():
    # 检查 Keil 项目文件是否存在
    if not os.path.exists(KEIL_PROJECT_FILE):
        print(f"Keil 项目文件 {KEIL_PROJECT_FILE} 不存在！")
        return

    # 解析 Keil 项目文件
    tree = ET.parse(KEIL_PROJECT_FILE)
    root = tree.getroot()

    # 定位到 Groups 节点
    groups_node = root.find(".//Groups")
    if groups_node is None:
        print("未找到 Groups 节点！")
        return

    # 获取当前已有的组名和文件名，防止重复添加
    existing_groups = {group.find("GroupName").text for group in groups_node.findall("Group")}
    existing_files = {
        file.text
        for group in groups_node.findall("Group")
        for file in group.findall(".//FileName")
    }

    # 遍历 User 目录下的所有文件夹
    for folder_name in os.listdir(USER_DIR):
        folder_path = os.path.join(USER_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue

        group_name = f"User/{folder_name}"
        if group_name in existing_groups:
            print(f"组 {group_name} 已存在，跳过...")
            continue

        # 创建新的组节点
        group_node = ET.SubElement(groups_node, "Group")
        group_name_node = ET.SubElement(group_node, "GroupName")
        group_name_node.text = group_name

        # 创建 Files 节点
        files_node = ET.SubElement(group_node, "Files")

        # 遍历文件夹中的所有文件
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if not os.path.isfile(file_path):
                continue

            if file_name in existing_files:
                print(f"文件 {file_name} 已存在于其他组中，跳过...")
                continue

            # 添加文件节点
            file_node = ET.SubElement(files_node, "File")
            file_name_node = ET.SubElement(file_node, "FileName")
            file_name_node.text = file_name
            file_path_node = ET.SubElement(file_node, "FilePath")
            file_path_node.text = file_path

    # 保存修改后的 Keil 项目文件
    tree.write(KEIL_PROJECT_FILE, encoding="utf-8", xml_declaration=True)
    print("Keil 项目文件已更新！")

if __name__ == "__main__":
    add_groups_and_files()