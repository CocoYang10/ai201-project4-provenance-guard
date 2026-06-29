from uuid import uuid4

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from audit_log import add_log_entry, get_recent_entries, update_entry_for_appeal
from detector import (
    classify_attribution,
    combine_scores,
    generate_transparency_label,
    llm_detection_signal,
    stylometric_signal,
)


app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
)


@app.errorhandler(429)
def rate_limit_handler(error):
    return (
        jsonify(
            {
                "error": "Rate limit exceeded. Please wait before submitting more content.",
                "details": str(error.description),
            }
        ),
        429,
    )


@app.post("/submit")
@limiter.limit("10 per minute;100 per day")
def submit_content():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    creator_id = data.get("creator_id") or "anonymous"

    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "A non-empty text field is required."}), 400

    content_id = str(uuid4())
    clean_text = text.strip()

    llm_result = llm_detection_signal(clean_text)
    stylometric_result = stylometric_signal(clean_text)

    llm_score = float(llm_result.get("score", 0.5))
    stylometric_score = float(stylometric_result.get("score", 0.5))
    confidence = combine_scores(llm_score, stylometric_score)
    attribution = classify_attribution(confidence)
    transparency_label = generate_transparency_label(attribution, confidence)

    log_entry = {
        "content_id": content_id,
        "creator_id": creator_id,
        "text_preview": clean_text[:160],
        "attribution": attribution,
        "confidence": confidence,
        "llm_score": round(llm_score, 2),
        "llm_label": llm_result.get("label", "uncertain"),
        "llm_reason": llm_result.get("reason", ""),
        "stylometric_score": round(stylometric_score, 2),
        "stylometric_features": stylometric_result.get("features", {}),
        "stylometric_reason": stylometric_result.get("reason", ""),
        "transparency_label": transparency_label,
        "status": "classified",
    }
    add_log_entry(log_entry)

    return jsonify(
        {
            "content_id": content_id,
            "creator_id": creator_id,
            "attribution": attribution,
            "confidence": confidence,
            "transparency_label": transparency_label,
            "signals": {
                "llm_score": round(llm_score, 2),
                "stylometric_score": round(stylometric_score, 2),
            },
            "status": "classified",
        }
    )


@app.get("/log")
def view_log():
    limit = request.args.get("limit", default=10, type=int)
    limit = max(1, min(limit, 100))
    return jsonify({"entries": get_recent_entries(limit)})


@app.post("/appeal")
def appeal_content():
    data = request.get_json(silent=True) or {}
    content_id = data.get("content_id")
    creator_reasoning = data.get("creator_reasoning", "")

    if not content_id:
        return jsonify({"error": "content_id is required."}), 400

    updated = update_entry_for_appeal(content_id, creator_reasoning)
    if not updated:
        return jsonify({"error": "No audit log entry found for that content_id."}), 404

    return jsonify(
        {
            "content_id": content_id,
            "status": "under_review",
            "message": "Appeal received and content is now under review.",
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
