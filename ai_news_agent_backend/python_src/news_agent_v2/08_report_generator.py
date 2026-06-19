"""
08_report_generator.py

功能：
1. 读取 data/summarized_news.json
2. 将所有数据转换为前端友好的结构
3. 生成统计概览、分类聚合、投资信号面板等
4. 输出 data/report.json

设计原则：
- 纯数据转换，不调用任何 API（速度快、可重复执行）
- 输出 Schema 与前端的 TypeScript 接口一一对应
- 包含完整的元信息，前端无需二次计算
"""

import json
import re
from collections import Counter
from datetime import datetime, timezone

INPUT_PATH  = "data/summarized_news.json"
OUTPUT_PATH = "data/report.json"

# =========================================================
# 投资信号 → 中文标签映射
# =========================================================

SIGNAL_LABELS = {
    "bullish": "利好信号",
    "bearish": "利空信号",
    "neutral": "中性信号",
    "watch": "值得观望"
}

# =========================================================
# 工具函数
# =========================================================

def extract_keywords(titles: list, top_n: int = 10) -> list:
    """
    从标题列表中提取高频关键词。

    使用简单的分词策略：提取长度 >= 3 的英文单词和连续中文字符。
    过滤常见停用词。

    参数：
        titles: 新闻标题列表
        top_n:  返回前 N 个关键词

    返回：
        关键词字符串列表
    """
    stopwords = {
        "the", "and", "for", "are", "but", "not", "you",
        "all", "can", "had", "her", "was", "one", "our",
        "out", "day", "get", "has", "him", "his", "how",
        "man", "new", "now", "old", "see", "two", "way",
        "who", "boy", "did", "its", "let", "put", "say",
        "she", "too", "use", "with", "have", "this", "will",
        "your", "from", "they", "know", "want", "been",
        "good", "much", "some", "time", "very", "when",
        "come", "here", "just", "like", "long", "make",
        "many", "over", "such", "take", "than", "them",
        "well", "were", "what", "发布", "表示", "认为",
        "进行", "通过", "已经", "开始", "可以", "公司",
        "一个", "没有", "成为", "得到", "需要", "关于"
    }

    word_counts = Counter()

    for title in titles:
        # 提取英文单词（长度 >= 3）
        words = re.findall(r'[a-zA-Z]{3,}', title.lower())
        for w in words:
            if w not in stopwords:
                word_counts[w] += 1

        # 提取连续中文字符（长度 >= 2）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', title)
        for w in chinese_words:
            if w not in stopwords:
                word_counts[w] += 1

    return [word for word, _ in word_counts.most_common(top_n)]


def generate_daily_digest(ai_news: list) -> dict:
    """
    生成每日摘要：一句话总结 + Top 3 新闻 + 市场情绪。

    算法：
    - 头条：取 importance 最高的一条新闻的 key_takeaway
    - Top 3：按 importance 降序取前 3 条的标题
    - 市场情绪：统计投资信号，取多数派
    """
    if not ai_news:
        return {
            "headline": "今日无 AI 产业重要新闻",
            "top_stories": [],
            "market_sentiment": "neutral"
        }

    # 按重要性降序排列
    sorted_news = sorted(ai_news, key=lambda x: x["analysis"]["importance"], reverse=True)

    # 头条：重要性最高新闻的核心观点
    top_story = sorted_news[0]
    headline = top_story.get("summary", {}).get(
        "key_takeaway",
        f"{top_story['title'][:40]}..."
    )

    # Top 3 新闻标题
    top_stories = [n["title"] for n in sorted_news[:3]]

    # 市场情绪：投资信号的多数派
    signals = [
        n.get("summary", {}).get("investment_signal", "neutral")
        for n in ai_news if not n.get("summary", {}).get("skipped", False)
    ]
    if signals:
        market_sentiment = Counter(signals).most_common(1)[0][0]
    else:
        market_sentiment = "neutral"

    return {
        "headline": headline,
        "top_stories": top_stories,
        "market_sentiment": market_sentiment
    }


# =========================================================
# 主流程
# =========================================================

