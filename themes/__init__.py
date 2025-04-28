from typing import List, Dict, Any
from .default import theme as default_theme
from .dark import theme as dark_theme
from .green import theme as green_theme
from .classic import theme as classic_theme

THEMES = {
    "default": default_theme,
    "dark": dark_theme,
    "green": green_theme,
    "classic": classic_theme
}

def get_theme(theme_name: str) -> Dict[str, Any]:
    """获取指定主题配置"""
    return THEMES.get(theme_name, default_theme)
