"""
05_article_compressor_fixed.py

功能：
1. 读取 data/article_cleaned.json
2. 调用 DeepSeek 压缩每条新闻正文为 3-5 条核心摘要（中文）
3. 增量保存到 data/compressed_news.json

修复：
  - Prompt 要求与示例统一（之前要求中英双语但示例只有中文，导致输出格式不稳定）
  - str.format() → str.replace()（统一风格，消除未来隐患）
  - 加入重试机制（最多 3 次，指数退避）
  - 加入增量保存（每条完成后立即写文件）
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

INPUT_PATH  = "data/article_cleaned.json"
OUTPUT_PATH = "data/compressed_news.json"
MIN_ARTICLE_LEN = 50   # 正文最短长度阈值，低于此值跳过
MAX_ARTICLE_CHARS = 3000  # 传入模型的最大正文字符数

# =========================================================
# Prompt 模板
#
# ★ 修复 1：要求与示例统一 —— 统一改为"只输出中文"
#   原 Prompt 要求"输出英文版本再输出中文翻译"，但示例只有中文，
#   模型行为不稳定：有时只输出中文、有时中英混排、有时带解释文字。
#   统一为中文后，downstream 分类器（06）也更容易处理。
#
# ★ 修复 2：改用 __ARTICLE__ 占位符 + str.replace() 替换
#   原 COMPRESS_PROMPT 的 {article} 本次未触发 Bug，但为了与项目其他
#   脚本风格统一（v2_fixed 和 v3_fixed 都用 str.replace()），
#   统一改为自定义占位符，彻底杜绝未来有人往 Prompt 里加规则说明
#   时不慎带入 {} 而踩坑。
# =========================================================

COMPRESS_PROMPT_TEMPLATE = """你是一名资深科技媒体编辑。

请阅读下面的新闻正文，提取最重要的3到5条核心事实。

输出要求：
1. 每条一句中文，只保留客观事实
2. 不评价、不推测、不扩写
3. 所有条目加起来不超过150字
4. 每条以 "- " 开头，不加序号

输出示例：
- OpenAI 发布新一代 GPT 模型
- 模型支持 128K 上下文窗口
- 企业版与消费者版同步上线
- 定价相比前代降低 50%

新闻正文：
__ARTICLE__"""


def build_compress_prompt(article: str) -> str:
    """
    构建压缩 Prompt，使用 str.replace() 安全替换占位符。

    截取前 MAX_ARTICLE_CHARS 个字符，防止超长正文超出模型 token 限制。
    """
    # 截取正文前 3000 字符（超出部分对摘要质量贡献有限）
    truncated = article[:MAX_ARTICLE_CHARS]
    return COMPRESS_PROMPT_TEMPLATE.replace("__ARTICLE__", truncated)


# =========================================================
# 压缩函数（含重试）
# =========================================================

def compress_article(article: str, max_retries: int = 3) -> str:
    """
    调用 DeepSeek 对正文进行压缩摘要。

    Args:
        article:     原始正文字符串
        max_retries: 最大重试次数

    Returns:
        压缩后的摘要字符串

    Raises:
        最后一次尝试的异常
    """
    prompt = build_compress_prompt(article)
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是科技媒体编辑。"
                            "只输出核心事实的 bullet points，不输出任何解释或前言。"
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=512,   # 摘要不需要太长，512 足够
            )
            result = response.choices[0].message.content
            if not result or not result.strip():
                raise ValueError("模型返回空内容")
            return result.strip()

        except Exception as e:
            last_exception = e
            print(f"  ⚠️  第 {attempt}/{max_retries} 次失败: {e}")
            if attempt < max_retries:
                wait_seconds = 2 ** attempt
                print(f"     {wait_seconds}s 后重试...")
                time.sleep(wait_seconds)

    raise last_exception


# =========================================================
# 主流程
# =========================================================

print("\n开始读取新闻数据...\n")

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    news_list = json.load(f)

print(f"读取完成，共 {len(news_list)} 条新闻")

compressed_news = []

for i, news in enumerate(news_list):

    print("\n" + "=" * 60)
    print(f"[{i+1}/{len(news_list)}] {news.get('title', '')}")
    print("=" * 60)

    article = news.get("clean_article", "").strip()

    # 正文过短：跳过 API 调用，直接置空
    if len(article) < MIN_ARTICLE_LEN:
        print(f"正文过短（{len(article)} 字符），跳过压缩")
        news["compressed_article"] = ""
        compressed_news.append(news)

        # 增量保存（即便是跳过的也保存，保持文件状态同步）
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(compressed_news, f, ensure_ascii=False, indent=2)
        continue

    try:
        compressed = compress_article(article)
        news["compressed_article"] = compressed

        print("\n压缩结果：")
        print(compressed)
        print(f"\n字符数：{len(compressed)}")

    except Exception as e:
        print(f"\n多次重试后仍失败：{e}")
        news["compressed_article"] = ""

    compressed_news.append(news)

    # ★ 修复：增量保存
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(compressed_news, f, ensure_ascii=False, indent=2)

    time.sleep(1)

# =========================================================
# 汇总
# =========================================================

success = sum(1 for n in compressed_news if n.get("compressed_article"))
skipped = sum(1 for n in compressed_news if not n.get("compressed_article"))

print("\n" + "=" * 60)
print("全部压缩完成")
print(f"输出文件   : {OUTPUT_PATH}")
print(f"成功压缩   : {success} 条")
print(f"跳过/失败  : {skipped} 条")
print("=" * 60)