import tempfile
import os

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from helpers import extract_audio, transcribe_to_srt, SUPPORTED_VIDEO_EXTENSIONS
from languages import LANGUAGES

app = FastAPI(title="Caption Generator with Whisper")
templates = Jinja2Templates(directory="templates")

@app.post("/transcribe")
async def transcribe_video(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    device: str = Form("cpu")
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported video format")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_video:
        tmp_video.write(await file.read())
        video_path = tmp_video.name

    try:
        audio_path = extract_audio(video_path)
        lang = None if language == "auto" else language
        srt_content = transcribe_to_srt(audio_path, lang, device)
    finally:
        for p in (video_path, audio_path):
            if p and os.path.exists(p):
                os.remove(p)

    out_name = os.path.splitext(file.filename)[0]

    return Response(
        content=srt_content,
        media_type="application/x-subrip",
        headers={
            "Content-Disposition": f'attachment; filename="{out_name}"'
        }
    )

@app.get("/")
def ui(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "languages": LANGUAGES}
    )