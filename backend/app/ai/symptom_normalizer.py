"""
Symptom Normalizer - Phase 6
Provides typo-tolerant, synonym-aware symptom normalization.

Two-stage approach:
  1. Exact synonym lookup (fastest, most accurate)
  2. Controlled fuzzy Levenshtein match (threshold >= FUZZY_THRESHOLD)

Safety: unknown terms are returned as-is, never silently converted.
"""

from typing import List, Set
from dataclasses import dataclass, field
import re

# ---------------------------------------------------------------------------
# CANONICAL SYMPTOM -> SYNONYMS / TYPOS / COLLOQUIALISMS MAPPING
# ---------------------------------------------------------------------------
SYNONYM_MAP: dict = {
    "fatigue": {
        "fatigue", "fatigued", "ftigue", "fatige", "fatiguee",
        "fatigee", "fatigu", "fataigue", "tired", "tiredness",
        "extreme tiredness", "very tired", "feeling tired", "feeling fatigued",
        "exhausted", "exhaustion", "lack of energy", "no energy", "low energy",
        "lethargic", "lethargy", "weak", "weakness", "weary",
        "always tired", "constantly tired", "body weakness", "feeling weak",
    },
    "fever": {
        "fever", "fevers", "febrile", "pyrexia", "high temperature", "high temp",
        "high fever", "mild fever", "low grade fever", "low-grade fever",
        "temperature", "running a fever", "feeling feverish", "feverish",
    },
    "vomiting": {
        "vomiting", "vomit", "vomits", "vomited", "nausea", "nauseous",
        "throwing up", "threw up", "puking", "puke", "retching",
        "feeling like vomiting", "urge to vomit", "feeling nauseous",
        "sick to stomach", "queasy",
    },
    "diarrhea": {
        "diarrhea", "diarrhoea", "diarrea", "loose stool",
        "loose stools", "loose motion", "loose motions", "watery stool",
        "watery stools", "frequent stools",
    },
    "headache": {
        "headache", "headaches", "head ache", "head pain",
        "pain in head", "pain in my head", "migraine", "migraines",
        "head pressure", "throbbing head", "heavy head",
    },
    "chest pain": {
        "chest pain", "chest pains", "chest ache", "pain in chest",
        "chest pressure", "chest tightness", "tight chest", "cardiac pain",
        "heart pain", "chest hurts", "chest discomfort",
    },
    "breathing difficulty": {
        "breathlessness", "difficulty breathing", "shortness of breath",
        "short of breath", "cannot breathe", "hard to breathe",
        "trouble breathing", "labored breathing", "breathless", "gasping",
        "gasping for air", "wheezing", "wheeze",
    },
    "abdominal pain": {
        "abdominal pain", "stomach pain", "stomach ache", "stomachache",
        "belly pain", "tummy pain", "abdominal ache", "gastric pain",
        "pain in stomach", "my stomach hurts", "stomach hurts",
        "stomach cramps", "cramps",
    },
    "dizziness": {
        "dizziness", "dizzy", "giddy", "giddiness", "lightheadedness",
        "lightheaded", "light-headed", "vertigo", "spinning",
        "feeling dizzy", "feeling faint", "faint",
    },
    "cough": {
        "cough", "coughing", "coughs", "dry cough", "wet cough",
        "persistent cough", "chronic cough",
    },
    "sore throat": {
        "sore throat", "throat pain", "throat ache", "throat hurts",
        "painful throat", "throat infection", "swollen throat",
    },
    "runny nose": {
        "runny nose", "running nose", "nasal discharge", "nose running",
        "stuffy nose", "blocked nose", "nasal congestion", "congestion",
    },
    "joint pain": {
        "joint pain", "joint ache", "joint stiffness", "stiff joints",
        "arthritis pain", "painful joints",
    },
    "back pain": {
        "back pain", "backache", "back ache", "pain in back", "lower back pain",
        "upper back pain", "my back hurts", "back hurts",
    },
    "knee pain": {
        "knee pain", "knee ache", "painful knee", "my knee hurts", "knee hurts",
    },
    "rash": {
        "rash", "skin rash", "rashes", "itchy rash", "hives", "urticaria",
        "red spots", "red patches", "skin lesion",
    },
    "itching": {
        "itching", "itchy", "itch", "itchiness", "skin itching",
    },
    "seizure": {
        "seizure", "seizures", "convulsion", "convulsions", "fits",
        "epileptic fit",
    },
    "numbness": {
        "numbness", "numb", "tingling", "pins and needles", "feeling numb",
    },
    "swelling": {
        "swelling", "swollen", "edema", "oedema", "puffiness", "puffy",
        "inflammation", "bloating",
    },
}

