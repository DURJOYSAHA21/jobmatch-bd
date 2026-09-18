"""
Pulls known skills out of free text (CV text, job descriptions, the
"interests"/"experience" fields a user types into their profile).

Uses spaCy's PhraseMatcher rather than a trained NER model on purpose:
- no model download needed (spacy.blank("en") ships with the library),
- deterministic and fast,
- trivial to extend: add a row to skills_taxonomy.py and it's picked up.

This is a "good enough for MVP" approach. A v2 could fine-tune a proper
skill-extraction NER model once you have labeled data.
"""

import re

import spacy
from spacy.matcher import PhraseMatcher

from app.nlp.skills_taxonomy import ALIAS_TO_CANONICAL, SKILLS_TAXONOMY

_nlp = spacy.blank("en")
_matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")

# Register every alias as a pattern. PhraseMatcher handles multi-word
# phrases ("machine learning") correctly, which a naive regex/split
# approach over commas would get wrong for skills embedded in sentences.
_all_aliases = list(ALIAS_TO_CANONICAL.keys())
_patterns = [_nlp.make_doc(alias) for alias in _all_aliases]
_matcher.add("SKILLS", _patterns)

# Some aliases (like "R" or "Go") are also common English words. We only
# trust single-token aliases like these when they appear with clear
# separators (comma list, bullet, "/", or a skill-list heading nearby)
# rather than mid-sentence, to cut down on false positives.
_AMBIGUOUS_SHORT_ALIASES = {"r", "go", "cv"}


def extract_skills(text: str) -> set[str]:
    """Return the set of canonical skill names found in `text`."""
    if not text:
        return set()

    doc = _nlp(text)
    matches = _matcher(doc)

    found: set[str] = set()
    for _match_id, start, end in matches:
        span = doc[start:end]
        alias = span.text.lower()
        canonical = ALIAS_TO_CANONICAL.get(alias)
        if not canonical:
            continue

        if alias in _AMBIGUOUS_SHORT_ALIASES:
            # Require the token to be flanked by comma/newline/bullet/slash
            # (a "skills list" context) rather than free prose.
            before = doc[start - 1].text if start > 0 else ""
            after = doc[end].text if end < len(doc) else ""
            separators = {",", "\n", "-", "/", "*", "\u2022", ":", ""}
            if before not in separators and after not in separators:
                continue

        found.add(canonical)

    return found


def extract_skills_from_list(raw: str) -> set[str]:
    """
    For a profile's comma/newline separated "Skills" field, e.g.
    "Python, C#, ASP.NET Core, SQL, Machine Learning". Splits first,
    then matches each chunk — more forgiving of skills that aren't in
    the taxonomy verbatim but are close to an alias.
    """
    if not raw:
        return set()

    chunks = [c.strip() for c in re.split(r"[,\n;]", raw) if c.strip()]
    found: set[str] = set()
    for chunk in chunks:
        canonical = ALIAS_TO_CANONICAL.get(chunk.lower())
        if canonical:
            found.add(canonical)
        else:
            # Fall back to phrase matching in case the chunk has extra
            # words, e.g. "Python programming".
            found |= extract_skills(chunk)
    return found


def all_known_skills() -> list[str]:
    return sorted(SKILLS_TAXONOMY.keys())
