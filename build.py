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
    print(f"创建了默认PNG图标: {png_icon_path}")

# 将PNG转换为ICO格式
if os.path.exists(png_icon_path) and not os.path.exists(ico_icon_path):
    try:
        from PIL import Image

        img = Image.open(png_icon_path)
        # 创建多种尺寸的ICO文件
        img.save(
            ico_icon_path,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
        print(f"转换PNG为ICO: {ico_icon_path}")
    except Exception as e:
        print(f"转换图标格式失败: {e}")
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
    print(f"使用图标文件: {ico_icon_path}")
elif os.path.exists(png_icon_path):
    pyinstaller_args.append(f"--icon={png_icon_path}")
    print(f"使用图标文件: {png_icon_path}")
else:
    print("警告: 没有找到图标文件")

# 添加数据文件（确保图标文件被包含到打包中）
if os.path.exists(ico_icon_path):
    pyinstaller_args.append(f"--add-data={ico_icon_path};.")
if os.path.exists(png_icon_path):
    pyinstaller_args.append(f"--add-data={png_icon_path};.")

print("PyInstaller参数:", pyinstaller_args)

# 运行PyInstaller
PyInstaller.__main__.run(pyinstaller_args)

print("Done check DIR dist")
