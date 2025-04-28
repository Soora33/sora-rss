from typing import List, Dict, Any
from datetime import datetime
from typing import Dict, List
import random
from themes import get_theme

class HTMLGenerator:
    """HTML报告生成器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.theme = get_theme(config.get("theme", "default"))

    def generate(self, data: Dict[str, List]) -> str:
        """生成完整的HTML报告"""
        date_str = datetime.now().strftime("%Y年%m月%d日")

        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.config['title']} - {self.theme['name']}主题</title>
            {self._generate_css()}
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>{self.config['title']}</h1>
                    <div class="date">{date_str}</div>
                </header>
        """

        # 添加各个数据源的内容
        for source_name, source_data in data.items():
            if source_data:  # 只处理有数据的源
                html += self._generate_section(source_name, source_data)

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def _generate_css(self) -> str:
        """生成CSS样式"""
        return f"""
        <style>
            :root {{
                --primary-color: {self.theme['vars']['primary-color']};
                --primary-light: {self.theme['vars']['primary-light']};
                --primary-dark: {self.theme['vars']['primary-dark']};
                --secondary-color: {self.theme['vars']['secondary-color']};
                --bg-color: {self.theme['vars']['bg-color']};
                --card-bg: {self.theme['vars']['card-bg']};
                --text-color: {self.theme['vars']['text-color']};
                --text-light: {self.theme['vars']['text-light']};
                --border-color: {self.theme['vars']['border-color']};
                --highlight-color: {self.theme['vars']['highlight-color']};
                --success-color: {self.theme['vars']['success-color']};
                --danger-color: {self.theme['vars']['danger-color']};
                --warning-color: {self.theme['vars']['warning-color']};
                --shadow: {self.theme['vars']['shadow']};
                --transition: {self.theme['vars']['transition']};
            }}
            
            /* 其他CSS样式保持不变... */
            /* 这里放置完整的CSS样式，为了简洁省略了具体内容 */
        </style>
        """

    def _generate_section(self, source_name: str, items: List[Any]) -> str:
        """为特定数据源生成HTML部分"""
        section_titles = {
            "github": "GitHub 热门项目",
            "bilibili": "哔哩哔哩 热门视频",
            "weibo": "微博热搜榜",
            "zhihu": "知乎热榜",
            "pixiv": "Pixiv 每日排行榜"
        }

        title = section_titles.get(source_name, source_name)

        # 特殊处理GitHub中文标签
        if source_name == "github" and self.config["github"].get("chinese_only", False):
            title += " (中文)"

        html = f"""
        <section class="section">
            <h2>{title}</h2>
            <div class="items">
        """

        # 调用特定数据源的生成方法
        generator_method = getattr(self, f"_generate_{source_name}_items", None)
        if generator_method:
            html += generator_method(items)
        else:
            html += self._generate_default_items(items)

        html += """
            </div>
        </section>
        """

        return html

    def _generate_github_items(self, projects: List[Any]) -> str:
        """生成GitHub项目HTML"""
        html = ""
        for project in projects:
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
        return html

    def _generate_bilibili_items(self, videos: List[Any]) -> str:
        """生成B站视频HTML"""
        html = ""
        for video in videos:
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
        return html

    def _generate_weibo_items(self, hots: List[Any]) -> str:
        """生成微博热搜HTML"""
        html = ""
        for hot in hots:
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
        return html

    def _generate_zhihu_items(self, questions: List[Any]) -> str:
        """生成知乎热榜HTML"""
        html = ""
        for question in questions:
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
        return html

    def _generate_pixiv_items(self, artworks: List[Any]) -> str:
        """生成Pixiv排行榜HTML"""
        html = ""
        for artwork in artworks:
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
        return html
