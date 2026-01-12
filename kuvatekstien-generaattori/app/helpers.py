import subprocess
import os
from faster_whisper import WhisperModel
import tempfile

# uses one context to avoid repeated model loading
_MODELS = {}

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


def get_model(device: str):
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
