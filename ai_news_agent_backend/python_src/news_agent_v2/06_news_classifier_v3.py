"""
06_news_classifier_v3_fixed.py

功能：
- 使用标题 + compressed_article 调用 DeepSeek 进行新闻分类
- 输出 is_ai_news / category / importance / reason
- 保存到 data/classified_news_v3.json

==========================================================================
修复清单
==========================================================================

Bug #1（致命）：str.format() 把 V3_PROMPT 中的 { 开头，以 } 结束 和
              JSON 示例块中的 {...} 解析为 Python format 字段，抛出：
              KeyError: ' 开头，以 '
              程序从未发出任何 API 请求。

  修复：彻底废弃 str.format()。
        改用 __TITLE__ 和 __ARTICLE__ 作为占位符，配合 str.replace() 替换。
        str.replace() 是纯字符串替换，完全不解析 {} 语义。

Bug #2（隐藏）：主循环中 safe_parse() 函数体内有多余的 `import json`。
              模块顶层已经 import json，函数内的 import 完全多余。

  修复：删除函数体内的 import，保留顶层的。

Bug #3（健壮性）：无重试机制，模型一次输出格式错误就直接进 except。

  修复：加入最多 3 次的指数退避重试（2s → 4s）。

Bug #4（健壮性）：全部处理完才保存一次文件。
              30 条新闻处理到第 25 条崩溃，25 条结果全部丢失。

  修复：每条处理完立即写一次文件（增量保存）。

Bug #5（完整性）：safe_parse() 只检查 JSON 能否解析，不校验字段是否齐全。
              模型可能输出 {"is_ai_news": true} 这种不完整 JSON。

  修复：加入 validate_result() 对字段做完整性和类型校验。

Bug #6（健壮性）：compressed_article 为空时没有任何提示，
              分类器在信息不足的情况下静默降级。

  修复：空 article 时将占位符替换为提示文字，让模型知道只有标题可参考。

==========================================================================
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

INPUT_PATH  = "data/compressed_news.json"
OUTPUT_PATH = "data/classified_news_v3.json"

# =========================================================
# Prompt 模板
#
# ★ Bug #1 修复的核心：
#
# 原来的 V3_PROMPT 包含：
#   "- 以 { 开头，以 } 结束"   ← Python 把 " 开头，以 " 当成 format 字段名
#   {                           ← JSON 示例块的 { 也被当成 format 字段开始
#     "is_ai_news": true,
#     ...
#   }
#   标题：{title}               ← 合法，但永远执行不到（前面已经 KeyError）
#   正文压缩：{compressed_article}
#
# 调用 V3_PROMPT.format(title=..., compressed_article=...) 时：
#   Python 在参数里找不到 " 开头，以 " 这个键
#   → KeyError: ' 开头，以 '
#   → 进入 except，输出 "分类失败"，实际上 LLM 从未被调用
#
# 修复方案：
#   1. 删除 Prompt 规则说明中的原生 { }，改用汉字描述
#   2. JSON 示例改为单行，减少多行 { } 被误解析的概率
#   3. 用 __TITLE__ 和 __ARTICLE__ 代替 {title} 和 {compressed_article}
#   4. 构建 Prompt 时用 str.replace()，完全不触碰 {} 语义
# =========================================================

PROMPT_TEMPLATE = """你是一个严格的JSON生成器。只输出JSON，不输出任何解释或markdown。

请根据以下新闻的标题和摘要完成四个判断：

1. is_ai_news（布尔）：该新闻是否属于人工智能领域，返回 true 或 false

2. category（字符串）：
   若 is_ai_news 为 true，从下列10个类别中选一个：
   科学研究成果、大模型发展、应用层发展、人工智能基础设施、产品与工具、
   公司动态、投融资、安全与伦理、国际竞争与战略、就业与社会影响
   若 is_ai_news 为 false，固定填写 "非AI新闻"

3. importance（整数 1-5）：5=重大事件，4=重要更新，3=一般更新，2=较小更新，1=边缘信息

4. reason（字符串）：一句中文，说明分类和评分依据

严格按照以下单行JSON格式输出，不允许任何其他内容：
{"is_ai_news": true, "category": "大模型发展", "importance": 4, "reason": "OpenAI发布新一代模型，对行业影响深远"}