def main():
    print("开始生成报告...")

    # 1. 读取 Step 7 输出
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        news_list = json.load(f)

    total = len(news_list)

    # 2. 分离 AI 新闻和非 AI 新闻
    ai_news = [n for n in news_list if n.get("analysis", {}).get("is_ai_news", False)]
    non_ai_news = [n for n in news_list if not n.get("analysis", {}).get("is_ai_news", False)]

    ai_count = len(ai_news)
    non_ai_count = len(non_ai_news)

    print(f"总新闻: {total} | AI 新闻: {ai_count} | 非 AI: {non_ai_count}")

    # 3. 生成统计概览
    # 3.1 分类分布
    categories = Counter(n["analysis"]["category"] for n in ai_news)

    # 3.2 重要性分布
    importance_dist = Counter(str(n["analysis"]["importance"]) for n in ai_news)

    # 3.3 投资信号分布（仅统计有评述的）
    analyzed_news = [
        n for n in ai_news
        if not n.get("summary", {}).get("skipped", False)
    ]
    signals = Counter(n["summary"]["investment_signal"] for n in analyzed_news)
    signal_dist = dict(signals)

    # 3.4 技术趋势分布
    trends = Counter(n["summary"]["tech_trend"] for n in analyzed_news)

    # 3.5 高频关键词
    keywords = extract_keywords([n["title"] for n in ai_news])

    # 4. 按分类组织新闻卡片
    category_groups = []
    for cat_name in sorted(categories.keys()):
        cat_news = [n for n in ai_news if n["analysis"]["category"] == cat_name]

        cards = []
        for idx, n in enumerate(cat_news):
            summary_data = n.get("summary", {})
            summary_obj = None

            # 只有成功评述的新闻才有 summary 对象
            if not summary_data.get("skipped", False):
                summary_obj = {
                    "key_takeaway": summary_data.get("key_takeaway", ""),
                    "industry_impact": summary_data.get("industry_impact", {
                        "short_term": "", "long_term": ""
                    }),
                    "investment_signal": summary_data.get("investment_signal", "neutral"),
                    "tech_trend": summary_data.get("tech_trend", "mature"),
                    "competitive_landscape": summary_data.get("competitive_landscape", ""),
                    "actionable_insights": summary_data.get("actionable_insights", [])
                }

            cards.append({
                "id": idx + 1,
                "title": n["title"],
                "source": n["source"],
                "link": n["link"],
                "published": n.get("published", ""),
                "importance": n["analysis"]["importance"],
                "category": n["analysis"]["category"],
                "compressed_article": n.get("compressed_article", ""),
                "reason": n["analysis"]["reason"],
                "summary": summary_obj
            })

        # 按重要性降序排列
        cards.sort(key=lambda x: x["importance"], reverse=True)

        category_groups.append({
            "category": cat_name,
            "count": len(cards),
            "news": cards
        })

    # 5. 按重要性排序的精选新闻（用于"重要"Tab）
    all_ai_cards = []
    for n in ai_news:
        summary_data = n.get("summary", {})
        all_ai_cards.append({
            "id": len(all_ai_cards) + 1,
            "title": n["title"],
            "source": n["source"],
            "link": n["link"],
            "importance": n["analysis"]["importance"],
            "category": n["analysis"]["category"],
            "key_takeaway": summary_data.get("key_takeaway", "") if not summary_data.get("skipped") else "",
            "investment_signal": summary_data.get("investment_signal", "neutral") if not summary_data.get("skipped") else "neutral"
        })

    # 按重要性降序，importance 相同的按 id 排序
    all_ai_cards.sort(key=lambda x: (-x["importance"], x["id"]))

    # 只保留 importance >= 3 的
    featured = [c for c in all_ai_cards if c["importance"] >= 3]

    # 6. 投资信号面板（用于"投资"Tab）
    signal_groups = []
    for signal in ["bullish", "bearish", "watch", "neutral"]:
        signal_news = [c for c in all_ai_cards if c["investment_signal"] == signal]
        if signal_news:
            signal_groups.append({
                "signal": signal,
                "label": SIGNAL_LABELS.get(signal, signal),
                "count": len(signal_news),
                "news": signal_news
            })

    # 7. 每日摘要
    daily_digest = generate_daily_digest(ai_news)

    # 8. 时间范围（从 published 字段提取）
    dates = [n.get("published", "") for n in news_list if n.get("published")]

    # 9. 组装最终报告
    report = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_news": total,
            "ai_news_count": ai_count,
            "date_range": {
                "start": dates[0] if dates else "",
                "end": dates[-1] if dates else ""
            }
        },
        "overview": {
            "category_distribution": dict(categories),
            "importance_distribution": dict(importance_dist),
            "signal_distribution": signal_dist,
            "trend_distribution": dict(trends),
            "top_keywords": keywords
        },
        "daily_digest": daily_digest,
        "categories": category_groups,
        "featured": featured,
        "investment_signals": signal_groups
    }

    # 10. 保存
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print("报告生成完成")
    print(f"文件: {OUTPUT_PATH}")
    print(f"AI 新闻: {ai_count} 条")
    print(f"分类数: {len(categories)}")
    print(f"精选新闻: {len(featured)} 条")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()