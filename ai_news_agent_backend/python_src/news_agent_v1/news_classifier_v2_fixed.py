"""
news_classifier_v2_fixed.py

功能：
1. 读取 data/clean_news.json
2. 调用 DeepSeek API 对每条新闻进行结构化分类
3. 输出字段：is_ai_news / category / importance / reason
4. 增量保存到 data/classified_news_v2.json

修复清单：
  Bug #1 (致命): str.format() 把 Prompt 中的 {} 误解析为格式化占位符
                 → 改用 __TITLE__ 占位符 + str.replace() 安全替换
  Bug #2 (隐藏): 主循环调用未定义的 extract_json()
                 → 改为正确的 safe_parse()
  Bug #3 (质量): 重复初始化、重复 import、缺乏重试和增量保存
                 → 全部整理修复
"""

import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# =========================================================
# 1. 初始化客户端
# =========================================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# =========================================================
# 2. Prompt 模板
#
# ⚠️ 关键设计决策：使用 __TITLE__ 而非 {title}
#
# 原因：str.format() 会把字符串里【所有】的 {...} 当成格式化字段，
# 不只是 {title}。Prompt 中包含的规则说明和 JSON 示例都有 { }，
# 全部会被误解析，导致 KeyError。
#
# 解决方案：用一个绝对不会在新闻标题里出现的字符串 __TITLE__ 作占位符，
# 然后用 str.replace() 替换——它不做任何格式化语法解析，纯字符串替换。
# =========================================================

PROMPT_TEMPLATE = """你是一个严格的 JSON 生成器。

分析以下新闻标题，严格按照格式输出 JSON，不输出任何其他内容。

任务说明：

1. is_ai_news（布尔）
   判断该新闻是否属于人工智能领域，返回 true 或 false。

2. category（字符串）
   若 is_ai_news 为 true，从下列类别中选一个：
   科学研究成果、大模型发展、应用层发展、人工智能基础设施、产品与工具、
   公司动态、投融资、安全与伦理、国际竞争与战略、就业与社会影响
   若 is_ai_news 为 false，固定填写 "非AI新闻"。

3. importance（整数 1-5）
   5=重大事件  4=重要更新  3=一般更新  2=较小更新  1=边缘信息

4. reason（字符串）
   一句中文解释分类和评分的理由。

输出示例（单行 JSON，不加 markdown，不加解释）：
{"is_ai_news": true, "category": "大模型发展", "importance": 4, "reason": "OpenAI 发布 GPT-5，性能大幅提升"}

新闻标题：__TITLE__"""
#
# ↑ 说明：
#   - JSON 示例改为单行，减少模型"先解释再输出"的概率
#   - 明确指定 is_ai_news=false 时 category 的填写规则，避免输出 null 导致字段缺失
#   - __TITLE__ 放在最后，模型读完 Prompt 后直接进入分析状态


def build_prompt(title: str) -> str:
    """
    构建最终发送给模型的 Prompt。

    使用 str.replace() 而非 str.format()，完全避开 Python 格式化语法。

    Args:
        title: 新闻标题字符串

    Returns:
        替换好占位符的完整 Prompt 字符串
    """
    # str.replace() 只做纯字符串替换，不解析任何 {} 语义，绝对安全
    return PROMPT_TEMPLATE.replace("__TITLE__", title)


# =========================================================
# 3. JSON 解析（鲁棒版）
# =========================================================

