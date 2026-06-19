"""
04_article_cleaner.py

功能：

1. 读取 article_news.json
2. 清理正文
3. 截断过长内容
4. 保存 article_cleaned.json
"""

import json

MAX_LENGTH = 1500

# ======================
# 读取数据
# ======================

with open(
    "data/article_news.json",
    "r",
    encoding="utf-8"
) as f:

    news_list = json.load(f)

# ======================
# 清洗正文
# ======================

for news in news_list:

    article = news.get("article", "")

    # 去除多余空格
    article = article.strip()

    # 截断
    article = article[:MAX_LENGTH]

    news["clean_article"] = article

# ======================
# 保存结果
# ======================

with open(
    "data/article_cleaned.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        news_list,
        f,
        ensure_ascii=False,
        indent=2
    )

print("完成")