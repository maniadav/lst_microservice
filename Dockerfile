FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install CPU-only PyTorch and matching packages first (avoids CUDA/libnvrtc deps)
RUN pip install --no-cache-dir \
    torch==2.11.0+cpu \
    torchaudio==2.11.0 \
    torchvision==0.26.0+cpu \
    torchcodec==0.14.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir whisperx@git+https://github.com/m-bain/whisperX.git --no-deps

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
