"""
批量生成快捷入口
用法：python run_batch.py

直接从 topics.txt 读取主题列表，批量生成
"""
from generator import batch_generate

# 从文件读取主题
with open("topics.txt", "r", encoding="utf-8") as f:
    topics = [line.strip() for line in f if line.strip()]

print(f"📖 从 topics.txt 读取了 {len(topics)} 个主题:")
for t in topics:
    print(f"   - {t}")

batch_generate(topics)
