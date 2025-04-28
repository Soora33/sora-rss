from dataclasses import dataclass
from typing import List, Dict

@dataclass
class GithubProject:
    """GitHub热门项目数据模型"""
    name: str
    url: str
    description: str
    language: str
    stars: int
    forks: int

@dataclass
class BilibiliVideo:
    """B站热门视频数据模型"""
    title: str
    url: str
    cover: str
    up_name: str
    up_url: str
    duration: str
    views: str
    danmaku: str

@dataclass
class WeiboHot:
    """微博热搜数据模型"""
    title: str
    url: str
    rank: int
    hot_score: str
    label: str  # 爆/热/新等标签

@dataclass
class ZhihuQuestion:
    """知乎热榜数据模型"""
    title: str
    url: str
    hot_score: str
    answer_count: int
    follower_count: int

@dataclass
class PixivArtwork:
    """Pixiv排行榜数据模型"""
    title: str
    url: str
    image_url: str
    author: str
    author_url: str
    width: int
    height: int
    bookmarks: int
