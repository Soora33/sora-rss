from typing import List
from .base_fetchers import BaseFetcher
from models import ZhihuQuestion
from utils.formatters import format_number

class ZhihuFetcher(BaseFetcher):
    """知乎热榜获取器"""

    def fetch(self) -> List[ZhihuQuestion]:
        """获取知乎热榜"""
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"

        try:
            data = self._make_request(url)
            if not data or "data" not in data:
                return []

            questions = []
            for item in data["data"][:self.config.get("limit", 10)]:
                target = item.get("target", {})
                questions.append(ZhihuQuestion(
                    title=target.get("title", "无标题"),
                    url=f"https://www.zhihu.com/question/{target.get('id', '')}",
                    hot_score=format_number(item.get("detail_text", "0")),
                    answer_count=target.get("answer_count", 0),
                    follower_count=target.get("follower_count", 0)
                ))
            return questions
        except Exception as e:
            print(f"获取知乎热榜失败: {e}")
            return []
