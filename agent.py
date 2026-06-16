#!/usr/bin/env python3
"""
Zalopay BD Agent — HTTP Server (AgentBase Runtime)
Expose:
  GET  /health        → 200 OK  (AgentBase health check)
  POST /chat          → {"message": "..."} → {"reply": "..."}
  GET  /              → agent info
Port: 8080 (required by AgentBase Runtime)
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from openai import OpenAI
from config import AGENT_NAME, MODEL, MAX_TOKENS, SYSTEM_PROMPT

# In-memory session store: session_id -> message history (excludes system prompt)
_sessions: dict[str, list[dict]] = {}

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

load_env()
client = OpenAI(
    api_key=os.environ.get("LLM_API_KEY"),
    base_url=os.environ.get("LLM_BASE_URL"),
)


def chat(session_id: str, user_msg: str) -> str:
    history = _sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": user_msg})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=messages,
    )
    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})
    return reply


class AgentHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # suppress default access log
        pass

    def _send_json(self, status: int, body: dict):
        payload = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "agent": AGENT_NAME})
        elif self.path in ("/", "/index.html"):
            self._serve_html()
        else:
            self._send_json(404, {"error": "not found"})

    def _serve_html(self):
        html_path = os.path.join(os.path.dirname(__file__), "index.html")
        try:
            with open(html_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self._send_json(404, {"error": "UI not found"})

    def do_POST(self):
        if self.path != "/chat":
            self._send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length))
        except Exception:
            self._send_json(400, {"error": "invalid JSON"})
            return

        message = body.get("message", "").strip()
        session_id = body.get("session_id", "default")

        if not message:
            self._send_json(400, {"error": "message is required"})
            return

        try:
            reply = chat(session_id, message)
            self._send_json(200, {"reply": reply, "session_id": session_id})
        except Exception as e:
            self._send_json(500, {"error": str(e)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), AgentHandler)
    print(f"[{AGENT_NAME}] Listening on 0.0.0.0:{port}")
    server.serve_forever()
