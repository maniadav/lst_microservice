# LST Microservice

A dedicated microservice for Language Sampling Task (LST) analysis, designed for autism and speech-language assessments. It evaluates a child's expressive language abilities by extracting semantic meaning and linguistic metrics from transcribed audio, entirely independent of the spoken language.

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Architecture / System Design](#architecture--system-design)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [Usage Examples](#usage-examples)
- [Development Workflow](#development-workflow)
- [Docker](#docker)
- [Troubleshooting](#troubleshooting)
- [Performance Notes](#performance-notes)
- [Security Considerations](#security-considerations)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)
- [License](#license)

## Project Overview

The Language Sampling Task (LST) service provides automated, deterministic evaluation of expressive language. By asking a child to describe a standard assessment image, the system measures two primary capabilities: semantic understanding (identifying objects, actions, and attributes) and expressive language (vocabulary richness, mean length of utterance). 

Designed for clinical use, the system successfully handles multi-lingual inputs and complex real-world audio where an observer or clinician may also be speaking.

## Key Features

- **Language-Agnostic Evaluation:** Evaluates the meaning behind the speech rather than syntax, naturally supporting multiple languages (English, Hindi, Tamil, etc.).
- **Speaker Diarization:** Automatically separates the child's speech from the observer's prompts to prevent inflated vocabulary scores.
- **Deterministic Scoring Engine:** Calculates final scores using strict Python logic based on semantic coverage, rather than relying on unpredictable LLM scoring.
- **Comprehensive Language Metrics:** Computes total words, unique words, vocabulary richness, sentence complexity, and mean length of utterance (MLU).
- **Offline Semantic Caching:** Pre-computes and caches baseline image semantics, minimizing runtime overhead.
- **Modular Architecture:** Decouples transcription, semantic extraction, and scoring to allow independent scaling and model replacement.

## Architecture / System Design

The system processes audio through a pipeline of specialized models before deterministic scoring.

```text
Audio Recording
   └─> WhisperX
        ├─> Voice Activity Detection (VAD)
        ├─> Speaker Diarization (Pyannote)
        └─> Speech-to-Text (STT)
             └─> Speaker-Attributed Transcript
                  └─> LLM (Groq)
                       ├─> Extracts Child Speech
                       ├─> Semantic Extraction (Objects, Actions, Attributes)
                       └─> Language Metrics Calculation
                            └─> Scoring Engine
                                 ├─> Compares against cached Image Semantics (MongoDB)
                                 └─> Computes Deterministic Final Score
```

## Repository Structure

```text
├── app/
│   ├── api/          # FastAPI routing and endpoints
│   ├── assessments/  # Assessment-specific logic and scorers
│   ├── core/         # Global configuration, exceptions, and logging
│   ├── database/     # MongoDB connection management
│   ├── repositories/ # Data access layer (Repository Pattern)
│   ├── services/     # Business logic (Whisper, Groq, Semantic Analysis)
│   └── main.py       # Application entry point and lifespan events
├── .env.example      # Example environment variables
├── docker-compose.yml# Local development orchestration
├── Dockerfile        # Container definition
└── requirements.txt  # Python dependencies
```

## Technology Stack

- **Language:** Python 3.12
- **Framework:** FastAPI, Uvicorn, Pydantic v2
- **Audio Processing:** FFmpeg
- **Speech-to-Text & Diarization:** WhisperX (Faster Whisper, Pyannote)
- **Machine Learning / LLM:** PyTorch, Groq API
- **Database:** MongoDB (Motor async driver)
- **Infrastructure:** Docker, Docker Compose

## Prerequisites

To run this project, you need the following installed:

- Python 3.12+
- FFmpeg (Required for audio processing)
- MongoDB 7.0+
- Docker and Docker Compose (if running via containers)

You will also need the following external accounts/tokens:
- **Groq API Key:** For LLM inference and semantic extraction.
- **HuggingFace Token:** For Pyannote speaker diarization models.

## Installation

```bash
git clone <repository-url>
cd lst_microservice
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

The service is configured entirely via environment variables. Copy the example file to get started:

```bash
cp .env.example .env
```

Key environment variables:
- `GROQ_API_KEY`: Your Groq API key.
- `HF_TOKEN`: HuggingFace token with access to Pyannote models.
- `MONGODB_URL`: Connection string for MongoDB (default: `mongodb://localhost:27017`).
- `API_KEY`: Secret key to protect API endpoints (optional for local dev).
- `WHISPER_MODEL_NAME`: e.g., `large-v3`.
- `WHISPER_DEVICE`: `cpu` or `cuda`.

## Running the Project

### Using Docker Compose (Recommended)

This will start both the FastAPI application and a local MongoDB instance.

```bash
docker-compose up --build
```

### Running Locally

If you have MongoDB running locally, you can start the application directly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Usage Examples

Analyze an audio recording for a specific assessment:

```bash
curl -X POST "http://localhost:8000/api/v1/lst/analyze" \
  -H "X-API-Key: your_api_key" \
  -F "audio=@sample_recording.wav" \
  -F "assessmentId=lst_001" \
  -F "imageId=img_01" \
  -F "childId=child_123"
```

*Expected Response:*

```json
{
  "assessmentId": "lst_001",
  "childId": "child_123",
  "language": "hi",
  "childTranscript": "Ek ladka football khel raha hai. Ek kutta bhi hai.",
  "observerTranscript": "Can you tell me what you see?",
  "semanticMetrics": {
    "sceneSimilarity": 91,
    "objectCoverage": 75,
    "actionCoverage": 100,
    "attributeCoverage": 50
  },
  "languageMetrics": {
    "totalWords": 10,
    "uniqueWords": 9,
    "sentenceCount": 2,
    "averageWordsPerSentence": 5.0,
    "mlu": 5.0,
    "sentenceQuality": "Simple Sentences",
    "grammarQuality": "Good",
    "vocabularyRichness": 0.90
  },
  "overallScore": 82.3
}
```

## Development Workflow

### Building

```bash
docker build -t lst_microservice .
```

*Note: Formatting, linting, and testing workflows could not be inferred from the current repository structure.*

## Docker

The repository includes a `Dockerfile` and a `docker-compose.yml` for seamless containerized deployment.

- **Models Volume:** WhisperX models are downloaded once on startup and cached in a named Docker volume (`whisper_models`). This prevents massive downloads on every container restart and keeps the image size small.
- **Database:** `docker-compose.yml` provisions a MongoDB 7 container automatically.

## Troubleshooting

| Symptom | Likely Cause | Resolution |
| ------- | ------------ | ---------- |
| Application fails to start | Missing `HF_TOKEN` | Ensure a valid HuggingFace token is set in the `.env` file for WhisperX diarization access. |
| Transcription fails / Slow boot | WhisperX model not downloaded | Ensure the Docker volume is properly mounted. The first boot takes longer as it downloads the model weights. |
| Database connection error | MongoDB not running | Ensure MongoDB is running locally or the `MONGODB_URL` in `.env` is correct. |

## Performance Notes

- **Model Caching:** The WhisperX model is loaded into memory only once during the application lifespan to ensure fast subsequent processing times.
- **Offline Processing:** Assessment image semantics are stored in MongoDB and read at runtime, removing the need to analyze the reference image on every request.
- **Hardware:** The service is configured to run on CPU during development but is architecturally ready for GPU deployment without code changes.

## Security Considerations

- **Authentication:** Endpoints are protected via an `X-API-Key` header.
- **Audio Handling:** Uploaded audio is processed temporarily and should be managed according to relevant data privacy compliance requirements.

## Limitations

- **Resource Intensive:** Running WhisperX `large-v3` on CPU requires significant system memory and compute. GPU deployment is recommended for production workloads.
- **Experimental Deployment:** Currently optimized for specific deployment targets (Railway, AWS EC2). 

## Future Improvements

- Add support for additional assessment modules (e.g., Story Retelling, Reading Assessment, Naming Test) by implementing new prompts and scoring modules without modifying the core engine.
- Implement automated GPU deployment configurations.

## License

No license has been specified for this repository.
