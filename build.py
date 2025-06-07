import os
import PyInstaller.__main__

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 图标文件路径
icon_path = os.path.join(current_dir, "icon.png")

# 如果图标文件不存在，则创建一个简单的图标
if not os.path.exists(icon_path):
    from PIL import Image, ImageDraw
    img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(50, 50), (206, 206)], outline=(0, 120, 215), fill=(240, 240, 240), width=10)
    img.save(icon_path)
    print(f"创建了默认图标: {icon_path}")

# 配置PyInstaller参数
PyInstaller.__main__.run([
    'main.py',                      # 主程序文件
    '--name=UnsplashWallpaper',     # 输出的exe文件名
    '--onefile',                    # 打包为单个文件
    f'--icon={icon_path}',          # 应用图标
    '--noconsole',                  # 不显示控制台窗口
    '--clean',                      # 清理临时文件
])

print("Done,check dir dist")
