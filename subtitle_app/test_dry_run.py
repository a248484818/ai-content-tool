"""
测试脚本 - 不调用 API，仅验证代码结构和逻辑
"""
from generator import format_result, save_to_file, batch_generate
import json
import os

# 模拟的返回数据
mock_result = {
    "titles": [
        "用下班后的2小时，我赚到了主业一半的工资",
        "从0到月入5位数：普通人也能复制的3个副业方向",
        "不辞职、不囤货、不露脸：适合内向者的高利润副业",
        "我靠这个信息差副业，每月多赚8000块",
        "别再只靠死工资了！5个低门槛副业，第一个今天就能开始"
    ],
    "article": "很多人觉得做副业需要很多启动资金或者特殊技能，其实不然。真正的副业高手，往往是从自己已有的资源和人脉出发，找到信息差和需求缺口。比如利用AI工具帮人写文案、做PPT美化、甚至代画头像——这些都是零成本、高利润的方向。关键在于执行力，而不是等待完美的时机。从今天开始，每天抽出1小时打磨一个技能，一个月后你一定会感谢现在的自己。",
    "covers": [
        "下班后2小时，多赚一份工资",
        "适合普通人的3个副业方向",
        "零成本、高利润：这个副业太香了"
    ]
}

print("=" * 50)
print("🧪 运行测试 - 不调用API，仅验证代码逻辑")
print("=" * 50)

# 1. 测试格式化
print("\n📋 测试 format_result...")
text = format_result("AI副业", mock_result)
assert "5 个爆款标题" in text
assert "正文（约200字）" in text
assert "3 个封面文案" in text
print("   ✅ 格式化正确")
print()
print(text[:200] + "...\n")

# 2. 测试保存文件
print("📋 测试 save_to_file...")
filepath = save_to_file("AI副业", text, "test_output")
assert os.path.exists(filepath)
print(f"   ✅ 文件已保存: {filepath}")

# 3. 清理测试输出
import shutil
shutil.rmtree("test_output", ignore_errors=True)

print("\n" + "=" * 50)
print("✅ 所有测试通过！代码可正常运行")
print("=" * 50)
print("""
🔑 下一步：配置 API Key

  编辑 config.py，将 DEEPSEEK_API_KEY 改为你的 Key：

    1. 打开 config.py
    2. 找到这一行：
       DEEPSEEK_API_KEY = "sk-your-api-key-here"
    3. 替换为你的 DeepSeek API Key
    4. 保存即可

  如何获取 API Key？
    访问 https://platform.deepseek.com/ -> 注册 -> API Key 管理

  运行方式：
    python generator.py         # 交互式运行
    python run_batch.py         # 批量运行（从 topics.txt 读取）
""")
