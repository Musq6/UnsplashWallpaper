import os
import json

class Settings:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_settings = {
            "frequency": "1小时",  # 壁纸更换频率
            "save_path": os.path.join(os.path.expanduser("~"), "Pictures", "Wallpapers"),  # 壁纸保存路径
            "favorite_path": os.path.join(os.path.expanduser("~"), "Pictures", "Favorite Wallpapers"),  # 收藏壁纸路径
            "auto_start": False  # 开机自启动
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        # 加载设置，如果文件不存在则创建默认设置
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return self.default_settings
        else:
            self.save_settings(self.default_settings)
            return self.default_settings
    
    def save_settings(self, settings=None):
        # 保存设置
        if settings is None:
            settings = self.settings
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    
    def get_setting(self, key, default=None):
        """获取设置值，如果不存在则返回默认值"""
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        # 设置值
        self.settings[key] = value
        self.save_settings()
    
    def reset_to_default(self):
        # 重置为默认设置
        self.settings = self.default_settings.copy()
        self.save_settings()