新闻内容：
标题：__TITLE__
正文摘要：__ARTICLE__"""
#
# ↑ 说明：
#   - "以花括号开始和结束" 的规则改为直接给示例，更直观
#   - JSON 示例改为单行，减少模型"在 {} 之间加解释"的概率
#   - 明确规定 is_ai_news=false 时 category 填 "非AI新闻"，避免 null 等异常值
#   - __TITLE__ 和 __ARTICLE__ 是完全不含 {} 的自定义占位符


def build_prompt(title: str, compressed_article: str) -> str:
    """
    用 str.replace() 安全地构建最终 Prompt，替换两个自定义占位符。

    为什么不用 str.format()？
      str.format() 会扫描整个模板字符串，把所有 {...} 都当成格式化字段，
      哪怕它们只是 Prompt 里的说明文字或 JSON 示例，都会导致 KeyError。
      str.replace() 只做纯字符串替换，完全不解析 {} 语义，绝对安全。

    为什么对空 article 添加提示文字？
      compressed_article 为空意味着正文抓取失败或文章太短被跳过。
      与其让模型看到一个空的"正文摘要："字段而输出不稳定的结果，
      不如明确告诉模型"无正文，请仅凭标题判断"，让行为更可预期。

    Args:
        title:              新闻标题
        compressed_article: 压缩摘要（可能为空字符串）

    Returns:
        替换好占位符的完整 Prompt 字符串
    """
    article_text = compressed_article.strip() if compressed_article else ""

    # 空摘要时插入明确提示，避免模型看到空字段后产生不稳定输出
    article_placeholder = article_text if article_text else "(无正文摘要，请仅凭标题判断)"

    return (
        PROMPT_TEMPLATE
        .replace("__TITLE__", title)
        .replace("__ARTICLE__", article_placeholder)
    )


# =========================================================
# JSON 解析
# =========================================================

def safe_parse(text: str) -> dict:
    """
    从模型的原始输出中提取并解析 JSON。

    处理常见的模型"乱输出"情况：
    - markdown 代码块包裹（```json ... ```）
    - JSON 前后有多余说明文字
    - 模型在 JSON 后面追加了解释

    Args:
        text: 模型原始输出字符串

    Returns:
        解析后的 dict

    Raises:
        ValueError: 找不到 JSON 或解析失败，错误信息含原始输出，方便调试
    """
    # ★ Bug #2 修复：删除此处的 `import json`
    # 模块顶层已经 `import json`，函数体内重复 import 是多余的
    # （Python 会从 sys.modules 缓存取，不影响功能，但影响代码整洁度）

    if not text or not text.strip():
        raise ValueError("模型返回空内容")

    # 去除 markdown 代码块标记
    text = text.replace("```json", "").replace("```", "").strip()

    # 定位 JSON 的起止括号
    start = text.find("{")
    end   = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            f"输出中未找到 JSON 括号。原始输出（前150字符）: {text[:150]!r}"
        )
    if start > end:
        raise ValueError(
            f"JSON 括号顺序异常（start={start} > end={end}）。原始输出: {text[:100]!r}"
        )

    json_str = text[start : end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"JSON 解析失败: {e}。"
            f"提取片段（前200字符）: {json_str[:200]!r}"
        )


# =========================================================
# 输出字段校验
# =========================================================

REQUIRED_KEYS = {"is_ai_news", "category", "importance", "reason"}


def validate_result(result: dict) -> None:
    """
    校验模型输出的 JSON 结构是否符合预期。

    ★ Bug #5 修复：safe_parse 只保证 JSON 可解析，不保证字段齐全。
    模型可能输出 {"is_ai_news": true} 这种缺字段的 JSON，
    不加校验的话会在后续 result.get("category") 时静默返回 None，
    导致数据脏、难以排查。

    Args:
        result: safe_parse() 返回的 dict

    Raises:
        ValueError: 字段缺失或值类型不合法时
    """
    # 检查必要字段是否存在
    missing = REQUIRED_KEYS - result.keys()
    if missing:
        raise ValueError(f"输出缺少必要字段: {missing}。完整输出: {result}")

    # 检查 importance 值域（1-5 整数）
    importance = result.get("importance")
    if not isinstance(importance, (int, float)) or not (1 <= importance <= 5):
        raise ValueError(
            f"importance 不合法: {importance!r}（应为 1-5 的整数）"
        )

    # 检查 is_ai_news 是否为布尔值
    # 模型有时会输出字符串 "true" / "false" 而非布尔 True / False
    if not isinstance(result.get("is_ai_news"), bool):
        raise ValueError(
            f"is_ai_news 应为布尔值，实际类型: {type(result.get('is_ai_news')).__name__}，"
            f"值: {result.get('is_ai_news')!r}"
        )


# =========================================================
# 核心分类函数（含重试）
# =========================================================

def classify_news(title: str, compressed_article: str, max_retries: int = 3) -> dict:
    """
    对单条新闻调用 DeepSeek 进行结构化分类。

    ★ Bug #3 修复：加入指数退避重试机制。
    模型输出偶尔会格式不对（多余文字、截断 JSON），重试通常能成功。
    指数退避（2s → 4s）同时能处理 API 限流的情况。

    Args:
        title:              新闻标题
        compressed_article: 压缩摘要（可以为空）
        max_retries:        最大尝试次数（默认 3）

    Returns:
        包含 is_ai_news / category / importance / reason 的 dict

    Raises:
        最后一次尝试的异常（超过重试次数后）
    """
    # ★ Bug #1 修复：使用 build_prompt() 而非 V3_PROMPT.format(...)
    # build_prompt() 内部用 str.replace()，完全不触碰 {} 语义
    prompt = build_prompt(title, compressed_article)

    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是严格的 JSON 生成器。"
                            "只输出 JSON，不输出任何解释、前言、markdown 或其他内容。"
                            "整个回复必须是一个完整的 JSON 对象。"
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,    # 零温度：确定性最强，减少随机格式变化
                max_tokens=256,   # 分类 JSON 约需 60-80 token，设上限防止模型"话多"
            )

            raw_output = response.choices[0].message.content

            # 调试输出（上线后可注释掉）
            print(f"\n📦 RAW OUTPUT（第 {attempt} 次）:")
            print("-" * 40)
            print(repr(raw_output))
            print("-" * 40)

            # 解析 + 校验
            result = safe_parse(raw_output)
            validate_result(result)

            return result  # 成功，直接返回

        except Exception as e:
            last_exception = e
            print(f"  ⚠️  第 {attempt}/{max_retries} 次失败: {type(e).__name__}: {e}")
            if attempt < max_retries:
                wait_seconds = 2 ** attempt  # 指数退避：2s → 4s
                print(f"     等待 {wait_seconds}s 后重试...")
                time.sleep(wait_seconds)

    # 超过最大重试次数
    raise last_exception


# =========================================================
# 主流程
# =========================================================

def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        news_list = json.load(f)

    classified_news = []

    for i, news in enumerate(news_list):

        title              = news.get("title", "").strip()
        compressed_article = news.get("compressed_article", "").strip()

        print("\n" + "=" * 60)
        print(f"[{i+1}/{len(news_list)}] 正在分类")
        print(f"标题    : {title}")
        print(f"有摘要  : {'是' if compressed_article else '否（仅凭标题判断）'}")
        print("=" * 60)

        try:
            result = classify_news(title, compressed_article)
            news["analysis"] = result

            print("✅ 分类成功")
            print(f"   AI相关  : {result['is_ai_news']}")
            print(f"   类别    : {result['category']}")
            print(f"   重要性  : {result['importance']}")
            print(f"   原因    : {result['reason']}")

        except Exception as e:
            # 多次重试后仍失败：记录真实错误，不中断整体流程
            error_msg = f"{type(e).__name__}: {str(e)[:120]}"
            print(f"❌ 多次重试后仍然失败: {error_msg}")

            news["analysis"] = {
                "is_ai_news"  : False,
                "category"    : "ERROR",
                "importance"  : 1,
                # ★ Bug #4 修复：记录真实错误信息，方便后续排查
                # 原来写死"解析失败或模型输出异常"，完全看不出哪里出了问题
                "reason"      : f"分类失败：{error_msg}"
            }

        classified_news.append(news)

        # ★ Bug #5 修复：增量保存
        # 每条完成后立即写文件，防止程序崩溃丢失已完成的结果
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(classified_news, f, ensure_ascii=False, indent=2)

    # =========================================================
    # 汇总统计
    # =========================================================

    total   = len(classified_news)
    success = sum(1 for n in classified_news if n["analysis"]["category"] != "ERROR")
    ai_news = sum(
        1 for n in classified_news
        if n["analysis"].get("is_ai_news") is True
    )
    errors  = total - success

    print("\n" + "=" * 60)
    print("🎉 全部分类完成")
    print(f"📁 输出文件    : {OUTPUT_PATH}")
    print(f"📊 总计        : {total} 条")
    print(f"   ✅ 成功     : {success} 条（其中 AI 新闻 {ai_news} 条）")
    print(f"   ❌ 失败     : {errors} 条")
    print("=" * 60)


if __name__ == "__main__":
    main()