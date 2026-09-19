"""Extracts raw text from an uploaded CV (PDF) and pulls out skills + a
best-guess education line. Deliberately simple for the MVP — no layout
analysis, no section detection. Good enough to auto-fill a profile that
the user can then edit before it's used for matching.

Note: `pdfplumber` is imported inside the function, not at module scope, so
that uploading CVs is the only thing that pays for it. See the note in
embeddings.py for why startup time matters on free-tier hosts.
"""

import io
import re

from app.nlp.extractor import extract_skills

_EDUCATION_PATTERNS = [
    r"\b(B\.?Sc\.?|Bachelor(?:'s)?)\s+(?:of\s+)?(?:Science\s+)?(?:in\s+)?([A-Za-z &]+)",
    r"\b(M\.?Sc\.?|Master(?:'s)?)\s+(?:of\s+)?(?:Science\s+)?(?:in\s+)?([A-Za-z &]+)",
    r"\b(CSE|Computer Science(?: and Engineering)?|EEE|BBA|Software Engineering)\b",
]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    import pdfplumber

    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)


def guess_education(text: str) -> str | None:
    for pattern in _EDUCATION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def parse_cv(file_bytes: bytes) -> dict:
    text = extract_text_from_pdf(file_bytes)
    skills = extract_skills(text)
    education = guess_education(text)
    return {
        "raw_text": text,
        "skills": sorted(skills),
        "education_guess": education,
    }
