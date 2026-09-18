import { useEffect, useState } from "react";

import { api } from "../api";

const STATUS_LABEL = {
  shortlisted: "Shortlisted",
  not_interested: "Not interested",
  saved: "Saved",
};

const STATUS_STYLE = {
  shortlisted: "bg-amber/10 text-amber border-amber/30",
  not_interested: "bg-coral/10 text-coral border-coral/30",
  saved: "bg-surface2 text-muted border-line",
};

export default function Shortlist({ profileId }) {
  const [entries, setEntries] = useState(null);

  useEffect(() => {
    api.getShortlist(profileId).then(setEntries);
  }, [profileId]);

  // ── Loading ──
  if (entries === null) {
    return (
      <div className="flex flex-col items-center py-16 animate-fade-in">
        <div className="w-10 h-10 mb-4 border-2 border-line border-t-amber rounded-full animate-spin-slow"></div>
        <p className="text-sm text-muted">Loading your shortlist...</p>
      </div>
    );
  }

  const shortlisted = entries.filter((e) => e.status === "shortlisted");

  // ── Empty state ──
  if (shortlisted.length === 0) {
    return (
      <div className="text-center py-16 animate-fade-in">
        <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-surface2 flex items-center justify-center text-2xl">
          ⭐
        </div>
        <p className="text-sm font-semibold text-ink mb-1">
          No shortlisted jobs yet
        </p>
        <p className="text-sm text-muted max-w-sm mx-auto">
          When you find a job you like, hit the Shortlist button to save it
          here for easy access.
        </p>
      </div>
    );
  }

  // ── Shortlist ──
  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-base font-semibold text-ink">Your Shortlist</h2>
          <p className="text-xs text-muted mt-0.5">
            {shortlisted.length} job{shortlisted.length === 1 ? "" : "s"} saved
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3 stagger-children">
        {shortlisted.map((entry) => (
          <div
            key={entry.id}
            className="bg-surface border border-line rounded-card p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-line/80 transition-colors animate-slide-up"
          >
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-ink">{entry.job.title}</h3>
              <p className="text-xs text-muted mt-0.5">
                {entry.job.company}
                {entry.job.location && (
                  <span> · 📍 {entry.job.location}</span>
                )}
              </p>
              {entry.job.description && (
                <p className="text-xs text-muted/70 mt-2 leading-relaxed line-clamp-2">
                  {entry.job.description}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <span
                className={`text-xs font-mono px-2.5 py-1 rounded-pill border ${
                  STATUS_STYLE[entry.status] || STATUS_STYLE.saved
                }`}
              >
                ⭐ {STATUS_LABEL[entry.status]}
              </span>
              {entry.job.source_url && (
                <a
                  href={entry.job.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-muted hover:text-ink px-2.5 py-1 rounded-pill border border-line hover:border-ink transition-colors"
                >
                  View →
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
