#!/usr/bin/env python3
"""
Zalopay BD Agent — Automated Test
Kịch bản: Chủ chuỗi cửa hàng bán lẻ hỏi về QR Zalopay và tối ưu phí.
Chạy: python test_agent.py
"""

import os
import sys
import time
from anthropic import Anthropic
from config import MODEL, MAX_TOKENS, SYSTEM_PROMPT, Color

def load_env():
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
        print(f"{Color.RED}[LỖI] ANTHROPIC_API_KEY không hợp lệ. Kiểm tra file .env{Color.RESET}")
        sys.exit(1)

# ─── Kịch bản giả lập ──────────────────────────────────────────────────────
TEST_SCENARIO = [
    {
        "label": "Turn 1 — Giới thiệu & nhu cầu",
        "message": (
            "Chào anh, tôi đang quản lý chuỗi 15 cửa hàng thời trang tại TP.HCM và Hà Nội, "
            "doanh thu mỗi tháng khoảng 5 tỷ. Tôi muốn tìm hiểu về giải pháp QR Zalopay, "
            "không biết quy trình tích hợp như thế nào và mất bao lâu?"
        ),
    },
    {
        "label": "Turn 2 — Hỏi về phí chiết khấu",
        "message": (
            "Anh có thể cho tôi biết biểu phí cụ thể không? "
            "Hiện tại bên tôi đang dùng một cổng khác với mức phí 1.3% cho QR. "
            "Zalopay có thể cạnh tranh được không?"
        ),
    },
    {
        "label": "Turn 3 — Hỏi tối ưu dòng tiền & BNPL",
        "message": (
            "Ngoài QR, tôi cũng đang nghĩ đến việc tích hợp trả góp cho khách mua hàng "
            "giá trị cao trên 3 triệu. Zalopay có giải pháp nào giúp tôi tăng giá trị đơn hàng "
            "mà không làm phức tạp quy trình thanh toán không?"
        ),
    },
    {
        "label": "Turn 4 — Chốt bước tiếp theo",
        "message": (
            "Nghe có vẻ phù hợp đấy. Nếu tôi muốn triển khai thử tại 3 cửa hàng trước, "
            "bước tiếp theo tôi cần làm gì và cần chuẩn bị những hồ sơ gì?"
        ),
    },
]

def run_test():
    load_env()
    check_api_key()
    client = Anthropic()
    history: list[dict] = []

    print(f"""
{Color.BOLD}{Color.CYAN}╔══════════════════════════════════════════════════════╗
║         ZALOPAY BD AGENT — AUTO TEST                  ║
║         Kịch bản: Chủ chuỗi bán lẻ × QR + BNPL       ║
╚══════════════════════════════════════════════════════╝{Color.RESET}
""")

    passed = 0
    failed = 0

    for idx, turn in enumerate(TEST_SCENARIO, 1):
        print(f"{Color.YELLOW}{'─'*60}")
        print(f"[{turn['label']}]{Color.RESET}")
        print(f"{Color.BLUE}[Merchant]{Color.RESET} {turn['message']}\n")

        start = time.time()
        try:
            history.append({"role": "user", "content": turn["message"]})
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=history,
            )
            reply = response.content[0].text
            history.append({"role": "assistant", "content": reply})
            elapsed = time.time() - start

            print(f"{Color.GREEN}[BD Agent]{Color.RESET} {reply}\n")
            print(f"{Color.CYAN}  ✓ Phản hồi thành công | Thời gian: {elapsed:.2f}s | "
                  f"Input tokens: {response.usage.input_tokens} | "
                  f"Output tokens: {response.usage.output_tokens}{Color.RESET}\n")
            passed += 1

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Color.RED}  ✗ LỖI sau {elapsed:.2f}s: {e}{Color.RESET}\n")
            failed += 1

    # Summary
    total = passed + failed
    print(f"\n{Color.BOLD}{'═'*60}")
    print(f"KẾT QUẢ KIỂM THỬ: {passed}/{total} turns thành công", end="")
    if failed == 0:
        print(f" ✓ PASS{Color.RESET}")
    else:
        print(f" ✗ FAIL ({failed} lỗi){Color.RESET}")
    print(f"{'═'*60}{Color.RESET}")

    return failed == 0

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
