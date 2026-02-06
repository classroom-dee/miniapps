from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import subprocess
import os

app = FastAPI()

DJVU_DIR = "/data"
CACHE_DIR = "/cache"

os.makedirs(CACHE_DIR, exist_ok=True)

@app.get("/page/{book}/{page}")
def get_page(book: str, page: int):
    djvu = f"{DJVU_DIR}/{book}.djvu"
    out = f"{CACHE_DIR}/{book}_{page}.png"

    if not os.path.exists(djvu):
        raise HTTPException(404, "Book not found")

    if not os.path.exists(out):
        subprocess.run([
            "ddjvu",
            "-format=png",
            f"-page={page}",
            djvu,
            out
        ], check=True)

    return FileResponse(out, media_type="image/png")
