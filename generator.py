"""
核心生成器 - 调用 DeepSeek API 生成内容
v3.0 模板系统 + 人设 + 评分 + 标签 + 评论区引导
"""
import os
import json
import time
import re
import random
from datetime import datetime

# 自动加载 .env 文件（本地开发用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import httpx
except ImportError:
    httpx = None

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
)


# ====================================================================
#  模板配置
# ====================================================================

TEMPLATES = {
    "fuye": {
        "name": "副业赚钱类",
        "personas": ["副业探索者", "上班族", "宝妈", "大学生", "自由职业者"],
        "tone": "搞钱搞钱搞钱！结果导向，数字说话，激动兴奋",
    },
    "share": {
        "name": "经验分享类",
        "personas": ["过来人", "踩坑无数的小白", "深度爱好者", "行业观察者"],
        "tone": "娓娓道来，真诚分享，有故事有细节，像跟朋友聊天",
    },
    "caikeng": {
        "name": "踩坑避雷类",
        "personas": ["冲动消费者", "交过智商税的打工人", "资深试错者", "理性回归者"],
        "tone": "痛心疾首！以亲身经历警示，先抑后扬，有反转有感悟",
    },
}

DEFAULT_TEMPLATE = "fuye"

EXPRESSION_VARIANTS = [
    "用第一人称，语气活泼，多用感叹号",
    "用第一人称，语气冷静理性，用数据说话",
    "用第二人称'你'开头，有强烈对话感，像在私聊",
    "用讲故事的方式开头，有场景感和画面感",
    "直接列干货，硬核实用风格，少废话",
]

OUTPUT_FORMAT = """
请严格按照以下 JSON 格式返回（不要加 markdown 代码块标记，不要用 ```）：

{
  "titles": ["标题1", "标题2", "标题3", "标题4", "标题5"],
  "article": "正文内容...",
  "covers": ["封面1", "封面2", "封面3"],
  "tags": ["#标签1", "#标签2", "#标签3", "#标签4"],
  "comment_hook": "评论区引导语",
  "scores": {
    "attraction": 8,
    "authenticity": 7,
    "conversion": 9
  }
}

各字段说明：
- titles: 5个爆款标题，每个要有吸引力要素（数字/反差/结果/情绪/悬念）
- article: 正文，150-300字，口语化，有真实感，适当换行分段
- covers: 3个封面文案，每个不超过10个字
- tags: 4个相关标签，带#号
- comment_hook: 1句评论区引导语，引导读者互动讨论
- scores: 自己为内容打分（1-10分）
  - attraction: 吸引力分数
  - authenticity: 真实感分数
  - conversion: 转化力分数
"""


# ====================================================================
#  Prompt 构建
# ====================================================================

def get_system_prompt(template_id=None):
    """根据模板生成 system prompt"""
    tpl = TEMPLATES.get(template_id, TEMPLATES[DEFAULT_TEMPLATE])
    persona = random.choice(tpl["personas"])
    return f"""你是「小红书爆款写作专家」，你是一个真实分享的{persona}。

你在小红书有3万粉丝，风格是{tpl['tone']}。

你的写作原则：
1. 标题必须有强吸引力：数字反差（"月入5k到5w"）、结果导向（"学会了轻松变现"）、情绪词（"太爽了/后悔没早做"）、悬念（"99%的人都不知道"）
2. 正文必须像真实用户分享：第一人称、有亲身经历感、有具体细节（时间/数字/场景）、有情绪起伏
3. 多用短句、换行、emoji，读起来轻松不累
4. 有明确的"人设感"——让读者感觉是活生生的人在说话
5. 结尾自然引导互动

{OUTPUT_FORMAT}"""


def build_user_prompt(topic, custom_instructions=None, template_id=None, variant_index=None):
    """构建 user prompt：主题 + 模板 + 风格变异 + 自定义指令"""
    tpl = TEMPLATES.get(template_id, TEMPLATES[DEFAULT_TEMPLATE])
    persona = random.choice(tpl["personas"])
    prompt = f"""请为「{topic}」这个主题生成完整的小红书爆款内容。

你今天的身份：一个分享「{tpl['name']}」的{persona}
你今天的写作风格：{tpl['tone']}

"""
    if variant_index is not None:
        style = EXPRESSION_VARIANTS[variant_index % len(EXPRESSION_VARIANTS)]
    else:
        style = random.choice(EXPRESSION_VARIANTS)
    prompt += f"表达方式：{style}\n\n"
    prompt += f"围绕「{topic}」这个关键词展开创作。\n{OUTPUT_FORMAT}"
    if custom_instructions:
        prompt += f"\n【额外要求（请务必遵守）】\n{custom_instructions}\n"
    return prompt


def get_template_labels():
    """返回模板选项列表，供前端使用"""
    return {k: v["name"] for k, v in TEMPLATES.items()}


