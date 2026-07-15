GET {{RUNTIME_URL}}/api/v1/chat
HTTP 200
[Asserts]
jsonpath "$.capability" == "chat"
jsonpath "$.models[0].id" == "demo-chat"

GET {{RUNTIME_URL}}/api/v1/image
HTTP 200
[Asserts]
jsonpath "$.capability" == "image"
jsonpath "$.models" count == 0
