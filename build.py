import os
import PyInstaller.__main__

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 图标文件路径
png_icon_path = os.path.join(current_dir, "icon.png")
ico_icon_path = os.path.join(current_dir, "icon.ico")

# 如果PNG图标文件不存在，则创建一个简单的图标
if not os.path.exists(png_icon_path):
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (256, 256), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle(
        [(50, 50), (206, 206)], outline=(0, 120, 215), fill=(240, 240, 240), width=10
    )
    img.save(png_icon_path)
    print(f"Created default PNG icon: {png_icon_path}")

# 将PNG转换为ICO格式
if os.path.exists(png_icon_path) and not os.path.exists(ico_icon_path):
    try:
        from PIL import Image

        img = Image.open(png_icon_path)
        # 创建多种尺寸的ICO文件
        img.save(
            ico_icon_path,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
        )
        print(f"Converted PNG to ICO: {ico_icon_path}")
    except Exception as e:
        print(f"Failed to convert icon format: {e}")
        ico_icon_path = png_icon_path  # 回退到PNG

# 配置PyInstaller参数
pyinstaller_args = [
    "main.py",  # 主程序文件
    "--name=UnsplashWallpaper",  # 输出的exe文件名
    "--onefile",  # 打包为单个文件
    "--noconsole",  # 不显示控制台窗口
    "--clean",  # 清理临时文件
]

# 添加图标参数
if os.path.exists(ico_icon_path):
    pyinstaller_args.append(f"--icon={ico_icon_path}")
    print(f"Using icon file: {ico_icon_path}")
elif os.path.exists(png_icon_path):
    pyinstaller_args.append(f"--icon={png_icon_path}")
    print(f"Using icon file: {png_icon_path}")
else:
    print("Warning: No icon file found")


if os.path.exists(ico_icon_path):
    pyinstaller_args.append(f"--add-data={ico_icon_path};.")
if os.path.exists(png_icon_path):
    pyinstaller_args.append(f"--add-data={png_icon_path};.")

print("PyInstaller arguments:", pyinstaller_args)

PyInstaller.__main__.run(pyinstaller_args)

print("Build completed, check dist directory")
