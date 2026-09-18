import { useEffect, useState } from "react";

import { api } from "../api";

export default function BrowseJobs({ profileId }) {
  const [jobs, setJobs] = useState(null);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [shortlistMap, setShortlistMap] = useState({});

  useEffect(() => {
    const load = async () => {
      try {
        const [jobData, shortlistData] = await Promise.all([
          api.getAllJobs(),
          profileId ? api.getShortlist(profileId) : Promise.resolve([]),
        ]);
        setJobs(jobData);
        const map = {};
        shortlistData.forEach((e) => { map[e.job.id] = e.status; });
        setShortlistMap(map);
      } catch (err) {
        setError(err.message);
      }
    };
    load();
  }, [profileId]);

  const handleShortlist = async (jobId) => {
    if (!profileId) return;
    const current = shortlistMap[jobId];
    const next = current === "shortlisted" ? "not_interested" : "shortlisted";
    setShortlistMap((m) => ({ ...m, [jobId]: next }));
    try {
      await api.shortlistJob(profileId, jobId, next);
    } catch { /* revert on error would go here */ }
  };

  if (jobs === null) {
    return (
      <div className="flex flex-col items-center py-16 animate-fade-in">
        <div className="w-10 h-10 mb-4 border-2 border-line border-t-amber rounded-full animate-spin-slow"></div>
        <p className="text-sm text-muted">Loading all jobs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-coral/30 bg-coral/5 rounded-card p-6 text-center animate-fade-in">
        <p className="text-sm text-coral">{error}</p>
      </div>
    );
  }

  const filtered = search.trim()
    ? jobs.filter((j) => {
        const q = search.toLowerCase();
        return (
          j.title.toLowerCase().includes(q) ||
          j.company.toLowerCase().includes(q) ||
          j.location.toLowerCase().includes(q) ||
          (j.description || "").toLowerCase().includes(q)
        );
      })
    : jobs;

  return (
    <div className="animate-fade-in">
      {/* Header + Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-base font-semibold text-ink">All Jobs</h2>
          <p className="text-xs text-muted mt-0.5">
            {jobs.length} job{jobs.length === 1 ? "" : "s"} in database
            {filtered.length !== jobs.length && (
              <span className="text-amber"> · {filtered.length} matching filter</span>
            )}
          </p>
        </div>
      </div>

      {/* Search bar */}
      <div className="mb-5">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by title, company, location, or skills..."
          className="w-full text-sm"
        />
      </div>

      {/* Empty state */}
      {filtered.length === 0 && (
        <div className="text-center py-12 animate-fade-in">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-surface2 flex items-center justify-center text-2xl">
            🔍
          </div>
          <p className="text-sm font-semibold text-ink mb-1">
            {search ? "No jobs match your search" : "No jobs in database"}
          </p>
          <p className="text-sm text-muted">
            {search
              ? "Try different keywords."
              : 'Click "Fetch more jobs" on the Matches tab to load real jobs.'}
          </p>
        </div>
      )}

      {/* Job list */}
      <div className="flex flex-col gap-3 stagger-children">
        {filtered.map((job) => (
          <div
            key={job.id}
            className="bg-surface border border-line rounded-card p-4 sm:p-5 hover:border-line/80 transition-colors animate-slide-up"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-semibold text-ink leading-snug">
                  {job.title}
                </h3>
                <p className="text-xs text-muted mt-0.5">
                  {job.company}
                  {job.location && <span> · 📍 {job.location}</span>}
                </p>
                {job.description && (
                  <p className="text-xs text-muted/70 mt-2 leading-relaxed line-clamp-2">
                    {job.description}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {profileId && (
                  <button
                    type="button"
                    onClick={() => handleShortlist(job.id)}
                    className={`text-xs font-medium px-2.5 py-1 rounded-card border transition-all ${
                      shortlistMap[job.id] === "shortlisted"
                        ? "bg-amber text-base border-amber"
                        : "border-line text-muted hover:text-ink hover:border-ink"
                    }`}
                  >
                    {shortlistMap[job.id] === "shortlisted" ? "⭐" : "☆"}
                  </button>
                )}
                {job.source_url && (
                  <a
                    href={job.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-muted hover:text-ink px-2.5 py-1 rounded-card border border-line hover:border-ink transition-colors"
                  >
                    View →
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
