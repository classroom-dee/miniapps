FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y ffmpeg python3 python3-pip && \
    useradd -m cap-gen-user && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .
RUN chown -R cap-gen-user:cap-gen-user /app

USER cap-gen-user

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
