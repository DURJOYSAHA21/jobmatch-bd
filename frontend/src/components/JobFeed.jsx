import { useEffect, useState } from "react";

import { api } from "../api";
import JobCard from "./JobCard";

export default function JobFeed({ profileId }) {
  const [matches, setMatches] = useState(null);
  const [shortlistMap, setShortlistMap] = useState({});
  const [error, setError] = useState(null);
  const [seeding, setSeeding] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [fetchResult, setFetchResult] = useState(null);

  const load = async () => {
    setError(null);
    try {
      const [matchData, shortlistData] = await Promise.all([
        api.getMatches(profileId),
        api.getShortlist(profileId),
      ]);
      setMatches(matchData);
      const map = {};
      shortlistData.forEach((entry) => {
        map[entry.job.id] = entry.status;
      });
      setShortlistMap(map);
    } catch (err) {
      setError(err.message);
      setMatches([]);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileId]);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await api.seedJobs();
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSeeding(false);
    }
  };

  const handleFetchJobs = async (source) => {
    setFetching(true);
    setFetchResult(null);
    try {
      const result = await api.fetchJobs(source);
      setFetchResult(result);
      // Reload matches to pick up new jobs
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setFetching(false);
    }
  };

  const handleShortlist = async (jobId, status) => {
    setShortlistMap((m) => ({ ...m, [jobId]: status }));
    try {
      await api.shortlistJob(profileId, jobId, status);
    } catch {
      load(); // revert to server truth on failure
    }
  };

  // ── Loading state ──
  if (matches === null) {
    return (
      <div className="flex flex-col items-center py-16 animate-fade-in">
        <div className="w-10 h-10 mb-4 border-2 border-line border-t-amber rounded-full animate-spin-slow"></div>
        <p className="text-sm text-muted">Finding your best matches...</p>
        <p className="text-xs text-muted/50 mt-1 font-mono">
          Analyzing semantic similarity & skill overlap
        </p>
      </div>
    );
  }

  // ── No jobs in database ──
  if (error?.includes("No jobs in the database")) {
    return (
      <div className="border border-line rounded-card p-10 text-center flex flex-col items-center gap-5 animate-scale-in">
        <div className="w-14 h-14 rounded-2xl bg-surface2 flex items-center justify-center text-2xl">
          📋
        </div>
        <div>
          <p className="text-sm font-semibold text-ink mb-1">No jobs loaded yet</p>
          <p className="text-sm text-muted max-w-md">
            Fetch real Bangladesh jobs from the internet, or load sample data to try the matching engine.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            type="button"
            onClick={() => handleFetchJobs()}
            disabled={fetching}
            className="bg-amber text-base font-semibold text-sm px-5 py-2.5 rounded-card
                       hover:bg-amber-dim transition-colors disabled:opacity-50
                       animate-pulse-glow flex items-center gap-2"
          >
            {fetching ? (
              <>
                <span className="w-3 h-3 border border-base border-t-transparent rounded-full animate-spin-slow"></span>
                Fetching jobs...
              </>
            ) : (
              "🌐 Fetch real jobs from internet"
            )}
          </button>

          <button
            type="button"
            onClick={handleSeed}
            disabled={seeding}
            className="text-sm px-5 py-2.5 rounded-card border border-line
                       text-muted hover:text-ink hover:border-ink
                       transition-colors disabled:opacity-50"
          >
            {seeding ? "Loading..." : "Load sample jobs instead"}
          </button>
        </div>

        {fetchResult && (
          <FetchResultBanner result={fetchResult} />
        )}
      </div>
    );
  }

  // ── Error state ──
  if (error) {
    return (
      <div className="border border-coral/30 bg-coral/5 rounded-card p-6 text-center animate-fade-in">
        <p className="text-sm text-coral mb-2">{error}</p>
        <button
          type="button"
          onClick={load}
          className="text-xs text-muted hover:text-ink underline underline-offset-4"
        >
          Try again
        </button>
      </div>
    );
  }

  // ── Empty matches ──
  if (matches.length === 0) {
    return (
      <div className="text-center py-16 animate-fade-in">
        <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-surface2 flex items-center justify-center text-2xl">
          🔍
        </div>
        <p className="text-sm font-semibold text-ink mb-1">No matches found</p>
        <p className="text-sm text-muted max-w-sm mx-auto">
          Try updating your profile with more skills and experience to improve matching.
        </p>
      </div>
    );
  }

  // ── Matches list ──
  const shortlistedCount = Object.values(shortlistMap).filter(
    (s) => s === "shortlisted"
  ).length;

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-base font-semibold text-ink">Your Top Matches</h2>
          <p className="text-xs text-muted mt-0.5">
            {matches.length} job{matches.length === 1 ? "" : "s"} ranked by
            compatibility
            {shortlistedCount > 0 && (
              <span className="text-amber ml-1">
                · {shortlistedCount} shortlisted
              </span>
            )}
          </p>
        </div>

        {/* Fetch more jobs button */}
        <button
          type="button"
          onClick={() => handleFetchJobs()}
          disabled={fetching}
          className="text-xs font-medium px-3 py-1.5 rounded-card border border-line
                     text-muted hover:text-ink hover:border-ink transition-colors
                     disabled:opacity-50 flex items-center gap-1.5 self-start"
        >
          {fetching ? (
            <>
              <span className="w-2.5 h-2.5 border border-muted border-t-transparent rounded-full animate-spin-slow"></span>
              Fetching...
            </>
          ) : (
            <>🌐 Fetch more jobs</>
          )}
        </button>
      </div>

      {/* Fetch result banner */}
      {fetchResult && (
        <div className="mb-4">
          <FetchResultBanner result={fetchResult} />
        </div>
      )}

      {/* Job cards */}
      <div className="flex flex-col gap-4 stagger-children">
        {matches.map((match) => (
          <JobCard
            key={match.job.id}
            match={match}
            onShortlist={handleShortlist}
            shortlistStatus={shortlistMap[match.job.id]}
          />
        ))}
      </div>
    </div>
  );
}


function FetchResultBanner({ result }) {
  if (result.status === "no_results") {
    return (
      <div className="bg-surface2/50 border border-line rounded-card px-4 py-3 text-xs text-muted animate-fade-in">
        No new jobs found. Make sure your <span className="font-mono text-amber">RAPIDAPI_KEY</span> is set in the backend .env file.
      </div>
    );
  }

  const sources = result.sources || {};
  const emailsSent = result.notifications?.emails_sent ?? 0;
  return (
    <div className="bg-teal/5 border border-teal/20 rounded-card px-4 py-3 text-xs animate-fade-in">
      <p className="text-teal font-medium mb-1">
        ✓ {result.new_jobs_added} new job{result.new_jobs_added === 1 ? "" : "s"} added
        <span className="text-muted font-normal ml-1">
          ({result.total_jobs_in_db} total in database)
        </span>
      </p>
      {emailsSent > 0 && (
        <p className="text-muted mb-1">
          ✉️ Sent {emailsSent} match alert email{emailsSent === 1 ? "" : "s"}
        </p>
      )}
      <div className="flex flex-wrap gap-3 text-muted">
        {Object.entries(sources).map(([name, stats]) => (
          <span key={name} className="font-mono">
            {name}: {stats.fetched} fetched, {stats.new} new, {stats.skipped} skipped
          </span>
        ))}
      </div>
    </div>
  );
}
