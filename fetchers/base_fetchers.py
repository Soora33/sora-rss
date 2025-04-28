import requests
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from typing import Union

class BaseFetcher(ABC):
    """所有数据获取器的基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def fetch(self) -> List[Any]:
        """获取数据的方法，子类必须实现"""
        pass

def _make_request(self, url: str, headers: Dict[str, str] = None, params: Dict[str, Any] = None) -> Union[Dict[str, Any], str]:
    """发送HTTP请求的通用方法"""
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"  # 明确要求JSON响应
    }

    if headers:
        default_headers.update(headers)

    try:
        response = requests.get(url, headers=default_headers, params=params)
        response.raise_for_status()

        # 根据Content-Type决定返回类型
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            return response.json()
        return response.text
    except Exception as e:
        print(f"请求失败: {url}, 错误: {e}")
        return None

