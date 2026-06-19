import feedparser
import json
from datetime import datetime

RSS_FEEDS = {
    "techcrunch": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "mit": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "reuters":"https://feeds.reuters.com/reuters/technologyNews"
}

all_news = []

for source, url in RSS_FEEDS.items():

    feed = feedparser.parse(url)

    for entry in feed.entries:

        news_item = {
            "source": source,
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", "")
        }

        all_news.append(news_item)

print(f"抓取完成，共获得 {len(all_news)} 条新闻")

with open(
    "data/raw_news.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_news,
        f,
        ensure_ascii=False,
        indent=2
    )

print("已保存到 data/raw_news.json")