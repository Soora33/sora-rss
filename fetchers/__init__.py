from typing import List, Dict, Any
from .github_fetcher import GithubFetcher
from .bilibili_fetcher import BilibiliFetcher
from .weibo_fetcher import WeiboFetcher
from .zhihu_fetcher import ZhihuFetcher
from .pixiv_fetcher import PixivFetcher

def get_fetcher(source_name: str, config: Dict[str, Any]):
    """获取对应数据源的Fetcher"""
    fetchers = {
        "github": GithubFetcher,
        "bilibili": BilibiliFetcher,
        "weibo": WeiboFetcher,
        "zhihu": ZhihuFetcher,
        "pixiv": PixivFetcher
    }

    fetcher_class = fetchers.get(source_name)
    if fetcher_class:
        return fetcher_class(config)
    raise ValueError(f"未知的数据源: {source_name}")
