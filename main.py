from typing import Dict, Any
from config import CONFIG
from fetchers import get_fetcher
from utils.html_generator import HTMLGenerator

def main():
    data = {}

    # 根据配置获取数据
    for source_name, enabled in CONFIG["sources"].items():
        if enabled:
            fetcher = get_fetcher(source_name, CONFIG.get(source_name, {}))
            data[source_name] = fetcher.fetch()

    # 生成HTML
    generator = HTMLGenerator(CONFIG)
    html_content = generator.generate(data)

    # 写入文件
    with open(CONFIG["output_file"], "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"报告已生成: {CONFIG['output_file']}")

if __name__ == "__main__":
    main()
