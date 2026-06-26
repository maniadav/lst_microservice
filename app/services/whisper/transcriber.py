"""WhisperX transcription service with speaker diarization."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Segment:
    """A single transcribed segment with speaker label."""

    text: str
    speaker: str = ""
    start: float = 0.0
    end: float = 0.0


@dataclass
class TranscriptionResult:
    """Full transcription output including speaker-attributed segments."""

    segments: list[Segment] = field(default_factory=list)
    language: str = ""

    @property
    def speaker_transcript(self) -> str:
        """Format segments as a speaker-attributed transcript for LLM consumption."""
        lines: list[str] = []
        current_speaker = ""
        for seg in self.segments:
            label = seg.speaker or "UNKNOWN"
            if label != current_speaker:
                current_speaker = label
                lines.append(f"\n{current_speaker}:")
            lines.append(seg.text.strip())
        return "\n".join(lines).strip()

    @property
    def full_text(self) -> str:
        return " ".join(seg.text.strip() for seg in self.segments)


class WhisperTranscriber:
    """Loads WhisperX once and reuses for all requests.

    Models are downloaded to the HuggingFace cache directory, which should be
    mounted as a Docker volume to persist across restarts.
    """

    def __init__(self) -> None:
        self._model: Any = None
        self._diarize_model: Any = None
        self._align_models: dict[str, Any] = {}
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load_model(self) -> None:
        """Load WhisperX model and diarization pipeline. Call once at startup."""
        import whisperx

        device = settings.WHISPER_DEVICE
        compute_type = settings.WHISPER_COMPUTE_TYPE

        logger.info(
            "Loading WhisperX model=%s device=%s compute_type=%s",
            settings.WHISPER_MODEL_NAME,
            device,
            compute_type,
        )

        self._model = whisperx.load_model(
            settings.WHISPER_MODEL_NAME,
            device=device,
            compute_type=compute_type,
        )

        if settings.HF_TOKEN:
            logger.info("Loading Pyannote diarization pipeline")
            from whisperx.diarize import DiarizationPipeline
            try:
                self._diarize_model = DiarizationPipeline(
                    model_name="pyannote/speaker-diarization-3.1",
                    token=settings.HF_TOKEN,
                    device=device,
                )
            except Exception as e:
                logger.warning(
                    "Failed to load Pyannote diarization pipeline (%s). "
                    "Speaker diarization will be unavailable. "
                    "Proceeding with transcription-only mode.",
                    str(e)
                )
                self._diarize_model = None
        else:
            logger.warning(
                "HF_TOKEN not set — speaker diarization will be unavailable. "
                "All segments will be attributed to a single speaker."
            )

        self._is_loaded = True
        logger.info("WhisperX model loaded successfully")

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcribe audio file with speaker diarization.

        Args:
            audio_path: Path to the audio file (wav/mp3/m4a).

        Returns:
            TranscriptionResult with speaker-attributed segments.
        """
        import whisperx

        if not self._is_loaded or self._model is None:
            raise RuntimeError("WhisperX model not loaded. Call load_model() first.")

        device = settings.WHISPER_DEVICE

        # Step 1: Transcribe
        logger.info("Transcribing audio: %s", audio_path)
        audio = whisperx.load_audio(audio_path)
        result = self._model.transcribe(audio, batch_size=16)
        detected_language = result.get("language", "en")
        logger.info("Detected language: %s", detected_language)

        # Step 2: Align word timestamps
        if detected_language not in self._align_models:
            logger.info("Loading WhisperX alignment model for language: %s", detected_language)
            self._align_models[detected_language] = whisperx.load_align_model(
                language_code=detected_language,
                device=device,
            )
        else:
            logger.debug("Reusing cached WhisperX alignment model for language: %s", detected_language)
        
        align_model, align_metadata = self._align_models[detected_language]
        result = whisperx.align(
            result["segments"],
            align_model,
            align_metadata,
            audio,
            device,
            return_char_alignments=False,
        )

        # Step 3: Speaker diarization
        if self._diarize_model is not None:
            logger.info("Running speaker diarization")
            diarize_segments = self._diarize_model(audio_path)
            result = whisperx.assign_word_speakers(diarize_segments, result)

        # Step 4: Build result
        segments: list[Segment] = []
        for seg in result.get("segments", []):
            segments.append(Segment(
                text=seg.get("text", ""),
                speaker=seg.get("speaker", "SPEAKER_00"),
                start=seg.get("start", 0.0),
                end=seg.get("end", 0.0),
            ))

        return TranscriptionResult(segments=segments, language=detected_language)
