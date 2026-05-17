"""
配置文件 - 所有配置优先从环境变量读取
"""
import os

# DeepSeek API 配置（必须通过环境变量设置 DEEPSEEK_API_KEY）
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError(
        "❌ 未设置环境变量 DEEPSEEK_API_KEY\n"
        "   请运行: export DEEPSEEK_API_KEY='sk-your-key-here'\n"
        "   或在项目根目录创建 .env 文件写入: DEEPSEEK_API_KEY=sk-your-key-here"
    )

DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# 服务器配置
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5001"))
DEBUG = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")

# 输出目录（临时存储，生产环境建议用云存储）
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")

