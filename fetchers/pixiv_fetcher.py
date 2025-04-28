import re
import json
from typing import List
from .base_fetchers import BaseFetcher
from models import PixivArtwork

class PixivFetcher(BaseFetcher):
    """Pixiv排行榜获取器"""

    def fetch(self) -> List[PixivArtwork]:
        """获取Pixiv排行榜"""
        mode = self.config.get("mode", "daily")
        url = f"https://www.pixiv.net/ranking.php?mode={mode}"

        try:
            headers = {
                "Referer": "https://www.pixiv.net/"
            }
            response = self._make_request(url, headers=headers)
            if not response:
                return []

            # 使用正则表达式提取JSON数据
            pattern = re.compile(r'window.__INITIAL_STATE__=({.*?});', re.DOTALL)
            match = pattern.search(response)

            if match:
                data = json.loads(match.group(1))
                illusts = data.get("ranking", {}).get("ranking", {}).get("illusts", [])
            else:
                # 备用方案：使用API接口
                api_url = f"https://www.pixiv.net/ranking.php?mode={mode}&format=json"
                api_response = self._make_request(api_url, headers=headers)
                if not api_response:
                    return []
                illusts = api_response.get("contents", [])[:self.config.get("limit", 10)]

            artworks = []
            for item in illusts[:self.config.get("limit", 10)]:
                try:
                    # 获取作品ID
                    illust_id = item.get("illust_id", item.get("illustId", ""))

                    # 获取图片URL - 使用pixiv.cat代理
                    image_url = f"https://pixiv.cat/{illust_id}.jpg"

                    # 获取作品标题
                    title = item.get("title", "无标题")

                    # 获取作者信息
                    user_name = item.get("user_name", item.get("userName", "未知作者"))
                    user_id = item.get("user_id", item.get("userId", ""))
                    author_url = f"https://www.pixiv.net/users/{user_id}" if user_id else ""

                    # 获取图片尺寸
                    width = item.get("width", 0)
                    height = item.get("height", 0)

                    # 获取收藏数
                    bookmarks = item.get("bookmark_count", item.get("bookmarkCount", 0))

                    artworks.append(PixivArtwork(
                        title=title,
                        url=f"https://www.pixiv.net/artworks/{illust_id}",
                        image_url=image_url,
                        author=user_name,
                        author_url=author_url,
                        width=width,
                        height=height,
                        bookmarks=bookmarks
                    ))
                except Exception as e:
                    print(f"处理Pixiv作品时出错: {e}")
                    continue

            return artworks
        except Exception as e:
            print(f"获取Pixiv排行榜失败: {e}")
            return []
