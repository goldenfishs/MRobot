import xml.etree.ElementTree as ET
import os

def add_include_path(project_file, new_path):
    # 检查文件是否存在
    if not os.path.exists(project_file):
        print(f"项目文件 {project_file} 不存在！")
        return

    # 解析 XML 文件
    tree = ET.parse(project_file)
    root = tree.getroot()

    # 定位到所有 IncludePath 节点
    include_path_nodes = root.findall(".//IncludePath")
    if not include_path_nodes:
        print("未找到任何 IncludePath 节点，无法添加路径。")
        return

    updated = False
    for include_path_node in include_path_nodes:
        # 获取当前 IncludePath 的值
        include_paths = include_path_node.text.split(";") if include_path_node.text else []

        # 检查是否已经包含 new_path
        if new_path in include_paths:
            print(f"路径 '{new_path}' 已存在于一个 IncludePath 节点中，无需重复添加。")
            continue

        # 添加新路径
        include_paths.append(new_path)
        include_path_node.text = ";".join(include_paths)
        updated = True
        print(f"路径 '{new_path}' 已成功添加到一个 IncludePath 节点中。")

    if updated:
        # 保存修改
        tree.write(project_file, encoding="utf-8", xml_declaration=True)
        print(f"项目文件已更新：{project_file}")
    else:
        print("未对项目文件进行任何修改。")

# 示例用法
if __name__ == "__main__":
    # 替换为您的 .uvprojx 文件路径
    project_file_path = r"C:\Mac\Home\Desktop\MR_test\MDK-ARM\MR_test.uvprojx"
    include_path_to_add = r"..\User"
    add_include_path(project_file_path, include_path_to_add)