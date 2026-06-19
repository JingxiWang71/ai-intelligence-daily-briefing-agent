"""
01b_news_searcher.py

功能：
1. 通过 Google News RSS 自动搜索 AI 相关新闻
2. 无需手动维护 RSS 源列表
3. 输出格式与 01_news_collector.py 完全一致（raw_news.json）

与 01_news_collector.py 的关系：
- 两者输出相同格式的 raw_news.json
- 可以二选一使用，也可以合并使用
- 推荐先用 01b 做主力，01 做补充

原理：
Google News 提供主题搜索 RSS，格式为：
  https://news.google.com/rss/search?q=KEYWORD&hl=en-US&gl=US&ceid=US:en

支持多个搜索关键词，自动去重合并。
"""

import feedparser
import json
import hashlib
from urllib.parse import quote

# =========================================================
# 搜索配置
# =========================================================

# 搜索关键词列表（可自由添加）
# 每条关键词会生成一个 Google News RSS 搜索
SEARCH_QUERIES = [
    "artificial intelligence",           # 英文主关键词
    "AI startup funding",                # AI 融资
    "OpenAI OR Anthropic OR Google AI",  # 头部公司动态
    "large language model",              # 大模型
    "AI regulation policy",              # AI 监管
    "NVIDIA AI chip",                    # AI 芯片
    "machine learning breakthrough",     # 技术突破
]

# 每条关键词最多取几条新闻
MAX_PER_QUERY = 10

# 输出路径（与 01_news_collector.py 保持一致）
OUTPUT_PATH = "data/raw_news.json"

# =========================================================
# 构建 Google News RSS URL
# =========================================================

def build_google_news_rss(query: str) -> str:
    """
    构建 Google News RSS 搜索 URL。

    参数：
        query: 搜索关键词（支持 OR、AND 等语法）

    返回：
        Google News RSS 的完整 URL
    """
    encoded = quote(query)
    # hl=en-US: 英文内容
    # gl=US: 美国区域（新闻来源更广）
    # ceid=US:en: 内容语言为英文
    return f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"


# =========================================================
# 新闻去重（基于标题哈希）
# =========================================================

def get_title_hash(title: str) -> str:
    """生成标题的 MD5 哈希，用于去重。"""
    return hashlib.md5(title.strip().lower().encode()).hexdigest()


# =========================================================
# 主流程
# =========================================================

def main():
    all_news = []
    seen_hashes = set()  # 用于去重

    for query in SEARCH_QUERIES:
        print(f"\n搜索: {query}")

        rss_url = build_google_news_rss(query)

        try:
            feed = feedparser.parse(rss_url)
        except Exception as e:
            print(f"  抓取失败: {e}")
            continue

        new_count = 0
        dup_count = 0

        for entry in feed.entries[:MAX_PER_QUERY]:
            title = entry.title.strip()
            title_hash = get_title_hash(title)

            # 去重：同一标题只保留一次
            if title_hash in seen_hashes:
                dup_count += 1
                continue

            seen_hashes.add(title_hash)

            news_item = {
                "source": "google_news",      # 统一标记来源
                "title": title,
                "link": entry.link,
                "published": entry.get("published", ""),
                # 新增：记录匹配到的关键词（方便追溯为什么抓到这条）
                "matched_query": query,
            }

            all_news.append(news_item)
            new_count += 1

        print(f"  新: {new_count} | 去重: {dup_count}")

    # =========================================================
    # 保存（与 01_news_collector.py 完全相同的格式）
    # =========================================================

    print(f"\n{'='*40}")
    print(f"总计: {len(all_news)} 条（来自 {len(SEARCH_QUERIES)} 个搜索）")
    print(f"{'='*40}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

    print(f"已保存: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
