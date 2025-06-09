# main.py
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor
from PyQt5.QtCore import Qt


def set_app_user_model_id():
    """设置Windows应用程序用户模型ID"""
    try:
        import ctypes

        # 设置应用程序ID，这样Windows就会将其视为独立应用
        app_id = "WallpaperChanger.UnsplashWallpaper.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        print(f"应用程序ID设置成功: {app_id}")
    except Exception as e:
        print(f"设置应用程序ID失败: {e}")


def create_app_icon():
    """创建应用程序图标"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, "icon.png")

    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        if not icon.isNull():
            print(f"成功加载图标文件: {icon_path}")
            return icon

    # 创建默认图标
    print("创建默认应用程序图标")
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setBrush(QBrush(QColor(70, 130, 180)))
    painter.drawEllipse(4, 4, 56, 56)

    painter.setBrush(QBrush(QColor(255, 255, 255)))
    painter.drawEllipse(18, 18, 28, 28)

    painter.setBrush(QBrush(QColor(70, 130, 180)))
    painter.drawEllipse(26, 26, 12, 12)

    painter.end()

    return QIcon(pixmap)


def main():
    # 在创建QApplication之前设置应用程序ID
    if sys.platform == "win32":
        set_app_user_model_id()

    app = QApplication(sys.argv)

    # 设置应用程序属性
    app.setApplicationName("Unsplash壁纸更换器")
    app.setApplicationVersion("0.2")
    app.setOrganizationName("WallpaperChanger")
    app.setApplicationDisplayName("Unsplash壁纸更换器")

    # 创建并设置应用程序图标
    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)

    print("启动应用程序...")

    try:
        from gui import MainWindow

        print("gui模块导入成功")

        # 创建主窗口
        window = MainWindow()
        window.setWindowIcon(app_icon)

        print("主窗口创建成功")

        # 显示窗口
        window.show()

        # Windows特定：延迟设置任务栏图标
        if sys.platform == "win32":
            from PyQt5.QtCore import QTimer

            def delayed_icon_setup():
                if hasattr(window, "setup_windows_taskbar_icon"):
                    window.setup_windows_taskbar_icon()

            QTimer.singleShot(500, delayed_icon_setup)  # 延迟500ms

        print("窗口显示成功")

        sys.exit(app.exec_())

    except Exception as e:
        print(f"启动应用程序时出错: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
