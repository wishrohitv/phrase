from typing import Literal

from pydantic import BaseModel, ConfigDict

Category = Literal[
    # Vocabulary
    "word",
    "phrasal_verb",
    "idiom",
    "expression",
    "slang",
    "collocation",
    "proverb",
    # Sentence structures
    "sentence_pattern",
    "conversational_phrase",
    "complete_sentence",
    # Grammar
    "grammar_rule",
    "tense",
    "modal_verb",
    "conditional",
    "voice",
    "clause",
    "preposition",
    "conjunction",
    "other_grammar",
]

SpeechRegister = Literal[
    "formal",
    "neutral",
    "informal",
    "slang",
    "vulgar",
    "literary",
    "regional",
]

Tone = Literal[
    "sarcastic",
    "humorous",
    "polite",
    "rude",
    "affectionate",
    "annoyed",
    "angry",
    "friendly",
    "persuasive",
    "dismissive",
    "serious",
    "playful",
    "other",
]

Confidence = Literal["high", "medium", "low"]


class Usage(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        from_attributes=True,
    )
    type: Literal[
        "Example",
        "Grammar",
        "Context",
        "Common Expression",
        "Alternative Expression",
        "Pronunciation",
        "Common Mistake",
    ]
    explanation: str


class PhraseOrSentence(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        from_attributes=True,
    )

    difficulty_level: Literal["easy", "medium", "hard"]
    category: Category

    # Exact extracted text from the subtitle
    original_sentence_or_word: str

    # Complete original subtitle sentence containing the extraction
    source_sentence: str

    # Reusable dictionary/learning form
    # Example: "she pisses me off" -> "piss someone off"
    canonical_form: str

    # Explanation in the user's native language
    explanation: list[str]

    # How the expression is normally used
    speech_register: list[SpeechRegister]

    # Emotional or conversational tone in this specific context
    tone: list[Tone]

    # Reliability of the interpretation based on available context
    confidence: Confidence

    # Explain ambiguity or context limitations; null when unnecessary
    context_note: str | None

    usage: list[Usage]
