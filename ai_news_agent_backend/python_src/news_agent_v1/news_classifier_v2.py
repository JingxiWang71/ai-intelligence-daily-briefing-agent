"""
news_classifier_v2.py

功能：
1. 读取 clean_news.json
2. 调用 DeepSeek进行AI新闻结构化分析
3. 输出：
   - 是否AI新闻
   - 分类
   - 重要性评分
   - 原因解释
4. 保存 classified_news_v2.json
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# =========================
# 读取环境变量
# =========================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# =========================
# V2 Prompt
# =========================

V2_PROMPT = """
你是一个严格的JSON生成器。

请严格执行以下任务：

【任务1：AI相关性判断】
判断该新闻是否属于人工智能领域：
true 或 false

【任务2：分类】
如果是AI新闻，从以下类别中选择：
1. 科学研究成果
2. 大模型发展
3. 应用层发展
4. 人工智能基础设施
5. 产品与工具
6. 公司动态
7. 投融资
8. 安全与伦理
9. 国际竞争与战略
10. 就业与社会影响

【任务3：重要性评分】
1-5评分：
5=重大事件
4=重要更新
3=一般更新
2=较小更新
1=边缘信息

【任务4：原因】
一句中文解释

【输出格式（必须严格JSON）】
⚠️ 强制规则：
1. 只能输出JSON
2. 不能有markdown
3. 不能有解释
4. 不能有多余字符
5. 必须以 { 开始
6. 必须以 } 结束

如果你不能遵守，你的输出将被系统直接丢弃。

输出格式：

{
  "is_ai_news": true,
  "category": "安全与伦理",
  "importance": 3,
  "reason": "一句中文原因"
}

新闻标题：
{title}
"""

# =========================
# 调用模型函数
# =========================

def classify_news_v2(title):
    """
    输入：新闻标题
    输出：结构化JSON字符串
    """

    prompt = V2_PROMPT.format(title=title)

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
    {
        "role": "system",
        "content": "你是严格的JSON生成器，只能输出JSON"
    },
    {
        "role": "user",
        "content": prompt
    }
    ],
        temperature=0
    )

    return response.choices[0].message.content


# =========================
# 读取数据
# =========================

with open("data/clean_news.json", "r", encoding="utf-8") as f:
    news_list = json.load(f)

classified_news = []

import json
import re

def safe_parse(text):
    import json
    import re

    if not text:
        raise ValueError("empty output")

    # 去markdown
    text = text.replace("```json", "").replace("```", "")

    # 找 JSON 起点
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"NO JSON: {text[:50]}")

    json_str = text[start:end+1]

    # ⚠️ 防止截断
    try:
        return json.loads(json_str)
    except:
        raise ValueError(f"INVALID JSON: {json_str[:100]}")

# =========================
# 主循环
# =========================

# =========================
# 主循环（稳定工程版）
# =========================

classified_news = []

for i, news in enumerate(news_list):

    title = news["title"]

    print("\n" + "=" * 60)
    print(f"[{i+1}/{len(news_list)}] 正在分类")
    print(f"标题: {title}")
    print("=" * 60)

    try:
        # =========================
        # Step 1: 调用LLM
        # =========================
        result_str = classify_news_v2(title)

        # 🔍 打印原始输出（调试用，非常重要）
        print("\n📦 RAW MODEL OUTPUT:")
        print("-" * 40)
        print(repr(result_str))  # repr可以显示\n等隐藏字符
        print("-" * 40)

        # =========================
        # Step 2: JSON解析（核心）
        # =========================
        result = extract_json(result_str)

        # =========================
        # Step 3: 数据合并
        # =========================
        news["analysis"] = result

        # 🟢 成功提示
        print("✅ 分类成功")
        print(f"AI相关: {result.get('is_ai_news')}")
        print(f"类别: {result.get('category')}")
        print(f"重要性: {result.get('importance')}")

    except Exception as e:

        # =========================
        # Step 4: 错误处理（不会中断程序）
        # =========================
        print("❌ 分类失败:")
        print(e)

        news["analysis"] = {
            "is_ai_news": False,
            "category": "ERROR",
            "importance": 1,
            "reason": "解析失败或模型输出异常"
        }

    # =========================
    # Step 5: 保存结果
    # =========================
    classified_news.append(news)

# =========================
# Step 6: 输出最终文件
# =========================

output_path = "data/classified_news_v2.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(classified_news, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 60)
print("🎉 全部分类完成")
print(f"📁 文件已保存: {output_path}")
print(f"📊 总新闻数: {len(classified_news)}")
print("=" * 60)