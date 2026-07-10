from faster_whisper import WhisperModel

# input audio file
file_path = "data/audio/16k16bit.mp3"
device = "cuda"  # or "cpu"
# "float16" on GPU with FP16
# "int8_float16" on GPU with INT8
# "int8" on CPU with INT8
compute_type = "float16"
model_size_or_path = "../models/faster-whisper-large-v3"

model = WhisperModel(model_size_or_path, device=device, compute_type=compute_type)

segments, info = model.transcribe(file_path, beam_size=5)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))       