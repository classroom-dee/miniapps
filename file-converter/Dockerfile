FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    djvulibre-bin \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install -r requirements.txt --no-cache-dir

WORKDIR /src

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
