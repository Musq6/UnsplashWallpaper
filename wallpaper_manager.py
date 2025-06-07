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
        
        self.unsplash_access_key = self.settings.get_setting("unsplash_access_key", "")
        self.unsplash_secret_key = self.settings.get_setting("unsplash_secret_key", "")
        
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
        """获取优化后的屏幕分辨率，考虑像素密度和特殊比例"""
        if platform.system() == "Windows":
            user32 = ctypes.windll.user32
            # 获取基础分辨率
            base_width = user32.GetSystemMetrics(0)
            base_height = user32.GetSystemMetrics(1)
            
            # 获取像素密度(DPI)
            hdc = user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            user32.ReleaseDC(0, hdc)
            density = max(1, dpi / 96)  # 标准DPI是96
            
            # 计算高分辨率
            width = int(base_width * density)
            height = int(base_height * density)
            
            # 处理特殊屏幕比例
            ratio = base_width / base_height
            if ratio >= 2:  # 超宽屏
                width = int(height * 2)
            elif ratio <= 0.5:  # 超窄屏
                height = int(width * 2)
                
            return {
                'full': (width, height),
                'medium': (width//2, height//2),
                'small': (width//4, height//4),
                'base': (base_width, base_height)
            }
        else:
            return {
                'full': (3840, 2160),
                'medium': (1920, 1080),
                'small': (960, 540),
                'base': (1920, 1080)
            }
    
    def download_wallpaper(self):
        resolutions = self.get_screen_resolution()
        save_path = self.settings.get_setting("save_path")
        # 根据设置选择分辨率，默认使用full
        size_setting = self.settings.get_setting("wallpaper_size", "full")
        width, height = resolutions.get(size_setting, resolutions['full'])
        
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
                    # 生成三种尺寸的URL
                    full_url = data["urls"]["raw"] + f"&w={resolutions['full'][0]}&h={resolutions['full'][1]}&fit=crop&q=100"
                    medium_url = data["urls"]["raw"] + f"&w={resolutions['medium'][0]}&h={resolutions['medium'][1]}&fit=crop&q=85" 
                    small_url = data["urls"]["raw"] + f"&w={resolutions['small'][0]}&h={resolutions['small'][1]}&fit=crop&q=75"
                    
                    # 根据设置选择要下载的尺寸
                    if size_setting == "full":
                        image_url = full_url
                    elif size_setting == "medium":
                        image_url = medium_url
                    else:
                        image_url = small_url
                    
                    print(f"使用{size_setting}尺寸: {image_url}")
                    
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
        """设置壁纸，根据屏幕比例自动选择最佳显示模式"""
        if platform.system() == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Control Panel\\Desktop", 0, winreg.KEY_SET_VALUE)
                
                # 获取屏幕比例
                resolutions = self.get_screen_resolution()
                base_width, base_height = resolutions['base']
                ratio = base_width / base_height
                
                # 根据比例选择最佳显示模式
                if ratio >= 2:  # 超宽屏
                    style = "10"  # 填充
                    print("检测到超宽屏，使用填充模式")
                elif ratio <= 0.5:  # 超窄屏
                    style = "6"  # 适应
                    print("检测到超窄屏，使用适应模式")
                else:  # 正常比例
                    size_setting = self.settings.get_setting("wallpaper_size", "full")
                    if size_setting == "full":
                        style = "10"  # 填充
                    else:
                        style = "6"  # 适应
                    print(f"使用{size_setting}尺寸，显示模式: {'填充' if style == '10' else '适应'}")
                
                # 设置显示模式
                winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, style)
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
        """下载并设置新壁纸，带重试机制"""
        max_retries = self.settings.get_setting("max_retries", 3)
        retry_delay = self.settings.get_setting("retry_delay", 5)  # 秒
        
        for attempt in range(1, max_retries + 1):
            print(f"尝试下载壁纸 (第{attempt}次，共{max_retries}次)...")
            wallpaper_path = self.download_wallpaper()
            
            if wallpaper_path:
                if self.set_wallpaper(wallpaper_path):
                    print("壁纸设置成功")
                    return
                else:
                    print("壁纸设置失败")
            else:
                print("壁纸下载失败")
            
            if attempt < max_retries:
                print(f"{retry_delay}秒后重试...")
                time.sleep(retry_delay)
        
        print(f"达到最大重试次数({max_retries})，放弃本次更换壁纸")
    
    def get_current_wallpaper_info(self):
        """获取当前壁纸的元数据信息"""
        if not self.current_wallpaper or not os.path.exists(self.current_wallpaper):
            return None
        
        try:
            # 查找对应的元数据文件
            base_filename = os.path.basename(self.current_wallpaper)
            filename, _ = os.path.splitext(base_filename)
            metadata_path = os.path.join(
                os.path.dirname(self.current_wallpaper),
                f"{filename}.json"
            )
            
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    return {
                        'image_path': self.current_wallpaper,
                        'author': metadata.get('author', '未知作者'),
                        'author_link': metadata.get('author_link', ''),
                        'source_link': metadata.get('unsplash_link', ''),
                        'download_date': metadata.get('download_date', '未知日期')
                    }
            else:
                return {
                    'image_path': self.current_wallpaper,
                    'author': '未知作者',
                    'author_link': '',
                    'source_link': '',
                    'download_date': '未知日期'
                }
        except Exception as e:
            print(f"获取壁纸元数据时出错: {e}")
            return None

    def cleanup_old_wallpapers(self):
        """清理过期的壁纸文件"""
        save_path = self.settings.get_setting("save_path")
        days_to_keep = self.settings.get_setting("days_to_keep", 30)
        
        if not os.path.exists(save_path):
            print(f"壁纸保存路径不存在: {save_path}")
            return
        
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        
        try:
            print(f"开始清理超过{days_to_keep}天的旧壁纸...")
            
            for filename in os.listdir(save_path):
                file_path = os.path.join(save_path, filename)
                
                # 只处理壁纸图片文件
                if filename.startswith("wallpaper_") and filename.endswith((".jpg", ".png")):
                    # 获取文件修改时间
                    file_time = os.path.getmtime(file_path)
                    
                    if file_time < cutoff_time:
                        print(f"删除过期壁纸: {filename}")
                        os.remove(file_path)
                        deleted_count += 1
                        
                        # 尝试删除对应的元数据文件
                        base_name = os.path.splitext(filename)[0]
                        metadata_path = os.path.join(save_path, f"{base_name}.json")
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                            print(f"删除对应的元数据文件: {os.path.basename(metadata_path)}")
            
            print(f"清理完成，共删除{deleted_count}个过期壁纸文件")
            return deleted_count
            
        except Exception as e:
            print(f"清理旧壁纸时出错: {e}")
            import traceback
            traceback.print_exc()
            return -1

    def get_favorite_wallpapers(self):
        """获取收藏夹中的所有壁纸信息"""
        favorite_path = self.settings.get_setting("favorite_path")
        if not os.path.exists(favorite_path):
            print(f"收藏夹路径不存在: {favorite_path}")
            return []
        
        wallpapers = []
        
        try:
            print(f"扫描收藏夹路径: {favorite_path}")
            
            for filename in os.listdir(favorite_path):
                if filename.startswith("favorite_") and filename.endswith((".jpg", ".png")):
                    file_path = os.path.join(favorite_path, filename)
                    
                    # 获取基础文件名
                    base_name = os.path.splitext(filename)[0]
                    metadata_path = os.path.join(favorite_path, f"{base_name}.json")
                    
                    if os.path.exists(metadata_path):
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                            wallpapers.append({
                                'image_path': file_path,
                                'author': metadata.get('author', '未知作者'),
                                'author_link': metadata.get('author_link', ''),
                                'source_link': metadata.get('unsplash_link', ''),
                                'download_date': metadata.get('download_date', '未知日期')
                            })
                    else:
                        wallpapers.append({
                            'image_path': file_path,
                            'author': '未知作者',
                            'author_link': '',
                            'source_link': '',
                            'download_date': '未知日期'
                        })
            
            print(f"找到{len(wallpapers)}张收藏的壁纸")
            return wallpapers
            
        except Exception as e:
            print(f"获取收藏壁纸时出错: {e}")
            import traceback
            traceback.print_exc()
            return []

    def set_random_favorite_wallpaper(self):
        """从收藏夹中随机选择一张壁纸并设置为当前壁纸"""
        favorites = self.get_favorite_wallpapers()
        if not favorites:
            print("收藏夹中没有壁纸")
            return None
        
        try:
            # 随机选择一张壁纸
            selected = random.choice(favorites)
            print(f"从收藏夹中选择壁纸: {selected['image_path']}")
            
            # 设置壁纸
            if self.set_wallpaper(selected['image_path']):
                print("成功设置收藏夹壁纸")
                return selected
            else:
                print("设置收藏夹壁纸失败")
                return None
                
        except Exception as e:
            print(f"设置收藏夹壁纸时出错: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_thumbnail(self, size="small"):
        """获取当前壁纸的缩略图路径，如果不存在则生成"""
        if not self.current_wallpaper or not os.path.exists(self.current_wallpaper):
            print("当前没有有效的壁纸")
            return None
            
        try:
            from PIL import Image
            import io
            
            # 定义缩略图尺寸
            sizes = {
                "small": (320, 180),
                "medium": (640, 360),
                "large": (1280, 720)
            }
            
            if size not in sizes:
                size = "small"
                
            width, height = sizes[size]
            
            # 构建缩略图路径
            base_name = os.path.basename(self.current_wallpaper)
            filename, ext = os.path.splitext(base_name)
            thumbnail_dir = os.path.join(
                os.path.dirname(self.current_wallpaper),
                "thumbnails"
            )
            thumbnail_path = os.path.join(
                thumbnail_dir,
                f"{filename}_{size}{ext}"
            )
            
            # 如果缩略图已存在且未过期，直接返回
            if os.path.exists(thumbnail_path):
                wallpaper_mtime = os.path.getmtime(self.current_wallpaper)
                thumbnail_mtime = os.path.getmtime(thumbnail_path)
                
                if thumbnail_mtime > wallpaper_mtime:
                    print(f"使用现有的{size}尺寸缩略图: {thumbnail_path}")
                    return thumbnail_path
            
            # 创建缩略图目录
            if not os.path.exists(thumbnail_dir):
                os.makedirs(thumbnail_dir)
                print(f"创建缩略图目录: {thumbnail_dir}")
            
            # 生成缩略图
            print(f"生成{size}尺寸缩略图: {thumbnail_path}")
            with Image.open(self.current_wallpaper) as img:
                img.thumbnail((width, height))
                img.save(thumbnail_path)
                
            return thumbnail_path
            
        except ImportError:
            print("Pillow库未安装，无法生成缩略图")
            return None
        except Exception as e:
            print(f"生成缩略图时出错: {e}")
            import traceback
            traceback.print_exc()
            return None

    def save_current_wallpaper(self, custom_path=None):
        """保存当前壁纸和元数据到收藏夹"""
        if not self.current_wallpaper or not os.path.exists(self.current_wallpaper):
            print("当前没有有效的壁纸可保存")
            return False
        
        # 确定保存目录
        save_dir = custom_path if custom_path else self.settings.get_setting("favorite_path")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 获取基础文件名
        base_filename = os.path.basename(self.current_wallpaper)
        filename, ext = os.path.splitext(base_filename)
        
        try:
            import shutil
            # 保存壁纸图片
            new_image_path = os.path.join(save_dir, f"favorite_{filename}{ext}")
            shutil.copy2(self.current_wallpaper, new_image_path)
            print(f"壁纸图片已保存到: {new_image_path}")
            
            # 尝试查找并保存对应的元数据文件
            metadata_path = os.path.join(
                os.path.dirname(self.current_wallpaper),
                f"{filename}.json"
            )
            
            if os.path.exists(metadata_path):
                new_metadata_path = os.path.join(save_dir, f"favorite_{filename}.json")
                shutil.copy2(metadata_path, new_metadata_path)
                print(f"壁纸元数据已保存到: {new_metadata_path}")
            
            return True
        except Exception as e:
            print(f"保存壁纸时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
