from bs4 import BeautifulSoup
from typing import List
from .base_fetchers import BaseFetcher
from models import GithubProject

class GithubFetcher(BaseFetcher):
    """GitHub热门项目获取器"""

    def fetch(self) -> List[GithubProject]:
        """获取GitHub热门项目"""
        if self.config.get("chinese_only", False):
            url = "https://github.com/trending?since=daily&spoken_language_code=zh"
        else:
            url = "https://github.com/trending?since=daily"

        try:
            response = self._make_request(url)
            if not response:
                return []

            soup = BeautifulSoup(response, 'html.parser')
            projects = []

            for repo in soup.select("article.Box-row")[:self.config.get("limit", 10)]:
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
