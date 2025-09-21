import os, time, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from scraper import canvas_scraper

from dotenv import set_key
from pathlib import Path

import runmodel 


load_dotenv()
app = Flask(__name__)
# CORS configuration for development (be more permissive for Chrome extensions)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
# ---- Config ----
CANVAS_BASE = os.getenv("CANVAS_BASE_URL", "").rstrip("/")
BACKEND_URL  = os.getenv("BACKEND_URL", "")  # Default to empty string for testing
BACKEND_AUTH = os.getenv("BACKEND_AUTH")  # e.g., "Bearer <key>"
env_path = Path(".env")
# ---- Helpers: Simple token validation ----
def validate_tokens(canvas_tokens: dict, google_tokens: dict) -> bool:
    """Check if at least one valid token is provided"""
    canvas_valid = bool(canvas_tokens and canvas_tokens.get("access_token"))
    google_valid = bool(google_tokens and google_tokens.get("access_token"))
    return canvas_valid or google_valid
# ---- Routes ----
@app.get("/api/health")
def health():
    return jsonify({"ok": True})
@app.post("/api/courses")
def get_courses():
    """Get list of courses from Canvas using the provided token"""
    body = request.get_json(force=True, silent=True) or {}
    canvas_tokens = body.get("canvas_tokens", {})
    # Debug logging
    print(f":mag: GET COURSES REQUEST:")
    print(f"   Canvas tokens: {bool(canvas_tokens.get('access_token'))}")
    print(f"   Full body: {body}")
    if not canvas_tokens.get("access_token"):
        return jsonify({"error": "missing_canvas_token", "message": "Canvas authentication required"}), 401

    # Real mode: call Canvas API
    headers = {
        "Authorization": f"Bearer {canvas_tokens['access_token']}",
        "Content-Type": "application/json"
    }
@app.post("/api/ask")
def ask():
    # 1) Read user input and tokens from request
    body = request.get_json(force=True, silent=True) or {}
    question = body.get("question", "").strip()
    context = body.get("context", {})
    canvas_tokens = body.get("canvas_tokens", {})
    google_tokens = body.get("google_tokens", {})
    if not question:
        return jsonify({"error":"missing_question"}), 400
    # 2) Validate that at least one token is provided
    if not validate_tokens(canvas_tokens, google_tokens):
        return jsonify({"error":"no_tokens_available","message":"Canvas or Google Drive authentication required"}), 401
    # 3) Check if we're in test mode (no backend URL configured)
    if not BACKEND_URL:
        test_response = {
            "status": "success",
            "message": None, #########################################################3
            "user_question": question,
            "user_context": context.get("courses", []),
            "tokens": {
                "canvas": {
                    "available": (canvas_tokens.get("access_token")),
                    "base_url": CANVAS_BASE if canvas_tokens.get("access_token") else None
                },
                "google_drive": {
                    "available": (google_tokens.get("access_token"))
                }
            },
            "simulated_answer": "",
            "timestamp": int(time.time())
        }
        course_code = test_response["user_context"]
        set_key(str(env_path), "CANVAS_ACCESS_TOKEN", test_response["tokens"]["canvas"]["available"])
        set_key(str(env_path), "DRIVE_API_KEY", google_tokens["access_token"])
        runmodel.change_selected_class(course_code)
        test_response["message"] = runmodel.prompt(question)

        return jsonify(test_response)
    # 4) Build payload to your team's backend with both tokens
    outbound = {
        "question": question,
        "context": context,
        "tokens": {
            "canvas": canvas_tokens,
            "google": google_tokens
        }
    }
    headers = {"Content-Type": "application/json"}
    if BACKEND_AUTH:
        headers["Authorization"] = BACKEND_AUTH
    try:
        resp = requests.post(BACKEND_URL, json=outbound, headers=headers, timeout=60)
    except requests.RequestException as e:
        return jsonify({"error":"backend_unreachable","details": str(e)}), 502
    if not resp.ok:
        return jsonify({"error":"backend_error","status": resp.status_code, "body": resp.text}), 502
    # 5) Pass the backend response back to the extension
    return (resp.text, 200, {"Content-Type": "application/json"})
if __name__ == "__main__":
    # Listen on all interfaces so other computers can connect
    app.run(host='0.0.0.0', port=5001, debug=True)