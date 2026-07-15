POST {{RUNTIME_URL}}/api/v1/chat/demo-chat
Content-Type: application/json
{
  "capability": "chat",
  "model": "demo-chat",
  "input": {
    "messages": []
  },
  "parameters": {
    "max_output_tokens": 128,
    "temperature": 0.7,
    "truncation": "auto"
  },
  "stream": true
}
HTTP 200
[Asserts]
header "content-type" contains "text/event-stream"
body contains "event: delta"
body contains "data: {\"delta\":\"demo response\"}"
body contains "event: done"