# Build reverse lookup: surface_form -> canonical
_REVERSE_LOOKUP: dict = {}
for _canonical, _forms in SYNONYM_MAP.items():
    for _form in _forms:
        _REVERSE_LOOKUP[_form.lower()] = _canonical

FUZZY_THRESHOLD = 0.78

STOPWORDS = {
    "the", "and", "for", "are", "but", "not", "you", "all", "can",
    "had", "her", "was", "one", "our", "out", "day", "get", "has",
    "him", "his", "how", "its", "may", "new", "now", "old", "see",
    "two", "way", "who", "did", "let", "put", "say", "she", "too",
    "use", "have", "been", "from", "this", "that", "with", "they",
    "will", "what", "when", "much", "also", "just", "feel", "very",
    "some", "more", "over", "like", "into", "only", "than", "then",
    "come", "make", "time", "know", "take", "last", "long", "look",
    "most", "came", "gave", "past", "give", "help", "here", "each",
    "well", "good", "need", "week", "year", "able", "keep", "seem",
    "show", "such", "sure", "next", "even", "find", "many",
    "high", "both", "went", "same", "tell", "work", "days", "body",
    "since", "having", "weeks", "hours", "sometimes", "often",
    "recently", "little", "around", "about", "after", "before", "during",
    "morning", "night", "mild", "severe", "three", "four", "five",
    "always", "felt", "getting", "kind",
}


def _levenshtein_similarity(a: str, b: str) -> float:
    """Return 1 - (edit_distance / max_len). Range: [0.0, 1.0]."""
    if not a or not b:
        return 0.0
    la, lb = len(a), len(b)
    dp = list(range(lb + 1))
    for i in range(1, la + 1):
        prev = dp[:]
        dp[0] = i
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev[j - 1] + cost)
    return 1.0 - (dp[lb] / max(la, lb))


def _fuzzy_match_canonical(token: str):
    """
    Fuzzy-match token against all known surface forms.
    Returns canonical name if similarity >= FUZZY_THRESHOLD, else None.
    Requires token length >= 4 to avoid false positives on short words.
    """
    if len(token) < 4:
        return None
    best_score = 0.0
    best_canonical = None
    for surface, canonical in _REVERSE_LOOKUP.items():
        # Skip if length difference is too large
        if abs(len(token) - len(surface)) > max(len(token), len(surface)) * 0.45:
            continue
        score = _levenshtein_similarity(token, surface)
        if score >= FUZZY_THRESHOLD and score > best_score:
            best_score = score
            best_canonical = canonical
    return best_canonical


@dataclass
class NormalizationResult:
    canonical_symptoms: List[str] = field(default_factory=list)
    unresolved_terms: List[str] = field(default_factory=list)


def normalize_symptoms(text: str) -> NormalizationResult:
    """
    Parse free-text user input and return recognized canonical symptoms.

    Guarantees:
    - "ftigue", "fatige", "fatigue", "feeling tired" all resolve to "fatigue"
    - "dragon blood syndrome" will NOT be converted to any known symptom
    - Multi-word surface forms are matched before single-word tokens
    """
    if not text or not text.strip():
        return NormalizationResult()

    lower = text.lower().strip()
    found_canonical: Set[str] = set()
    unresolved: Set[str] = set()

    # Stage 1: exact multi-word and single-word surface forms (longest first)
    sorted_forms = sorted(_REVERSE_LOOKUP.keys(), key=lambda s: -len(s))
    remaining = lower
    for form in sorted_forms:
        if form in remaining:
            found_canonical.add(_REVERSE_LOOKUP[form])
            remaining = remaining.replace(form, " ", 1)

    # Stage 2: fuzzy-match remaining tokens
    remaining_tokens = re.findall(r"[a-z]+", remaining)
    for token in remaining_tokens:
        if len(token) < 3 or token in STOPWORDS:
            continue
        if token in _REVERSE_LOOKUP:
            found_canonical.add(_REVERSE_LOOKUP[token])
            continue
        fuzzy_result = _fuzzy_match_canonical(token)
        if fuzzy_result:
            found_canonical.add(fuzzy_result)
        elif len(token) >= 4:
            unresolved.add(token)

    return NormalizationResult(
        canonical_symptoms=sorted(found_canonical),
        unresolved_terms=sorted(unresolved),
    )
