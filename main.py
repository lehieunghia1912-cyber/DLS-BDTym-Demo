#!/usr/bin/env python3
"""
ZaloPay BD Agent — Interactive CLI
Chạy: python main.py
Yêu cầu: ANTHROPIC_API_KEY trong môi trường hoặc file .env
"""

import os
import sys
from anthropic import Anthropic
from config import AGENT_NAME, MODEL, MAX_TOKENS, SYSTEM_PROMPT, Color

def load_env():
    """Đọc .env nếu có (không cần python-dotenv)."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

def check_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key or not key.startswith("sk-"):
        print(f"{Color.RED}[LỖI] Không tìm thấy ANTHROPIC_API_KEY hợp lệ.")
        print(f"  → Tạo file .env trong thư mục này với nội dung:")
        print(f"      ANTHROPIC_API_KEY=sk-ant-xxxxxxx{Color.RESET}")
        sys.exit(1)

def print_banner():
    print(f"""
{Color.BOLD}{Color.CYAN}╔══════════════════════════════════════════════════════╗
║         ZALOPAY BD AGENT — Trợ lý Phát triển KD      ║
║         Powered by Anthropic Claude                   ║
╚══════════════════════════════════════════════════════╝{Color.RESET}
{Color.YELLOW}Nhập câu hỏi để bắt đầu tư vấn. Gõ 'quit' hoặc 'exit' để thoát.
Gõ 'new' để bắt đầu cuộc hội thoại mới.{Color.RESET}
""")

def chat(client: Anthropic, history: list[dict], user_msg: str) -> str:
    history.append({"role": "user", "content": user_msg})
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=history,
    )
    assistant_msg = response.content[0].text
    history.append({"role": "assistant", "content": assistant_msg})
    return assistant_msg

def run_interactive():
    load_env()
    check_api_key()
    client = Anthropic()
    history: list[dict] = []

    print_banner()
    print(f"{Color.GREEN}[{AGENT_NAME}] Xin chào! Tôi là Minh Tuấn từ đội BD ZaloPay. "
          f"Anh/chị cần tư vấn về giải pháp thanh toán nào hôm nay ạ?{Color.RESET}\n")

    while True:
        try:
            user_input = input(f"{Color.BLUE}[Merchant] {Color.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Color.YELLOW}Cảm ơn anh/chị đã quan tâm đến ZaloPay. Hẹn gặp lại!{Color.RESET}")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print(f"{Color.YELLOW}Cảm ơn anh/chị. Chúc anh/chị ngày tốt lành!{Color.RESET}")
            break
        if user_input.lower() == "new":
            history.clear()
            print(f"{Color.CYAN}[Cuộc hội thoại mới được bắt đầu]{Color.RESET}\n")
            continue

        print(f"{Color.CYAN}[{AGENT_NAME}] Đang xử lý...{Color.RESET}", end="\r")
        reply = chat(client, history, user_input)
        print(f"\r{Color.GREEN}[{AGENT_NAME}]{Color.RESET} {reply}\n")

if __name__ == "__main__":
    run_interactive()
