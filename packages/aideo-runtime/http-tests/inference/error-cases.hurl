POST {{RUNTIME_URL}}/api/v1/chat/missing
Content-Type: application/json
{
  "capability": "chat",
  "model": "missing",
  "input": {"messages": []}
}
HTTP 404

POST {{RUNTIME_URL}}/api/v1/image/demo-chat
Content-Type: application/json
{
  "capability": "image",
  "model": "demo-chat",
  "input": {"prompt": "cat"}
}
HTTP 409

POST {{RUNTIME_URL}}/api/v1/chat/demo-chat
Content-Type: application/json
{
  "capability": "chat",
  "model": "different-model",
  "input": {"messages": []}
}
HTTP 422

POST {{RUNTIME_URL}}/api/v1/chat/demo-chat
Content-Type: application/json
{
  "capability": "chat",
  "model": "demo-chat",
  "input": {"messages": []},
  "parameters": {"max_output_tokens": 1025}
}
HTTP 422
