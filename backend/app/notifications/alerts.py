"""
Notify profiles that have an email when newly added jobs are a good match.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app import models
from app.config import MATCH_EMAIL_THRESHOLD
from app.nlp.matcher import compute_match
from app.notifications.email_sender import send_email

logger = logging.getLogger(__name__)


def notify_profiles_of_new_jobs(db: Session, new_jobs: list[models.Job]) -> dict:
    """
    For every profile with an email, score the new jobs and email a digest
    of those that meet MATCH_EMAIL_THRESHOLD.
    """
    if not new_jobs:
        return {"emails_sent": 0, "profiles_checked": 0}

    profiles = (
        db.query(models.Profile)
        .filter(models.Profile.email.isnot(None))
        .filter(models.Profile.email != "")
        .all()
    )
    if not profiles:
        return {"emails_sent": 0, "profiles_checked": 0}

    emails_sent = 0
    for profile in profiles:
        matches = []
        for job in new_jobs:
            try:
                result = compute_match(profile, job)
            except Exception as exc:
                logger.warning(
                    "Match failed for profile %s / job %s: %s",
                    profile.id,
                    job.id,
                    exc,
                )
                continue
            if result.overall_score >= MATCH_EMAIL_THRESHOLD:
                matches.append((job, result))

        if not matches:
            continue

        matches.sort(key=lambda pair: pair[1].overall_score, reverse=True)
        if _send_match_digest(profile, matches):
            emails_sent += 1

    return {"emails_sent": emails_sent, "profiles_checked": len(profiles)}


def _send_match_digest(profile: models.Profile, matches: list) -> bool:
    name = (profile.name or "there").strip() or "there"
    lines = [
        f"Hi {name},",
        "",
        f"JobMatch BD found {len(matches)} new job"
        f"{'' if len(matches) == 1 else 's'} that look like a good fit:",
        "",
    ]
    for job, result in matches[:10]:
        score = round(result.overall_score)
        lines.append(f"• {job.title} @ {job.company} ({score}% match)")
        if job.location:
            lines.append(f"  Location: {job.location}")
        if result.matched_skills:
            lines.append(f"  Skills: {', '.join(result.matched_skills[:8])}")
        if job.source_url:
            lines.append(f"  Link: {job.source_url}")
        lines.append(f"  Why: {result.explanation}")
        lines.append("")

    lines.extend(
        [
            "Open JobMatch BD to see your full ranked matches and shortlist roles.",
            "",
            "— JobMatch BD",
        ]
    )

    subject = (
        f"JobMatch BD: {len(matches)} new matching job"
        f"{'' if len(matches) == 1 else 's'}"
    )
    return send_email(profile.email, subject, "\n".join(lines))
