# Document to PNG API

A minimal FastAPI service that converts document pages into PNG images on demand. It currently supports DjVu files and returns rendered page images through a simple HTTP endpoint, with basic caching to avoid repeated conversions.

### What it does
- Serves document pages as PNG images
- Converts DjVu pages on demand using ddjvu
- Caches rendered pages after first request
- Returns images directly from a simple API route
- Uses FastAPI for a lightweight HTTP interface
- Designed to be easy to extend to other document formats

### Why
- Built as a small utility for turning document pages into browser-friendly images
- Useful for previewing archived or scanned documents without converting entire files ahead of time
- Keeps the implementation intentionally small and focused

### Dependencies
- See `requirements.txt`
- Docker

### Setup
1. Put your .djvu files in the mounted /data directory
2. Build the Docker image: `docker build -t your_image .`

### Run
```bash
docker run --name doc2png \
    -p 8000:8000 \
    -v /your/djvu/folder:/data \
    -v /your/cache/folder:/cache \
    your_image

# and then
curl http://localhost:8000/page/your_book/target_page
# for example, http://localhost:8000/page/my_book/1
```

### Screenshot
![Screenshot](#)

### Future Improvements
- Add PDF to PNG support
- Add support for more output formats
- UI
- Add cache cleanup strategy
- Add filename sanitization and stricter validation