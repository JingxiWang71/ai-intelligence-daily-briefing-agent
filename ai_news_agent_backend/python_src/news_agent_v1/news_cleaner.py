"""
news_cleaner.py

功能：
1. 读取 raw_news.json
2. 基于标题相似度进行去重
3. 输出 clean_news.json

"""

import json

# Python内置库
# 用于计算两个字符串的相似度
from difflib import SequenceMatcher


# ==========================
# 相似度计算函数
# ==========================

def calculate_similarity(text1, text2):
    """
    计算两个标题之间的相似度

    返回值范围：
    0 ~ 1

    1：
    完全相同

    0：
    完全不同
    """

    return SequenceMatcher(
        None,
        text1,
        text2
    ).ratio()


# ==========================
# 读取原始新闻
# ==========================

with open(
    "data/raw_news.json",
    "r",
    encoding="utf-8"
) as f:

    news_list = json.load(f)


# ==========================
# 参数设置
# ==========================

# 相似度阈值

SIMILARITY_THRESHOLD = 0.80

# 保存最终结果

clean_news = []

# 统计被删除数量

duplicate_count = 0


# ==========================
# 开始去重
# ==========================

for current_news in news_list:

    current_title = current_news["title"]

    is_duplicate = False

    # 与已经保留的新闻逐条比较

    for saved_news in clean_news:

        saved_title = saved_news["title"]

        similarity = calculate_similarity(
            current_title,
            saved_title
        )

        # 如果超过阈值

        if similarity >= SIMILARITY_THRESHOLD:

            is_duplicate = True

            duplicate_count += 1

            print(
                f"\n发现相似新闻："
            )

            print(
                f"当前标题：{current_title}"
            )

            print(
                f"已有标题：{saved_title}"
            )

            print(
                f"相似度：{similarity:.2f}"
            )

            break

    # 如果不是重复新闻

    if not is_duplicate:

        clean_news.append(current_news)


# ==========================
# 输出统计信息
# ==========================

print("\n===================")

print(
    f"原始新闻数量: {len(news_list)}"
)

print(
    f"去重后数量: {len(clean_news)}"
)

print(
    f"删除数量: {duplicate_count}"
)

print("===================\n")


# ==========================
# 保存结果
# ==========================

with open(
    "data/clean_news.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        clean_news,
        f,
        ensure_ascii=False,
        indent=2
    )

print(
    "clean_news.json 已保存"
)