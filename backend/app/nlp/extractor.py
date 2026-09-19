"""Pulls known skills out of free text (CV text, job descriptions, the
"interests"/"experience" fields a user types into their profile).

Uses spaCy's PhraseMatcher rather than a trained NER model on purpose:
- no model download needed (spacy.blank("en") ships with the library),
- deterministic and fast,
- trivial to extend: add a row to skills_taxonomy.py and it's picked up.

This is a "good enough for MVP" approach. A v2 could fine-tune a proper
skill-extraction NER model once you have labeled data.

IMPORTANT — lazy loading
------------------------
spaCy costs ~2.5 seconds to import. uvicorn must finish importing the app
before it can bind a port, and hosts like Render kill a deploy that hasn't
opened a port in time, so the import happens on first use instead of at
module scope.
"""

import logging
import re
from functools import lru_cache

from app.nlp.skills_taxonomy import ALIAS_TO_CANONICAL, SKILLS_TAXONOMY

logger = logging.getLogger(__name__)

# Some aliases (like "R" or "Go") are also common English words. We only
# trust single-token aliases like these when they appear with clear
# separators (comma list, bullet, "/", or a skill-list heading nearby)
# rather than mid-sentence, to cut down on false positives.
_AMBIGUOUS_SHORT_ALIASES = {"r", "go", "cv"}


@lru_cache(maxsize=1)
def _get_matcher():
    """
    Build the spaCy pipeline + PhraseMatcher on first use, then reuse it.

    PhraseMatcher handles multi-word phrases ("machine learning") correctly,
    which a naive regex/split approach over commas would get wrong for skills
    embedded in sentences.
    """
    import spacy
    from spacy.matcher import PhraseMatcher

    nlp = spacy.blank("en")
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    matcher.add("SKILLS", [nlp.make_doc(alias) for alias in ALIAS_TO_CANONICAL])
    return nlp, matcher


def extract_skills(text: str) -> set[str]:
    """Return the set of canonical skill names found in `text`."""
    if not text:
        return set()

    try:
        nlp, matcher = _get_matcher()
    except Exception:
        # Skill extraction is one of five signals. If spaCy can't run, return
        # nothing and let the other signals rank the jobs rather than failing
        # the whole request.
        logger.warning("spaCy unavailable — skipping skill extraction", exc_info=True)
        return set()

    doc = nlp(text)
    matches = matcher(doc)

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
