import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QCheckBox,
    QSystemTrayIcon,
    QMenu,
    QAction,
    QMessageBox,
    QStyle,
    QApplication,
    QLineEdit,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor
from settings import Settings
from wallpaper_manager import WallpaperManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unsplash壁纸更换器")
        self.setMinimumSize(600, 500)

        # 初始化设置和壁纸管理器
        self.settings = Settings()
        self.wallpaper_manager = WallpaperManager(self.settings)
        self.wallpaper_manager.wallpaper_changed.connect(self.on_wallpaper_changed)

        # 设置应用程序图标
        self.setup_application_icon()

        # 创建UI
        self.init_ui()

        # 创建系统托盘
        self.create_tray_icon()

        # 启动壁纸更换
        self.wallpaper_manager.start_timer()

    def setup_application_icon(self):
        """设置应用程序图标"""
        print("开始设置应用程序图标...")

        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "icon.png")

        print(f"尝试加载图标: {icon_path}")
        print(f"图标文件存在: {os.path.exists(icon_path)}")

        if os.path.exists(icon_path):
            try:
                icon = QIcon(icon_path)
                if not icon.isNull():
                    print("图标加载成功")
                    self.setWindowIcon(icon)
                    QApplication.instance().setWindowIcon(icon)
                    self.app_icon = icon
                    return
                else:
                    print("图标文件无效")
            except Exception as e:
                print(f"加载图标时出错: {e}")

        # 创建默认图标
        print("创建默认图标")
        self.create_default_icon()

    def create_default_icon(self):
        """创建默认图标"""
        try:
            # 创建一个32x32的图标
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # 绘制一个蓝色圆圈
            painter.setBrush(QBrush(QColor(70, 130, 180)))
            painter.drawEllipse(2, 2, 28, 28)

            # 绘制一个白色内圆
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(10, 10, 12, 12)

            painter.end()

            # 创建图标
            icon = QIcon(pixmap)
            self.setWindowIcon(icon)
            QApplication.instance().setWindowIcon(icon)
            self.app_icon = icon

            print("默认图标创建成功")

        except Exception as e:
            print(f"创建默认图标失败: {e}")
            # 使用系统图标
            system_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
            self.setWindowIcon(system_icon)
            QApplication.instance().setWindowIcon(system_icon)
            self.app_icon = system_icon

    def init_ui(self):
        """初始化用户界面"""
        print("开始初始化UI...")

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 壁纸预览区域
        preview_group = QGroupBox("当前壁纸")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel("尚未设置壁纸")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet(
            "border: 1px solid gray; background-color: #f0f0f0;"
        )
        preview_layout.addWidget(self.preview_label)

        # 壁纸操作按钮
        buttons_layout = QHBoxLayout()
        self.change_now_btn = QPushButton("立即更换壁纸")
        self.save_btn = QPushButton("保存当前壁纸")

        self.change_now_btn.clicked.connect(self.manual_change_wallpaper)
        self.save_btn.clicked.connect(self.save_current_wallpaper)

        buttons_layout.addWidget(self.change_now_btn)
        buttons_layout.addWidget(self.save_btn)
        preview_layout.addLayout(buttons_layout)

        main_layout.addWidget(preview_group)

        # 设置区域
        settings_group = QGroupBox("基本设置")
        settings_layout = QVBoxLayout(settings_group)

        # 更换频率设置
        freq_layout = QHBoxLayout()
        freq_label = QLabel("壁纸更换频率:")
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["1小时", "2小时", "4小时", "1天"])
        current_freq = self.settings.get_setting("frequency", "1小时")
        if current_freq in ["1小时", "2小时", "4小时", "1天"]:
            self.freq_combo.setCurrentText(current_freq)
        self.freq_combo.currentTextChanged.connect(self.on_frequency_changed)

        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_combo)
        freq_layout.addStretch()
        settings_layout.addLayout(freq_layout)

        # 分辨率信息
        res_layout = QHBoxLayout()
        res_label = QLabel("屏幕分辨率:")
        try:
            resolutions = self.wallpaper_manager.get_screen_resolution()
            base_res = resolutions.get("base", (1920, 1080))
            self.res_info = QLabel(f"{base_res[0]} x {base_res[1]} (自动检测)")
        except Exception as e:
            print(f"获取屏幕分辨率时出错: {e}")
            self.res_info = QLabel("1920 x 1080 (默认)")

        res_layout.addWidget(res_label)
        res_layout.addWidget(self.res_info)
        res_layout.addStretch()
        settings_layout.addLayout(res_layout)

        # API设置
        api_layout = QHBoxLayout()
        api_label = QLabel("Unsplash API密钥:")
        self.api_key_edit = QLineEdit(
            self.settings.get_setting("unsplash_access_key", "")
        )
        self.api_key_edit.setPlaceholderText("输入你的Unsplash Access Key")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.editingFinished.connect(self.save_api_key)

        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_edit)
        settings_layout.addLayout(api_layout)

        main_layout.addWidget(settings_group)

        # 合集设置组
        self.create_collection_settings(main_layout)

        # 路径设置组
        self.create_path_settings(main_layout)

        # 其他设置组
        self.create_other_settings(main_layout)

        print("UI初始化完成")

    def create_collection_settings(self, main_layout):
        """创建合集设置区域"""
        collection_group = QGroupBox("合集设置")
        collection_layout = QVBoxLayout(collection_group)

        # 启用合集模式
        collection_mode_layout = QHBoxLayout()
        self.use_collection_check = QCheckBox("使用合集模式")
        self.use_collection_check.setChecked(
            self.settings.get_setting("use_collection", False)
        )
        self.use_collection_check.stateChanged.connect(self.on_collection_mode_changed)

        collection_mode_layout.addWidget(self.use_collection_check)
        collection_mode_layout.addStretch()
        collection_layout.addLayout(collection_mode_layout)

        # 合集选择（现有代码）
        collection_select_layout = QHBoxLayout()
        collection_select_label = QLabel("选择合集:")
        self.collection_combo = QComboBox()
        self.collection_combo.setMinimumWidth(200)

        # 刷新合集按钮
        refresh_collections_btn = QPushButton("刷新合集")
        refresh_collections_btn.clicked.connect(self.refresh_collections)

        # 搜索合集按钮
        search_collections_btn = QPushButton("搜索合集")
        search_collections_btn.clicked.connect(self.search_collections_dialog)

        collection_select_layout.addWidget(collection_select_label)
        collection_select_layout.addWidget(self.collection_combo)
        collection_select_layout.addWidget(refresh_collections_btn)
        collection_select_layout.addWidget(search_collections_btn)
        collection_layout.addLayout(collection_select_layout)

        # 自定义合集按钮行（现有代码）
        custom_collection_layout = QHBoxLayout()
        add_custom_btn = QPushButton("添加自定义合集")
        add_custom_btn.clicked.connect(self.add_custom_collection_dialog)

        manage_custom_btn = QPushButton("管理自定义合集")
        manage_custom_btn.clicked.connect(self.manage_custom_collections_dialog)

        custom_collection_layout.addWidget(add_custom_btn)
        custom_collection_layout.addWidget(manage_custom_btn)
        custom_collection_layout.addStretch()
        collection_layout.addLayout(custom_collection_layout)

        # 信息显示区域
        self.collection_info_label = QLabel("未选择合集或用户")
        self.collection_info_label.setWordWrap(True)
        self.collection_info_label.setStyleSheet(
            "color: #666; font-size: 12px; padding: 5px;"
        )
        collection_layout.addWidget(self.collection_info_label)

        # 预览区域
        collection_preview_layout = QHBoxLayout()
        self.collection_preview_label = QLabel("合集/用户预览")
        self.collection_preview_label.setAlignment(Qt.AlignCenter)
        self.collection_preview_label.setMinimumHeight(100)
        self.collection_preview_label.setStyleSheet(
            "border: 1px solid gray; background-color: #f9f9f9;"
        )
        collection_preview_layout.addWidget(self.collection_preview_label)
        collection_layout.addLayout(collection_preview_layout)

        main_layout.addWidget(collection_group)

        # 初始化相关功能
        self.load_popular_collections()
        self.collection_combo.currentTextChanged.connect(self.on_collection_changed)
        self.update_collection_controls()

    def create_path_settings(self, main_layout):
        """创建路径设置区域"""
        path_group = QGroupBox("路径设置")
        path_layout = QVBoxLayout(path_group)

        # 保存路径设置
        save_path_layout = QHBoxLayout()
        save_path_label = QLabel("壁纸保存位置:")
        self.save_path_edit = QLabel(self.settings.get_setting("save_path", ""))
        save_path_btn = QPushButton("浏览...")
        save_path_btn.clicked.connect(self.browse_save_path)

        save_path_layout.addWidget(save_path_label)
        save_path_layout.addWidget(self.save_path_edit)
        save_path_layout.addWidget(save_path_btn)
        path_layout.addLayout(save_path_layout)

        # 收藏路径设置
        fav_path_layout = QHBoxLayout()
        fav_path_label = QLabel("收藏壁纸位置:")
        self.fav_path_edit = QLabel(self.settings.get_setting("favorite_path", ""))
        fav_path_btn = QPushButton("浏览...")
        fav_path_btn.clicked.connect(self.browse_favorite_path)

        fav_path_layout.addWidget(fav_path_label)
        fav_path_layout.addWidget(self.fav_path_edit)
        fav_path_layout.addWidget(fav_path_btn)
        path_layout.addLayout(fav_path_layout)

        main_layout.addWidget(path_group)

    def create_other_settings(self, main_layout):
        """创建其他设置区域"""
        other_group = QGroupBox("其他设置")
        other_layout = QVBoxLayout(other_group)

        # 自启动设置
        autostart_layout = QHBoxLayout()
        self.autostart_check = QCheckBox("开机自动启动")
        self.autostart_check.setChecked(self.settings.get_setting("auto_start", False))
        self.autostart_check.stateChanged.connect(self.on_autostart_changed)

        autostart_layout.addWidget(self.autostart_check)
        autostart_layout.addStretch()
        other_layout.addLayout(autostart_layout)

        # 程序控制按钮
        control_layout = QHBoxLayout()
        minimize_btn = QPushButton("最小化到托盘")
        minimize_btn.clicked.connect(self.hide)

        exit_btn = QPushButton("退出程序")
        exit_btn.clicked.connect(self.close_application)
        exit_btn.setStyleSheet(
            "QPushButton { background-color: #ff6b6b; color: white; }"
        )

        control_layout.addWidget(minimize_btn)
        control_layout.addWidget(exit_btn)
        control_layout.addStretch()
        other_layout.addLayout(control_layout)

        main_layout.addWidget(other_group)

    def create_tray_icon(self):
        """创建系统托盘图标"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(self, "系统托盘", "系统不支持托盘功能")
            return

        self.tray_icon = QSystemTrayIcon(self)

        # 使用应用程序图标作为托盘图标
        if hasattr(self, "app_icon"):
            self.tray_icon.setIcon(self.app_icon)
        else:
            system_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
            self.tray_icon.setIcon(system_icon)

        self.tray_icon.setToolTip("Unsplash壁纸更换器")

        # 创建托盘菜单
        tray_menu = QMenu()

        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_main_window)

        change_action = QAction("立即更换壁纸", self)
        change_action.triggered.connect(self.manual_change_wallpaper)

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
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def show_main_window(self):
        """显示主窗口"""
        self.show()
        self.raise_()
        self.activateWindow()

    def on_tray_icon_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()

    def closeEvent(self, event):
        """窗口关闭事件"""
        if hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            # 询问用户是否要退出
            reply = QMessageBox.question(
                self,
                "确认操作",
                "您想要:\n\n"
                '• 最小化到系统托盘 (点击"No")\n'
                '• 完全退出程序 (点击"Yes")',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,  # 默认选择No（最小化）
            )

            if reply == QMessageBox.Yes:
                # 用户选择完全退出
                self.close_application()
                event.accept()
            else:
                # 用户选择最小化到托盘
                event.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    "Unsplash壁纸更换器",
                    "应用程序已最小化到系统托盘。双击图标可以重新打开窗口。",
                    QSystemTrayIcon.Information,
                    2000,
                )
        else:
            # 如果托盘不可用，直接退出
            self.close_application()
            event.accept()

    def close_application(self):
        """完全退出应用"""
        try:
            print("正在关闭应用程序...")

            # 停止壁纸管理器
            if hasattr(self, "wallpaper_manager"):
                self.wallpaper_manager.stop_timer()

            # 隐藏托盘图标
            if hasattr(self, "tray_icon"):
                self.tray_icon.hide()

            # 处理所有待处理的事件
            QApplication.processEvents()

            # 退出应用程序
            QApplication.quit()

            # 如果QApplication.quit()没有工作，强制退出
            import sys

            sys.exit(0)

        except Exception as e:
            print(f"关闭应用程序时出错: {e}")
            # 强制退出
            import sys

            sys.exit(0)

    def manual_change_wallpaper(self):
        """手动更换壁纸"""
        self.wallpaper_manager.change_wallpaper()

    def on_frequency_changed(self, text):
        """频率改变事件"""
        self.settings.set_setting("frequency", text)
        self.wallpaper_manager.stop_timer()
        self.wallpaper_manager.start_timer()

    def on_autostart_changed(self, state):
        """自启动设置改变"""
        self.settings.set_setting("auto_start", state == Qt.Checked)
        self.update_autostart_registry()

    def update_autostart_registry(self):
        """更新自启动注册表"""
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "UnsplashWallpaper"

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
            )

            if self.settings.get_setting("auto_start"):
                app_path = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except:
                    pass

            winreg.CloseKey(key)
        except Exception as e:
            print(f"更新自启动设置时出错: {e}")

    def on_collection_mode_changed(self, state):
        """合集模式开关改变"""
        use_collection = state == Qt.Checked
        self.settings.set_setting("use_collection", use_collection)
        self.update_collection_controls()

        # 重启定时器以应用新设置
        self.wallpaper_manager.stop_timer()
        self.wallpaper_manager.start_timer()

    def update_collection_controls(self):
        """更新合集控件的启用状态"""
        use_collection = self.settings.get_setting("use_collection", False)

        self.collection_combo.setEnabled(use_collection)

        # 更新信息标签
        if use_collection:
            selected_collection = self.settings.get_setting("selected_collection", "")
            if selected_collection:
                collection_name = self.get_collection_name_by_id(selected_collection)

                # 检查是否是用户likes合集
                if selected_collection.startswith("user_likes_"):
                    self.collection_info_label.setText(
                        f"✅ 当前选择: {collection_name} (用户Likes)"
                    )
                else:
                    self.collection_info_label.setText(
                        f"✅ 当前选择: {collection_name}"
                    )

                self.collection_info_label.setStyleSheet(
                    "color: #27ae60; font-size: 13px; padding: 8px; font-weight: bold; "
                    "font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;"
                )

                # 加载预览信息
                self.load_collection_preview(selected_collection)
            else:
                self.collection_info_label.setText("⚠️ 请选择一个合集或用户")
                self.collection_info_label.setStyleSheet(
                    "color: #f39c12; font-size: 13px; padding: 8px; "
                    "font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;"
                )

                # 清空预览
                empty_html = """
                <div style="font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif; text-align: center;">
                    <p style="margin: 0 0 12px 0; font-size: 13px; color: #95a5a6;">
                        🎯 选择合集后显示预览
                    </p>
                    <p style="margin: 0; font-size: 11px; color: #bdc3c7; line-height: 1.4;">
                        包含合集标题、作者、照片数量等详细信息
                    </p>
                </div>
                """

                self.collection_preview_label.setText(empty_html)
                self.collection_preview_label.setTextFormat(Qt.RichText)
                self.collection_preview_label.setStyleSheet(
                    "QLabel {"
                    "   border: 1px solid #ecf0f1;"
                    "   background-color: #fafbfc;"
                    "   padding: 20px;"
                    "   border-radius: 8px;"
                    "   font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;"
                    "}"
                )
        else:
            self.collection_info_label.setText("🔄 使用随机壁纸模式")
            self.collection_info_label.setStyleSheet(
                "color: #7f8c8d; font-size: 13px; padding: 8px; "
                "font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;"
            )

            # 显示随机模式状态
            random_html = """
            <div style="font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif; text-align: center;">
                <p style="margin: 0 0 12px 0; font-size: 13px; color: #95a5a6;">
                    🎲 随机壁纸模式
                </p>
                <p style="margin: 0 0 8px 0; font-size: 11px; color: #bdc3c7;">
                    从Unsplash随机获取高质量壁纸
                </p>
            </div>
            """

            self.collection_preview_label.setText(random_html)
            self.collection_preview_label.setTextFormat(Qt.RichText)
            self.collection_preview_label.setStyleSheet(
                "QLabel {"
                "   border: 1px solid #ecf0f1;"
                "   background-color: #f8f9fa;"
                "   padding: 20px;"
                "   border-radius: 8px;"
                "   font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;"
                "}"
            )

    def load_popular_collections(self):
        """加载热门合集到下拉框"""
        try:
            self.collection_combo.clear()

            # 添加默认选项
            self.collection_combo.addItem("请选择合集...", "")

            # 获取热门合集
            popular_collections = self.wallpaper_manager.get_popular_collections()

            for name, collection_id in popular_collections.items():
                self.collection_combo.addItem(name, collection_id)

            # 添加分隔符（如果有自定义合集）
            custom_collections = self.settings.get_custom_collections()
            if custom_collections:
                # 添加分隔符项
                separator_item = "--- 自定义合集 ---"
                self.collection_combo.addItem(separator_item, "separator")

                # 添加自定义合集
                for name, collection_id in custom_collections.items():
                    display_name = f"{name} (自定义)"
                    self.collection_combo.addItem(display_name, collection_id)

            # 设置当前选择
            current_collection = self.settings.get_setting("selected_collection", "")
            if current_collection:
                index = self.collection_combo.findData(current_collection)
                if index >= 0:
                    self.collection_combo.setCurrentIndex(index)

            print("合集列表加载完成")

        except Exception as e:
            print(f"加载合集失败: {e}")

    def refresh_collections(self):
        """刷新合集列表"""
        try:
            # 重新加载热门合集
            self.load_popular_collections()

            # 显示成功消息
            QMessageBox.information(self, "刷新完成", "合集列表已刷新")

        except Exception as e:
            QMessageBox.warning(self, "刷新失败", f"刷新合集列表失败: {str(e)}")

    def on_collection_changed(self, collection_name):
        """合集选择改变"""
        if (
            collection_name == "请选择合集..."
            or collection_name == "--- 自定义合集 ---"
        ):
            self.settings.set_setting("selected_collection", "")
            self.collection_info_label.setText("⚠️ 请选择一个合集")
            self.collection_info_label.setStyleSheet(
                "color: #ffc107; font-size: 12px; padding: 5px;"
            )

            # 显示选择提示
            self.collection_preview_label.setText(
                "🎯 请从下拉列表中选择一个合集\n\n" "📋 选择后将显示合集的详细信息"
            )
            self.collection_preview_label.setStyleSheet(
                "border: 1px solid #dee2e6; "
                "background-color: #f8f9fa; "
                "padding: 15px; "
                "border-radius: 5px; "
                "font-size: 12px; "
                "color: #6c757d;"
            )
            return

        # 获取选中的合集ID
        current_index = self.collection_combo.currentIndex()
        collection_id = self.collection_combo.itemData(current_index)

        # 如果是分隔符，跳过
        if collection_id == "separator":
            self.settings.set_setting("selected_collection", "")
            return

        if collection_id:
            self.settings.set_setting("selected_collection", collection_id)
            self.collection_info_label.setText(f"✅ 当前选择: {collection_name}")
            self.collection_info_label.setStyleSheet(
                "color: #28a745; font-size: 12px; padding: 5px; font-weight: bold;"
            )

            # 加载合集预览
            self.load_collection_preview(collection_id)

            print(f"选择合集: {collection_name} (ID: {collection_id})")
        else:
            self.settings.set_setting("selected_collection", "")

    def search_collections_dialog(self):
        """打开搜索合集对话框"""
        print("search_collections_dialog 被调用")  # 调试信息

        from PyQt5.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLineEdit,
            QPushButton,
            QListWidget,
            QListWidgetItem,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("搜索合集")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialog)

        # 搜索输入
        search_layout = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText("输入搜索关键词，如：nature, city, abstract...")
        search_btn = QPushButton("搜索")

        search_layout.addWidget(search_input)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

        # 搜索结果列表
        results_list = QListWidget()
        layout.addWidget(results_list)

        # 按钮
        button_layout = QHBoxLayout()
        select_btn = QPushButton("选择")
        cancel_btn = QPushButton("取消")

        select_btn.setEnabled(False)

        button_layout.addWidget(select_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        # 定义内部函数
        def perform_search():
            query = search_input.text().strip()
            if not query:
                QMessageBox.warning(dialog, "提示", "请输入搜索关键词")
                return

            search_btn.setText("搜索中...")
            search_btn.setEnabled(False)
            results_list.clear()

            try:
                collections = self.wallpaper_manager.search_collections(query)

                for collection in collections:
                    item_text = (
                        f"{collection['title']}\n照片数量: {collection['total_photos']}"
                    )
                    if collection["description"]:
                        item_text += f"\n描述: {collection['description'][:100]}..."

                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, collection["id"])
                    results_list.addItem(item)

                if not collections:
                    item = QListWidgetItem("未找到相关合集")
                    results_list.addItem(item)

            except Exception as e:
                item = QListWidgetItem(f"搜索失败: {str(e)}")
                results_list.addItem(item)

            finally:
                search_btn.setText("搜索")
                search_btn.setEnabled(True)

        def on_selection_changed():
            current_item = results_list.currentItem()
            has_valid_selection = (
                current_item is not None and current_item.data(Qt.UserRole) is not None
            )
            select_btn.setEnabled(has_valid_selection)

        def select_collection():
            current_item = results_list.currentItem()
            if current_item and current_item.data(Qt.UserRole):
                collection_id = current_item.data(Qt.UserRole)
                collection_name = current_item.text().split("\n")[0]

                # 添加到下拉框
                self.collection_combo.addItem(collection_name, collection_id)
                self.collection_combo.setCurrentText(collection_name)

                # 保存为自定义合集
                self.settings.add_custom_collection(collection_name, collection_id)

                dialog.accept()

        def on_double_click(item):
            if item and item.data(Qt.UserRole):
                select_collection()

        # 连接事件
        search_btn.clicked.connect(perform_search)
        search_input.returnPressed.connect(perform_search)
        results_list.itemSelectionChanged.connect(on_selection_changed)
        select_btn.clicked.connect(select_collection)
        cancel_btn.clicked.connect(dialog.reject)
        results_list.itemDoubleClicked.connect(on_double_click)

        # 显示对话框
        dialog.exec_()

    def add_custom_collection_dialog(self):
        """添加自定义合集对话框 - 整合版"""
        print("add_custom_collection_dialog 被调用")  # 调试信息

        from PyQt5.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLineEdit,
            QPushButton,
            QLabel,
            QScrollArea,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("添加自定义合集")
        dialog.setMinimumSize(500, 400)
        dialog.resize(500, 500)

        layout = QVBoxLayout(dialog)

        # 说明标签
        info_label = QLabel("输入合集ID或URL来添加自定义合集:")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # 输入区域
        input_layout = QVBoxLayout()

        # 合集ID/URL输入
        input_layout.addWidget(QLabel("合集ID或URL:"))
        collection_input = QLineEdit()
        collection_input.setPlaceholderText("输入合集ID 或完整URL")
        input_layout.addWidget(collection_input)

        # 合集名称输入
        input_layout.addWidget(QLabel("合集名称:"))
        collection_name_input = QLineEdit()
        collection_name_input.setPlaceholderText(
            "为这个合集起一个名字（验证成功后会自动填充）"
        )
        input_layout.addWidget(collection_name_input)

        # 验证按钮
        validate_btn = QPushButton("验证合集")
        validate_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px; }"
        )
        input_layout.addWidget(validate_btn)

        layout.addLayout(input_layout)

        # 验证结果显示区域
        result_scroll = QScrollArea()
        result_scroll.setWidgetResizable(True)
        result_scroll.setMinimumHeight(150)
        result_scroll.setMaximumHeight(250)

        result_label = QLabel("验证会消耗一次API请求，添加后会缓存数据")
        result_label.setWordWrap(True)
        result_label.setAlignment(Qt.AlignTop)
        result_label.setStyleSheet(
            "color: #666; padding: 15px; border: 1px solid #ddd; background-color: #f9f9f9; border-radius: 5px;"
        )
        result_label.setMinimumHeight(120)
        result_label.setSizePolicy(
            result_label.sizePolicy().Expanding, result_label.sizePolicy().Expanding
        )

        result_scroll.setWidget(result_label)
        layout.addWidget(result_scroll)

        # 支持格式说明
        help_label = QLabel(
            "支持的格式:\n"
            "• 合集ID: 字母数字混合 或 纯数字\n"
            "• 合集URL: https://unsplash.com/collections/xxxx\n"
            "• 用户Likes: https://unsplash.com/@username/likes"
        )
        help_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 10px;")
        layout.addWidget(help_label)

        # 按钮
        button_layout = QHBoxLayout()
        add_btn = QPushButton("添加合集")
        add_btn.setEnabled(False)
        add_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 16px; }"
        )

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("QPushButton { padding: 8px 16px; }")

        button_layout.addWidget(add_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 存储验证结果
        validated_collection = {}

        # ========== 内部函数定义（注意顺序）==========

        def update_result_display(text, status):
            """更新结果显示，并自动调整大小"""
            result_label.setText(text)

            if status == "success":
                style = "color: green; padding: 15px; border: 1px solid #4CAF50; background-color: #f0f8f0; border-radius: 5px;"
            elif status == "error":
                style = "color: red; padding: 15px; border: 1px solid #f44336; background-color: #f9f9f9; border-radius: 5px;"
            else:
                style = "color: #666; padding: 15px; border: 1px solid #ddd; background-color: #f9f9f9; border-radius: 5px;"

            result_label.setStyleSheet(style)

            # 计算所需高度并调整
            font_metrics = result_label.fontMetrics()
            text_rect = font_metrics.boundingRect(
                0, 0, result_label.width() - 30, 0, Qt.TextWordWrap, text
            )
            needed_height = max(120, text_rect.height() + 30)

            result_label.setMinimumHeight(needed_height)
            result_label.updateGeometry()
            dialog.adjustSize()

        def reset_validation():
            """重置验证状态"""
            add_btn.setEnabled(False)
            validated_collection.clear()
            update_result_display("请输入合集ID或URL并点击验证", "default")

        def auto_detect_and_validate():
            """自动检测输入类型并验证"""
            user_input = collection_input.text().strip()
            if not user_input:
                update_result_display("请输入合集ID、URL或用户likes链接", "error")
                return

            validate_btn.setText("验证中...")
            validate_btn.setEnabled(False)

            try:
                # 检查API密钥
                if not self.wallpaper_manager.unsplash_access_key:
                    update_result_display(
                        "✗ 验证失败\n\n"
                        "错误: 未设置Unsplash API密钥\n\n"
                        "请在基本设置中输入您的API密钥",
                        "error",
                    )
                    add_btn.setEnabled(False)
                    return

                # 首先检查是否是用户likes链接
                username = self.wallpaper_manager.extract_user_from_likes_url(
                    user_input
                )

                if username:
                    # 处理用户likes
                    input_type = "用户Likes链接"
                    collection_id = f"user_likes_{username}"

                    print(f"检测为用户likes链接，用户名: {username}")

                    # 验证用户likes
                    collection_info = (
                        self.wallpaper_manager.get_user_likes_as_collection_info(
                            username
                        )
                    )

                    if (
                        collection_info
                        and isinstance(collection_info, dict)
                        and "id" in collection_info
                    ):
                        validated_collection["id"] = collection_id
                        validated_collection["info"] = collection_info
                        validated_collection["input_type"] = input_type

                        # 安全地获取各个字段
                        title = collection_info.get("title", "未知标题")
                        total_photos = collection_info.get("total_photos", 0)
                        user = collection_info.get("user", "未知用户")
                        description = collection_info.get("description") or "无描述"

                        # 自动填充名称
                        if not collection_name_input.text().strip():
                            collection_name_input.setText(title)

                        # 安全地截取描述
                        if description and description != "无描述":
                            desc_preview = (
                                description[:150] + "..."
                                if len(description) > 150
                                else description
                            )
                        else:
                            desc_preview = "无描述"

                        success_text = (
                            f"✓ 用户Likes验证成功！\n\n"
                            f"输入类型: {input_type}\n"
                            f"用户名: @{username}\n"
                            f"显示名称: {title}\n"
                            f"Likes数量: {total_photos}\n"
                            f"用户: {user}\n"
                            f"描述: {desc_preview}"
                        )

                        update_result_display(success_text, "success")
                        add_btn.setEnabled(True)

                        print("用户likes验证成功")
                        return
                    else:
                        error_msg = (
                            f"✗ 用户Likes验证失败\n\n"
                            f"用户名: @{username}\n\n"
                            f"可能的原因:\n"
                            f"• 用户不存在\n"
                            f"• 用户没有likes任何照片\n"
                            f"• 网络连接问题"
                        )

                        update_result_display(error_msg, "error")
                        add_btn.setEnabled(False)
                        return

                # 如果不是用户likes链接，按原有逻辑处理合集
                collection_id = None
                input_type = "未知"

                print(f"用户输入: {user_input}")

                # 检查是否是URL
                if "unsplash.com" in user_input.lower() or user_input.startswith(
                    "http"
                ):
                    collection_id = self.extract_collection_id_from_url(user_input)
                    input_type = "URL"
                    print(f"检测为URL，提取的ID: {collection_id}")
                else:
                    # 检查是否是有效的合集ID
                    if self._is_valid_collection_id(user_input):
                        collection_id = user_input
                        input_type = "ID"
                        print(f"检测为合集ID: {collection_id}")
                    else:
                        # 尝试作为URL处理
                        collection_id = self.extract_collection_id_from_url(user_input)
                        if collection_id:
                            input_type = "URL片段"
                            print(f"作为URL片段处理，提取的ID: {collection_id}")

                if not collection_id:
                    update_result_display(
                        "✗ 无法识别输入格式\n\n"
                        f"您输入的内容: {user_input}\n\n"
                        "请确保输入正确的合集ID、URL或用户likes链接格式",
                        "error",
                    )
                    add_btn.setEnabled(False)
                    return

                print(f"开始验证合集ID: {collection_id}")

                # 验证合集
                collection_info = self.wallpaper_manager.get_collection_info(
                    collection_id, cache_if_added=False
                )
                print(f"API返回的合集信息: {collection_info}")

                if (
                    collection_info
                    and isinstance(collection_info, dict)
                    and "id" in collection_info
                ):
                    validated_collection["id"] = collection_id
                    validated_collection["info"] = collection_info
                    validated_collection["input_type"] = input_type

                    # 安全地获取各个字段
                    title = collection_info.get("title", "未知标题")
                    total_photos = collection_info.get("total_photos", 0)
                    user = collection_info.get("user", "未知用户")
                    description = collection_info.get("description") or "无描述"

                    # 自动填充名称
                    if not collection_name_input.text().strip():
                        collection_name_input.setText(title)

                    # 安全地截取描述
                    if description and description != "无描述":
                        desc_preview = (
                            description[:150] + "..."
                            if len(description) > 150
                            else description
                        )
                    else:
                        desc_preview = "无描述"

                    success_text = (
                        f"✓ 合集验证成功！\n\n"
                        f"输入类型: {input_type}\n"
                        f"合集ID: {collection_id}\n"
                        f"标题: {title}\n"
                        f"照片数量: {total_photos}\n"
                        f"作者: {user}\n"
                        f"描述: {desc_preview}"
                    )

                    update_result_display(success_text, "success")
                    add_btn.setEnabled(True)

                    print("界面更新成功")

                else:
                    # 详细的错误信息
                    error_msg = "✗ 合集验证失败\n\n"
                    error_msg += f"输入类型: {input_type}\n"
                    error_msg += f"提取的合集ID: {collection_id}\n\n"

                    if collection_info is None:
                        error_msg += "API返回了空值"
                    elif not isinstance(collection_info, dict):
                        error_msg += f"API返回了意外的数据类型: {type(collection_info)}"
                    elif "id" not in collection_info:
                        error_msg += "API返回的数据中缺少必要字段"
                    else:
                        error_msg += "未知错误"

                    update_result_display(error_msg, "error")
                    add_btn.setEnabled(False)

            except Exception as e:
                import traceback

                error_details = traceback.format_exc()
                print(f"验证过程中发生异常: {error_details}")

                error_text = (
                    f"✗ 验证过程中发生错误\n\n"
                    f"错误类型: {type(e).__name__}\n"
                    f"错误信息: {str(e)}\n"
                    f"输入内容: {user_input}"
                )

                update_result_display(error_text, "error")
                add_btn.setEnabled(False)

            finally:
                validate_btn.setText("验证合集")
                validate_btn.setEnabled(True)

        def add_collection():
            """添加合集到自定义列表 (缓存)"""
            if not validated_collection:
                QMessageBox.warning(dialog, "提示", "请先验证合集")
                return

            name = collection_name_input.text().strip()
            if not name:
                QMessageBox.warning(dialog, "提示", "请输入合集名称")
                return

            name = collection_name_input.text().strip()
            if not name:
                QMessageBox.warning(dialog, "提示", "请输入合集名称")
                return

            collection_id = validated_collection["id"]

            # 检查是否已存在
            existing_collections = self.settings.get_custom_collections()
            if name in existing_collections:
                reply = QMessageBox.question(
                    dialog,
                    "合集已存在",
                    f"合集名称 '{name}' 已存在，是否覆盖？\n\n"
                    f"现有ID: {existing_collections[name]}\n"
                    f"新的ID: {collection_id}",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return

            try:
                # 添加到设置
                self.settings.add_custom_collection(name, collection_id)

                # 现在缓存合集信息（因为已经添加了）
                self.wallpaper_manager.get_collection_info(
                    collection_id, cache_if_added=True
                )

                # 重新加载合集列表
                self.load_popular_collections()

                # 选择新添加的合集
                for i in range(self.collection_combo.count()):
                    if self.collection_combo.itemData(i) == collection_id:
                        self.collection_combo.setCurrentIndex(i)
                        break

                QMessageBox.information(
                    dialog,
                    "添加成功",
                    f"自定义合集 '{name}' 已添加成功！\n\n"
                    f"合集ID: {collection_id}\n"
                    f"照片数量: {validated_collection['info'].get('total_photos', 0)}\n\n"
                    f"合集信息已缓存，后续使用不会消耗额外API请求。",
                )
                dialog.accept()

            except Exception as e:
                QMessageBox.critical(
                    dialog, "添加失败", f"添加合集时发生错误:\n{str(e)}"
                )

        # ========== 连接事件 ==========

        # 连接事件
        validate_btn.clicked.connect(auto_detect_and_validate)
        add_btn.clicked.connect(add_collection)
        cancel_btn.clicked.connect(dialog.reject)

        # 输入框变化时重置验证状态
        collection_input.textChanged.connect(reset_validation)

        # 回车键快捷验证
        collection_input.returnPressed.connect(auto_detect_and_validate)

        # 显示对话框
        dialog.exec_()

    def manage_custom_collections_dialog(self):
        """管理自定义合集对话框"""
        print("manage_custom_collections_dialog 被调用")  # 调试信息

        from PyQt5.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QPushButton,
            QListWidget,
            QListWidgetItem,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("管理自定义合集")
        dialog.setMinimumSize(400, 300)

        layout = QVBoxLayout(dialog)

        # 说明标签
        info_label = QLabel("管理您添加的自定义合集:")
        layout.addWidget(info_label)

        # 合集列表
        collections_list = QListWidget()
        layout.addWidget(collections_list)

        # 按钮
        button_layout = QHBoxLayout()
        delete_btn = QPushButton("删除选中")
        delete_btn.setEnabled(False)
        close_btn = QPushButton("关闭")

        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        # 定义内部函数
        def load_custom_collections():
            collections_list.clear()
            custom_collections = self.settings.get_custom_collections()

            if not custom_collections:
                item = QListWidgetItem("暂无自定义合集")
                item.setData(Qt.UserRole, None)
                collections_list.addItem(item)
            else:
                for name, collection_id in custom_collections.items():
                    item_text = f"{name} (ID: {collection_id})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, name)
                    collections_list.addItem(item)

        def on_selection_changed():
            current_item = collections_list.currentItem()
            has_valid_selection = (
                current_item is not None and current_item.data(Qt.UserRole) is not None
            )
            delete_btn.setEnabled(has_valid_selection)

        def delete_collection():
            current_item = collections_list.currentItem()
            if current_item and current_item.data(Qt.UserRole):
                collection_name = current_item.data(Qt.UserRole)

                reply = QMessageBox.question(
                    dialog,
                    "确认删除",
                    f"确定要删除自定义合集 '{collection_name}' 吗？",
                    f"注意：这也会清除该合集的缓存数据。",
                    QMessageBox.Yes | QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    # 获取合集ID用于清除缓存
                    custom_collections = self.settings.get_custom_collections()
                    collection_id = custom_collections.get(collection_name)

                    # 从设置中删除
                    self.settings.remove_custom_collection(collection_name)

                    # 清除缓存
                    if collection_id:
                        self.wallpaper_manager.remove_collection_cache(collection_id)

                    # 重新加载列表
                    load_custom_collections()

                    # 重新加载主界面的合集列表
                    self.load_popular_collections()

                    QMessageBox.information(
                        dialog,
                        "删除成功",
                        f"自定义合集 '{collection_name}' 及其缓存已删除",
                    )

        def on_double_click(item):
            if item and item.data(Qt.UserRole):
                delete_collection()

        # 连接事件
        collections_list.itemSelectionChanged.connect(on_selection_changed)
        delete_btn.clicked.connect(delete_collection)
        close_btn.clicked.connect(dialog.accept)
        collections_list.itemDoubleClicked.connect(on_double_click)

        # 加载数据
        load_custom_collections()

        # 显示对话框
        dialog.exec_()

    def extract_collection_id_from_url(self, url):
        """从URL中提取合集ID"""
        import re

        print(f"正在提取URL中的合集ID: {url}")  # 调试信息

        try:
            # 清理URL，移除多余的空格和换行
            url = url.strip()

            # 更新的正则表达式模式，支持字母数字混合ID
            patterns = [
                # 新格式：字母数字混合ID（11位左右）
                r"unsplash\.com/collections/([a-zA-Z0-9_-]+)",  # 标准Unsplash URL
                r"unsplash\.com/@[^/]+/collections/([a-zA-Z0-9_-]+)",  # 用户合集URL
                r"/collections/([a-zA-Z0-9_-]+)",  # 路径中的合集
                r"collections/([a-zA-Z0-9_-]+)",  # 简单的合集路径
                # 旧格式：纯数字ID（向后兼容）
                r"unsplash\.com/collections/(\d+)",  # 旧的数字ID格式
                r"unsplash\.com/@[^/]+/collections/(\d+)",  # 旧的用户合集
                r"/collections/(\d+)",  # 旧的路径格式
                r"collections/(\d+)",  # 旧的简单路径
                r"collection/(\d+)",  # 单数形式（不太常见）
            ]

            for i, pattern in enumerate(patterns):
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    collection_id = match.group(1)
                    print(f"使用模式 {i+1} 提取到合集ID: {collection_id}")

                    # 验证提取的ID格式是否合理
                    if self._is_valid_collection_id(collection_id):
                        return collection_id
                    else:
                        print(f"提取的ID格式不合理: {collection_id}")
                        continue

            # 如果输入的就是一个ID（数字或字母数字混合）
            if self._is_valid_collection_id(url):
                print(f"输入的就是合集ID: {url}")
                return url

            print("无法从URL中提取合集ID")
            return None

        except Exception as e:
            print(f"提取合集ID失败: {e}")
            return None

    def _is_valid_collection_id(self, collection_id):
        """验证合集ID格式是否有效"""
        import re

        if not collection_id:
            return False

        # 新格式：字母数字混合，通常11位左右
        if re.match(r"^[a-zA-Z0-9_-]{8,15}$", collection_id):
            return True

        # 旧格式：纯数字，通常6-8位
        if re.match(r"^\d{4,10}$", collection_id):
            return True

        return False

    def on_collection_changed(self, collection_name):
        """合集选择改变"""
        if (
            collection_name == "请选择合集..."
            or collection_name == "--- 自定义合集 ---"
        ):
            self.settings.set_setting("selected_collection", "")
            self.collection_info_label.setText("请选择一个合集")
            return

        # 获取选中的合集ID
        current_index = self.collection_combo.currentIndex()
        collection_id = self.collection_combo.itemData(current_index)

        # 如果是分隔符，跳过
        if collection_id == "separator":
            self.settings.set_setting("selected_collection", "")
            self.collection_info_label.setText("请选择一个合集")
            return

        if collection_id:
            self.settings.set_setting("selected_collection", collection_id)
            self.collection_info_label.setText(f"当前选择: {collection_name}")

            # 加载合集预览
            self.load_collection_preview(collection_id)

            print(f"选择合集: {collection_name} (ID: {collection_id})")
        else:
            self.settings.set_setting("selected_collection", "")

    def get_collection_name_by_id(self, collection_id):
        """根据ID获取合集名称"""
        for i in range(self.collection_combo.count()):
            if self.collection_combo.itemData(i) == collection_id:
                return self.collection_combo.itemText(i)
        return "未知合集"

    def load_collection_preview(self, collection_id):
        """加载合集预览信息"""
        try:
            # 获取合集信息（如果是已添加的合集会使用缓存）
            is_custom_collection = collection_id in [
                self.collection_combo.itemData(i)
                for i in range(self.collection_combo.count())
            ]
            collection_info = self.wallpaper_manager.get_collection_info(
                collection_id, cache_if_added=is_custom_collection
            )

            if collection_info:
                # 格式化描述
                description = collection_info.get("description", "")
                if description and description.strip():
                    # 限制描述长度，避免显示区域过大
                    if len(description) > 80:
                        desc_text = description[:80] + "..."
                    else:
                        desc_text = description
                else:
                    desc_text = "暂无描述"

                # 更简洁美观的预览文本
                title = collection_info.get("title", "未知标题")
                user = collection_info.get("user", "未知用户")
                total_photos = collection_info.get("total_photos", 0)

                # 使用HTML格式化文本
                preview_html = f"""
                <div style="font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;">
                    <p style="margin: 0 0 12px 0; font-size: 14px; font-weight: bold; color: #2c3e50;">
                        📁 {title}
                    </p>
                    
                    <p style="margin: 0 0 8px 0; font-size: 12px; color: #34495e;">
                        <span style="color: #7f8c8d;">👤 作者：</span>{user}
                    </p>
                    
                    <p style="margin: 0 0 8px 0; font-size: 12px; color: #34495e;">
                        <span style="color: #7f8c8d;">📸 照片：</span>{total_photos} 张
                    </p>
                    
                    <p style="margin: 0 0 8px 0; font-size: 12px; color: #34495e;">
                        <span style="color: #7f8c8d;">🆔 ID：</span>{collection_id}
                    </p>
                    
                    <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #ecf0f1;">
                        <p style="margin: 0; font-size: 11px; color: #7f8c8d; line-height: 1.4;">
                            📝 {desc_text}
                        </p>
                    </div>
                </div>
                """

                self.collection_preview_label.setText(preview_html)

                # 设置样式，让显示更美观
                self.collection_preview_label.setStyleSheet(
                    "QLabel {"
                    "   border: 1px solid #bdc3c7;"
                    "   background-color: #ffffff;"
                    "   padding: 16px;"
                    "   border-radius: 8px;"
                    "   font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;"
                    "}"
                )

                # 设置文本格式为富文本
                self.collection_preview_label.setTextFormat(Qt.RichText)
                self.collection_preview_label.setWordWrap(True)

                print(f"已加载合集预览: {title}")

            else:
                # 如果获取信息失败，显示基本信息
                loading_html = f"""
                <div style="font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif; text-align: center;">
                    <p style="margin: 0 0 12px 0; font-size: 13px; color: #f39c12;">
                        🔄 正在加载合集信息...
                    </p>
                    <p style="margin: 0 0 8px 0; font-size: 12px; color: #95a5a6;">
                        合集ID: {collection_id}
                    </p>
                    <p style="margin: 0; font-size: 11px; color: #95a5a6;">
                        💡 点击"立即更换壁纸"预览效果
                    </p>
                </div>
                """

                self.collection_preview_label.setText(loading_html)
                self.collection_preview_label.setTextFormat(Qt.RichText)

                self.collection_preview_label.setStyleSheet(
                    "QLabel {"
                    "   border: 1px solid #f39c12;"
                    "   background-color: #fef9e7;"
                    "   padding: 16px;"
                    "   border-radius: 8px;"
                    "   font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;"
                    "}"
                )

        except Exception as e:
            print(f"加载合集预览失败: {e}")

            # 显示错误信息
            error_html = f"""
            <div style="font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif; text-align: center;">
                <p style="margin: 0 0 12px 0; font-size: 13px; color: #e74c3c;">
                    ❌ 预览加载失败
                </p>
                <p style="margin: 0 0 8px 0; font-size: 12px; color: #c0392b;">
                    合集ID: {collection_id}
                </p>
                <p style="margin: 0; font-size: 11px; color: #c0392b;">
                    🔄 请检查网络连接或稍后重试
                </p>
            </div>
            """

            self.collection_preview_label.setText(error_html)
            self.collection_preview_label.setTextFormat(Qt.RichText)

            self.collection_preview_label.setStyleSheet(
                "QLabel {"
                "   border: 1px solid #e74c3c;"
                "   background-color: #fdf2f2;"
                "   padding: 16px;"
                "   border-radius: 8px;"
                "   font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;"
                "}"
            )

    def browse_save_path(self):
        """浏览壁纸保存路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择壁纸保存位置", self.settings.get_setting("save_path", "")
        )

        if path:
            self.settings.set_setting("save_path", path)
            self.save_path_edit.setText(path)

    def browse_favorite_path(self):
        """浏览收藏壁纸路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择收藏壁纸位置", self.settings.get_setting("favorite_path", "")
        )

        if path:
            self.settings.set_setting("favorite_path", path)
            self.fav_path_edit.setText(path)

    def save_api_key(self):
        """保存API密钥"""
        api_key = self.api_key_edit.text().strip()
        self.settings.set_setting("unsplash_access_key", api_key)
        self.wallpaper_manager.unsplash_access_key = api_key
        print(f"API密钥已更新")

    def save_current_wallpaper(self):
        """保存当前壁纸"""
        try:
            current_wallpaper = getattr(self.wallpaper_manager, "current_wallpaper", "")
            if current_wallpaper and os.path.exists(current_wallpaper):
                import shutil

                favorite_path = self.settings.get_setting("favorite_path", "")

                if not favorite_path:
                    # 如果没有设置收藏路径，使用默认路径
                    favorite_path = os.path.join(
                        os.path.expanduser("~"), "Pictures", "Wallpapers"
                    )

                if not os.path.exists(favorite_path):
                    os.makedirs(favorite_path, exist_ok=True)

                filename = os.path.basename(current_wallpaper)
                dest_path = os.path.join(favorite_path, filename)
                shutil.copy2(current_wallpaper, dest_path)

                QMessageBox.information(
                    self, "保存成功", f"壁纸已成功保存到:\n{dest_path}"
                )
            else:
                QMessageBox.warning(self, "保存失败", "当前没有可保存的壁纸。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存当前壁纸: {str(e)}")

    def on_wallpaper_changed(self, image_path):
        """壁纸更换事件"""
        if os.path.exists(image_path):
            try:
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # 计算合适的预览尺寸
                    label_size = self.preview_label.size()
                    if label_size.width() > 0 and label_size.height() > 0:
                        scaled_pixmap = pixmap.scaled(
                            label_size.width() - 10,
                            label_size.height() - 10,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation,
                        )
                        self.preview_label.setPixmap(scaled_pixmap)
                    else:
                        # 如果label尺寸还没有确定，使用固定尺寸
                        scaled_pixmap = pixmap.scaled(
                            300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                        self.preview_label.setPixmap(scaled_pixmap)
                else:
                    self.preview_label.setText("无法加载壁纸预览")
            except Exception as e:
                print(f"更新壁纸预览时出错: {e}")
                self.preview_label.setText("预览加载失败")
        else:
            self.preview_label.setText("壁纸文件不存在")

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 窗口大小改变时更新预览
        if (
            hasattr(self.wallpaper_manager, "current_wallpaper")
            and self.wallpaper_manager.current_wallpaper
        ):
            self.on_wallpaper_changed(self.wallpaper_manager.current_wallpaper)

    def add_user_likes_dialog(self):
        """添加用户likes对话框"""
        QMessageBox.information(
            self,
            "添加用户Likes",
            '请使用"添加自定义合集"功能，\n'
            "输入用户likes页面链接：\n"
            "https://unsplash.com/@username/likes\n\n"
            "系统会自动识别并添加为合集。",
        )

    def manage_user_likes_dialog(self):
        """管理用户likes对话框"""
        QMessageBox.information(
            self,
            "管理用户Likes",
            "用户likes已整合到自定义合集中，\n"
            '请使用"管理自定义合集"功能进行管理。\n\n'
            "用户likes合集的ID格式为：user_likes_用户名",
        )
