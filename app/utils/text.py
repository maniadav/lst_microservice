"""Text processing utilities."""

from __future__ import annotations


def count_words(text: str) -> int:
    """Count total words in text."""
    return len(text.split()) if text.strip() else 0


def count_unique_words(text: str) -> int:
    """Count unique words (case-insensitive)."""
    if not text.strip():
        return 0
    return len({w.lower() for w in text.split()})


def count_sentences(text: str) -> int:
    """Count sentences by splitting on sentence-ending punctuation."""
    if not text.strip():
        return 0

    count = 0
    for char in text:
        if char in ".!?":
            count += 1

    # If no punctuation found, count non-empty lines
    if count == 0:
        count = sum(1 for line in text.split("\n") if line.strip())

    return max(count, 1)


def compute_vocabulary_richness(text: str) -> float:
    """Compute Type-Token Ratio."""
    total = count_words(text)
    if total == 0:
        return 0.0
    unique = count_unique_words(text)
    return round(unique / total, 2)