# ====================================================================
#  API 调用
# ====================================================================

def call_deepseek_api(system_prompt, user_prompt, max_retries=3, temperature=0.85):
    """调用 DeepSeek API"""

    if OpenAI is not None:
        return _call_with_openai(system_prompt, user_prompt, max_retries, temperature)

    if httpx is not None:
        return _call_with_httpx(system_prompt, user_prompt, max_retries, temperature)

    raise ImportError("请安装依赖：pip install openai 或 pip install httpx")


def _call_with_openai(system_prompt, user_prompt, max_retries=3, temperature=0.85):
    """通过 openai 库调用"""
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=temperature,
                max_tokens=3072,
                stream=False,
            )
            return _parse_response(response.choices[0].message.content.strip())
        except Exception as e:
            print(f"  ⚠️  第 {attempt+1} 次调用失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise


def _call_with_httpx(system_prompt, user_prompt, max_retries=3, temperature=0.85):
    """通过 httpx 库调用"""
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        "temperature": temperature,
        "max_tokens": 3072,
        "stream": False,
    }
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(f"{DEEPSEEK_BASE_URL}/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                return _parse_response(resp.json()["choices"][0]["message"]["content"].strip())
        except Exception as e:
            print(f"  ⚠️  第 {attempt+1} 次调用失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise


def _parse_response(content):
    """从模型返回内容中解析 JSON，兼容旧字段"""
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:] if lines[-1].strip() == "```" else lines[1:-1])
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
            except json.JSONDecodeError:
                raise ValueError(f"无法从 API 返回中解析 JSON\n原始内容:\n{content}")
        else:
            raise ValueError(f"API 返回中没有找到 JSON 数据\n原始内容:\n{content}")
    required = {"titles": list, "article": str, "covers": list}
    for key, typ in required.items():
        if key not in result or not isinstance(result[key], typ):
            raise ValueError(f"返回数据缺少字段或类型错误: {key}")
        if key in ("titles", "covers") and len(result[key]) == 0:
            raise ValueError(f"{key} 列表为空")
    if "tags" not in result or not isinstance(result["tags"], list):
        result["tags"] = []
    if "comment_hook" not in result or not isinstance(result["comment_hook"], str):
        result["comment_hook"] = "你们觉得呢？评论区聊聊～"
    if "scores" not in result or not isinstance(result["scores"], dict):
        result["scores"] = {"attraction": 7, "authenticity": 7, "conversion": 7}
    else:
        for k in ("attraction", "authenticity", "conversion"):
            if k not in result["scores"] or not isinstance(result["scores"][k], (int, float)):
                result["scores"][k] = 7
    return result


def generate_for_topic(topic, custom_instructions=None, template_id=None, variant_index=None):
    """
    为单个主题生成所有内容
    参数：
      topic: 主题关键词
      custom_instructions: 可选的自定义指令
      template_id: 模板ID（fuye / share / caikeng）
      variant_index: 风格变异序号（批量差异化用）
    返回 dict: {"titles": [...], "article": "...", "covers": [...], "tags": [...], "comment_hook": "...", "scores": {...}}
    """
    if template_id is None:
        template_id = DEFAULT_TEMPLATE
    system_prompt = get_system_prompt(template_id)
    user_prompt = build_user_prompt(topic, custom_instructions, template_id, variant_index)
    try:
        result = call_deepseek_api(system_prompt, user_prompt)
        return result
    except Exception as e:
        raise RuntimeError(f"生成失败: {e}")


# ── 格式化 & 保存 ───────────────────────────────────────────

