GET {{RUNTIME_URL}}/api/v1
HTTP 200
[Asserts]
header "content-type" contains "application/json"
jsonpath "$.models[0].id" == "demo-chat"
jsonpath "$.models[0].capability" == "chat"
jsonpath "$.capabilities[0]" == "chat"
