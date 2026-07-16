POST {{RUNTIME_URL}}/api/v1/asr/faster-whisper2
Content-Type: application/json
{
  "capability": "asr",
  "model": "faster-whisper2",
  "input": {
    "audio_path": "{{WHISPER_AUDIO_PATH}}"
  },
  "parameters": {
    "vad_filter": true
  },
  "stream": false
}
HTTP 200
[Asserts]
header "content-type" contains "application/json"
jsonpath "$.outputs[0].mime_type" == "text/plain"
jsonpath "$.metadata.language" == "zh"
jsonpath "$.metadata.duration_seconds" > 0

POST {{RUNTIME_URL}}/api/v1/asr/faster-whisper2
Content-Type: application/json
{
  "capability": "asr",
  "model": "faster-whisper2",
  "input": {
    "audio_path": "{{WHISPER_AUDIO_PATH}}"
  },
  "parameters": {
    "vad_filter": true
  },
  "stream": true
}
HTTP 200
[Asserts]
header "content-type" contains "text/event-stream"
body contains "event: progress"
body contains "event: done"
body contains "\"language\":\"zh\""
