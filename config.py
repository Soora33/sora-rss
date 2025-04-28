# 配置文件 - 包含所有可配置项
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
