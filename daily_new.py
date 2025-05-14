import os
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
# (数据模型部分保持不变)
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
    published_date: str  # 新增发布时间字段

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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]
def get_random_user_agent():
    """随机获取一个User-Agent"""
    return random.choice(USER_AGENTS)

# =============== 数据获取函数 ===============
# (数据获取函数保持不变 - 来源于你提供的文件)
def fetch_github_trending(limit: int = 10, chinese_only: bool = False) -> List[GithubProject]:
    """获取GitHub热门项目"""
    if chinese_only:
        url = "https://github.com/trending?since=daily&spoken_language_code=zh"
    else:
        url = "https://github.com/trending?since=daily"
    try:
        headers = {"User-Agent": get_random_user_agent()}  # 修改为随机User-Agent
        response = requests.get(url, headers=headers)
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
        headers = {"User-Agent": get_random_user_agent()}  # 修改为随机User-Agent
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        videos = []
        video_list = data.get("data", {}).get("list", [])
        if not video_list:
            video_list = data.get("data", [])
        for item in video_list[:limit]:
            owner = item.get("owner", {})
            stat = item.get("stat", {})
            # 获取发布时间并格式化
            pub_timestamp = item.get("pubdate", 0)
            published_date = datetime.fromtimestamp(pub_timestamp).strftime("%Y-%m-%d")
            video = BilibiliVideo(
                title=item.get("title", "无标题"),
                url=f"https://www.bilibili.com/video/{item.get('bvid', '')}" if item.get('bvid') else item.get("short_link_v2", "#"),
                cover=item.get("pic", "").replace("http://", "https://"),
                up_name=owner.get("name", "未知UP主"),
                up_url=f"https://space.bilibili.com/{owner.get('mid', '')}" if owner.get('mid') else "#",
                duration=format_duration(item.get("duration", 0)),
                views=format_number(stat.get("view", 0)),
                danmaku=format_number(stat.get("danmaku", 0)),
                published_date=published_date  # 存储格式化后的时间
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
        headers = {
            "User-Agent": get_random_user_agent(),  # 修改为随机User-Agent
            # "Cookie": "YOUR_WEIBO_COOKIE" # 如果需要登录信息
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        hot_list = []
        # 实时热搜
        realtime_data = data.get("data", {}).get("realtime", [])
        for idx, item in enumerate(realtime_data[:limit], 1):
            # 处理热度值
            hot_score = item.get("raw_hot", "") # 优先用 raw_hot
            if not hot_score:
                hot_score = item.get("num", "") # 备选 num
            if isinstance(hot_score, int):
                hot_score = format_number(hot_score)
            elif isinstance(hot_score, str) and '万' in hot_score: # 如果已经是带万的字符串
                pass # 保持原样
            elif isinstance(hot_score, str): # 尝试转换纯数字字符串
                try: hot_score = format_number(int(hot_score))
                except: pass # 无法转换则保持原样
            # 处理标签
            label = item.get("label_name", "") # 使用 label_name
            # label_map 在 HTML 生成部分处理
            word = item.get("word", "无标题") # 使用 word
            # 优化 URL 获取逻辑
            search_url = item.get("scheme", "") # 优先使用 scheme (通常是 m.weibo.cn 链接)
            if not search_url:
                encoded_word = requests.utils.quote(word)
                search_url = f"https://s.weibo.com/weibo?q=%23{encoded_word}%23" # 备选话题链接
            hot_list.append(WeiboHot(
                title=word,
                url=search_url,
                rank=idx, # rank 仍然获取，但在 HTML 中不显示
                hot_score=hot_score or "N/A",
                label=label
            ))
        return hot_list[:limit]
    except Exception as e:
        print(f"获取微博热搜失败: {e}")
        return []

def fetch_zhihu_hot(limit: int = 10, category: str = "hot") -> List[ZhihuQuestion]:
    """获取知乎热榜"""
    url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
    headers = {"User-Agent": get_random_user_agent()}  # 修改为随机User-Agent
    try:
        questions = []
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response.raise_for_status()
            data = response.json()
            for item in data.get("data", [])[:limit]:
                target = item.get("target", {})
                question_id = target.get('id')
                question_url = f"https://www.zhihu.com/question/{question_id}" if question_id else "#"
                hot_score_text = item.get("detail_text", "") # 获取热度文本
                hot_score = hot_score_text.replace(" 热度", "").strip() # 清理
                questions.append(ZhihuQuestion(
                    title=target.get("title", "无标题"),
                    url=question_url,
                    hot_score=hot_score or "N/A", # 处理空值
                    answer_count=target.get("answer_count", 0),
                    follower_count=target.get("follower_count", 0)
                ))
        # 添加了网页解析的备选方案 (来自上一版，但保留以防 API 失效)
        if not questions:
            print("API获取知乎热榜失败，尝试解析网页...")
            web_url = "https://www.zhihu.com/billboard"
            web_response = requests.get(web_url, headers=headers)
            web_response.raise_for_status()
            soup = BeautifulSoup(web_response.text, 'html.parser')
            script_tag = soup.find('script', id='js-initialData')
            if script_tag:
                json_data = json.loads(script_tag.string)
                hot_list = json_data.get("initialState", {}).get("topstory", {}).get("hotList", [])
                for item in hot_list[:limit]:
                    card_id = item.get("cardId", "")
                    question_id_match = re.search(r'Question-(\d+)', card_id)
                    if question_id_match:
                        question_id = question_id_match.group(1)
                        target = item.get("target", {})
                        metrics_text = target.get("metricsArea", {}).get("text", "N/A").replace(" 热度", "").strip()
                        questions.append(ZhihuQuestion(
                            title=target.get("titleArea", {}).get("text", "无标题"),
                            url=f"https://www.zhihu.com/question/{question_id}",
                            hot_score=metrics_text,
                            answer_count=0,
                            follower_count=0
                        ))
        return questions[:limit]
    except Exception as e:
        print(f"获取知乎热榜失败: {e}")
        return []

def fetch_pixiv_ranking(limit: int = 10, mode: str = "daily") -> List[PixivArtwork]:
    """获取Pixiv排行榜 (包含本地缓存)"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    image_dir = os.path.join("images", date_str)
    try:
        os.makedirs(image_dir, exist_ok=True)
        url = f"https://www.pixiv.net/ranking.php?mode={mode}"
        headers = {
            "User-Agent": get_random_user_agent(),  # 修改为随机User-Agent
            "Referer": "https://www.pixiv.net/"
        }
        # 优先尝试解析网页中的 JSON 数据
        print(f"尝试解析 Pixiv 网页: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        pattern = re.compile(r'window.__INITIAL_STATE__\s*=\s*({.*?})\s*;?\s*</script>', re.DOTALL)
        match = pattern.search(response.text)
        illusts = []
        if match:
            print("成功匹配到网页内 JSON 数据。")
            data = json.loads(match.group(1))
            # 提取插画信息，需要适配可能的层级结构
            # (根据实际观察到的结构调整路径)
            illust_items = data.get("ranking", {}).get("ranking", []) # 尝试路径 1
            if not illust_items:
                illust_items = data.get("illusts", []) # 尝试路径 2
            for item in illust_items[:limit]:
                # 提取需要的信息
                illust_id = item.get("illustId")
                if illust_id:
                    illusts.append(item) # 如果结构匹配，添加到列表中
        else:
            # 备用方案：使用 API 接口 (如果网页解析失败)
            print("网页解析失败，尝试备用 API 接口...")
            api_url = f"https://www.pixiv.net/ranking.php?mode={mode}&format=json"
            api_response = requests.get(api_url, headers=headers)
            api_response.raise_for_status()
            data = api_response.json()
            illusts = data.get("contents", [])[:limit] # API 接口结构通常是 contents
        # 下载图片函数
        def download_image(img_url, img_path):
            if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                return True
            try:
                response = requests.get(img_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    with open(img_path, 'wb') as f:
                        f.write(response.content)
                    return True
            except Exception as e:
                print(f"下载图片失败 {img_url}: {e}")
                return False
        artworks = []
        for item in illusts:
            illust_id = item.get("illust_id", item.get("illustId", ""))
            if not illust_id:
                continue
            # 构建本地路径
            image_path = os.path.join(image_dir, f"{illust_id}.jpg")
            # 使用本地代理可能导致图片无法正常下载，改用原始图片链接
            original_url = item.get("url", "")  # 这里需要获取原始大图地址
            if not download_image(original_url, image_path):
                image_path = ""  # 下载失败时保留空路径
            artworks.append(PixivArtwork(
                title=item.get("title", "无标题"),
                url=f"https://www.pixiv.net/artworks/{illust_id}",
                image_url=image_path or "/static/placeholder.jpg",  # 提供默认占位图
                author=item.get("user_name", "未知作者"),
                author_url=f"https://www.pixiv.net/users/{item.get('user_id', '')}",
                width=item.get("width", 0),
                height=item.get("height", 0),
                bookmarks=item.get("bookmarks", 0)
            ))
        return artworks
    except Exception as e:
        print(f"获取Pixiv排行榜失败: {e}")
        return []


# =============== 辅助函数 ===============
# (辅助函数保持不变 - 来源于你提供的文件)
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
    try:
        seconds = int(seconds)
    except (ValueError, TypeError):
        return "00:00" # 处理无效输入
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

# =============== HTML生成函数 (修改版) ===============
def generate_html(data: Dict[str, List], config: Dict) -> str:
    """生成HTML报告"""
    date_str = datetime.now().strftime("%Y年%m月%d日") # 使用你文件中的日期格式

    theme = config.get("theme", "default")

    # --- 主题配置 (使用你文件中的配置) ---
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
    theme_vars = selected_theme["vars"] # 获取变量字典

    # --- CSS样式 (修改版) ---
    css = f"""
    <style>
        :root {{
            --primary-color: {theme_vars["primary-color"]};
            --primary-light: {theme_vars["primary-light"]};
            --primary-dark: {theme_vars["primary-dark"]};
            --secondary-color: {theme_vars["secondary-color"]};
            --bg-color: {theme_vars["bg-color"]};
            --card-bg: {theme_vars["card-bg"]};
            --text-color: {theme_vars["text-color"]};
            --text-light: {theme_vars["text-light"]};
            --border-color: {theme_vars["border-color"]};
            --highlight-color: {theme_vars["highlight-color"]};
            --success-color: {theme_vars["success-color"]};
            --danger-color: {theme_vars["danger-color"]};
            --warning-color: {theme_vars["warning-color"]};
            --shadow: {theme_vars["shadow"]};
            --transition: {theme_vars["transition"]};
            --bg-image: {theme_vars["bg-image"]}; /* 添加背景图像变量 */
            --header-bg: {theme_vars["header-bg"]}; /* 添加header背景变量 */
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
            padding: 20px 0; /* 在 body 上加垂直 padding */
            background-color: var(--bg-color); /* 使用背景色 */
            background-image: var(--bg-image); /* 使用背景图像 */
            color: var(--text-color);
            min-height: 100vh;
            background-attachment: fixed; /* 固定背景 */
            background-size: cover; /* 覆盖整个视口 */
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px; /* 容器左右 padding */
        }}

        header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
            background: var(--header-bg); /* 使用 header 背景变量 */
            border-radius: 10px;
            backdrop-filter: blur(8px); /* 轻微模糊效果 */
            /* 移除 position: sticky */
        }}

        h1 {{
            color: var(--primary-dark);
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .date {{
            color: var(--text-light); /* 使用浅色文本 */
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
            backdrop-filter: blur(5px); /* 卡片背景模糊 */
            overflow: hidden; /* 防止内部元素溢出 */
        }}

        h2 {{
            color: var(--primary-dark);
            font-size: 1.6rem; /* 稍微增大标题 */
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--primary-light); /* 使用浅主色调 */
            display: flex;
            align-items: center;
            gap: 10px; /* emoji 和文字间距 */
            font-weight: 500; /* 字体稍细 */
        }}
         h2 .emoji {{ /* 为 emoji 添加样式 */
            font-size: 1.3em; /* 让 emoji 稍微大一点 */
            display: inline-block;
            line-height: 1;
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
            height: 100%; /* 确保项目高度一致 */
            position: relative; /* 用于可能的绝对定位子元素 */
            overflow: hidden; /* 防止内容溢出 */
        }}

        .item:hover {{
            transform: translateY(-5px) scale(1.01); /* 悬停效果微调 */
            box-shadow: 0 8px 20px {theme_vars["primary-light"].replace('0.2', '0.3')}; /* 悬停阴影加深 */
            border-color: var(--primary-color);
        }}

        /* GitHub项目样式 (保持不变) */
        .github-item {{ }}
        .github-item h3 {{
            font-size: 1.1rem; margin-bottom: 10px; line-height: 1.4;
            display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
            overflow: hidden; text-overflow: ellipsis; color: var(--text-color);
        }}
        .github-item p {{
            color: var(--text-light); font-size: 0.9rem; margin-bottom: 12px; flex-grow: 1;
            display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
            overflow: hidden; text-overflow: ellipsis;
        }}
        .github-item .meta {{
            display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-top: auto;
            border-top: 1px solid var(--border-color); padding-top: 10px; /* 添加分隔线 */
        }}
        .github-item .language {{
            display: inline-flex; align-items: center; padding: 3px 10px;
            background: var(--primary-light); border-radius: 20px; font-size: 0.8rem;
            color: var(--primary-color); font-weight: 500;
        }}
        .github-item .stats {{
            display: flex; gap: 12px; font-size: 0.8rem; color: var(--text-light);
            margin-left: auto; /* 推到右边 */
        }}

        /* B站视频样式 (保持不变) */
        .bilibili-item {{ display: flex; gap: 15px; }}
        .bilibili-cover-link {{ display: block; flex-shrink: 0;}} /* 包裹图片链接 */
        .bilibili-cover {{
            width: 120px; height: 80px; object-fit: cover; border-radius: 8px;
            transition: var(--transition); display: block;
        }}
        .bilibili-item:hover .bilibili-cover {{ transform: scale(1.05); }}
        .bilibili-info {{ flex: 1; display: flex; flex-direction: column; }}
        .bilibili-info h3 {{
            font-size: 1rem; margin-bottom: 8px; line-height: 1.4;
            display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
            overflow: hidden; text-overflow: ellipsis; color: var(--text-color);
        }}
        .up-name {{ color: var(--text-light); font-size: 0.85rem; margin-bottom: 8px; }}
        .bilibili-stats {{
            display: flex; flex-wrap: wrap; gap: 12px; font-size: 0.8rem; color: var(--text-light);
            margin-top: auto; border-top: 1px solid var(--border-color); padding-top: 8px; /* 分隔线 */
        }}
        .bilibili-stats span {{ display: inline-flex; align-items: center; gap: 4px; }} /* 图标和文字间距 */

        /* --- 微博热搜样式 (修改) --- */
        .weibo-item {{
            padding: 15px;
            border-radius: 8px;
            /* background: var(--card-bg); /* 统一背景在 .item */
            transition: var(--transition);
            display: flex; /* 使用 flex 布局 */
            flex-direction: column;
        }}

        .weibo-content {{ /* 容器 */
             display: flex;
             flex-direction: column;
             flex-grow: 1; /* 占据剩余空间 */
        }}

        .weibo-content h3 {{ /* 标题部分 */
            font-size: 1.05rem; /* 稍大一点 */
            margin-bottom: 10px; /* 增加标题和下方间距 */
            color: var(--text-color);
            font-weight: 500; /* 字体调整 */
            line-height: 1.45;
             display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; /* 最多3行 */
             overflow: hidden; text-overflow: ellipsis;
        }}
        .weibo-content h3 a {{ color: inherit; text-decoration: none; }} /* 继承颜色 */
        .weibo-content h3 a:hover {{ color: var(--primary-color); }}

        .weibo-meta {{ /* 热度和标签容器 */
            display: flex;
            align-items: center;
            gap: 8px; /* 热度和标签间距 */
            margin-top: auto; /* 推到底部 */
            padding-top: 10px; /* 与上方内容间距 */
            border-top: 1px solid var(--border-color); /* 分隔线 */
            flex-wrap: wrap; /* 允许换行 */
        }}

        .weibo-hot {{ /* 热度 */
            font-size: 0.9rem;
            color: var(--danger-color);
            font-weight: bold;
            white-space: nowrap; /* 不换行 */
            order: 1; /* 热度靠前 */
        }}
        .weibo-hot::before {{ content: '🔥 '; }}

        .weibo-label {{ /* 标签 */
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 3px;
            color: white;
            text-transform: uppercase;
            font-weight: bold;
            line-height: 1;
            white-space: nowrap;
            order: 2; /* 标签在后 */
        }}
        .weibo-label.hot {{ background-color: var(--warning-color); }}
        .weibo-label.new {{ background-color: var(--success-color); }}
        .weibo-label.boom {{ background-color: var(--danger-color); animation: pulse 1.2s infinite ease-in-out; }}
        .weibo-label.boil {{ background-color: var(--info-color, var(--primary-color)); }} /* Fallback color */
        .weibo-label.recommend {{ background-color: var(--primary-color); }}
        /* --- 微博样式修改结束 --- */

        /* 知乎热榜样式 (保持不变) */
        .zhihu-item {{ padding: 15px; border-radius: 8px; transition: var(--transition); }}
        .zhihu-item h3 {{
            font-size: 1.05rem; /* 稍大 */ margin-bottom: 12px; line-height: 1.4;
            display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
            overflow: hidden; text-overflow: ellipsis; color: var(--text-color);
        }}
         .zhihu-item h3 a {{ color: inherit; text-decoration: none; }}
         .zhihu-item h3 a:hover {{ color: var(--primary-color); }}
        .zhihu-meta {{
            display: flex; justify-content: space-between; align-items: center;
            margin-top: auto; border-top: 1px solid var(--border-color); padding-top: 10px;
        }}
        .zhihu-hot {{
            font-size: 0.9rem; color: var(--danger-color); font-weight: bold;
            background: color-mix(in srgb, var(--danger-color) 10%, transparent); /* 调整混合比例 */
            padding: 3px 8px; border-radius: 10px; white-space: nowrap;
        }}
         .zhihu-hot::before {{ content: '💡 '; }} /* 换个图标 */
        .zhihu-stats {{
            display: flex; gap: 12px; font-size: 0.85rem; color: var(--text-light);
        }}
        .zhihu-stats span {{ display: inline-flex; align-items: center; gap: 4px; }}

        /* Pixiv排行榜样式 (保持不变) */
        .pixiv-item {{ }}
        .pixiv-image-container {{
            position: relative; padding-top: 75%; /* 4:3 ratio */
            overflow: hidden; border-radius: 8px; margin-bottom: 12px;
            background: var(--border-color); /* 占位背景 */
        }}
        .pixiv-image {{
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            object-fit: cover; transition: var(--transition); display: block;
        }}
        .pixiv-item:hover .pixiv-image {{ transform: scale(1.08); filter: brightness(1.1); }}
        .pixiv-title {{
            font-size: 1rem; margin-bottom: 8px; line-height: 1.4;
            display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
            overflow: hidden; text-overflow: ellipsis; color: var(--text-color);
        }}
        .pixiv-title a {{ color: inherit; text-decoration: none; }}
        .pixiv-title a:hover {{ color: var(--primary-color); }}
        .pixiv-author {{ font-size: 0.85rem; color: var(--text-light); margin-bottom: 8px; }}
        .pixiv-author a {{ color: inherit; text-decoration: none; }}
        .pixiv-author a:hover {{ color: var(--primary-color); }}
        .pixiv-stats {{
            display: flex; justify-content: space-between; gap: 12px; font-size: 0.8rem; color: var(--text-light);
            margin-top: auto; border-top: 1px solid var(--border-color); padding-top: 8px;
        }}
         .pixiv-stats span {{ display: inline-flex; align-items: center; gap: 4px; }}

        /* 链接样式 (保持不变) */
        a {{ color: var(--text-color); text-decoration: none; transition: var(--transition); }}
        a:hover {{ color: var(--primary-color); text-decoration: underline; }}

        /* 动画效果 (保持不变) */
        @keyframes pulse {{
            0% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.08); opacity: 0.7; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}

        /* 响应式设计 (保持不变) */
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            h1 {{ font-size: 2rem; }}
            h2 {{ font-size: 1.4rem; }}
            .items {{ grid-template-columns: 1fr; gap: 15px; }}
            .bilibili-item {{ flex-direction: column; }}
            .bilibili-cover {{ width: 100%; height: auto; aspect-ratio: 16/9; }}
        }}
         @media (max-width: 480px) {{
             body {{ padding: 10px 0; }}
             .container {{ padding: 0 10px; }}
             h1 {{ font-size: 1.8rem; }}
             h2 {{ font-size: 1.3rem; }}
             .section {{ padding: 15px; }}
             .item {{ padding: 12px; }}
         }}
    </style>
    """

    # --- HTML生成内容 (修改版) ---
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config['title']} - {selected_theme['name']}</title>
        {css}
    </head>
    <body>
        <div class="container">
            <header>
                <h1>{config['title']}</h1>
                <div class="date">{date_str}</div>
            </header>

            <main>
    """

    # GitHub部分
    if config["sources"]["github"] and data.get("github"):
        chinese_label = " (中文)" if config["github"]["chinese_only"] else ""
        html += f"""
        <section class="section github-section">
            <h2><span class="emoji">💻</span> GitHub 热门项目{chinese_label}</h2>
            <div class="items">
        """
        for project in data["github"]:
            html += f"""
            <article class="item github-item">
                <h3><a href="{project.url}" target="_blank" rel="noopener noreferrer">{project.name}</a></h3>
                <p>{project.description}</p>
                <div class="meta">
                    <span class="language">{project.language or 'N/A'}</span>
                    <div class="stats">
                        <span>⭐ {format_number(project.stars)}</span>
                        <span>🍴 {format_number(project.forks)}</span>
                    </div>
                </div>
            </article>
            """
        html += """
            </div>
        </section>
        """
    elif config["sources"]["github"]:
        html += f"""<section class="section github-section"><h2><span class="emoji">💻</span> GitHub 热门项目{chinese_label}</h2><p>未能加载GitHub数据。</p></section>"""


    # B站部分
    if config["sources"]["bilibili"] and data.get("bilibili"):
        html += f"""
        <section class="section bilibili-section">
            <h2><span class="emoji">📺</span> 哔哩哔哩 热门视频</h2>
            <div class="items">
        """
        for video in data["bilibili"]:
            cover_url = video.cover.replace("http://", "https://") if video.cover else ""

            html += f"""
            <article class="item bilibili-item">
                <a href="{video.url}" target="_blank" rel="noopener noreferrer" class="bilibili-cover-link">
                    <img src="{cover_url}" class="bilibili-cover" alt="封面" loading="lazy">
                </a>
                <div class="bilibili-info">
                    <h3><a href="{video.url}" target="_blank" rel="noopener noreferrer">{video.title}</a></h3>
                    <div class="up-name">
                        👨‍🎨 <a href="{video.up_url}" target="_blank" rel="noopener noreferrer">{video.up_name}</a>
                    </div>
                    <div class="bilibili-stats">
                        <span>▶️ {video.views}</span>
                        <span>💬 {video.danmaku}</span>
                        <span>📅 {video.published_date}</span>
                    </div>
                </div>
            </article>
            """
        html += """
            </div>
        </section>
        """
    elif config["sources"]["bilibili"]:
        html += f"""<section class="section bilibili-section"><h2><span class="emoji">📺</span> 哔哩哔哩 热门视频</h2><p>未能加载B站数据。</p></section>"""

    # 微博部分 (修改HTML结构)
    # === 修改微博部分 ===
    if config["sources"]["weibo"] and data.get("weibo"):
        html += f"""
        <section class="section weibo-section">
            <h2><span class="emoji">🔥</span> 微博热搜榜</h2>
            <div class="items">
        """
        for hot in data["weibo"]:
            label_class = {"爆": "boom", "热": "hot", "新": "new", "沸": "boil", "荐": "recommend"}.get(hot.label, "")
            label_html = f'<span class="weibo-label {label_class}">{hot.label}</span>' if label_class else ''

            html += f"""
            <article class="item zhihu-item">  <!-- 使用知乎的样式 -->
                <h3><a href="{hot.url}" target="_blank" rel="noopener noreferrer" title="{hot.title}">{hot.title}</a></h3>
                <div class="zhihu-meta">
                    <div class="zhihu-stats">
                        {label_html}
                    </div>
                    <div class="weibo-hot">{hot.hot_score}</div>
                </div>
            </article>
            """
        html += """
            </div>
        </section>
        """
    elif config["sources"]["weibo"]:
        html += f"""<section class="section weibo-section"><h2><span class="emoji">🔥</span> 微博热搜榜</h2><p>未能加载微博数据。</p></section>"""


    # 知乎部分
    if config["sources"]["zhihu"] and data.get("zhihu"):
        html += f"""
        <section class="section zhihu-section">
            <h2><span class="emoji">💡</span> 知乎热榜</h2>
            <div class="items">
        """
        for question in data["zhihu"]:
            html += f"""
            <article class="item zhihu-item">
                <h3><a href="{question.url}" target="_blank" rel="noopener noreferrer" title="{question.title}">{question.title}</a></h3>
                <div class="zhihu-meta">
                    <div class="zhihu-stats">
                        <span>💬 {format_number(question.answer_count)} 回答</span>
                        <span>👀 {format_number(question.follower_count)} 关注</span>
                    </div>
                    <div class="zhihu-hot">{question.hot_score}</div>
                </div>
            </article>
            """
        html += """
            </div>
        </section>
        """
    elif config["sources"]["zhihu"]:
        html += f"""<section class="section zhihu-section"><h2><span class="emoji">💡</span> 知乎热榜</h2><p>未能加载知乎数据。</p></section>"""

    # === 修改Pixiv部分 ===
    if config["sources"]["pixiv"] and data.get("pixiv"):
        html += f"""
        <section class="section pixiv-section">
            <h2><span class="emoji">🎨</span> Pixiv 排行榜</h2>
            <div class="items">
        """
        for artwork in data["pixiv"]:
            html += f"""
            <article class="item pixiv-item">
                <a href="{artwork.url}" target="_blank" rel="noopener noreferrer" class="pixiv-image-link">
                    <div class="pixiv-image-container">
                        <img src="{artwork.image_url}" class="pixiv-image" alt="{artwork.title}" loading="lazy">
                    </div>
                </a>
                <div class="pixiv-info">
                    <h3 class="pixiv-title">{artwork.title}</h3>
                    <div class="pixiv-author">🎨 {artwork.author}</div>
                    <div class="pixiv-stats">
                        <span>❤️ {format_number(artwork.bookmarks)}</span>
                        <span style="margin-left: auto;">{artwork.width}×{artwork.height}</span>
                    </div>
                </div>
            </article>
            """
        html += """
            </div>
        </section>
        """
    elif config["sources"]["pixiv"]:
        html += f"""<section class="section pixiv-section"><h2><span class="emoji">🎨</span> Pixiv 排行榜</h2><p>未能加载Pixiv数据。</p></section>"""


    html += """
            </main>
            <footer>
                <p style="text-align: center; font-size: 0.85rem; color: var(--text-light); margin-top: 40px; padding: 20px 0; border-top: 1px solid var(--border-color);">
                    Generated by Daily News Aggregator | Theme: {selected_theme['name']}
                </p>
            </footer>
        </div>
    </body>
    </html>
    """

    return html

