"""Audio file validation utilities."""

from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import AudioProcessingError

ALLOWED_CONTENT_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/m4a",
    "application/octet-stream",  # Some clients send this
}

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a"}


def validate_audio_file(filename: str, content_type: str | None, size: int) -> None:
    """Validate an uploaded audio file.

    Raises AudioProcessingError if validation fails.
    """
    if not filename:
        raise AudioProcessingError("No filename provided")

    ext = _get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise AudioProcessingError(
            f"Unsupported audio format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if size > settings.max_upload_size_bytes:
        raise AudioProcessingError(
            f"File too large ({size} bytes). Maximum: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    if size == 0:
        raise AudioProcessingError("Empty audio file")


def _get_extension(filename: str) -> str:
    """Extract lowercase file extension."""
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()
