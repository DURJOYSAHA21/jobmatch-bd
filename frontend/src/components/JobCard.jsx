import { useState } from "react";

const BREAKDOWN_LABELS = {
  semantic_similarity: "Semantic similarity",
  skill_overlap: "Skill overlap",
  education_match: "Education",
  experience_match: "Experience",
  location_match: "Location",
};

function scoreColor(score) {
  if (score >= 75) return "bg-teal";
  if (score >= 50) return "bg-amber";
  return "bg-coral";
}

function scoreBadgeStyle(score) {
  if (score >= 75) return "text-teal bg-teal/10 border-teal/30";
  if (score >= 50) return "text-amber bg-amber/10 border-amber/30";
  return "text-coral bg-coral/10 border-coral/30";
}

export default function JobCard({ match, onShortlist, shortlistStatus }) {
  const [expanded, setExpanded] = useState(false);
  const { job, overall_score, breakdown, matched_skills, missing_skills, explanation } = match;

  return (
    <div className="bg-surface border border-line rounded-card p-5 flex flex-col gap-4 hover:border-line/80 transition-all duration-200 animate-slide-up">
      {/* Title row */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-ink leading-snug">{job.title}</h3>
          <p className="text-sm text-muted mt-0.5">
            {job.company}
            {job.location && (
              <span>
                {" · "}
                <span className="inline-flex items-center gap-0.5">
                  📍 {job.location}
                </span>
              </span>
            )}
          </p>
        </div>

        {/* Score badge */}
        <div className="text-right shrink-0">
          <div
            className={`inline-flex items-baseline gap-0.5 px-3 py-1.5 rounded-card border font-mono ${scoreBadgeStyle(
              overall_score
            )}`}
          >
            <span className="text-xl font-bold leading-none">
              {Math.round(overall_score)}
            </span>
            <span className="text-xs opacity-70">%</span>
          </div>
          <div className="w-20 h-1.5 bg-surface2 rounded-pill mt-2 overflow-hidden">
            <div
              className={`h-full rounded-pill score-fill ${scoreColor(overall_score)}`}
              style={{ width: `${Math.min(100, Math.max(0, overall_score))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Skill tags */}
      {(matched_skills.length > 0 || missing_skills.length > 0) && (
        <div className="flex flex-wrap gap-1.5">
          {matched_skills.map((skill) => (
            <span
              key={skill}
              className="text-xs font-mono px-2 py-0.5 rounded-pill bg-teal/10 text-teal border border-teal/30"
            >
              ✓ {skill}
            </span>
          ))}
          {missing_skills.map((skill) => (
            <span
              key={skill}
              className="text-xs font-mono px-2 py-0.5 rounded-pill bg-coral/10 text-coral border border-coral/30"
            >
              {skill}
            </span>
          ))}
        </div>
      )}

      {/* Explanation */}
      <p className="text-sm text-muted leading-relaxed">{explanation}</p>

      {/* Breakdown toggle */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="text-xs text-muted hover:text-ink self-start underline decoration-line underline-offset-4 transition-colors"
      >
        {expanded ? "Hide score breakdown ↑" : "Show score breakdown ↓"}
      </button>

      {expanded && (
        <div className="flex flex-col gap-2.5 border-t border-line pt-3 animate-fade-in">
          {Object.entries(breakdown).map(([key, value]) => (
            <div key={key} className="flex items-center gap-3">
              <span className="text-xs text-muted w-36 shrink-0">
                {BREAKDOWN_LABELS[key]}
              </span>
              <div className="flex-1 h-1.5 bg-surface2 rounded-pill overflow-hidden">
                <div
                  className={`h-full rounded-pill score-fill ${scoreColor(value)}`}
                  style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
                />
              </div>
              <span className="font-mono text-xs text-muted w-9 text-right">
                {Math.round(value)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2 pt-1">
        <button
          type="button"
          onClick={() => onShortlist(job.id, "shortlisted")}
          className={`text-xs font-medium px-3 py-1.5 rounded-card border transition-all duration-200 ${
            shortlistStatus === "shortlisted"
              ? "bg-amber text-base border-amber shadow-sm shadow-amber/20"
              : "border-line text-muted hover:text-ink hover:border-ink"
          }`}
        >
          {shortlistStatus === "shortlisted" ? "⭐ Shortlisted" : "☆ Shortlist"}
        </button>
        <button
          type="button"
          onClick={() => onShortlist(job.id, "not_interested")}
          className={`text-xs font-medium px-3 py-1.5 rounded-card border transition-all duration-200 ${
            shortlistStatus === "not_interested"
              ? "border-coral/50 text-coral bg-coral/5"
              : "border-line text-muted hover:text-ink hover:border-ink"
          }`}
        >
          Not interested
        </button>
        {job.source_url && (
          <a
            href={job.source_url}
            target="_blank"
            rel="noreferrer"
            className="text-xs font-medium px-3 py-1.5 rounded-card border border-line text-muted hover:text-ink hover:border-ink ml-auto transition-colors"
          >
            View posting →
          </a>
        )}
      </div>
    </div>
  );
}
