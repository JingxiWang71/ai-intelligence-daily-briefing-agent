"""
news_classifier.py

功能：

1. 读取 clean_news.json

2. 调用 DeepSeek API

3. 自动分类新闻

4. 保存结果

输出：

classified_news.json
"""

# ==========================
# 导入库
# ==========================

import json

from openai import OpenAI

from dotenv import load_dotenv

import os


# ==========================
# 读取环境变量
# ==========================

# 读取 .env 文件

load_dotenv()

# 获取 API Key

DEEPSEEK_API_KEY = os.getenv(
    "DEEPSEEK_API_KEY"
)


# ==========================
# 创建客户端
# ==========================

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


# ==========================
# 分类函数
# ==========================

def classify_news(title):
    """
    输入：

    新闻标题

    输出：

    分类结果
    """

    prompt = f"""
你是AI产业分析师。

请判断下面新闻属于哪个类别。

可选类别：

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

只返回JSON：

{{
    "category":"类别名称"
}}

新闻标题：

{title}
"""

    response = client.chat.completions.create(
        model="deepseek-chat",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0
    )

    return response.choices[0].message.content


# ==========================
# 读取新闻数据
# ==========================

with open(
    "data/clean_news.json",
    "r",
    encoding="utf-8"
) as f:

    news_list = json.load(f)


# ==========================
# 开始分类
# ==========================

classified_news = []

for index, news in enumerate(news_list):

    title = news["title"]

    print(
        f"正在分类：{index+1}/{len(news_list)}"
    )

    print(title)

    try:

        result = classify_news(title)

        result_json = json.loads(result)

        news["classification"] = result_json

        classified_news.append(news)

    except Exception as e:

        print("JSON解析失败")

        print(e)

        news["classification"] = {
        "category": "解析失败"
        }

        classified_news.append(news)


# ==========================
# 保存结果
# ==========================

with open(
    "data/classified_news.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        classified_news,
        f,
        ensure_ascii=False,
        indent=2
    )

print("分类完成")