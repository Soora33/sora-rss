from typing import List
from .base_fetchers import BaseFetcher
import json
from models import BilibiliVideo
from utils.formatters import format_number, format_duration

class BilibiliFetcher(BaseFetcher):
    """B站热门视频获取器"""

    def fetch(self) -> List[BilibiliVideo]:
        """获取B站热门视频"""
        region = self.config.get("region", "all")
        if region == "all":
            url = "https://api.bilibili.com/x/web-interface/popular"
        else:
            url = f"https://api.bilibili.com/x/web-interface/ranking/region?rid={region}"

        try:
            # 明确指定需要JSON响应
            response = self._make_request(url)
            if not response:
                return []

            # 确保我们处理的是字典数据
            if isinstance(response, str):
                try:
                    data = json.loads(response)
                except json.JSONDecodeError:
                    print("B站API返回的不是有效JSON")
                    return []
            else:
                data = response

            if not data or "data" not in data:
                return []

            videos = []
            for item in data["data"]["list"][:self.config.get("limit", 10)]:
                video = BilibiliVideo(
                    title=item["title"],
                    url=f"https://www.bilibili.com/video/{item['bvid']}",
                    cover=item["pic"],
                    up_name=item["owner"]["name"],
                    up_url=f"https://space.bilibili.com/{item['owner']['mid']}",
                    duration=format_duration(item["duration"]),
                    views=format_number(item["stat"]["view"]),
                    danmaku=format_number(item["stat"]["danmaku"])
                )
                videos.append(video)
            return videos
        except Exception as e:
            print(f"获取B站热门视频失败: {e}")
            return []
