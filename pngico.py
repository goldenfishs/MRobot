from PIL import Image
import os

def crop_transparent_background(input_path, output_path):
    """
    裁切 PNG 图片的透明背景并保存。
    
    :param input_path: 输入图片路径
    :param output_path: 输出图片路径
    """
    try:
        # 打开图片
        img = Image.open(input_path)
        
        # 确保图片是 RGBA 模式
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        # 获取图片的 alpha 通道
        bbox = img.getbbox()
        
        if bbox:
            # 裁切图片
            cropped_img = img.crop(bbox)
            # 保存裁切后的图片
            cropped_img.save(output_path, format="PNG")
            print(f"图片已保存到: {output_path}")
        else:
            print("图片没有透明背景或为空。")
    except Exception as e:
        print(f"处理图片时出错: {e}")

if __name__ == "__main__":
    # 示例：输入和输出路径
    input_file = "C:\Mac\Home\Desktop\MRobot\img\M.png"  # 替换为你的输入图片路径
    output_file = "C:\Mac\Home\Desktop\MRobot\img\M.png"  # 替换为你的输出图片路径

    # 检查文件是否存在
    if os.path.exists(input_file):
        crop_transparent_background(input_file, output_file)
    else:
        print(f"输入文件不存在: {input_file}")