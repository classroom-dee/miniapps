import subprocess
import os
import tempfile
import gc
import time
import threading

from faster_whisper import WhisperModel

# uses one context to avoid repeated model loading
_MODELS = {}

# on idle unload
_MODEL_LAST_USED = {}
_MODEL_LOCK = threading.Lock()
_SWEEPER_STARTED = False
_MODEL_IDLE_TIMEOUT_SEC = 30.0
_SWEEP_INTERVAL_SEC = 2.0

SUPPORTED_VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".flv", ".mov", ".webm", ".mpg", ".mpeg"
}


def extract_audio(video_path: str) -> str:
    """
    Extract mono 16kHz WAV audio from video using ffmpeg.
    Returns path to wav file.
    """
    wav_fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(wav_fd)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-ac", "1",
        "-ar", "16000",
        "-vn",
        wav_path
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return wav_path


def _maybe_empty_cuda_cache():
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def _unload_model(device: str):
    # Remove cached model and force cleanup.
    with _MODEL_LOCK:
        model = _MODELS.pop(device, None)
        _MODEL_LAST_USED.pop(device, None)

    if model is not None:
        # Drop reference + collect garbage to encourage VRAM release.
        del model
        gc.collect()
        if device == "cuda":
            _maybe_empty_cuda_cache()


def _sweeper_loop():
    while True:
        now = time.monotonic()
        to_unload = []

        with _MODEL_LOCK:
            for device, last_used in list(_MODEL_LAST_USED.items()):
                if (now - last_used) >= _MODEL_IDLE_TIMEOUT_SEC:
                    to_unload.append(device)

        for device in to_unload:
            _unload_model(device)

        time.sleep(_SWEEP_INTERVAL_SEC)


def _ensure_sweeper_started():
    global _SWEEPER_STARTED
    with _MODEL_LOCK:
        if _SWEEPER_STARTED:
            return
        
        # daemon sweeper thread 
        t = threading.Thread(target=_sweeper_loop, daemon=True)
        t.start()
        _SWEEPER_STARTED = True


def get_model(device: str):
    _ensure_sweeper_started()

    with _MODEL_LOCK:
        if device not in _MODELS:
            if device == "cuda":
                _MODELS[device] = WhisperModel(
                    "medium",
                    device="cuda",
                    compute_type="float16"
                )
            else:
                _MODELS[device] = WhisperModel(
                    "medium",
                    device="cpu",
                    compute_type="int8"
                )

    # mark as used whenever fetched
    _MODEL_LAST_USED[device] = time.monotonic()
    return _MODELS[device]


def transcribe_to_srt(audio_path: str, language: str, device: str) -> str:
    """
    Transcribe audio and return SRT content as string.
    """
    model = get_model(device)

    segments, _ = model.transcribe(
        audio_path,
        language=language, # None -> autodetect
        vad_filter=True
    )

    with _MODEL_LOCK:
        _MODEL_LAST_USED[device] = time.monotonic()

    def format_timestamp(seconds: float) -> str:
        ms = int((seconds % 1) * 1000)
        s = int(seconds) % 60
        m = int(seconds // 60) % 60
        h = int(seconds // 3600)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    srt_lines = []
    for i, seg in enumerate(segments, start=1):
        start = format_timestamp(seg.start)
        end = format_timestamp(seg.end)
        text = seg.text.strip()

        srt_lines.extend([
            str(i),
            f"{start} --> {end}",
            text,
            ""
        ])

    return "\n".join(srt_lines)
