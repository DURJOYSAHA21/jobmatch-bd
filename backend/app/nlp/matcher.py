"""
The heart of JobMatch BD: turns (profile, job) into a match score with
a breakdown and a plain-English explanation, instead of a bare percentage.

Score = weighted sum of four signals, each 0-100:
  - semantic_similarity : embedding similarity between the profile's
                           full text and the job description. Catches
                           matches a keyword search would miss, e.g.
                           "intelligent systems using neural networks"
                           matching a profile that lists "deep learning".
  - skill_overlap        : structured overlap between the profile's
                           extracted skill set and the job's extracted
                           skill set. Catches the precise, literal
                           requirements the semantic score can be fuzzy
                           about (e.g. "must know Docker").
  - education_match      : simple keyword check for now (see docstring
                           on score_education).
  - experience_match     : simple seniority-keyword heuristic for now
                           (see docstring on score_experience).
  - location_match       : exact/"remote" match on location strings.

Weights are deliberately explicit and easy to tune — see WEIGHTS below.
This is a transparent, explainable scoring function on purpose: for an
NLP project like this, being able to say *why* a job scored the way it
did is more valuable (and more defensible in a viva/interview) than
squeezing out a fancier black-box model.
"""

from dataclasses import dataclass, field

from app.nlp import embeddings
from app.nlp.extractor import extract_skills, extract_skills_from_list

WEIGHTS = {
    "semantic_similarity": 0.30,
    "skill_overlap": 0.35,
    "education_match": 0.10,
    "experience_match": 0.10,
    "location_match": 0.15,
}

_SENIORITY_LEVELS = ["intern", "junior", "mid", "senior", "lead"]


@dataclass
class MatchResult:
    overall_score: float
    breakdown: dict[str, float]
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: str


def _profile_full_text(profile) -> str:
    """Concatenate every free-text field so the embedding sees the whole picture."""
    parts = [
        profile.education or "",
        profile.skills or "",
        profile.interests or "",
        profile.experience or "",
    ]
    return ". ".join(p for p in parts if p)


def score_semantic(profile, job) -> float:
    profile_vec = embeddings.embed(_profile_full_text(profile))
    job_vec = embeddings.embed(job.description or "")
    similarity = embeddings.cosine_similarity(profile_vec, job_vec)
    # Cosine similarity for MiniLM on real-world text rarely exceeds ~0.7
    # even for a great match, so rescale to use the 0-100 range sensibly
    # rather than reporting a technically-correct-but-misleadingly-low number.
    return max(0.0, min(100.0, similarity * 140))


def score_skill_overlap(profile_skills: set[str], job_skills: set[str]) -> float:
    if not job_skills:
        # Job posting didn't yield any recognized skills (short/vague
        # description) — don't penalize the candidate for that.
        return 70.0
    overlap = profile_skills & job_skills
    return 100.0 * len(overlap) / len(job_skills)


def score_education(profile, job) -> float:
    """
    MVP heuristic: if the profile's education field (e.g. "CSE", "BBA")
    or common expansions appear in the job description, score high;
    otherwise a neutral-ish default rather than penalizing hard, since
    most postings don't spell out degree requirements precisely.
    Swap for a proper degree-requirement parser once you have labeled data.
    """
    if not profile.education:
        return 60.0
    education = profile.education.lower()
    description = (job.description or "").lower()
    if education in description:
        return 100.0
    # Common CS-adjacent aliases
    cs_terms = ["computer science", "cse", "software engineering", "it"]
    if education in cs_terms and any(t in description for t in cs_terms):
        return 90.0
    return 65.0


def score_experience(profile, job) -> float:
    """
    MVP heuristic: match on seniority keywords (junior/mid/senior/lead/
    intern) if the job specifies one. If the job doesn't mention a level
    at all, don't penalize. This is intentionally simple — a natural
    place to extend with parsed years-of-experience later.
    """
    profile_text = (profile.experience or "").lower()
    job_text = (job.description or "").lower() + " " + (job.title or "").lower()

    job_level = next((lvl for lvl in _SENIORITY_LEVELS if lvl in job_text), None)
    if not job_level:
        return 80.0

    profile_level = next((lvl for lvl in _SENIORITY_LEVELS if lvl in profile_text), None)
    if profile_level == job_level:
        return 100.0
    if profile_level is None:
        return 70.0
    return 50.0


def score_location(profile, job) -> float:
    if not profile.location or not job.location:
        return 70.0
    profile_loc = profile.location.strip().lower()
    job_loc = job.location.strip().lower()
    if "remote" in job_loc or "remote" in profile_loc:
        return 100.0
    if profile_loc == job_loc:
        return 100.0
    if profile_loc in job_loc or job_loc in profile_loc:
        return 85.0
    return 40.0


def _build_explanation(
    matched: list[str], missing: list[str], breakdown: dict[str, float]
) -> str:
    sentences = []

    if matched:
        shown = matched[:5]
        skill_list = ", ".join(shown)
        sentences.append(f"Strong match on {skill_list}.")

    if missing:
        shown = missing[:3]
        skill_list = ", ".join(shown)
        sentences.append(
            f"The posting also asks for {skill_list}, which "
            f"{'isn' if len(shown) == 1 else 'aren'}'t listed in your profile."
        )

    if breakdown["location_match"] < 50:
        sentences.append("Note: the location doesn't look like a close match.")

    if not sentences:
        sentences.append(
            "Overall semantic similarity to your profile is the main driver here "
            "— the description doesn't name specific skills to compare against."
        )

    return " ".join(sentences)


def compute_match(profile, job) -> MatchResult:
    profile_skills = extract_skills_from_list(profile.skills) | extract_skills(
        _profile_full_text(profile)
    )
    job_skills = extract_skills(job.description or "")

    breakdown = {
        "semantic_similarity": round(score_semantic(profile, job), 1),
        "skill_overlap": round(score_skill_overlap(profile_skills, job_skills), 1),
        "education_match": round(score_education(profile, job), 1),
        "experience_match": round(score_experience(profile, job), 1),
        "location_match": round(score_location(profile, job), 1),
    }

    overall = sum(breakdown[k] * WEIGHTS[k] for k in WEIGHTS)

    matched = sorted(profile_skills & job_skills)
    missing = sorted(job_skills - profile_skills)

    return MatchResult(
        overall_score=round(overall, 1),
        breakdown=breakdown,
        matched_skills=matched,
        missing_skills=missing,
        explanation=_build_explanation(matched, missing, breakdown),
    )
