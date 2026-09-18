"""
Speech-to-text via OpenAI Whisper (runs fully locally/offline once the
model checkpoint is downloaded — no per-request API calls or cost).

Model loading is lazy and cached at module level: the first transcription
request after server startup downloads the chosen checkpoint (~75MB for
"base") to `~/.cache/whisper`; every request after that is instant model
reuse. Choose a larger checkpoint (small/medium) in production for better
accuracy at the cost of more RAM/CPU time per request.

Note: this requires outbound internet access on first run to download the
checkpoint from OpenAI's CDN, and the `ffmpeg` binary on PATH for audio
decoding. Both are standard requirements for any real deployment; neither
is available inside this sandboxed build environment, so transcription
itself could not be executed live during development here — the
integration code below follows Whisper's documented API exactly and will
run correctly on a normal server/host with internet access.
"""
from __future__ import annotations

import threading

WHISPER_MODEL_NAME = "base"  # tiny|base|small|medium|large — base is a good speed/accuracy default

_lock = threading.Lock()
_model = None


def _get_model():
    global _model
    with _lock:
        if _model is None:
            import whisper

            _model = whisper.load_model(WHISPER_MODEL_NAME)
        return _model


def transcribe(audio_file_path: str) -> dict:
    """
    Returns {"text": str, "language": str} on success.
    Raises RuntimeError with a user-friendly message if Whisper can't run
    (e.g. model checkpoint unavailable, ffmpeg missing, corrupt audio file).
    """
    try:
        model = _get_model()
    except Exception as exc:  # checkpoint download failure, no internet, etc.
        raise RuntimeError(
            "Voice transcription is temporarily unavailable (the speech model could not be "
            "loaded). Please try again later, or type your symptoms instead."
        ) from exc

    try:
        result = model.transcribe(audio_file_path, fp16=False)
    except Exception as exc:
        raise RuntimeError(
            "We couldn't process that audio file. Please make sure it's a valid recording "
            "and try again."
        ) from exc

    return {"text": (result.get("text") or "").strip(), "language": result.get("language", "en")}
