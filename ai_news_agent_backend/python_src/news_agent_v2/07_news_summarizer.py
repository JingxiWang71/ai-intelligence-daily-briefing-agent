"""
07_news_summarizer.py

功能：
1. 读取 data/classified_news_v3.json
2. 筛选 AI 相关新闻（is_ai_news = true）
3. 调用 DeepSeek 进行深度评述，引入主观分析维度
4. 输出字段：
   - key_takeaway:        一句话核心观点
   - industry_impact:     行业影响（短期+长期）
   - investment_signal:   投资信号（bullish/bearish/neutral/watch）
   - tech_trend:          技术趋势定位
   - competitive_landscape: 竞争格局变化
   - actionable_insights: 从业者行动建议（3-5条）
5. 增量保存到 data/summarized_news.json

设计原则：
- 只处理 AI 新闻（is_ai_news=true），非 AI 新闻跳过评述
- 使用 JSON Mode 强制合法 JSON 输出
- 继续使用 str.replace() + 自定义占位符，彻底避免 {} 相关问题
"""

import json
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

# =========================================================
# 初始化
# =========================================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

INPUT_PATH  = "data/classified_news_v3.json"
OUTPUT_PATH = "data/summarized_news.json"

# =========================================================
# Prompt 模板
# =========================================================
#
# 设计要点：
# 1. 上下文注入：将 Step 6 已有的分类结果（category、importance、reason）
#    作为上下文一并送入，让模型基于已有客观分析做更深入的主观判断
# 2. 明确的分析框架：每个维度给出简短说明，约束模型不跑题
# 3. 统一输出中文：与 Step 5/6 保持一致
# 4. 枚举值提示：investment_signal 和 tech_trend 给出可选值

SUMMARIZE_PROMPT_TEMPLATE = """你是一位资深的 AI 产业战略分析师，擅长从新闻中提炼深层洞察。

请基于以下新闻信息，提供深度评述分析。要求见解独到、逻辑清晰、有前瞻性。

## 已掌握的客观信息

- 新闻标题：__TITLE__
- 事实摘要：__ARTICLE__
- 新闻分类：__CATEGORY__
- 重要性评分：__IMPORTANCE__/5
- 分类依据：__REASON__

## 请输出以下 6 个维度的分析（严格 JSON 格式）

1. key_takeaway（字符串）：
   一句话概括这条新闻最核心的意义和洞察。要求精准、有信息量，不是标题的重复。

2. industry_impact（对象，包含两个字段）：
   - short_term：未来 1-3 个月内的直接影响（50字以内）
   - long_term：未来 6-12 个月的深层影响（50字以内）

3. investment_signal（字符串，只能选以下之一）：
   bullish（利好）/ bearish（利空）/ neutral（中性）/ watch（值得观望）
   从资本市场角度判断这条新闻对相关赛道的影响方向。

4. tech_trend（字符串，只能选以下之一）：
   emerging（新趋势萌芽）/ accelerating（正在加速）/ mature（趋于成熟）/ declining（走向衰落）
   判断这条新闻所反映的技术方向处于哪个阶段。

5. competitive_landscape（字符串，80字以内）：
   分析这条新闻对行业竞争格局的影响——哪些公司受益、哪些受冲击、市场地位如何变化。

6. actionable_insights（字符串数组，3-5条）：
   给 AI 从业者的具体行动建议。每条以动词开头，简洁有力。

## 输出格式

只输出 JSON，不要任何解释或 markdown：

{
  "key_takeaway": "...",
  "industry_impact": {
    "short_term": "...",
    "long_term": "..."
  },
  "investment_signal": "bullish|bearish|neutral|watch",
  "tech_trend": "emerging|accelerating|mature|declining",
  "competitive_landscape": "...",
  "actionable_insights": ["...", "...", "..."]
}"""


