# ZaloPay BD Agent

Trợ lý Phát triển Kinh doanh ZaloPay — deployed trên GreenNode AgentBase Runtime.

## Endpoint Production

```
https://endpoint-b1a92c63-92e9-4420-9bf0-3aea94356a56.agentbase-runtime.aiplatform.vngcloud.vn
```

## Cấu trúc dự án

```
ZaloPay-BD-Agent/
├── agent.py               # HTTP server chính (port 8080, /health, /chat)
├── main.py                # CLI interactive (chạy local)
├── config.py              # Role/Persona, System Prompt, biểu phí
├── test_agent.py          # Auto-test 4 turns kịch bản bán lẻ
├── verify_deployment.sh   # Kiểm tra endpoint production
├── Dockerfile             # Build image linux/amd64
├── .dockerignore
├── requirements.txt
├── .env.example
└── greennode-agentbase-skills/   # AgentBase skill toolkit
```

## API

### Health check
```bash
curl https://endpoint-b1a92c63-92e9-4420-9bf0-3aea94356a56.agentbase-runtime.aiplatform.vngcloud.vn/health
# → {"status": "ok", "agent": "ZaloPay BD Assistant"}
```

### Chat
```bash
curl -X POST https://endpoint-b1a92c63-92e9-4420-9bf0-3aea94356a56.agentbase-runtime.aiplatform.vngcloud.vn/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Quy trình tích hợp QR ZaloPay mất bao lâu?", "session_id": "user-123"}'
# → {"reply": "...", "session_id": "user-123"}
```

- `session_id` tùy chọn — dùng để duy trì lịch sử hội thoại multi-turn
- Mỗi session lưu in-memory; reset khi container restart

## Verify deployment

```bash
bash verify_deployment.sh
```

## Chạy local

```bash
cp .env.example .env          # điền ANTHROPIC_API_KEY
pip install -r requirements.txt
python main.py                # CLI interactive
python agent.py               # HTTP server local (port 8080)
python test_agent.py          # Auto-test 4 turns
```

## Console GreenNode

https://aiplatform.console.vngcloud.vn/agent-runtime?tab=runtime