# =============== 主函数 ===============
# (主函数保持不变 - 来源于你提供的文件)
def main():
    data = {}

    print("开始获取数据...") # 添加打印信息

    # 根据配置获取数据
    if CONFIG["sources"]["github"]:
        print(" - 获取 GitHub 数据...") # 添加打印信息
        data["github"] = fetch_github_trending(
            limit=CONFIG["github"]["limit"],
            chinese_only=CONFIG["github"]["chinese_only"]
        )
        print(f"   > 获取到 {len(data.get('github', []))} 条 GitHub 数据") # 添加打印信息

    if CONFIG["sources"]["bilibili"]:
        print(" - 获取 Bilibili 数据...") # 添加打印信息
        data["bilibili"] = fetch_bilibili_hot(
            limit=CONFIG["bilibili"]["limit"],
            region=CONFIG["bilibili"]["region"]
        )
        print(f"   > 获取到 {len(data.get('bilibili', []))} 条 Bilibili 数据") # 添加打印信息

    if CONFIG["sources"]["weibo"]:
        print(" - 获取 Weibo 数据...") # 添加打印信息
        data["weibo"] = fetch_weibo_hot(
            limit=CONFIG["weibo"]["limit"],
            category=CONFIG["weibo"]["category"]
        )
        print(f"   > 获取到 {len(data.get('weibo', []))} 条 Weibo 数据") # 添加打印信息

    if CONFIG["sources"]["zhihu"]:
        print(" - 获取 Zhihu 数据...") # 添加打印信息
        data["zhihu"] = fetch_zhihu_hot(
            limit=CONFIG["zhihu"]["limit"],
            category=CONFIG["zhihu"]["category"]
        )
        print(f"   > 获取到 {len(data.get('zhihu', []))} 条 Zhihu 数据") # 添加打印信息

    if CONFIG["sources"]["pixiv"]:
        print(" - 获取 Pixiv 数据 (可能较慢或失败)...") # 添加打印信息
        data["pixiv"] = fetch_pixiv_ranking(
            limit=CONFIG["pixiv"]["limit"],
            mode=CONFIG["pixiv"]["mode"]
        )
        print(f"   > 获取到 {len(data.get('pixiv', []))} 条 Pixiv 数据") # 添加打印信息

    print("数据获取完毕, 开始生成HTML...") # 添加打印信息

    # 生成HTML
    html_content = generate_html(data, CONFIG)

    # 写入文件
    output_filename = CONFIG["output_file"]
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"🎉 报告已成功生成: {output_filename}") # 修改打印信息
    except IOError as e:
        print(f"❌ 写入文件失败: {e}") # 添加错误处理打印

if __name__ == "__main__":
    main()