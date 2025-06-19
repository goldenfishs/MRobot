from PIL import Image
import os

def png_to_ico(png_path, ico_path=None, sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)]):
    if not os.path.isfile(png_path):
        print(f"文件不存在: {png_path}")
        return
    if ico_path is None:
        ico_path = os.path.splitext(png_path)[0] + ".ico"
    img = Image.open(png_path)
    img.save(ico_path, format='ICO', sizes=sizes)
    print(f"已生成: {ico_path}")

if __name__ == "__main__":
    # 直接写死路径
    png = r"C:\Mac\Home\Documents\R\MRobot\img\m1.png"
    ico = r"c:\Mac\Home\Documents\R\MRobot\img\M1.ico"
    png_to_ico(png, ico)