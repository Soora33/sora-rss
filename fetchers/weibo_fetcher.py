from typing import List
from .base_fetchers import BaseFetcher
import json
from models import WeiboHot
from utils.formatters import format_number

class WeiboFetcher(BaseFetcher):
    """微博热搜获取器"""

    def fetch(self) -> List[WeiboHot]:
        """获取微博热搜"""
        url = "https://weibo.com/ajax/side/hotSearch"
        try:
            response = self._make_request(url)
            if not response:
                return []

            # 确保我们处理的是字典数据
            if isinstance(response, str):
                try:
                    data = json.loads(response)
                except json.JSONDecodeError:
                    print("微博API返回的不是有效JSON")
                    return []
            else:
                data = response

            if not data or "data" not in data:
                return []

            hot_list = []
            # 实时热搜
            for idx, item in enumerate(data["data"]["realtime"][:self.config.get("limit", 10)], 1):
                # 处理热度值
                hot_score = item.get("hot", "")
                if isinstance(hot_score, int):
                    hot_score = format_number(hot_score)

                # 处理标签
                label = item.get("label_name", "")
                if label == "爆":
                    label = "爆"
                elif label == "热":
                    label = "热"
                elif label == "新":
                    label = "新"
                else:
                    label = ""

                hot_list.append(WeiboHot(
                    title=item.get("note", "无标题"),
                    url=f"https://s.weibo.com/weibo?q={item.get('word', '')}",
                    rank=idx,
                    hot_score=hot_score,
                    label=label
                ))

            return hot_list
        except Exception as e:
            print(f"获取微博热搜失败: {e}")
            return []

