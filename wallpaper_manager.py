import os
import ctypes
import requests
import platform
import json
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
import time
import random
from datetime import datetime
import tempfile

class WallpaperManager(QObject):
    wallpaper_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.timer = QTimer()
        self.timer.timeout.connect(self.change_wallpaper)
        self.current_wallpaper = ""
        
        self.unsplash_access_key = self.settings.get_setting("unsplash_access_key", "")
        self.unsplash_secret_key = self.settings.get_setting("unsplash_secret_key", "")
        
        # 创建壁纸存储目录
        self.wallpaper_dir = os.path.join(tempfile.gettempdir(), "wallpaper_changer")
        os.makedirs(self.wallpaper_dir, exist_ok=True)
        
        # 只为已添加的自定义合集创建缓存
        self.collection_info_cache = {}  # 合集信息缓存
        self.collection_photos_cache = {}  # 合集照片缓存
        
        # 预定义的热门合集
        self.popular_collections = {
            "自然风光": "1065976",
            "城市建筑": "1114848", 
            "抽象艺术": "1065396",
            "动物世界": "181581",
            "太空宇宙": "1162961",
            "简约风格": "1114847",
            "复古怀旧": "1065412",
            "黑白摄影": "1163637",
            "山川湖海": "1065976",
            "花卉植物": "1154337",
            "汽车": "1163808",
            "美食": "1114849",
            "运动健身": "1163809",
            "科技数码": "1163810"
        }
        
        # 初始化时加载已保存的合集缓存
        self.load_cached_collections()
        
        if not self.unsplash_access_key:
            print("未设置Unsplash API密钥")

    def load_cached_collections(self):
        """加载已缓存的合集信息"""
        try:
            cached_data = self.settings.get_setting("cached_collections", {})
            current_time = time.time()
            
            # 清理过期缓存（7天）
            valid_cache = {}
            for collection_id, data in cached_data.items():
                if current_time - data.get('cached_time', 0) < 7 * 24 * 3600:
                    valid_cache[collection_id] = data
                    # 加载到内存缓存
                    self.collection_info_cache[collection_id] = data['info']
                    if 'photos' in data:
                        self.collection_photos_cache[collection_id] = data['photos']
            
            # 保存清理后的缓存
            if len(valid_cache) != len(cached_data):
                self.settings.set_setting("cached_collections", valid_cache)
                print(f"清理过期缓存，保留 {len(valid_cache)} 个合集")
            
            print(f"加载了 {len(valid_cache)} 个已缓存的合集")
            
        except Exception as e:
            print(f"加载缓存失败: {e}")

    def get_collection_info(self, collection_id, cache_if_added=False):
        """获取合集详细信息（支持用户likes）"""
        # 检查是否是用户likes
        if self.is_user_likes_collection(collection_id):
            username = self.get_username_from_collection_id(collection_id)
            if username:
                # 如果有缓存且要求使用缓存
                if cache_if_added and collection_id in self.collection_info_cache:
                    print(f"从缓存获取用户likes信息: {username}")
                    return self.collection_info_cache[collection_id]
                
                # 获取用户likes信息
                user_likes_info = self.get_user_likes_as_collection_info(username)
                
                # 如果要求缓存，则缓存结果
                if cache_if_added and user_likes_info:
                    self.collection_info_cache[collection_id] = user_likes_info
                    self.save_collection_to_cache(collection_id, user_likes_info)
                    print(f"已缓存用户likes信息: {username}")
                
                return user_likes_info
        
        # 原有的合集处理逻辑
        if cache_if_added and collection_id in self.collection_info_cache:
            print(f"从缓存获取合集信息: {collection_id}")
            return self.collection_info_cache[collection_id]
        
        if not self.unsplash_access_key:
            print("错误: 未设置Unsplash API密钥")
            return None
        
        try:
            url = f"https://api.unsplash.com/collections/{collection_id}"
            params = {
                'client_id': self.unsplash_access_key
            }
            
            print(f"请求合集信息 (缓存模式: {cache_if_added}): {collection_id}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            collection_info = response.json()
            
            # 检查返回的数据结构
            if not isinstance(collection_info, dict) or 'id' not in collection_info:
                print("API返回的数据格式不正确")
                return None
            
            # 安全地提取信息
            result = {
                'id': collection_info.get('id', collection_id),
                'title': collection_info.get('title', '未知标题'),
                'description': collection_info.get('description', ''),
                'total_photos': collection_info.get('total_photos', 0),
                'user': collection_info.get('user', {}).get('name', '未知用户') if collection_info.get('user') else '未知用户',
                'cover_photo': collection_info.get('cover_photo', {}).get('urls', {}).get('small', '') if collection_info.get('cover_photo') else '',
                'type': 'collection'  # 标识为普通合集
            }
            
            # 只有在明确要求缓存时才缓存
            if cache_if_added:
                self.collection_info_cache[collection_id] = result
                self.save_collection_to_cache(collection_id, result)
                print(f"已缓存合集信息: {collection_id}")
            
            return result
            
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response.status_code == 404:
                print(f"合集不存在: {collection_id}")
            elif hasattr(e, 'response') and e.response.status_code == 401:
                print("API密钥无效或未授权")
            elif hasattr(e, 'response') and e.response.status_code == 403:
                print("API访问被禁止，可能是速率限制")
            else:
                print(f"HTTP错误: {e}")
            return None
        except Exception as e:
            print(f"获取合集信息时发生错误: {e}")
            return None

    def get_collection_photos(self, collection_id, per_page=30):
        """获取合集中的照片列表（支持用户likes）"""
        # 检查是否是用户likes
        if self.is_user_likes_collection(collection_id):
            username = self.get_username_from_collection_id(collection_id)
            if username:
                return self.get_user_likes(username, per_page)
            return []
        # 检查缓存
        if collection_id in self.collection_photos_cache:
            cached_photos, timestamp = self.collection_photos_cache[collection_id]
            # 缓存1小时内有效
            if time.time() - timestamp < 3600:
                print(f"从缓存获取照片列表: {collection_id}")
                return cached_photos
        
        if not self.unsplash_access_key:
            return []
        
        try:
            url = f"https://api.unsplash.com/collections/{collection_id}/photos"
            params = {
                'client_id': self.unsplash_access_key,
                'per_page': per_page,
                'page': random.randint(1, 3)  # 随机选择页面
            }
            
            print(f"请求合集照片: {collection_id}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            photos = response.json()
            
            # 缓存结果（只缓存已添加的合集）
            if self.is_collection_added(collection_id):
                self.collection_photos_cache[collection_id] = (photos, time.time())
                self.update_collection_photos_cache(collection_id, photos)
                print(f"已缓存照片列表: {collection_id}")
            
            return photos
            
        except Exception as e:
            print(f"获取合集照片失败: {e}")
            return []

    def is_collection_added(self, collection_id):
        """检查合集是否已添加到自定义合集中（支持用户likes）"""
        custom_collections = self.settings.get_custom_collections()
        return collection_id in custom_collections.values()

    def save_collection_to_cache(self, collection_id, collection_info):
        """保存合集信息到持久化缓存"""
        try:
            cached_data = self.settings.get_setting("cached_collections", {})
            cached_data[collection_id] = {
                'info': collection_info,
                'cached_time': time.time()
            }
            self.settings.set_setting("cached_collections", cached_data)
        except Exception as e:
            print(f"保存缓存失败: {e}")

    def update_collection_photos_cache(self, collection_id, photos):
        """更新合集照片缓存"""
        try:
            cached_data = self.settings.get_setting("cached_collections", {})
            if collection_id in cached_data:
                cached_data[collection_id]['photos'] = (photos, time.time())
                self.settings.set_setting("cached_collections", cached_data)
        except Exception as e:
            print(f"更新照片缓存失败: {e}")

    def remove_collection_cache(self, collection_id):
        """移除合集缓存（当用户删除自定义合集时调用）"""
        try:
            # 从内存缓存中移除
            self.collection_info_cache.pop(collection_id, None)
            self.collection_photos_cache.pop(collection_id, None)
            
            # 从持久化缓存中移除
            cached_data = self.settings.get_setting("cached_collections", {})
            if collection_id in cached_data:
                del cached_data[collection_id]
                self.settings.set_setting("cached_collections", cached_data)
                print(f"已移除合集缓存: {collection_id}")
        except Exception as e:
            print(f"移除缓存失败: {e}")
    
    def get_popular_collections(self):
        """获取预定义的热门合集"""
        return self.popular_collections
    
    def search_collections(self, query, per_page=20):
        """搜索合集"""
        if not self.unsplash_access_key:
            return []
        
        try:
            url = "https://api.unsplash.com/search/collections"
            params = {
                'client_id': self.unsplash_access_key,
                'query': query,
                'per_page': per_page
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            collections = []
            
            for collection in data.get('results', []):
                collections.append({
                    'id': collection['id'],
                    'title': collection['title'],
                    'description': collection.get('description', ''),
                    'total_photos': collection['total_photos'],
                    'preview_photos': [photo['urls']['small'] for photo in collection.get('preview_photos', [])[:3]]
                })
            
            return collections
            
        except Exception as e:
            print(f"搜索合集失败: {e}")
            return []
    
    def extract_user_from_likes_url(self, url):
        """从用户likes URL中提取用户名（仅支持明确的likes链接）"""
        import re
        
        print(f"正在提取likes URL中的用户名: {url}")
        
        try:
            url = url.strip()
            
            # 只支持明确的用户likes URL格式：
            # https://unsplash.com/@username/likes
            # http://unsplash.com/@username/likes
            
            patterns = [
                r'https?://(?:www\.)?unsplash\.com/@([a-zA-Z0-9_.-]+)/likes',  # 完整likes URL
                r'unsplash\.com/@([a-zA-Z0-9_.-]+)/likes',                    # 不带协议的likes URL
            ]
            
            for i, pattern in enumerate(patterns):
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    print(f"使用模式 {i+1} 提取到用户名: {username}")
                    return username
            
            print("输入的不是有效的用户likes链接")
            return None
            
        except Exception as e:
            print(f"提取用户名失败: {e}")
            return None

    def get_user_info(self, username):
        """获取用户基本信息"""
        if not self.unsplash_access_key:
            return None
        
        try:
            url = f"https://api.unsplash.com/users/{username}"
            params = {
                'client_id': self.unsplash_access_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            user_info = response.json()
            return {
                'id': user_info.get('id'),
                'username': user_info.get('username'),
                'name': user_info.get('name', ''),
                'bio': user_info.get('bio', ''),
                'total_likes': user_info.get('total_likes', 0),
                'total_photos': user_info.get('total_photos', 0),
                'profile_image': user_info.get('profile_image', {}).get('medium', ''),
                'portfolio_url': user_info.get('portfolio_url', ''),
                'location': user_info.get('location', '')
            }
            
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            return None

    def get_user_likes(self, username, per_page=30, page=1):
        """获取用户的likes页面照片"""
        if not self.unsplash_access_key:
            return []
        
        try:
            url = f"https://api.unsplash.com/users/{username}/likes"
            params = {
                'client_id': self.unsplash_access_key,
                'per_page': per_page,
                'page': page
            }
            
            print(f"请求用户likes: {username} (页面: {page})")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            photos = response.json()
            print(f"获取到 {len(photos)} 张likes照片")
            return photos
            
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response.status_code == 404:
                print(f"用户不存在: {username}")
            else:
                print(f"HTTP错误: {e}")
            return []
        except Exception as e:
            print(f"获取用户likes失败: {e}")
            return []
        
    def get_user_likes_as_collection_info(self, username):
        """将用户likes信息格式化为合集信息格式"""
        try:
            user_info = self.get_user_info(username)
            if not user_info:
                return None
            
            # 检查用户是否有likes
            if user_info.get('total_likes', 0) == 0:
                return None
            
            # 格式化为合集信息格式
            collection_info = {
                'id': f"user_likes_{username}",  # 特殊ID格式标识这是用户likes
                'title': f"{user_info.get('name', username)} 的 Likes",
                'description': f"来自 @{username} 的喜欢照片。{user_info.get('bio', '')}",
                'total_photos': user_info.get('total_likes', 0),
                'user': user_info.get('name', username),
                'cover_photo': user_info.get('profile_image', ''),
                'username': username,  # 额外字段，用于标识这是用户likes
                'type': 'user_likes'   # 标识类型
            }
            
            return collection_info
            
        except Exception as e:
            print(f"获取用户likes信息失败: {e}")
            return None

    def is_user_likes_collection(self, collection_id):
        """检查是否是用户likes合集"""
        return collection_id.startswith("user_likes_")

    def get_username_from_collection_id(self, collection_id):
        """从用户likes合集ID中提取用户名"""
        if self.is_user_likes_collection(collection_id):
            return collection_id.replace("user_likes_", "")
        return None

    def validate_user_likes(self, username):
        """验证用户是否存在且有likes"""
        user_info = self.get_user_info(username)
        if not user_info:
            return False, "用户不存在"
        
        if user_info['total_likes'] == 0:
            return False, f"用户 {user_info['name'] or username} 还没有likes任何照片"
        
        # 尝试获取第一页likes来确认可以访问
        likes = self.get_user_likes(username, per_page=1)
        if not likes:
            return False, "无法获取用户的likes"
        
        return True, user_info

    def download_from_user_likes(self, username, width, height):
        """从用户likes中下载壁纸"""
        try:
            # 随机选择页面（假设用户有多页likes）
            page = random.randint(1, 5)  # 最多尝试前5页
            photos = self.get_user_likes(username, per_page=30, page=page)
            
            if not photos:
                # 如果随机页面没有照片，尝试第一页
                photos = self.get_user_likes(username, per_page=30, page=1)
            
            if not photos:
                print(f"用户 {username} 的likes中没有找到照片")
                return None
            
            # 随机选择一张照片
            photo = random.choice(photos)
            image_url = photo['urls']['raw']
            
            # 构建下载URL
            download_url = f"{image_url}&w={width}&h={height}&fit=crop&crop=entropy"
            
            # 下载图片
            image_response = requests.get(download_url, timeout=60)
            image_response.raise_for_status()
            
            # 保存图片
            timestamp = int(time.time())
            filename = f"wallpaper_{timestamp}.jpg"
            filepath = os.path.join(self.wallpaper_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_response.content)
            
            # 清理旧的壁纸文件
            self._cleanup_old_wallpapers()
            
            print(f"从用户 {username} 的likes下载壁纸成功: {photo.get('description', '无描述')}")
            return filepath
            
        except Exception as e:
            print(f"从用户likes下载壁纸失败: {e}")
            return None

    def download_wallpaper(self):
        """从Unsplash下载壁纸"""
        if not self.unsplash_access_key:
            print("未设置Unsplash API密钥")
            return None
            
        try:
            resolution = self.get_screen_resolution()
            quality = self.settings.get_setting("quality", "high")
            width, height = resolution.get(quality, resolution['medium'])
            
            # 检查是否启用了用户likes模式
            use_user_likes = self.settings.get_setting("use_user_likes", False)
            selected_user = self.settings.get_setting("selected_user", "")
            
            # 检查是否启用了合集模式
            use_collection = self.settings.get_setting("use_collection", False)
            selected_collection = self.settings.get_setting("selected_collection", "")
            
            if use_user_likes and selected_user:
                # 从用户likes中下载
                print(f"从用户 {selected_user} 的likes下载壁纸")
                return self.download_from_user_likes(selected_user, width, height)
            elif use_collection and selected_collection:
                # 从合集中下载
                print(f"从合集 {selected_collection} 下载壁纸")
                return self.download_from_collection(selected_collection, width, height)
            else:
                # 从随机照片或关键词搜索中下载
                print("下载随机壁纸")
                return self.download_random_wallpaper(width, height)
                
        except Exception as e:
            print(f"下载壁纸时发生未知错误: {e}")
            return None
    
    def download_from_collection(self, collection_id, width, height):
        """从指定合集下载壁纸"""
        try:
            # 获取合集中的照片
            photos = self.get_collection_photos(collection_id)
            
            if not photos:
                print("合集中没有找到照片")
                return None
            
            # 随机选择一张照片
            photo = random.choice(photos)
            image_url = photo['urls']['raw']
            
            # 构建下载URL
            download_url = f"{image_url}&w={width}&h={height}&fit=crop&crop=entropy"
            
            # 下载图片
            image_response = requests.get(download_url, timeout=60)
            image_response.raise_for_status()
            
            # 保存图片
            timestamp = int(time.time())
            filename = f"wallpaper_{timestamp}.jpg"
            filepath = os.path.join(self.wallpaper_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_response.content)
            
            # 清理旧的壁纸文件
            self._cleanup_old_wallpapers()
            
            print(f"从合集下载壁纸成功: {photo.get('description', '无描述')}")
            return filepath
            
        except Exception as e:
            print(f"从合集下载壁纸失败: {e}")
            return None
    
    def download_random_wallpaper(self, width, height):
        """下载随机壁纸（原有功能）"""
        try:
            # 构建Unsplash API请求
            params = {
                'client_id': self.unsplash_access_key,
                'w': width,
                'h': height,
                'fit': 'crop',
                'crop': 'entropy'
            }
            
            # 添加搜索关键词（如果设置了的话）
            keywords = self.settings.get_setting("keywords", "")
            if keywords:
                params['query'] = keywords
                url = "https://api.unsplash.com/photos/random"
            else:
                url = "https://api.unsplash.com/photos/random"
            
            # 发送请求
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            image_url = data['urls']['raw']
            
            # 下载图片
            image_response = requests.get(image_url, timeout=60)
            image_response.raise_for_status()
            
            # 保存图片
            timestamp = int(time.time())
            filename = f"wallpaper_{timestamp}.jpg"
            filepath = os.path.join(self.wallpaper_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_response.content)
            
            # 清理旧的壁纸文件
            self._cleanup_old_wallpapers()
            
            return filepath
            
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return None
        except Exception as e:
            print(f"下载随机壁纸时发生未知错误: {e}")
            return None
    
    # ... 其他现有方法保持不变 ...
    
    def start_timer(self):
        frequency = self.settings.get_setting("frequency")
        interval_ms = self._convert_frequency_to_ms(frequency)
        self.timer.start(interval_ms)
        
    def stop_timer(self):
        self.timer.stop()
        
    def _convert_frequency_to_ms(self, frequency):
        frequency_map = {
            "1小时": 60 * 60 * 1000,
            "2小时": 2 * 60 * 60 * 1000,
            "4小时": 4 * 60 * 60 * 1000,
            "1天": 24 * 60 * 60 * 1000
        }
        return frequency_map.get(frequency, 60 * 60 * 1000)
    
    def get_screen_resolution(self):
        if platform.system() == "Windows":
            try:
                user32 = ctypes.windll.user32
                base_width = user32.GetSystemMetrics(0)
                base_height = user32.GetSystemMetrics(1)
                
                hdc = user32.GetDC(0)
                dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
                user32.ReleaseDC(0, hdc)
                density = max(1, dpi / 96)
                
                width = int(base_width * density)
                height = int(base_height * density)
                
                ratio = base_width / base_height
                if ratio >= 2:
                    width = int(height * 2)
                elif ratio <= 0.5:
                    height = int(width * 2)
                
                if width >= 3840 or height >= 2160:
                    resolution_levels = {
                        'full': (width, height),
                        'high': (2560, 1440),
                        'medium': (1920, 1080),
                        'small': (1280, 720),
                        'base': (base_width, base_height)
                    }
                elif width >= 2560 or height >= 1440:
                    resolution_levels = {
                        'full': (2560, 1440),
                        'high': (2560, 1440),
                        'medium': (1920, 1080),
                        'small': (1280, 720),
                        'base': (base_width, base_height)
                    }
                else:
                    resolution_levels = {
                        'full': (1920, 1080),
                        'high': (1920, 1080),
                        'medium': (1280, 720),
                        'small': (960, 540),
                        'base': (base_width, base_height)
                    }
                    
                return resolution_levels
            except Exception as e:
                print(f"获取屏幕分辨率失败: {e}")
                return self._get_default_resolution()
        else:
            return self._get_default_resolution()
    
    def _get_default_resolution(self):
        return {
            'full': (3840, 2160),
            'high': (2560, 1440),
            'medium': (1920, 1080),
            'small': (1280, 720),
            'base': (1920, 1080)
        }
    
    def change_wallpaper(self):
        try:
            wallpaper_path = self.download_wallpaper()
            if wallpaper_path:
                self._set_wallpaper(wallpaper_path)
                self.current_wallpaper = wallpaper_path
                self.wallpaper_changed.emit(wallpaper_path)
            else:
                self.error_occurred.emit("下载壁纸失败")
        except Exception as e:
            self.error_occurred.emit(f"更换壁纸时发生错误: {str(e)}")
            
    def _set_wallpaper(self, wallpaper_path):
        try:
            if platform.system() == "Windows":
                ctypes.windll.user32.SystemParametersInfoW(20, 0, wallpaper_path, 3)
            elif platform.system() == "Darwin":
                os.system(f"osascript -e 'tell application \"Finder\" to set desktop picture to POSIX file \"{wallpaper_path}\"'")
            else:
                os.system(f"gsettings set org.gnome.desktop.background picture-uri file://{wallpaper_path}")
        except Exception as e:
            raise Exception(f"设置壁纸失败: {str(e)}")
    
    def _cleanup_old_wallpapers(self):
        try:
            files = []
            for filename in os.listdir(self.wallpaper_dir):
                if filename.startswith("wallpaper_") and filename.endswith(".jpg"):
                    filepath = os.path.join(self.wallpaper_dir, filename)
                    files.append((filepath, os.path.getctime(filepath)))
            
            files.sort(key=lambda x: x[1], reverse=True)
            
            for filepath, _ in files[5:]:
                try:
                    os.remove(filepath)
                except OSError:
                    pass
                    
        except Exception as e:
            print(f"清理旧壁纸文件时出错: {e}")
    
    def manual_change_wallpaper(self):
        self.change_wallpaper()
    
    def get_current_wallpaper(self):
        return self.current_wallpaper
