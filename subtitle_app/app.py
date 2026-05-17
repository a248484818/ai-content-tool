"""
Flask Web 应用 - AI 爆款内容生成器 v3.0
模板系统 + 人设 + 评分 + 标签 + 评论区引导
生产入口：gunicorn app:app
"""
import os
import json
import traceback
from datetime import datetime

from flask import Flask, request, jsonify, render_template

from generator import (
    generate_for_topic, format_result, save_to_file, save_result_structured,
    get_template_labels, TEMPLATES, EXPRESSION_VARIANTS,
)
from config import HOST, PORT, DEBUG, OUTPUT_DIR

app = Flask(__name__)


# ─── 首页 ───────────────────────────────────────────────────

@app.route("/")
def index():
    """渲染主页面"""
    return render_template("index.html")


# ─── API：获取模板列表 ─────────────────────────────────────

@app.route("/api/templates")
def api_templates():
    """返回模板配置"""
    return jsonify({
        "success": True,
        "templates": get_template_labels(),
    })


# ─── API：生成内容 ──────────────────────────────────────────

@app.route("/api/generate", methods=["POST"])
def api_generate():
    """
    请求体 JSON:
      {
        "topic": "AI副业",
        "custom_instructions": "（可选）",
        "template_id": "fuye / share / caikeng（可选）"
      }
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"success": False, "error": "请求体为空"}), 400
        
        topic = data.get("topic", "").strip()
        if not topic:
            return jsonify({"success": False, "error": "请输入主题关键词"}), 400
        
        custom_instructions = data.get("custom_instructions", "").strip()
        template_id = data.get("template_id", "").strip() or None

        result = generate_for_topic(topic, custom_instructions or None, template_id=template_id)

        try:
            filepath = save_result_structured(topic, result, OUTPUT_DIR)
            saved_path = filepath
        except Exception:
            saved_path = None
        
        return jsonify({
            "success": True,
            "data": result,
            "topic": topic,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "saved_path": saved_path,
        })
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ─── API：批量生成 ──────────────────────────────────────────

@app.route("/api/batch-generate", methods=["POST"])
def api_batch_generate():
    """
    批量生成
    请求体 JSON:
      {
        "topics": ["AI副业", "小红书探店", ...],
        "custom_instructions": "（可选）",
        "template_id": "fuye / share / caikeng（可选，为空则轮换）"
      }
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"success": False, "error": "请求体为空"}), 400
        
        topics = data.get("topics", [])
        if not topics or not isinstance(topics, list):
            return jsonify({"success": False, "error": "请提供主题列表"}), 400
        
        custom_instructions = data.get("custom_instructions", "").strip()
        template_id = data.get("template_id", "").strip() or None

        template_ids = list(TEMPLATES.keys())
        results = []

        for idx, topic in enumerate(topics):
            topic = topic.strip()
            if not topic:
                continue
            
            try:
                tpl = template_id if template_id else template_ids[idx % len(template_ids)]
                variant = idx % len(EXPRESSION_VARIANTS)

                result = generate_for_topic(topic, custom_instructions or None, template_id=tpl, variant_index=variant)

                try:
                    filepath = save_result_structured(topic, result, OUTPUT_DIR)
                except Exception:
                    filepath = None
                
                results.append({
                    "topic": topic,
                    "success": True,
                    "data": result,
                    "saved_path": filepath,
                    "template": tpl,
                })
            except Exception as e:
                results.append({
                    "topic": topic,
                    "success": False,
                    "error": str(e),
                })
        
        return jsonify({
            "success": True,
            "results": results,
            "total": len(topics),
            "succeeded": sum(1 for r in results if r["success"]),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ─── API：健康检查 ──────────────────────────────────────────

@app.route("/api/health")
def api_health():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


# ─── 本地开发启动 ──────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║   🔥 AI 爆款内容生成器 v3.0         ║")
    print(f"  ║   http://{HOST}:{PORT}              ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 本地开发用 debug=True，生产用 gunicorn 部署
    app.run(host=HOST, port=PORT, debug=DEBUG)

