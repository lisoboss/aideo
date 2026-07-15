GET {{RUNTIME_URL}}/health
HTTP 200
[Asserts]
header "content-type" contains "application/json"
jsonpath "$.status" == "ok"
jsonpath "$.models" == 1
