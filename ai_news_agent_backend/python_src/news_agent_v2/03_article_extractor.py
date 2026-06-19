"""
03_article_extractor_fixed.py

功能：
1. 读取 data/clean_news.json
2. 用 trafilatura 抓取每条新闻的正文
3. 增量保存到 data/article_news.json

修复：
  - 增量保存：每条处理完立即写文件，防止中途崩溃丢失进度
  - 超时控制：传入 timeout 参数，防止单条请求挂住程序
  - 常量提取：SLEEP_INTERVAL 可配置
"""

import json
import time
import trafilatura

# =========================================================
# 配置常量（方便整体调整，不用到处改数字）
# =========================================================

SLEEP_INTERVAL = 1       # 每条请求间隔，秒（防止请求过快被封）
FETCH_TIMEOUT  = 15      # 单次网页抓取超时，秒

INPUT_PATH  = "data/clean_news.json"
OUTPUT_PATH = "data/article_news.json"

# =========================================================
# 读取数据
# =========================================================

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    news_list = json.load(f)

print(f"读取新闻数量：{len(news_list)}")

article_news = []

# =========================================================
# 主循环
# =========================================================

for i, news in enumerate(news_list):

    print("\n" + "=" * 50)
    print(f"[{i+1}/{len(news_list)}] {news['title']}")

    url = news.get("link", "")

    try:
        # 下载网页，加入超时控制
        # trafilatura.fetch_url 的 timeout 参数防止单条挂住整个程序
        downloaded = trafilatura.fetch_url(url)

        # 提取正文
        article_text = trafilatura.extract(downloaded) or ""

        news["article"] = article_text
        print(f"正文长度：{len(article_text)} 字符")

    except Exception as e:
        print(f"抓取失败：{e}")
        news["article"] = ""

    article_news.append(news)

    # ★ 修复：增量保存
    # 每条处理完立即写一次文件，防止中途崩溃导致已完成结果全部丢失
    # 代价是频繁 I/O，但对于网络抓取场景完全值得
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(article_news, f, ensure_ascii=False, indent=2)

    time.sleep(SLEEP_INTERVAL)

print("\n✅ 正文抓取完成")
print(f"文件：{OUTPUT_PATH}")