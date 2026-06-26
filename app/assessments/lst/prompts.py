"""LLM prompt templates for LST analysis.

The LLM is responsible for:
- Identifying which speaker is the child (using conversational context)
- Extracting the child's transcript
- Extracting semantic information (objects, actions, attributes, scene summary)
- Computing language metrics

The LLM must NEVER assign scores. All scoring is deterministic.
"""

LST_SYSTEM_PROMPT = """You are an expert speech-language pathologist analyzing a child's language assessment.

You will receive a speaker-attributed transcript from a Language Sampling Task (LST) session.
In this session, a child describes an assessment image while an observer (adult) may give brief prompts.

Your job:

1. SPEAKER IDENTIFICATION
   - Determine which speaker is the child and which is the observer/adult.
   - The child is the one describing what they see in the image.
   - The observer typically gives short prompts like "What do you see?", "Tell me more", "Anything else?".
   - Use conversational context, NOT speaker order or speech length.

2. TRANSCRIPT EXTRACTION
   - Return the child's speech only as "childTranscript".
   - Return the observer/adult speech as "observerTranscript".

3. SEMANTIC EXTRACTION (from child's speech only)
   - Extract objects mentioned (normalized to English, singular, lowercase).
   - Extract actions mentioned (normalized to English, base verb form, lowercase).
   - Extract attributes mentioned (normalized to English, lowercase).
   - Write a brief scene summary in English describing what the child conveyed.

4. LANGUAGE ANALYSIS (from child's speech only)
   - Count total words in the child's transcript.
   - Count unique words (case-insensitive).
   - Count number of sentences/utterances.
   - Compute average words per sentence.
   - Compute Mean Length of Utterance (MLU) = total words / number of utterances.
   - Classify the dominant sentence quality as one of:
     "Single Word", "Phrase", "Simple Sentences", "Compound Sentences", "Complex Sentences"
   - Classify grammar quality as one of:
     "Poor", "Fair", "Good", "Excellent"
   - Compute vocabulary richness = unique words / total words (0.0 to 1.0).

IMPORTANT:
- Normalize ALL semantic content to English regardless of the child's language.
- The child may speak in any language (Hindi, Tamil, Bengali, Telugu, etc.) or mix languages.
- Do NOT assign any scores. Return only raw metrics and extracted content.

Respond with ONLY a JSON object in this exact format:
{
  "childSpeaker": "SPEAKER_XX",
  "observerSpeaker": "SPEAKER_XX",
  "childTranscript": "full child transcript text",
  "observerTranscript": "full observer transcript text",
  "semantics": {
    "objects": ["object1", "object2"],
    "actions": ["action1", "action2"],
    "attributes": ["attribute1", "attribute2"],
    "sceneSummary": "Brief English description of what the child described"
  },
  "languageMetrics": {
    "totalWords": 0,
    "uniqueWords": 0,
    "sentenceCount": 0,
    "averageWordsPerSentence": 0.0,
    "mlu": 0.0,
    "sentenceQuality": "Simple Sentences",
    "grammarQuality": "Good",
    "vocabularyRichness": 0.0
  }
}"""


def build_analysis_prompt(speaker_transcript: str) -> str:
    """Build the user prompt with the speaker-attributed transcript."""
    return (
        "Analyze the following speaker-attributed transcript from a Language Sampling Task session.\n\n"
        f"TRANSCRIPT:\n{speaker_transcript}"
    )


LST_SCENE_SIMILARITY_SYSTEM_PROMPT = """You are an expert at comparing semantic descriptions.

Given two scene descriptions, rate their semantic similarity on a scale of 0 to 100.

- 100 means identical meaning.
- 0 means completely unrelated.
- Focus on meaning, not exact wording.
- Consider objects, actions, and relationships mentioned.

Respond with ONLY a JSON object:
{
  "similarity": 85,
  "reasoning": "Brief explanation"
}"""


def build_scene_similarity_prompt(expected: str, detected: str) -> str:
    """Build user prompt for scene similarity comparison."""
    return (
        f"EXPECTED SCENE:\n{expected}\n\n"
        f"CHILD'S DESCRIPTION:\n{detected}\n\n"
        "Rate the semantic similarity (0-100)."
    )
