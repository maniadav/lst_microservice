import os
import tempfile
import time
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.responses import JSONResponse
import modal

# Define the Modal App
app = modal.App("whisperx-service")

# Define the container environment
# We install ffmpeg, torch (with CUDA support), and WhisperX from git
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git")
    .pip_install(
        "fastapi",
        "uvicorn",
        "python-multipart",
    )
    .pip_install(
        "torch==2.1.2",
        "torchaudio==2.1.2",
        index_url="https://download.pytorch.org/whl/cu121"
    )
    .pip_install(
        "git+https://github.com/m-bain/whisperX.git",
        "pyannote-audio>=4.0.0",
        "pandas>=2.2.3"
    )
)

@app.cls(
    gpu="T4",  # Use NVIDIA T4 GPU for ultra-fast transcription (approx. $0.0001 per second)
    image=image,
    timeout=600,
    min_containers=1,  # Keep 1 container warm to minimize cold starts
    secrets=[modal.Secret.from_name("HF_TOKEN")]  # Store your HF_TOKEN in Modal Secrets
)
class WhisperXTranscriber:
    @modal.enter()
    def load_models(self):
        """Loads WhisperX models into GPU memory on startup."""
        import whisperx
        
        device = "cuda"
        compute_type = "float16"  # Using float16 speedup on GPU
        model_name = "large-v3"
        
        print("Loading WhisperX transcription model...")
        self.model = whisperx.load_model(model_name, device=device, compute_type=compute_type)
        
        # Load Pyannote Diarization Pipeline if HF_TOKEN is present
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            print("Loading Pyannote diarization pipeline...")
            from whisperx.diarize import DiarizationPipeline
            try:
                # In whisperx, DiarizationPipeline uses 'token' parameter
                self.diarize_model = DiarizationPipeline(
                    model_name="pyannote/speaker-diarization-3.1",
                    token=hf_token,
                    device=device,
                )
            except Exception as e:
                print(f"Failed to load DiarizationPipeline: {e}. Falling back to transcription-only.")
                self.diarize_model = None
        else:
            print("WARNING: HF_TOKEN secret not found. Diarization will be disabled.")
            self.diarize_model = None

    @modal.method()
    def transcribe(self, audio_bytes: bytes, audio_suffix: str, language: str = "auto") -> dict:
        """Run WhisperX transcription + speaker alignment + diarization."""
        import whisperx
        import numpy as np

        device = "cuda"
        
        # Save bytes to temp file inside the container
        with tempfile.NamedTemporaryFile(suffix=audio_suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # 1. Transcribe audio
            print(f"Processing audio: {tmp_path}")
            audio = whisperx.load_audio(tmp_path)
            
            # If auto-detection or auto-language
            asr_options = {}
            if language and language != "auto":
                asr_options["language"] = language

            result = self.model.transcribe(audio, batch_size=16, **asr_options)
            detected_language = result.get("language", "en")
            print(f"Detected/Selected language: {detected_language}")

            # 2. Align word timestamps (essential for diarization mapping)
            try:
                align_model, align_metadata = whisperx.load_align_model(
                    language_code=detected_language,
                    device=device,
                )
                result = whisperx.align(
                    result["segments"],
                    align_model,
                    align_metadata,
                    audio,
                    device,
                    return_char_alignments=False,
                )
            except Exception as align_err:
                print(f"Alignment failed: {align_err}. Proceeding with raw segments.")

            # 3. Speaker Diarization
            if self.diarize_model is not None:
                try:
                    print("Running speaker diarization...")
                    diarize_segments = self.diarize_model(tmp_path)
                    result = whisperx.assign_word_speakers(diarize_segments, result)
                except Exception as diarize_err:
                    print(f"Diarization failed: {diarize_err}. Returning un-diarized text.")

            # 4. Group consecutive speech by speaker
            conversation = []

            for seg in result.get("segments", []):
                speaker = seg.get("speaker", "SPEAKER_00")
                text = seg.get("text", "").strip()

                if not text:
                    continue

                # Merge consecutive segments from the same speaker
                if conversation and conversation[-1]["speaker"] == speaker:
                    conversation[-1]["text"] += " " + text
                else:
                    conversation.append({
                        "speaker": speaker,
                        "text": text
                    })

            return {
                "language": detected_language,
                "transcript": conversation
            }
                        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


# --- Expose the Modal class as a HTTP Web API Endpoint ---
web_app = FastAPI()
transcriber = WhisperXTranscriber()

@web_app.post("/transcribe")
async def api_transcribe(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    authorization: Optional[str] = Header(None)
):
    
    
    # Simple API Key Verification (Configure via env var inside Modal if needed)
    secret_key = os.environ.get("TRANSCRIPTION_API_KEY")
    if secret_key and authorization != f"Bearer {secret_key}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    content = await file.read()
    suffix = os.path.splitext(file.filename or "")[1] or ".wav"
    
    # Delegate execution to the Modal class instance running on GPU

    result = transcriber.transcribe.remote(
        audio_bytes=content,
        audio_suffix=suffix,
        language=language
    )
    
    return JSONResponse(content=result)


# Wrap FastAPI inside Modal app
@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    return web_app
