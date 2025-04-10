import os
import ctypes
import requests
import platform
import json
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
import time
import random
from datetime import datetime

class WallpaperManager(QObject):
    wallpaper_changed = pyqtSignal(str)
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.timer = QTimer()
        self.timer.timeout.connect(self.change_wallpaper)
        self.current_wallpaper = ""
        
        # 从设置中读取API密钥，而不是硬编码
        self.unsplash_access_key = self.settings.get_setting("unsplash_access_key", "")
        self.unsplash_secret_key = self.settings.get_setting("unsplash_secret_key", "")
        
        # 如果密钥为空，可以提示用户设置
        if not self.unsplash_access_key:
            print("未设置Unsplash API密钥，将使用备用图片源")
        
    def start_timer(self):
        # 根据设置的频率设置定时器
        frequency = self.settings.get_setting("frequency")
        interval_ms = self._convert_frequency_to_ms(frequency)
        self.timer.start(interval_ms)
        
    def stop_timer(self):
        self.timer.stop()
        
    def _convert_frequency_to_ms(self, frequency):
        # 将频率转换为毫秒
        if frequency == "1小时":
            return 60 * 60 * 1000
        elif frequency == "2小时":
            return 2 * 60 * 60 * 1000
        elif frequency == "4小时":
            return 4 * 60 * 60 * 1000
        elif frequency == "1天":
            return 24 * 60 * 60 * 1000
        else:  # 默认1小时
            return 60 * 60 * 1000
    
    def get_screen_resolution(self):
        # 获取屏幕分辨率
        if platform.system() == "Windows":
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            return width, height
        else:
            # 默认分辨率，实际应用中可能需要其他方法获取
            return 1920, 1080
    
    def download_wallpaper(self):
        width, height = self.get_screen_resolution()
        save_path = self.settings.get_setting("save_path")
        
        # 确保保存目录存在
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        try:
            print("开始下载壁纸...")
            
            # 检查是否有API密钥
            if self.unsplash_access_key:
                # 使用Unsplash API获取随机图片
                api_url = "https://api.unsplash.com/photos/random"
                params = {
                    "orientation": "landscape",
                    "query": "nature,landscape",
                }
                headers = {
                    "Authorization": f"Client-ID {self.unsplash_access_key}",
                    "Accept-Version": "v1"
                }
                
                print(f"请求Unsplash API: {api_url}")
                response = requests.get(api_url, params=params, headers=headers)
                print(f"API响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    # 修改这里：始终使用raw格式获取最高分辨率图片
                    image_url = data["urls"]["raw"] + f"&w={width}&h={height}&fit=crop&q=100"
                    
                    # 获取图片作者信息
                    author = data["user"]["name"]
                    author_link = data["user"]["links"]["html"]
                    print(f"图片作者: {author} ({author_link})")
                    
                    # 下载图片
                    print(f"下载图片: {image_url}")
                    image_response = requests.get(image_url)
                    
                    if image_response.status_code == 200:
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        filename = f"wallpaper_{timestamp}.jpg"
                        file_path = os.path.join(save_path, filename)
                        
                        print(f"保存壁纸到: {file_path}")
                        
                        with open(file_path, "wb") as f:
                            f.write(image_response.content)
                        
                        # 保存图片元数据
                        metadata = {
                            "id": data["id"],
                            "author": author,
                            "author_link": author_link,
                            "download_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "unsplash_link": data["links"]["html"]
                        }
                        
                        metadata_path = os.path.join(save_path, f"wallpaper_{timestamp}.json")
                        with open(metadata_path, "w", encoding="utf-8") as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)
                        
                        # 验证文件是否成功保存
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            print("壁纸下载成功")
                            return file_path
                        else:
                            print("壁纸文件保存失败或文件大小为0")
                            return None
                    else:
                        print(f"下载图片失败，HTTP状态码: {image_response.status_code}")
                        return None
                else:
                    print(f"API请求失败，HTTP状态码: {response.status_code}")
                    if response.status_code == 403:
                        print("可能是API密钥无效或已达到请求限制")
                    elif response.status_code == 429:
                        print("已达到API请求限制")
            
            # 尝试备用方法
            print("尝试使用备用方法...")
            random_url = "https://picsum.photos/{}/{}".format(width, height)
            print(f"请求URL: {random_url}")
            image_response = requests.get(random_url)
            
            if image_response.status_code == 200:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"wallpaper_{timestamp}.jpg"
                file_path = os.path.join(save_path, filename)
                
                with open(file_path, "wb") as f:
                    f.write(image_response.content)
                
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    print("使用备用方法下载壁纸成功")
                    return file_path
            
            return None
                
        except Exception as e:
            print(f"下载壁纸时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def set_wallpaper(self, image_path):
        # 设置壁纸
        if platform.system() == "Windows":
            # 修改这里：使用更多参数控制壁纸显示方式
            try:
                # 设置壁纸显示方式为"适应"(FIT)
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Control Panel\\Desktop", 0, winreg.KEY_SET_VALUE)
                # 0=居中，1=平铺，2=拉伸，6=适应，10=填充
                winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "6")
                winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
                winreg.CloseKey(key)
                
                # 设置壁纸
                ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
                self.current_wallpaper = image_path
                self.wallpaper_changed.emit(image_path)
                return True
            except Exception as e:
                print(f"设置壁纸显示方式时出错: {e}")
                # 如果设置显示方式失败，仍然尝试设置壁纸
                ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
                self.current_wallpaper = image_path
                self.wallpaper_changed.emit(image_path)
                return True
        else:
            # 其他操作系统的壁纸设置方法
            return False
    
    def change_wallpaper(self):
        # 下载并设置新壁纸
        wallpaper_path = self.download_wallpaper()
        if wallpaper_path:
            self.set_wallpaper(wallpaper_path)
    
    def save_current_wallpaper(self, custom_path=None):
        # 保存当前壁纸到指定位置
        if not self.current_wallpaper or not os.path.exists(self.current_wallpaper):
            return False
        
        if custom_path:
            save_dir = custom_path
        else:
            save_dir = self.settings.get_setting("favorite_path")
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        filename = os.path.basename(self.current_wallpaper)
        new_path = os.path.join(save_dir, f"favorite_{filename}")
        
        try:
            import shutil
            shutil.copy2(self.current_wallpaper, new_path)
            return True
        except Exception as e:
            print(f"保存壁纸时出错: {e}")
            return False