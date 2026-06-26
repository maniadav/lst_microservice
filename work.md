# Updated Technical Requirements

## Tech Stack

Use:

* Python 3.12
* FastAPI
* Uvicorn
* Pydantic v2
* WhisperX
* PyTorch
* FFmpeg
* MongoDB
* Motor (async MongoDB driver)
* httpx
* Docker
* Docker Compose

Use the Repository Pattern for database access.

Do **not** use PostgreSQL, SQLAlchemy or Alembic.

The existing platform already uses MongoDB, and this microservice should integrate with the existing database.

---

# API

## POST

`/api/v1/lst/analyze`

Accept **multipart/form-data**

Fields

```
audio (wav/mp3/m4a)

assessmentId

imageId

childId

language (optional, default auto)
```

Response

```json
{
  "assessmentId": "lst_001",
  "childId": "child_123",

  "language": "hi",

  "childTranscript": "...",

  "observerTranscript": "...",

  "semanticMetrics": {
    "sceneSimilarity": 91,
    "objectCoverage": 75,
    "actionCoverage": 100,
    "attributeCoverage": 50
  },

  "languageMetrics": {
    "totalWords": 38,
    "uniqueWords": 27,
    "sentenceCount": 7,
    "averageWordsPerSentence": 5.4,
    "mlu": 5.4,
    "sentenceQuality": "Simple Sentences",
    "grammarQuality": "Good",
    "vocabularyRichness": 0.71
  },

  "overallScore": 82.3
}
```

---

# Processing Pipeline

1. Receive uploaded audio.
2. Save audio to temporary storage.
3. Run WhisperX.
4. Generate speaker-attributed transcript.
5. Pass the complete transcript (with speaker labels) to the Groq LLM.
6. The LLM must:

   * identify which speaker is the child
   * identify observer speech
   * return only the child transcript
   * extract semantic information
   * compute language metrics
7. Load stored assessment image semantics from MongoDB using `assessmentId` and `imageId`.
8. Compute deterministic scores in Python.
9. Save assessment results to MongoDB using the supplied `childId`.
10. Return the JSON response.

---

# Speaker Identification

Do **not** rely on heuristics such as:

* longest speaker
* first speaker
* shortest speaker

Instead:

WhisperX provides speaker labels such as:

```
SPEAKER_00

SPEAKER_01
```

Pass the speaker-attributed transcript to the LLM.

The LLM should determine which speaker is the child using conversational context.

This produces much more reliable results for clinical assessments.

---

# Scene Similarity

Do **not** hardcode embeddings.

Implement a provider interface.

Example

```python
SceneSimilarityProvider
```

Implement the first provider using the Groq LLM.

The scoring service should call only the interface.

This allows replacing the provider later with OpenAI embeddings or sentence-transformers without changing business logic.

---

# WhisperX

Use WhisperX for:

* transcription
* word timestamps
* speaker diarization

Load the model once during application startup.

Do not reload the model for every request.

Do not bundle WhisperX models inside the Docker image.

Instead:

* download on first startup
* cache inside a mounted Docker volume

This keeps Docker images much smaller and improves deployment speed.

---

# MongoDB Collections

## assessments

Stores assessment definitions.

Contains:

* assessmentId
* title
* description
* module

---

## assessment_images

Stores pre-generated image semantics.

Fields

* imageId
* assessmentId
* imageUrl
* objects
* actions
* attributes
* sceneSummary
* version

---

## assessment_results

Store every processed assessment.

Fields

```
_id

childId

assessmentId

imageId

language

childTranscript

observerTranscript

semanticMetrics

languageMetrics

overallScore

processingVersion

createdAt
```

Every successful assessment request should automatically create a new document in this collection.

---

# Authentication

Support API key authentication.

Use

```
X-API-Key
```

Compare against

```
API_KEY
```

stored in environment variables.

If `API_KEY` is not configured, authentication should be disabled automatically for local development.

---

# Deployment Requirements

The project should support the following deployment progression without architecture changes:

1. Local Docker Compose
2. Railway ($5 plan)
3. AWS EC2
4. Future GPU deployment

The service should remain lightweight enough to run on CPU during development while allowing GPU acceleration later without code changes.

---

# Code Quality

The architecture should remain modular.

Separate into:

* Speech Service (WhisperX)
* LLM Service (Groq)
* Semantic Service
* Language Service
* Scoring Service
* Mongo Repository Layer

The API layer must never contain business logic.

All scoring must be deterministic Python code.

The LLM must never calculate the final assessment score.

Design the project so additional assessment modules (Story Retelling, Reading Assessment, Expressive Language, Naming Test, Articulation, etc.) can be added by implementing new prompts and scoring modules without modifying the core engine.