def build_summarize_prompt(title: str, article: str, category: str,
                           importance: int, reason: str) -> str:
    """
    构建深度评述的 Prompt。

    将 Step 6 已有的客观分析结果作为上下文注入，
    让模型在"已知事实"的基础上做更深入的主观判断，
    而不是从零开始分析，这样输出质量更高、更稳定。

    占位符替换顺序不影响结果（各占位符唯一且不重叠）。
    """
    article_text = article.strip() if article else "(无摘要)"

    return (
        SUMMARIZE_PROMPT_TEMPLATE
        .replace("__TITLE__", title)
        .replace("__ARTICLE__", article_text)
        .replace("__CATEGORY__", category)
        .replace("__IMPORTANCE__", str(importance))
        .replace("__REASON__", reason)
    )


# =========================================================
# JSON 解析（复用 Step 6 的经验，继续强化）
# =========================================================

def safe_parse(text: str) -> dict:
    """
    从模型输出中提取并解析 JSON。

    与 Step 6 版本保持一致，确保项目内所有 JSON 解析逻辑统一。
    """
    if not text or not text.strip():
        raise ValueError("模型返回空内容")

    text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            f"输出中未找到 JSON 括号。原始输出（前150字符）: {text[:150]!r}"
        )
    if start > end:
        raise ValueError(
            f"JSON 括号顺序异常。原始输出: {text[:100]!r}"
        )

    json_str = text[start:end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"JSON 解析失败: {e}。提取片段（前200字符）: {json_str[:200]!r}"
        )


# =========================================================
# 字段校验
# =========================================================

VALID_SIGNALS = {"bullish", "bearish", "neutral", "watch"}
VALID_TRENDS  = {"emerging", "accelerating", "mature", "declining"}
REQUIRED_KEYS = {
    "key_takeaway", "industry_impact", "investment_signal",
    "tech_trend", "competitive_landscape", "actionable_insights"
}


def validate_summary(result: dict) -> None:
    """
    校验评述 JSON 的完整性和值的合法性。

    比 Step 6 的校验更复杂，因为字段类型更多（嵌套对象、枚举字符串、数组）。
    """
    # 1. 检查顶层字段
    missing = REQUIRED_KEYS - result.keys()
    if missing:
        raise ValueError(f"缺少字段: {missing}。完整输出: {result}")

    # 2. 校验 investment_signal 枚举值
    signal = result.get("investment_signal")
    if signal not in VALID_SIGNALS:
        raise ValueError(
            f"investment_signal 值不合法: {signal!r}"
            f"（应为: {VALID_SIGNALS}）"
        )

    # 3. 校验 tech_trend 枚举值
    trend = result.get("tech_trend")
    if trend not in VALID_TRENDS:
        raise ValueError(
            f"tech_trend 值不合法: {trend!r}"
            f"（应为: {VALID_TRENDS}）"
        )

    # 4. 校验 industry_impact 结构
    impact = result.get("industry_impact", {})
    if not isinstance(impact, dict):
        raise ValueError(f"industry_impact 应为对象，实际: {type(impact).__name__}")
    if "short_term" not in impact or "long_term" not in impact:
        raise ValueError(
            f"industry_impact 缺少 short_term 或 long_term。"
            f"实际内容: {impact}"
        )

    # 5. 校验 actionable_insights 是数组
    insights = result.get("actionable_insights", [])
    if not isinstance(insights, list):
        raise ValueError(
            f"actionable_insights 应为数组，实际: {type(insights).__name__}"
        )
    if len(insights) < 2:
        raise ValueError(
            f"actionable_insights 条目过少（{len(insights)}条），"
            f"期望至少 2-5 条"
        )


# =========================================================
# 核心评述函数（含重试）
# =========================================================

