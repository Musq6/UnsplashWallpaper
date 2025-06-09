import os
import json

class Settings:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_settings = {
            "frequency": "1小时",  # 壁纸更换频率
            "save_path": os.path.join(os.path.expanduser("~"), "Pictures", "Wallpapers"),  # 壁纸保存路径
            "favorite_path": os.path.join(os.path.expanduser("~"), "Pictures", "Favorite Wallpapers"),  # 收藏壁纸路径
            "auto_start": False,  # 开机自启动
            "unsplash_access_key": "",  # Unsplash API密钥
            "unsplash_secret_key": "",  # Unsplash Secret密钥（可选）
            "keywords": "",  # 搜索关键词
            "quality": "high",  # 图片质量 (small, medium, high, full)
            "use_collection": False,  # 是否使用合集模式
            "selected_collection": "",  # 选中的合集ID
            "collection_mode": "popular",  # 合集模式 (popular 或 search)
            "last_collection_search": "",  # 上次搜索的合集关键词
            "custom_collections": {}  # 用户自定义添加的合集 {name: id}
        }
        self.settings = self.load_settings()
        
        # 确保所有默认设置都存在（用于版本升级兼容性）
        self._ensure_all_settings()
    
    def _ensure_all_settings(self):
        """确保所有默认设置都存在，用于版本升级时的兼容性"""
        updated = False
        for key, value in self.default_settings.items():
            if key not in self.settings:
                self.settings[key] = value
                updated = True
                print(f"添加新设置: {key} = {value}")
        
        if updated:
            self.save_settings()
    
    def load_settings(self):
        """加载设置，如果文件不存在则创建默认设置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)
                    print(f"成功加载配置文件: {self.config_file}")
                    return loaded_settings
            except json.JSONDecodeError as e:
                print(f"配置文件格式错误: {e}")
                print("使用默认设置")
                return self.default_settings.copy()
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self.default_settings.copy()
        else:
            print("配置文件不存在，创建默认配置")
            default_copy = self.default_settings.copy()
            self.save_settings(default_copy)
            return default_copy
    
    def save_settings(self, settings=None):
        """保存设置"""
        if settings is None:
            settings = self.settings
        
        try:
            # 确保目录存在
            config_dir = os.path.dirname(os.path.abspath(self.config_file))
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            print(f"设置已保存到: {self.config_file}")
            
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def get_setting(self, key, default=None):
        """获取设置值，如果不存在则返回默认值"""
        if key in self.settings:
            return self.settings[key]
        elif key in self.default_settings:
            # 如果设置中没有但默认设置中有，添加到设置中
            self.settings[key] = self.default_settings[key]
            self.save_settings()
            return self.default_settings[key]
        else:
            return default
    
    def set_setting(self, key, value):
        """设置值"""
        self.settings[key] = value
        self.save_settings()
        print(f"设置已更新: {key} = {value}")
    
    def reset_to_default(self):
        """重置为默认设置"""
        self.settings = self.default_settings.copy()
        self.save_settings()
        print("设置已重置为默认值")
    
    def add_custom_collection(self, name, collection_id):
        """添加自定义合集"""
        custom_collections = self.get_setting("custom_collections", {})
        custom_collections[name] = collection_id
        self.set_setting("custom_collections", custom_collections)
        print(f"添加自定义合集: {name} (ID: {collection_id})")
    
    def remove_custom_collection(self, name):
        """移除自定义合集"""
        custom_collections = self.get_setting("custom_collections", {})
        if name in custom_collections:
            del custom_collections[name]
            self.set_setting("custom_collections", custom_collections)
            print(f"移除自定义合集: {name}")
            return True
        return False
    
    def get_custom_collections(self):
        """获取自定义合集列表"""
        return self.get_setting("custom_collections", {})
    
    def export_settings(self, export_path):
        """导出设置到指定路径"""
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            print(f"设置已导出到: {export_path}")
            return True
        except Exception as e:
            print(f"导出设置失败: {e}")
            return False
    
    def import_settings(self, import_path):
        """从指定路径导入设置"""
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                imported_settings = json.load(f)
            
            # 验证导入的设置
            for key in imported_settings:
                if key in self.default_settings:
                    self.settings[key] = imported_settings[key]
            
            self.save_settings()
            print(f"设置已从 {import_path} 导入")
            return True
        except Exception as e:
            print(f"导入设置失败: {e}")
            return False
    
    def get_all_settings(self):
        """获取所有设置"""
        return self.settings.copy()
    
    def print_current_settings(self):
        """打印当前所有设置（用于调试）"""
        print("当前设置:")
        for key, value in self.settings.items():
            if "key" in key.lower() and value:  # 隐藏API密钥的值
                print(f"  {key}: {'*' * len(str(value))}")
            else:
                print(f"  {key}: {value}")