def format_result(topic, result):
    """格式化成可读的文本（含标签、评论区引导、评分）"""
    lines = []
    lines.append("=" * 60)
    lines.append(f"  主题：{topic}")
    lines.append(f"  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("🔥 5 个爆款标题")
    lines.append("-" * 30)
    for i, title in enumerate(result["titles"], 1):
        lines.append(f"  {i}. {title}")
    lines.append("")
    lines.append("📝 正文")
    lines.append("-" * 30)
    lines.append(result["article"])
    lines.append("")
    lines.append("🖼️  3 个封面文案")
    lines.append("-" * 30)
    for i, cover in enumerate(result["covers"], 1):
        lines.append(f"  {i}. {cover}")
    if result.get("tags"):
        lines.append("")
        lines.append("🏷️  标签")
        lines.append("-" * 30)
        lines.append("  " + " ".join(result["tags"]))
    if result.get("comment_hook"):
        lines.append("")
        lines.append("💬 评论区引导")
        lines.append("-" * 30)
        lines.append("  " + result["comment_hook"])
    if result.get("scores"):
        s = result["scores"]
        lines.append("")
        lines.append("📊 内容评分")
        lines.append("-" * 30)
        lines.append(f"  吸引力：{s.get('attraction', '?')}/10")
        lines.append(f"  真实感：{s.get('authenticity', '?')}/10")
        lines.append(f"  转化力：{s.get('conversion', '?')}/10")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def save_to_file(topic, text, output_dir="output"):
    """保存到 txt 文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    safe_name = topic.strip().replace(" ", "_").replace("/", "_")[:30]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    
    return filepath


def save_result_structured(topic, result, output_dir="output"):
    """按结构化格式保存生成结果（JSON + TXT），含全部新字段"""
    os.makedirs(output_dir, exist_ok=True)
    safe_name = topic.strip().replace(" ", "_").replace("/", "_")[:30]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"{safe_name}_{timestamp}.json"
    json_filepath = os.path.join(output_dir, json_filename)
    save_data = {
        "topic": topic,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "titles": result["titles"],
        "article": result["article"],
        "covers": result["covers"],
        "tags": result.get("tags", []),
        "comment_hook": result.get("comment_hook", ""),
        "scores": result.get("scores", {}),
    }
    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    txt_path = json_filepath.replace(".json", ".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(format_result(topic, result))
    return json_filepath


# ── 批量处理（CLI 用） ─────────────────────────────────────

def batch_generate(topics, output_dir="output"):
    """批量处理多个主题，模板轮换 + 风格差异化"""
    all_results = []
    template_ids = list(TEMPLATES.keys())
    print(f"\n{'='*60}")
    print(f"🚀 批量生成开始 — 共 {len(topics)} 个主题（模板轮换 + 风格差异化）")
    print(f"{'='*60}")
    for idx, topic in enumerate(topics, 1):
        print(f"\n[{idx}/{len(topics)}] ", end="")
        try:
            tpl_id = template_ids[(idx - 1) % len(template_ids)]
            variant = (idx - 1) % len(EXPRESSION_VARIANTS)
            result = generate_for_topic(topic, template_id=tpl_id, variant_index=variant)
            filepath = save_result_structured(topic, result, output_dir)
            print(f"  ✅ [{TEMPLATES[tpl_id]['name']}] 已保存: {filepath}")
            all_results.append({"topic": topic, "result": result, "filepath": filepath})
        except Exception as e:
            print(f"  ❌ {e}")
    summary_path = os.path.join(output_dir, f"_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"批量生成汇总报告\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n主题数：{len(topics)}\n成功：{len(all_results)}\n\n")
        for item in all_results:
            f.write(f"✅ 【{item['topic']}】 → {item['filepath']}\n")
    print(f"\n{'='*60}\n🎉 批量生成完成！\n   ✅ 成功: {len(all_results)} / {len(topics)}\n   📂 文件目录: {os.path.abspath(output_dir)}\n   📋 汇总文件: {summary_path}\n{'='*60}")
    return all_results


# ── CLI 主入口 ─────────────────────────────────────────────

def main():
    """主入口：交互式运行"""
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║   🔥 AI 爆款内容生成器 v3.0         ║")
    print("  ║   调用 DeepSeek API · 模板系统       ║")
    print("  ╚══════════════════════════════════════╝")
    print()
    print("请选择模式：")
    print("  1️⃣  输入单个主题")
    print("  2️⃣  批量输入多个主题（逗号分隔）")
    print("  3️⃣  从文件读取主题列表")
    print()
    choice = input("请输入选项 (1/2/3): ").strip()
    topics = []
    if choice == "1":
        topic = input("请输入主题: ").strip()
        if topic:
            topics.append(topic)
    elif choice == "2":
        raw = input("请输入多个主题（用逗号分隔）: ").strip()
        topics = [t.strip() for t in raw.split(",") if t.strip()]
    elif choice == "3":
        filepath = input("请输入主题列表文件路径: ").strip()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                topics = [line.strip() for line in f if line.strip()]
            print(f"  ✅ 已读取 {len(topics)} 个主题")
        except FileNotFoundError:
            print(f"  ❌ 文件不存在: {filepath}")
            return
    else:
        print("❌ 无效选项")
        return
    if not topics:
        print("❌ 未输入任何主题")
        return
    print()
    print("请选择内容模板：")
    for k, v in TEMPLATES.items():
        print(f"  [{k}] {v['name']}")
    tpl_choice = input("（直接回车使用默认「副业赚钱类」）: ").strip()
    if tpl_choice not in TEMPLATES:
        tpl_choice = DEFAULT_TEMPLATE
    print()
    custom = input("（可选）额外要求（直接回车跳过）: ").strip()
    for topic in topics:
        try:
            result = generate_for_topic(topic, custom or None, template_id=tpl_choice)
            filepath = save_result_structured(topic, result)
            print(f"  ✅ 【{topic}】 → {filepath}")
        except Exception as e:
            print(f"  ❌ 【{topic}】 → {e}")


if __name__ == "__main__":
    main()

