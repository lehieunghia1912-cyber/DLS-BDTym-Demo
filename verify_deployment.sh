#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# ZaloPay BD Agent — Deployment Verification Script
# Chạy: bash verify_deployment.sh
# ─────────────────────────────────────────────────────────────────

ENDPOINT="https://endpoint-b1a92c63-92e9-4420-9bf0-3aea94356a56.agentbase-runtime.aiplatform.vngcloud.vn"
GREEN='\033[92m'; RED='\033[91m'; YELLOW='\033[93m'; CYAN='\033[96m'; BOLD='\033[1m'; RESET='\033[0m'

PASS=0; FAIL=0

check() {
  local label="$1" status="$2" expected="$3" body="$4"
  if [ "$status" = "$expected" ]; then
    echo -e "${GREEN}  ✓ ${label} — HTTP ${status}${RESET}"
    [ -n "$body" ] && echo -e "    ${CYAN}$(echo $body | python3 -m json.tool 2>/dev/null || echo $body)${RESET}"
    PASS=$((PASS+1))
  else
    echo -e "${RED}  ✗ ${label} — HTTP ${status} (expected ${expected})${RESET}"
    [ -n "$body" ] && echo -e "    ${YELLOW}${body}${RESET}"
    FAIL=$((FAIL+1))
  fi
}

echo -e "\n${BOLD}${CYAN}╔══════════════════════════════════════════════════════╗"
echo -e "║      ZALOPAY BD AGENT — DEPLOYMENT VERIFY             ║"
echo -e "╚══════════════════════════════════════════════════════╝${RESET}"
echo -e "  Endpoint: ${CYAN}${ENDPOINT}${RESET}\n"

# ── Test 1: Health check ──────────────────────────────────────
echo -e "${BOLD}[1/4] Health Check${RESET}"
STATUS=$(curl -s -o /tmp/zp_body.txt -w "%{http_code}" --max-time 10 "${ENDPOINT}/health")
BODY=$(cat /tmp/zp_body.txt)
check "GET /health" "$STATUS" "200" "$BODY"

# ── Test 2: Root info ─────────────────────────────────────────
echo -e "\n${BOLD}[2/4] Root Info${RESET}"
STATUS=$(curl -s -o /tmp/zp_body.txt -w "%{http_code}" --max-time 10 "${ENDPOINT}/")
BODY=$(cat /tmp/zp_body.txt)
check "GET /" "$STATUS" "200" "$BODY"

# ── Test 3: Chat — Turn 1 (QR ZaloPay) ───────────────────────
echo -e "\n${BOLD}[3/4] Chat Test — Hỏi về QR ZaloPay${RESET}"
STATUS=$(curl -s -o /tmp/zp_body.txt -w "%{http_code}" --max-time 20   -X POST "${ENDPOINT}/chat"   -H "Content-Type: application/json"   -d '{"message":"Chào anh, tôi đang quản lý chuỗi 15 cửa hàng thời trang. Quy trình tích hợp QR ZaloPay mất bao lâu và cần chuẩn bị gì?","session_id":"verify-001"}')
BODY=$(cat /tmp/zp_body.txt)
check "POST /chat (Turn 1)" "$STATUS" "200" "$BODY"

# ── Test 4: Chat — Turn 2 (hỏi phí, cùng session) ────────────
echo -e "\n${BOLD}[4/4] Chat Test — Hỏi về phí chiết khấu (multi-turn)${RESET}"
STATUS=$(curl -s -o /tmp/zp_body.txt -w "%{http_code}" --max-time 20   -X POST "${ENDPOINT}/chat"   -H "Content-Type: application/json"   -d '{"message":"Phí MDR cho QR là bao nhiêu? Có thể thương lượng không nếu doanh thu tháng trên 5 tỷ?","session_id":"verify-001"}')
BODY=$(cat /tmp/zp_body.txt)
check "POST /chat (Turn 2 — multi-turn session)" "$STATUS" "200" "$BODY"

# ── Summary ───────────────────────────────────────────────────
TOTAL=$((PASS+FAIL))
echo -e "\n${BOLD}═══════════════════════════════════════════"
if [ $FAIL -eq 0 ]; then
  echo -e "${GREEN}  KẾT QUẢ: ${PASS}/${TOTAL} PASS ✓ — Agent hoạt động ổn định!${RESET}"
else
  echo -e "${RED}  KẾT QUẢ: ${PASS}/${TOTAL} PASS — ${FAIL} lỗi cần kiểm tra${RESET}"
fi
echo -e "${BOLD}  Console: https://aiplatform.console.vngcloud.vn/agent-runtime?tab=runtime${RESET}"
echo -e "═══════════════════════════════════════════${RESET}\n"
