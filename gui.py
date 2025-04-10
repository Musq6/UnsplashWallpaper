import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QComboBox, QFileDialog, 
                            QGroupBox, QCheckBox, QSystemTrayIcon, QMenu, QAction,
                            QMessageBox, QStyle, QApplication)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from settings import Settings
from wallpaper_manager import WallpaperManager
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QComboBox, QFileDialog, QMenu,
    QAction, QSystemTrayIcon, QCheckBox, QLineEdit  # 添加QLineEdit
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unsplash壁纸更换器")
        self.setMinimumSize(600, 400)
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 初始化设置和壁纸管理器
        self.settings = Settings()
        self.wallpaper_manager = WallpaperManager(self.settings)
        self.wallpaper_manager.wallpaper_changed.connect(self.on_wallpaper_changed)
        
        # 创建UI
        self.init_ui()
        
        # 创建系统托盘
        self.create_tray_icon()
        
        # 启动壁纸更换
        self.wallpaper_manager.start_timer()
    
    def init_ui(self):
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 壁纸预览区域
        preview_group = QGroupBox("当前壁纸")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel("尚未设置壁纸")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        preview_layout.addWidget(self.preview_label)
        
        # 壁纸操作按钮
        buttons_layout = QHBoxLayout()
        self.change_now_btn = QPushButton("立即更换壁纸")
        self.save_btn = QPushButton("保存当前壁纸")
        
        self.change_now_btn.clicked.connect(self.wallpaper_manager.change_wallpaper)
        self.save_btn.clicked.connect(self.save_current_wallpaper)
        
        buttons_layout.addWidget(self.change_now_btn)
        buttons_layout.addWidget(self.save_btn)
        preview_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(preview_group)
        
        # 设置区域
        settings_group = QGroupBox("设置")
        settings_layout = QVBoxLayout(settings_group)
        
        # 更换频率设置
        freq_layout = QHBoxLayout()
        freq_label = QLabel("壁纸更换频率:")
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["1小时", "2小时", "4小时", "1天"])
        current_freq = self.settings.get_setting("frequency")
        self.freq_combo.setCurrentText(current_freq)
        self.freq_combo.currentTextChanged.connect(self.on_frequency_changed)
        
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_combo)
        freq_layout.addStretch()
        settings_layout.addLayout(freq_layout)
        
        # 分辨率信息
        res_layout = QHBoxLayout()
        res_label = QLabel("屏幕分辨率:")
        width, height = self.wallpaper_manager.get_screen_resolution()
        self.res_info = QLabel(f"{width} x {height} (自动检测)")
        
        res_layout.addWidget(res_label)
        res_layout.addWidget(self.res_info)
        res_layout.addStretch()
        settings_layout.addLayout(res_layout)
        
        # 保存路径设置
        save_path_layout = QHBoxLayout()
        save_path_label = QLabel("壁纸保存位置:")
        self.save_path_edit = QLabel(self.settings.get_setting("save_path"))
        save_path_btn = QPushButton("浏览...")
        save_path_btn.clicked.connect(self.browse_save_path)
        
        save_path_layout.addWidget(save_path_label)
        save_path_layout.addWidget(self.save_path_edit)
        save_path_layout.addWidget(save_path_btn)
        settings_layout.addLayout(save_path_layout)
        
        # 收藏路径设置
        fav_path_layout = QHBoxLayout()
        fav_path_label = QLabel("收藏壁纸位置:")
        self.fav_path_edit = QLabel(self.settings.get_setting("favorite_path"))
        fav_path_btn = QPushButton("浏览...")
        fav_path_btn.clicked.connect(self.browse_favorite_path)
        
        fav_path_layout.addWidget(fav_path_label)
        fav_path_layout.addWidget(self.fav_path_edit)
        fav_path_layout.addWidget(fav_path_btn)
        settings_layout.addLayout(fav_path_layout)
        
        # 自启动设置
        autostart_layout = QHBoxLayout()
        self.autostart_check = QCheckBox("开机自动启动")
        self.autostart_check.setChecked(self.settings.get_setting("auto_start"))
        self.autostart_check.stateChanged.connect(self.on_autostart_changed)
        
        autostart_layout.addWidget(self.autostart_check)
        autostart_layout.addStretch()
        settings_layout.addLayout(autostart_layout)
        
        # 在init_ui方法中添加API设置部分
        
        # API设置
        api_layout = QHBoxLayout()
        api_label = QLabel("Unsplash API密钥:")
        self.api_key_edit = QLineEdit(self.settings.get_setting("unsplash_access_key", ""))
        self.api_key_edit.setPlaceholderText("输入你的Unsplash Access Key")
        self.api_key_edit.setEchoMode(QLineEdit.Password)  # 隐藏输入内容
        self.api_key_edit.editingFinished.connect(self.save_api_key)
        
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_edit)
        settings_layout.addLayout(api_layout)
        
        main_layout.addWidget(settings_group)
    
    def create_tray_icon(self):
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 使用自定义图标替代系统图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        
        # 如果图标文件存在，则使用自定义图标
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # 否则使用系统默认图标
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        
        change_action = QAction("立即更换壁纸", self)
        change_action.triggered.connect(self.wallpaper_manager.change_wallpaper)
        
        save_action = QAction("保存当前壁纸", self)
        save_action.triggered.connect(self.save_current_wallpaper)
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close_application)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(change_action)
        tray_menu.addAction(save_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # 点击托盘图标显示主窗口
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
    
    def on_tray_icon_activated(self, reason):
        try:
            # 处理不同类型的托盘图标激活事件
            if reason == QSystemTrayIcon.DoubleClick:
                self.show()
            elif reason == QSystemTrayIcon.Trigger:  # 单击
                # 可以选择显示菜单或其他操作
                pass
            elif reason == QSystemTrayIcon.MiddleClick:
                # 中键点击操作
                pass
            elif reason == QSystemTrayIcon.Context:
                # 右键点击，系统已自动显示上下文菜单
                pass
        except Exception as e:
            print(f"处理托盘图标事件时出错: {e}")
    
    def closeEvent(self, event):
        # 关闭窗口时最小化到托盘
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Unsplash壁纸更换器",
            "应用程序已最小化到系统托盘。双击图标可以重新打开窗口。",
            QSystemTrayIcon.Information,
            2000
        )
    
    def close_application(self):
        # 完全退出应用
        try:
            print("正在关闭应用程序...")
            self.wallpaper_manager.stop_timer()
            self.tray_icon.hide()
            # 确保应用程序能够正常退出
            QApplication.processEvents()
            QApplication.quit()
        except Exception as e:
            print(f"关闭应用程序时出错: {e}")
            # 如果正常退出失败，强制退出
            import sys
            sys.exit(0)
    
    def on_frequency_changed(self, text):
        # 更新频率设置
        self.settings.set_setting("frequency", text)
        self.wallpaper_manager.stop_timer()
        self.wallpaper_manager.start_timer()
    
    def on_autostart_changed(self, state):
        # 更新自启动设置
        self.settings.set_setting("auto_start", state == Qt.Checked)
        self.update_autostart_registry()
    
    def update_autostart_registry(self):
        # 更新注册表中的自启动设置
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "UnsplashWallpaper"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            if self.settings.get_setting("auto_start"):
                # 添加自启动
                app_path = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                # 移除自启动
                try:
                    winreg.DeleteValue(key, app_name)
                except:
                    pass
            
            winreg.CloseKey(key)
        except Exception as e:
            print(f"更新自启动设置时出错: {e}")
    
    def browse_save_path(self):
        # 浏览壁纸保存路径
        path = QFileDialog.getExistingDirectory(
            self, "选择壁纸保存位置", 
            self.settings.get_setting("save_path")
        )
        
        if path:
            self.settings.set_setting("save_path", path)
            self.save_path_edit.setText(path)
    
    def browse_favorite_path(self):
        # 浏览收藏壁纸路径
        path = QFileDialog.getExistingDirectory(
            self, "选择收藏壁纸位置", 
            self.settings.get_setting("favorite_path")
        )
        
        if path:
            self.settings.set_setting("favorite_path", path)
            self.fav_path_edit.setText(path)
    
    # 添加这个方法作为类的成员方法
    def save_api_key(self):
        api_key = self.api_key_edit.text().strip()
        self.settings.set_setting("unsplash_access_key", api_key)
        # 更新壁纸管理器中的密钥
        self.wallpaper_manager.unsplash_access_key = api_key
        print(f"API密钥已更新")
    
    def save_current_wallpaper(self):
        # 保存当前壁纸
        if self.wallpaper_manager.save_current_wallpaper():
            QMessageBox.information(self, "保存成功", "壁纸已成功保存到收藏夹！")
        else:
            QMessageBox.warning(self, "保存失败", "无法保存当前壁纸，请稍后再试。")
    
    def on_wallpaper_changed(self, image_path):
        # 更新壁纸预览
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(
                self.preview_label.width(), 
                self.preview_label.height(),
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(pixmap)
        else:
            self.preview_label.setText("无法加载壁纸预览")
    
    def resizeEvent(self, event):
        # 窗口大小改变时更新预览
        super().resizeEvent(event)
        if hasattr(self.wallpaper_manager, "current_wallpaper") and self.wallpaper_manager.current_wallpaper:
            self.on_wallpaper_changed(self.wallpaper_manager.current_wallpaper)