def summarize_news(title: str, article: str, category: str,
                   importance: int, reason: str,
                   max_retries: int = 3) -> dict:
    """
    对单条 AI 新闻调用 DeepSeek 进行深度评述。

    参数：
        title:      新闻标题
        article:    压缩摘要（Step 5 输出）
        category:   分类（Step 6 输出）
        importance: 重要性评分（Step 6 输出）
        reason:     分类依据（Step 6 输出）
        max_retries: 最大重试次数

    返回：
        包含 6 个主观分析维度的 dict

    说明：
        将 Step 6 的客观分析结果作为上下文注入，
        让模型在已知事实基础上做更深入的主观判断。
    """
    prompt = build_summarize_prompt(title, article, category, importance, reason)
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是资深 AI 产业战略分析师。"
                            "只输出 JSON，不输出任何解释、前言或 markdown。"
                            "整个回复必须是一个完整的 JSON 对象。"
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                # ★ 温度设为 0.3（而非 0）的原因：
                # 评述任务需要适度的"创造性洞察"，完全确定性的输出容易变得死板
                # 0.3 是在"稳定"和"有见地"之间的平衡点
                max_tokens=512,
                response_format={"type": "json_object"}
                # ★ 使用 JSON Mode 强制合法 JSON 输出
                # DeepSeek 支持此参数，模型会在 API 层面保证输出可解析的 JSON
            )

            raw_output = response.choices[0].message.content

            print(f"\n📦 RAW OUTPUT（第 {attempt} 次）:")
            print("-" * 40)
            print(repr(raw_output))
            print("-" * 40)

            result = safe_parse(raw_output)
            validate_summary(result)

            return result

        except Exception as e:
            last_exception = e
            print(f"  ⚠️ 第 {attempt}/{max_retries} 次失败: {type(e).__name__}: {e}")
            if attempt < max_retries:
                wait_seconds = 2 ** attempt
                print(f"     等待 {wait_seconds}s 后重试...")
                time.sleep(wait_seconds)

    raise last_exception


# =========================================================
# 主流程
# =========================================================

def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        news_list = json.load(f)

    summarized_news = []

    # 统计
    ai_news_count = 0
    non_ai_skipped = 0
    error_count = 0

    for i, news in enumerate(news_list):

        title = news.get("title", "").strip()
        analysis = news.get("analysis", {})

        # 检查是否是 AI 新闻
        is_ai = analysis.get("is_ai_news", False)
        category = analysis.get("category", "")
        importance = analysis.get("importance", 1)
        reason = analysis.get("reason", "")

        print("\n" + "=" * 60)
        print(f"[{i+1}/{len(news_list)}] {title[:55]}")
        print(f"AI新闻: {is_ai} | 分类: {category} | 重要性: {importance}")
        print("=" * 60)

        # ★ 只处理 AI 新闻，非 AI 新闻跳过主观评述
        # 原因：非 AI 新闻（如 iPhone 硬件更新）不需要产业分析
        if not is_ai:
            print("⏭️  非 AI 新闻，跳过评述")
            news["summary"] = {
                "skipped": True,
                "reason": "非 AI 新闻，无需产业分析"
            }
            non_ai_skipped += 1
            summarized_news.append(news)

            # 增量保存（即使是跳过的也保存，保持状态同步）
            with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
                json.dump(summarized_news, f, ensure_ascii=False, indent=2)
            continue

        # 获取压缩摘要（Step 5 输出）
        compressed = news.get("compressed_article", "").strip()

        try:
            summary = summarize_news(title, compressed, category, importance, reason)
            news["summary"] = summary

            ai_news_count += 1
            print("✅ 评述成功")
            print(f"   核心观点 : {summary['key_takeaway'][:50]}...")
            print(f"   投资信号 : {summary['investment_signal']}")
            print(f"   技术趋势 : {summary['tech_trend']}")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)[:120]}"
            print(f"❌ 评述失败: {error_msg}")

            news["summary"] = {
                "skipped": True,
                "reason": f"评述失败: {error_msg}",
                "key_takeaway": "",
                "industry_impact": {"short_term": "", "long_term": ""},
                "investment_signal": "neutral",
                "tech_trend": "mature",
                "competitive_landscape": "",
                "actionable_insights": []
            }
            error_count += 1

        summarized_news.append(news)

        # 增量保存
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(summarized_news, f, ensure_ascii=False, indent=2)

        time.sleep(1)  # 礼貌间隔，避免触发 API 限流

    # =========================================================
    # 汇总
    # =========================================================

    print("\n" + "=" * 60)
    print("🎉 全部评述完成")
    print(f"📁 输出文件    : {OUTPUT_PATH}")
    print(f"📊 AI 新闻评述 : {ai_news_count} 条")
    print(f"   非 AI 跳过  : {non_ai_skipped} 条")
    print(f"   评述失败    : {error_count} 条")
    print("=" * 60)


if __name__ == "__main__":
    main()