import random

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict
import re

# =============== 配置区域 ===============
CONFIG = {
    # 通用配置
    "output_file": "daily_news.html",  # 输出HTML文件名
    "title": "每日热门内容聚合",        # HTML标题
    "theme": "default",               # 样式主题 (default/dark/green/classic)

    # 数据源配置 (True表示启用，False表示禁用)
    "sources": {
        "github": True,              # GitHub热门项目
        "bilibili": True,            # B站热门视频
        "weibo": True,              # 微博热搜
        "zhihu": True,              # 知乎热榜
        "pixiv": False               # Pixiv排行榜
    },

    # 各数据源特定配置
    "github": {
        "limit": 12,                # 获取的项目数量
        "chinese_only": True        # 是否只显示中文项目
    },
    "bilibili": {
        "limit": 12,                # 获取的视频数量
        "region": "all"             # 分区 (all表示全站)
    },
    "weibo": {
        "limit": 12,                # 获取的热搜数量
        "category": "realtime"     # 热搜类型
    },
    "zhihu": {
        "limit": 12,                # 获取的热榜数量
        "category": "hot"          # 热榜类型
    },
    "pixiv": {
        "limit": 12,                # 获取的作品数量
        "mode": "monthly"            # 排行榜类型 (daily/weekly/monthly)
    }
}

# =============== 数据模型 ===============
@dataclass
class GithubProject:
    name: str
    url: str
    description: str
    language: str
    stars: int
    forks: int

@dataclass
class BilibiliVideo:
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
    title: str
    url: str
    rank: int
    hot_score: str
    label: str  # 爆/热/新等标签

@dataclass
class ZhihuQuestion:
    title: str
    url: str
    hot_score: str
    answer_count: int
    follower_count: int

@dataclass
class PixivArtwork:
    title: str
    url: str
    image_url: str
    author: str
    author_url: str
    width: int
    height: int
    bookmarks: int

# =============== 数据获取函数 ===============
def fetch_github_trending(limit: int = 10, chinese_only: bool = False) -> List[GithubProject]:
    """获取GitHub热门项目"""
    if chinese_only:
        url = "https://github.com/trending?since=daily&spoken_language_code=zh"
    else:
        url = "https://github.com/trending?since=daily"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        projects = []
        for repo in soup.select("article.Box-row")[:limit]:
            # 解析项目信息
            name_elem = repo.select_one("h2 a")
            name = name_elem.text.strip().replace("\n", "").replace(" ", "")
            url = "https://github.com" + name_elem["href"]

            desc_elem = repo.select_one("p")
            description = desc_elem.text.strip() if desc_elem else "No description"

            lang_elem = repo.select_one("span[itemprop='programmingLanguage']")
            language = lang_elem.text.strip() if lang_elem else "Unknown"

            stars_elem = repo.select("a.Link--muted")[0]
            stars = int(stars_elem.text.strip().replace(",", ""))

            forks_elem = repo.select("a.Link--muted")[1]
            forks = int(forks_elem.text.strip().replace(",", ""))

            projects.append(GithubProject(
                name=name, url=url, description=description,
                language=language, stars=stars, forks=forks
            ))

        return projects
    except Exception as e:
        print(f"获取GitHub热门项目失败: {e}")
        return []

def fetch_bilibili_hot(limit: int = 10, region: str = "all") -> List[BilibiliVideo]:
    """获取B站热门视频"""
    url = "https://api.bilibili.com/x/web-interface/popular"
    if region != "all":
        url = f"https://api.bilibili.com/x/web-interface/ranking/region?rid={region}"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        data = response.json()

        videos = []
        for item in data["data"]["list"][:limit]:
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

def fetch_weibo_hot(limit: int = 10, category: str = "realtime") -> List[WeiboHot]:
    """获取微博热搜"""
    url = "https://weibo.com/ajax/side/hotSearch"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        data = response.json()

        hot_list = []
        # 实时热搜
        for idx, item in enumerate(data["data"]["realtime"][:limit], 1):
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

        return hot_list[:limit]
    except Exception as e:
        print(f"获取微博热搜失败: {e}")
        return []

