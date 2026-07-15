# aideo-models

`aideo-models` contains the lazy local-model implementations used by Aideo
inference runtimes. It currently provides LTX2 text-to-video and
Faster-Whisper2 speech-to-text execution.

It deliberately does not provide HTTP APIs, Provider routing, or filesystem
path policy. `aideo-runtime` owns the shared models/input/output roots, checks
relative paths, and passes validated `pathlib.Path` values to this package.

## Platform support

The package itself imports on macOS and other development platforms without GPU
libraries. LTX, Faster-Whisper2, PyTorch CUDA 13, and NVIDIA dependencies are
declared only for Linux and are imported lazily on first model use.

Production configuration remains in the Runtime `.env` file. In particular,
LTX checkpoint paths and Whisper download storage are relative to the Runtime's
`AIDEO_RUNTIME_MODELS_DIR`; this package does not introduce private model,
input, or output roots.

## Public API

```python
from aideo_models import (
    FasterWhisper2Model,
    LTX2Model,
    TranscriptionRequest,
    VideoGenerationRequest,
)
```

The calling Runtime must validate `TranscriptionRequest.audio_path` and
`VideoGenerationRequest.output_path` before invoking a model.
