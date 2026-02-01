from cairosvg import svg2png
from PIL import Image
import io
import os
from pathlib import Path

PROJ_PATH = Path(__file__).resolve().parent.parent
IMG_DIR = os.path.join(os.path.join(PROJ_PATH, "assets"), "meteocon")
SIZE = 18  # px

for f in os.listdir(IMG_DIR):
    if not f.endswith(".svg"):
        continue

    svg_path = os.path.join(IMG_DIR, f)
    png_path = os.path.join(IMG_DIR, f.replace(".svg", ".png"))

    png_bytes = svg2png(url=svg_path, output_width=SIZE, output_height=SIZE)
    img = Image.open(io.BytesIO(png_bytes))
    img.save(png_path)