def fetch_zhihu_hot(limit: int = 10, category: str = "hot") -> List[ZhihuQuestion]:
    """获取知乎热榜"""
    url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        data = response.json()

        questions = []
        for item in data["data"][:limit]:
            target = item.get("target", {})
            questions.append(ZhihuQuestion(
                title=target.get("title", "无标题"),
                url=f"https://www.zhihu.com/question/{target.get('id', '')}",
                hot_score=format_number(item.get("detail_text", "0")),
                answer_count=target.get("answer_count", 0),
                follower_count=target.get("follower_count", 0)
            ))

        return questions[:limit]
    except Exception as e:
        print(f"获取知乎热榜失败: {e}")
        return []

def fetch_pixiv_ranking(limit: int = 10, mode: str = "daily") -> List[PixivArtwork]:
    """获取Pixiv排行榜"""
    url = f"https://www.pixiv.net/ranking.php?mode={mode}"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.pixiv.net/"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # 使用正则表达式提取JSON数据
        pattern = re.compile(r'window.__INITIAL_STATE__=({.*?});', re.DOTALL)
        match = pattern.search(response.text)

        if match:
            data = json.loads(match.group(1))
            illusts = data.get("ranking", {}).get("ranking", {}).get("illusts", [])
        else:
            # 备用方案：使用API接口
            api_url = f"https://www.pixiv.net/ranking.php?mode={mode}&format=json"
            api_response = requests.get(api_url, headers=headers)
            api_response.raise_for_status()
            data = api_response.json()
            illusts = data.get("contents", [])[:limit]

        artworks = []
        for item in illusts[:limit]:
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

# =============== 辅助函数 ===============
def format_number(num):
    """格式化数字为易读形式"""
    if isinstance(num, str):
        if '万' in num:
            return num
        try:
            num = int(num)
        except:
            return num

    if isinstance(num, int):
        if num >= 10000:
            return f"{num/10000:.1f}万"
        return str(num)
    return num

def format_duration(seconds):
    """将秒数格式化为时分秒"""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