def safe_parse(text: str) -> dict:
    """
    从模型的原始输出中提取并解析 JSON。

    处理以下常见的"模型乱输出"情况：
    - 输出被 markdown 代码块包裹（```json ... ```）
    - JSON 前后有多余的说明文字
    - JSON 内部格式轻微不规范

    Args:
        text: 模型返回的原始字符串

    Returns:
        解析后的 Python dict

    Raises:
        ValueError: 无法找到或解析 JSON 时，附带详细的原始输出信息
    """
    if not text or not text.strip():
        raise ValueError("模型返回了空内容")

    # Step 1：去除 markdown 代码块标记
    # 有些模型会在 JSON 外面加 ```json ... ``` 包裹
    text = text.replace("```json", "").replace("```", "").strip()

    # Step 2：定位 JSON 的起止位置
    # 用 find("{") 找第一个左括号，rfind("}") 找最后一个右括号
    # 这样可以容忍 JSON 前后有任意文字
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        # 完全找不到括号，说明模型输出了非 JSON 的内容
        raise ValueError(
            f"输出中没有找到 JSON 括号。"
            f"原始输出（前150字符）: {text[:150]!r}"
        )

    if start > end:
        # 括号顺序异常（极少见，但做防御性检查）
        raise ValueError(
            f"JSON 括号顺序异常（start={start} > end={end}）。"
            f"原始输出: {text[:150]!r}"
        )

    # Step 3：提取 JSON 子串并解析
    json_str = text[start : end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # json.JSONDecodeError 包含行号和列号，方便调试
        raise ValueError(
            f"JSON 解析失败: {e}。"
            f"提取的 JSON 片段（前200字符）: {json_str[:200]!r}"
        )


# =========================================================
# 4. 输出字段校验
# =========================================================

REQUIRED_KEYS = {"is_ai_news", "category", "importance", "reason"}


def validate_result(result: dict) -> None:
    """
    校验模型输出的 JSON 是否符合预期结构。

    检查项：
    - 所有必要字段存在
    - importance 是 1-5 范围内的数字
    - is_ai_news 是布尔值

    Args:
        result: safe_parse() 解析后的 dict

    Raises:
        ValueError: 字段缺失或值不合法时
    """
    # 检查必要字段
    missing = REQUIRED_KEYS - result.keys()
    if missing:
        raise ValueError(f"输出缺少必要字段: {missing}。完整输出: {result}")

    # 检查 importance 范围
    importance = result.get("importance")
    if not isinstance(importance, (int, float)) or not (1 <= importance <= 5):
        raise ValueError(
            f"importance 值不合法: {importance!r}（应为 1-5 的整数）"
        )

    # 检查 is_ai_news 类型
    # 防止模型输出字符串 "true"/"false" 而不是布尔值
    if not isinstance(result.get("is_ai_news"), bool):
        raise ValueError(
            f"is_ai_news 应为布尔值，实际类型: {type(result.get('is_ai_news')).__name__}，"
            f"值: {result.get('is_ai_news')!r}"
        )


# =========================================================
# 5. 核心分类函数（含重试）
# =========================================================

def classify_news(title: str, max_retries: int = 3) -> dict:
    """
    对单条新闻标题调用 DeepSeek API 进行结构化分类。

    包含指数退避重试，用于应对：
    - 模型偶发输出格式错误（重试通常能成功）
    - API 限流（等待后重试）
    - 网络短暂抖动

    Args:
        title:       新闻标题
        max_retries: 最大尝试次数（默认 3 次）

    Returns:
        包含 is_ai_news / category / importance / reason 的 dict

    Raises:
        最后一次尝试的异常（超过重试次数后）
    """
    # ★ Bug #1 修复：使用 build_prompt() 而非 V2_PROMPT.format(title=title)
    #   build_prompt 内部用 str.replace()，不会把 Prompt 里的 {} 当格式化占位符
    prompt = build_prompt(title)

    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        # System prompt 双重强调纯 JSON 输出
                        # DeepSeek 对 system 指令遵从度较高
                        "content": (
                            "你是严格的 JSON 生成器。"
                            "只输出 JSON，不输出任何解释、前言、markdown 或其他内容。"
                            "你的整个回复必须是一个合法的 JSON 对象。"
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,    # 温度为 0：输出确定性最强，减少随机"创作"
                max_tokens=256,   # 分类结果只需约 80 token，限制上限防止模型"话多"
            )

            raw_output = response.choices[0].message.content

            # 打印原始输出（调试用，上线后可注释掉）
            print(f"\n📦 RAW OUTPUT（第 {attempt} 次）:")
            print("-" * 40)
            print(repr(raw_output))  # repr() 让 \n 等隐藏字符可见
            print("-" * 40)

            # ★ Bug #2 修复：原代码写的是 extract_json()，函数根本不存在
            #   正确的函数名是 safe_parse()
            result = safe_parse(raw_output)

            # 校验字段完整性和值的合法性
            validate_result(result)

            return result  # 成功，直接返回

        except Exception as e:
            last_exception = e
            print(f"⚠️  第 {attempt}/{max_retries} 次失败: {type(e).__name__}: {e}")

            if attempt < max_retries:
                # 指数退避：2s → 4s
                # 避免频繁重试触发 API 限流
                wait_seconds = 2 ** attempt
                print(f"   等待 {wait_seconds}s 后重试...")
                time.sleep(wait_seconds)

    # 超过最大重试次数，抛出最后一次的异常
    raise last_exception


# =========================================================
# 6. 主流程
# =========================================================

def main():
    input_path  = "data/clean_news.json"
    output_path = "data/classified_news_v2.json"

    # 读取待分类新闻列表
    with open(input_path, "r", encoding="utf-8") as f:
        news_list = json.load(f)

    # ★ Bug #3 修复：classified_news 只初始化一次
    #   原代码在两处各初始化了一次，第一次赋值被第二次覆盖，逻辑混乱
    classified_news = []

    for i, news in enumerate(news_list):
        title = news.get("title", "").strip()

        print("\n" + "=" * 60)
        print(f"[{i + 1}/{len(news_list)}] 正在分类")
        print(f"标题: {title}")
        print("=" * 60)

        try:
            result = classify_news(title)
            news["analysis"] = result

            print("✅ 分类成功")
            print(f"   AI相关  : {result['is_ai_news']}")
            print(f"   类别    : {result['category']}")
            print(f"   重要性  : {result['importance']}")
            print(f"   原因    : {result['reason']}")

        except Exception as e:
            # 多次重试后仍然失败：记录错误信息，继续处理下一条，不中断程序
            error_msg = f"{type(e).__name__}: {str(e)[:120]}"
            print(f"❌ 多次重试后仍然失败: {error_msg}")

            news["analysis"] = {
                "is_ai_news": False,
                "category": "ERROR",
                "importance": 1,
                "reason": f"分类失败：{error_msg}"  # 保存真实报错，方便后续排查
            }

        classified_news.append(news)

        # ★ Bug #3 修复：增量保存
        # 每处理完一条就写一次文件，防止程序中途崩溃导致已完成的结果全部丢失
        # 代价：文件 I/O 略多，但对于新闻分类这种耗时任务完全值得
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(classified_news, f, ensure_ascii=False, indent=2)

    # 汇总输出
    total = len(classified_news)
    success = sum(1 for n in classified_news if n["analysis"]["category"] != "ERROR")
    failed  = total - success

    print("\n" + "=" * 60)
    print("🎉 全部分类完成")
    print(f"📁 文件已保存  : {output_path}")
    print(f"📊 总计        : {total} 条")
    print(f"   ✅ 成功     : {success} 条")
    print(f"   ❌ 失败     : {failed} 条")
    print("=" * 60)


if __name__ == "__main__":
    main()