"""Heuristic extraction of candidate person-name mentions from free-text feedback.

This is intentionally dependency-free (no spaCy/LLM model to deploy) so it stays
easy to run anywhere the backend runs. It trades recall/precision for simplicity:
it WILL miss lowercase or single-token informal references and WILL occasionally
flag a capitalized non-name word (a proper noun, an acronym, a sentence-initial
word it failed to filter). Treat its output as a lead for the admin to open the
underlying submissions and judge in context, not as a verified identification.

Upgrade path if this proves too noisy in practice: swap `extract_names()` for a
call to a proper NER model (spaCy en_core_web_sm) or a local LLM (Ollama) prompted
to extract person names - the rest of the pipeline (ExtractedName table, stats
aggregation) does not need to change.
"""

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")

# Common capitalized words that are not names: days, months, pronoun "I", and
# frequent sentence-initial / workplace-generic capitalized words.
_STOPWORDS = {
    "i",
    "the",
    "a",
    "an",
    "he",
    "she",
    "they",
    "we",
    "you",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
    "hr",
    "it",
    "ceo",
    "cto",
    "cfo",
    "manager",
    "team",
    "please",
    "also",
    "but",
    "and",
    "so",
    "this",
    "that",
    "our",
    "my",
    "his",
    "her",
    "their",
    "however",
    "meanwhile",
    "recently",
    "overall",
    "additionally",
    "sometimes",
    "everyone",
    "someone",
    "management",
    "today",
    "yesterday",
    "tomorrow",
    "there",
    "here",
}

MIN_NAME_LEN = 3


def extract_names(text: str) -> list[str]:
    if not text:
        return []

    candidates: list[str] = []

    for sentence in _SENTENCE_SPLIT.split(text):
        words = sentence.strip().split()
        run: list[str] = []

        for raw_word in words:
            match = _WORD.match(raw_word)
            token = match.group(0) if match else ""

            is_capitalized = token[:1].isupper() and len(token) >= MIN_NAME_LEN
            is_stopword = token.lower() in _STOPWORDS

            # Deliberately NOT excluding sentence-initial words: a huge share of
            # real feedback opens with the name ("John never listens." /
            # "Priya was great this month."), and dropping those silently would
            # defeat the point of this feature. The trade-off is more false
            # positives from ordinary sentence-initial capitalization (mitigated
            # by _STOPWORDS below) - acceptable since callers already treat this
            # as a heuristic lead to verify, not a verified match.
            if is_capitalized and not is_stopword:
                run.append(token)
            else:
                if run:
                    candidates.append(" ".join(run))
                    run = []

        if run:
            candidates.append(" ".join(run))

    # De-duplicate within a single submission (a name mentioned 3x in one
    # confession should count once towards cross-submission repetition).
    seen: set[str] = set()
    unique: list[str] = []
    for name in candidates:
        key = name.lower()
        if key not in seen:
            seen.add(key)
            unique.append(name)

    return unique