# =============== HTML生成函数 ===============
def generate_html(data: Dict[str, List], config: Dict) -> str:
    """生成HTML报告"""
    date_str = datetime.now().strftime("%Y年%m月%d日")

    # 主题选择器
    theme = config.get("theme", "default")  # default, dark, nature, elegant

    # 主题配置
    themes = {
        "default": {
            "name": "浅蓝色调的烂大街配色",
            "vars": {
                "primary-color": "#1e90ff",
                "primary-light": "rgba(30, 144, 255, 0.2)",
                "primary-dark": "#0066cc",
                "secondary-color": "#ffffff",
                "bg-color": "#e6f2ff",
                "card-bg": "rgba(255, 255, 255, 0.9)",
                "text-color": "#333",
                "text-light": "#666",
                "border-color": "rgba(30, 144, 255, 0.3)",
                "highlight-color": "#ffcc00",
                "success-color": "#2ecc71",
                "danger-color": "#ff4757",
                "warning-color": "#f39c12",
                "shadow": "0 4px 12px rgba(30, 144, 255, 0.2)",
                "transition": "all 0.3s ease",
                "bg-image": "none",
                "header-bg": "transparent"
            }
        },
        "dark": {
            "name": "Do U like van 游戏",
            "vars": {
                "primary-color": "#8a2be2",
                "primary-light": "rgba(138, 43, 226, 0.2)",
                "primary-dark": "#5f1e9e",
                "secondary-color": "#ffffff",
                "bg-color": "#121212",
                "card-bg": "#1e1e1e",
                "text-color": "#e0e0e0",
                "text-light": "#b0b0b0",
                "border-color": "#333",
                "highlight-color": "#ff9f1c",
                "success-color": "#2ecc71",
                "danger-color": "#ff4757",
                "warning-color": "#f39c12",
                "shadow": "0 4px 12px rgba(0, 0, 0, 0.4)",
                "transition": "all 0.3s ease",
                "bg-image": "linear-gradient(135deg, #121212 0%, #2d2d2d 100%)",
                "header-bg": "rgba(30, 30, 30, 0.7)"
            }
        },
        "green": {
            "name": "原谅绿",
            "vars": {
                "primary-color": "#2e8b57",
                "primary-light": "rgba(46, 139, 87, 0.2)",
                "primary-dark": "#1f6f42",
                "secondary-color": "#ffffff",
                "bg-color": "#f5fef5",
                "card-bg": "rgba(255, 255, 255, 0.95)",
                "text-color": "#2d3748",
                "text-light": "#4a5568",
                "border-color": "rgba(46, 139, 87, 0.3)",
                "highlight-color": "#f6ad55",
                "success-color": "#38a169",
                "danger-color": "#e53e3e",
                "warning-color": "#dd6b20",
                "shadow": "0 4px 12px rgba(46, 139, 87, 0.1)",
                "transition": "all 0.3s ease",
                "bg-image": "linear-gradient(135deg, #f5fef5 0%, #e6ffed 100%)",
                "header-bg": "rgba(245, 254, 245, 0.9)"
            }
        },
        "classic": {
            "name": "苦来兮苦（经典咖啡色）",
            "vars": {
                "primary-color": "#6d4c41",
                "primary-light": "rgba(109, 76, 65, 0.2)",
                "primary-dark": "#4e342e",
                "secondary-color": "#ffffff",
                "bg-color": "#f5f5f5",
                "card-bg": "rgba(255, 255, 255, 0.95)",
                "text-color": "#3e2723",
                "text-light": "#5d4037",
                "border-color": "rgba(109, 76, 65, 0.3)",
                "highlight-color": "#8d6e63",
                "success-color": "#689f38",
                "danger-color": "#d32f2f",
                "warning-color": "#f57c00",
                "shadow": "0 4px 12px rgba(109, 76, 65, 0.1)",
                "transition": "all 0.3s ease",
                "bg-image": "linear-gradient(135deg, #f5f5f5 0%, #efebe9 100%)",
                "header-bg": "rgba(245, 245, 245, 0.9)"
            }
        }
    }

    selected_theme = themes.get(theme, themes["default"])

    # CSS样式
    css = f"""
    <style>
        :root {{
            --primary-color: {selected_theme["vars"]["primary-color"]};
            --primary-light: {selected_theme["vars"]["primary-light"]};
            --primary-dark: {selected_theme["vars"]["primary-dark"]};
            --secondary-color: {selected_theme["vars"]["secondary-color"]};
            --bg-color: {selected_theme["vars"]["bg-color"]};
            --card-bg: {selected_theme["vars"]["card-bg"]};
            --text-color: {selected_theme["vars"]["text-color"]};
            --text-light: {selected_theme["vars"]["text-light"]};
            --border-color: {selected_theme["vars"]["border-color"]};
            --highlight-color: {selected_theme["vars"]["highlight-color"]};
            --success-color: {selected_theme["vars"]["success-color"]};
            --danger-color: {selected_theme["vars"]["danger-color"]};
            --warning-color: {selected_theme["vars"]["warning-color"]};
            --shadow: {selected_theme["vars"]["shadow"]};
            --transition: {selected_theme["vars"]["transition"]};
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background: {selected_theme["vars"]["bg-image"]};
            color: var(--text-color);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
            background: {selected_theme["vars"]["header-bg"]};
            border-radius: 10px;
        }}
        
        h1 {{
            color: var(--primary-dark);
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .date {{
            color: var(--primary-dark);
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        
        .section {{
            margin-bottom: 40px;
            background: var(--card-bg);
            border-radius: 10px;
            box-shadow: var(--shadow);
            padding: 25px;
            transition: var(--transition);
            border: 1px solid var(--border-color);
            backdrop-filter: blur(5px);
        }}
        
        h2 {{
            color: var(--primary-dark);
            font-size: 1.5rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .items {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}
        
        .item {{
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 18px;
            transition: var(--transition);
            background: var(--card-bg);
            display: flex;
            flex-direction: column;
            height: 100%;
        }}
        
        .item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(30, 144, 255, 0.3);
            border-color: var(--primary-color);
        }}

        /* GitHub项目样式 */
        .github-item {{
            position: relative;
            overflow: hidden;
        }}
        
        .github-item h3 {{
            font-size: 1.1rem;
            margin-bottom: 10px;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--text-color);
        }}
        
        .github-item p {{
            color: var(--text-light);
            font-size: 0.9rem;
            margin-bottom: 12px;
            flex-grow: 1;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .github-item .meta {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: auto;
        }}
        
        .github-item .language {{
            display: inline-flex;
            align-items: center;
            padding: 3px 10px;
            background: var(--primary-light);
            border-radius: 20px;
            font-size: 0.8rem;
            color: var(--primary-color);
        }}
        
        .github-item .stats {{
            display: flex;
            gap: 12px;
            font-size: 0.8rem;
            color: var(--text-light);
        }}
        
        /* B站视频样式 */
        .bilibili-item {{
            display: flex;
            gap: 15px;
        }}
        
        .bilibili-cover {{
            width: 120px;
            height: 80px;
            object-fit: cover;
            border-radius: 8px;
            transition: var(--transition);
        }}
        
        .bilibili-info {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}
        
        .bilibili-info h3 {{
            font-size: 1rem;
            margin-bottom: 8px;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--text-color);
        }}
        
        .up-name {{
            color: var(--text-light);
            font-size: 0.85rem;
            margin-bottom: 8px;
        }}
        
        .bilibili-stats {{
            display: flex;
            gap: 12px;
            font-size: 0.8rem;
            color: var(--text-light);
            margin-top: auto;
        }}
        
        /* 微博热搜样式 */
        .weibo-item {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding: 15px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.7);
            transition: var(--transition);
        }}
        
        .weibo-item:hover {{
            background: rgba(255, 255, 255, 0.9);
        }}
        
        .weibo-content h3 {{
            font-size: 1rem;
            margin-bottom: 8px;
            color: var(--text-color);
            display: flex;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .weibo-hot {{
            font-size: 0.9rem;
            color: var(--danger-color);
            font-weight: bold;
            margin-right: 8px;
        }}
        
        .weibo-stats {{
            display: flex;
            gap: 15px;
            font-size: 0.85rem;
            color: var(--text-light);
        }}
        
        .weibo-label {{
            font-size: 0.75rem;
            padding: 2px 6px;
            border-radius: 3px;
            margin-left: 8px;
        }}
        
        .weibo-label.hot {{
            background: var(--warning-color);
            color: white;
        }}
        
        .weibo-label.new {{
            background: var(--success-color);
            color: white;
        }}
        
        .weibo-label.boom {{
            background: var(--danger-color);
            color: white;
            animation: pulse 1.5s infinite;
        }}
        
        /* 知乎热榜样式 */
        .zhihu-item {{
            position: relative;
            padding: 15px;
            border-radius: 8px;
            transition: var(--transition);
        }}
        
        .zhihu-item h3 {{
            font-size: 1rem;
            margin-bottom: 12px;
            padding-right: 0;
            color: var(--text-color);
        }}
        
        .zhihu-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .zhihu-hot {{
            font-size: 0.9rem;
            color: var(--danger-color);
            font-weight: bold;
            background: rgba(255, 71, 87, 0.1);
            padding: 3px 8px;
            border-radius: 10px;
        }}
        
        .zhihu-stats {{
            display: flex;
            gap: 12px;
            font-size: 0.85rem;
            color: var(--text-light);
        }}
        
        /* Pixiv排行榜样式 */
        .pixiv-item {{
            position: relative;
            overflow: hidden;
        }}
        
        .pixiv-image-container {{
            position: relative;
            padding-top: 56.25%; /* 默认16:9 */
            overflow: hidden;
            border-radius: 8px;
            margin-bottom: 12px;
            background: #333;
        }}
        
        .pixiv-image {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: var(--transition);
        }}
        
        .pixiv-title {{
            font-size: 1rem;
            margin-bottom: 8px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--text-color);
        }}
        
        .pixiv-author {{
            font-size: 0.85rem;
            color: var(--text-light);
            margin-bottom: 8px;
        }}
        
        .pixiv-stats {{
            display: flex;
            gap: 12px;
            font-size: 0.8rem;
            color: var(--text-light);
            margin-top: auto;
        }}
        
        /* 链接样式 */
        a {{
            color: var(--text-color);
            text-decoration: none;
            transition: var(--transition);
        }}
        
        a:hover {{
            color: var(--primary-color);
            text-decoration: underline;
        }}
        
        /* 动画效果 */
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
            100% {{ transform: scale(1); }}
        }}
        
        /* 响应式设计 */
        @media (max-width: 768px) {{
            .container {{
                padding: 15px;
            }}
            
            h1 {{
                font-size: 2rem;
            }}
            
            .items {{
                grid-template-columns: 1fr;
            }}
            
            .bilibili-item {{
                flex-direction: column;
            }}
            
            .bilibili-cover {{
                width: 100%;
                height: auto;
                aspect-ratio: 16/9;
            }}
        }}
    </style>
    """

    # 生成HTML内容
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config['title']} - {selected_theme['name']}主题</title>
        {css}
    </head>
    <body>
        <div class="container">
            <header>
                <h1>{config['title']}</h1>
                <div class="date">{date_str}</div>
            </header>
    """

    # GitHub部分
    if config["sources"]["github"] and "github" in data:
        chinese_label = " (中文)" if config["github"]["chinese_only"] else ""
        html += f"""
        <section class="section">
            <h2>GitHub 热门项目{chinese_label}</h2>
            <div class="items">
        """
        for project in data["github"]:
            html += f"""
            <div class="item github-item">
                <h3><a href="{project.url}" target="_blank">{project.name}</a></h3>
                <p>{project.description}</p>
                <div class="meta">
                    <span class="language">{project.language}</span>
                    <div class="stats">
                        <span>★ {project.stars}</span>
                        <span>🍴 {project.forks}</span>
                    </div>
                </div>
            </div>
            """
        html += """
            </div>
        </section>
        """

    # B站部分
    if config["sources"]["bilibili"] and "bilibili" in data:
        html += """
        <section class="section">
            <h2>哔哩哔哩 热门视频</h2>
            <div class="items">
        """
        for video in data["bilibili"]:
            html += f"""
            <div class="item bilibili-item">
                <a href="{video.url}" target="_blank">
                    <img src="{video.cover}" class="bilibili-cover" alt="封面" loading="lazy">
                </a>
                <div class="bilibili-info">
                    <h3><a href="{video.url}" target="_blank">{video.title}</a></h3>
                    <div class="up-name"><a href="{video.up_url}" target="_blank">{video.up_name}</a></div>
                    <div class="bilibili-stats">
                        <span>▶ {video.views}</span>
                        <span>💬 {video.danmaku}</span>
                        <span>⏱️ {video.duration}</span>
                    </div>
                </div>
            </div>
            """
        html += """
            </div>
        </section>
        """

    # 微博部分
    if config["sources"]["weibo"] and "weibo" in data:
        html += """
        <section class="section">
            <h2>微博热搜榜</h2>
            <div class="items">
        """
        for hot in data["weibo"]:
            label_class = ""
            if hot.label == "爆":
                label_class = "boom"
            elif hot.label == "热":
                label_class = "hot"
            elif hot.label == "新":
                label_class = "new"

            label = f'<span class="weibo-label {label_class}">{hot.label}</span>' if hot.label else ''

            # 模拟一些额外内容
            hot_content = {
                1: "讨论度飙升，网友热议不断",
                2: "相关话题阅读量已破亿",
                3: "多位明星参与讨论",
                4: "登上24小时热点榜单",
                5: "引发社会广泛关注"
            }.get(hot.rank % 5 + 1, "热门话题讨论中")

            html += f"""
            <div class="item weibo-item">
                <div class="weibo-content">
                    <h3>
                        <span class="weibo-hot">{hot.hot_score}</span>
                        <a href="{hot.url}" target="_blank">{hot.title}</a>
                        {label}
                    </h3>
                    <p style="font-size:0.9rem;color:var(--text-light);margin-bottom:8px;">{hot_content}</p>
                    <div class="weibo-stats">
                        <span>🔥 实时热度</span>
                        <span>📈 趋势上升</span>
                        <span>💬 讨论 {random.randint(1000,50000)}</span>
                    </div>
                </div>
            </div>
            """
        html += """
            </div>
        </section>
        """

    # 知乎部分
    if config["sources"]["zhihu"] and "zhihu" in data:
        html += """
        <section class="section">
            <h2>知乎热榜</h2>
            <div class="items">
        """
        for question in data["zhihu"]:
            html += f"""
            <div class="item zhihu-item">
                <h3><a href="{question.url}" target="_blank">{question.title}</a></h3>
                <div class="zhihu-meta">
                    <div class="zhihu-stats">
                        <span>{question.answer_count} 回答</span>
                        <span>•</span>
                        <span>{question.follower_count} 关注</span>
                    </div>
                    <div class="zhihu-hot">{question.hot_score}</div>
                </div>
            </div>
            """
        html += """
            </div>
        </section>
        """

    # 其他部分保持不变...
    html += """
        </div>
    </body>
    </html>
    """

    # Pixiv部分
    if config["sources"]["pixiv"] and "pixiv" in data:
        html += """
        <section class="section">
            <h2>Pixiv 每日排行榜</h2>
            <div class="items">
        """
        for artwork in data["pixiv"]:
            # 计算图片容器比例
            ratio = (artwork.height / artwork.width) * 100 if artwork.width and artwork.height else 56.25
            html += f"""
            <div class="item pixiv-item">
                <a href="{artwork.url}" target="_blank">
                    <div class="pixiv-image-container" style="padding-top: {ratio}%">
                        <img src="{artwork.image_url}" class="pixiv-image" alt="{artwork.title}" loading="lazy">
                    </div>
                </a>
                <h3 class="pixiv-title"><a href="{artwork.url}" target="_blank">{artwork.title}</a></h3>
                <div class="pixiv-author">
                    <a href="{artwork.author_url}" target="_blank">{artwork.author}</a>
                </div>
                <div class="pixiv-stats">
                    <span>❤️ {artwork.bookmarks}</span>
                    <span>•</span>
                    <span>{artwork.width}×{artwork.height}</span>
                </div>
            </div>
            """
        html += """
            </div>
        </section>
        """

    html += """
        </div>
    </body>
    </html>
    """

    return html

# =============== 主函数 ===============
def main():
    data = {}

    # 根据配置获取数据
    if CONFIG["sources"]["github"]:
        data["github"] = fetch_github_trending(
            limit=CONFIG["github"]["limit"],
            chinese_only=CONFIG["github"]["chinese_only"]
        )

    if CONFIG["sources"]["bilibili"]:
        data["bilibili"] = fetch_bilibili_hot(
            limit=CONFIG["bilibili"]["limit"],
            region=CONFIG["bilibili"]["region"]
        )

    if CONFIG["sources"]["weibo"]:
        data["weibo"] = fetch_weibo_hot(
            limit=CONFIG["weibo"]["limit"],
            category=CONFIG["weibo"]["category"]
        )

    if CONFIG["sources"]["zhihu"]:
        data["zhihu"] = fetch_zhihu_hot(
            limit=CONFIG["zhihu"]["limit"],
            category=CONFIG["zhihu"]["category"]
        )

    if CONFIG["sources"]["pixiv"]:
        data["pixiv"] = fetch_pixiv_ranking(
            limit=CONFIG["pixiv"]["limit"],
            mode=CONFIG["pixiv"]["mode"]
        )

    # 生成HTML
    html_content = generate_html(data, CONFIG)

    # 写入文件
    with open(CONFIG["output_file"], "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"报告已生成: {CONFIG['output_file']}")

if __name__ == "__main__":
    main()