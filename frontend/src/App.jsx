import { useEffect, useState } from "react";

import { api } from "./api";
import BrowseJobs from "./components/BrowseJobs";
import JobFeed from "./components/JobFeed";
import LandingPage from "./components/LandingPage";
import ProfileForm from "./components/ProfileForm";
import Shortlist from "./components/Shortlist";

const STORAGE_KEY = "jobmatch-bd:profile-id";

export default function App() {
  const [profile, setProfile] = useState(null);
  const [loadingStoredProfile, setLoadingStoredProfile] = useState(true);
  const [editing, setEditing] = useState(false);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [tab, setTab] = useState("feed");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Try to restore a previously-saved profile from localStorage
  useEffect(() => {
    const storedId = localStorage.getItem(STORAGE_KEY);
    if (!storedId) {
      setLoadingStoredProfile(false);
      return;
    }
    api
      .getProfile(Number(storedId))
      .then((p) => {
        setProfile(p);
        setEditing(false);
      })
      .catch(() => localStorage.removeItem(STORAGE_KEY))
      .finally(() => setLoadingStoredProfile(false));
  }, []);

  const handleProfileReady = (saved, shouldEdit = false) => {
    setProfile(saved);
    localStorage.setItem(STORAGE_KEY, String(saved.id));
    setEditing(shouldEdit);
    setShowManualEntry(false);
  };

  const handleSaved = (saved) => {
    setProfile(saved);
    localStorage.setItem(STORAGE_KEY, String(saved.id));
    setEditing(false);
  };

  const handleLogout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setProfile(null);
    setEditing(false);
    setShowManualEntry(false);
    setTab("feed");
  };

  // ── Loading ──
  if (loadingStoredProfile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <div className="w-10 h-10 mx-auto mb-3 border-2 border-line border-t-amber rounded-full animate-spin-slow"></div>
          <p className="text-sm text-muted font-mono">Loading...</p>
        </div>
      </div>
    );
  }

  // ── Landing page (no profile yet) ──
  if (!profile?.id && !showManualEntry) {
    return (
      <LandingPage
        onProfileReady={handleProfileReady}
        onManualEntry={() => setShowManualEntry(true)}
      />
    );
  }

  // ── Manual profile creation (from landing "Build manually") ──
  if (!profile?.id && showManualEntry) {
    return (
      <div className="min-h-screen flex flex-col">
        <header className="border-b border-line px-6 py-4 flex items-center justify-between animate-slide-down">
          <div className="flex items-baseline gap-2">
            <h1 className="text-lg font-semibold tracking-tight">
              <span className="text-amber">Job</span>Match BD
            </h1>
          </div>
          <button
            type="button"
            onClick={() => setShowManualEntry(false)}
            className="text-xs text-muted hover:text-ink transition-colors"
          >
            ← Back
          </button>
        </header>
        <main className="flex-1 flex items-center justify-center px-6 py-12">
          <div className="w-full max-w-md animate-slide-up">
            <p className="text-sm text-muted mb-6 leading-relaxed">
              Tell us your education, skills, and interests. We'll compare your
              profile against open postings using semantic matching — not just
              keyword search — and rank the ones worth your time.
            </p>
            <ProfileForm profile={null} onSaved={handleSaved} />
          </div>
        </main>
      </div>
    );
  }

  // ── Dashboard (profile exists) ──
  const TABS = [
    { key: "feed", label: "Matches", icon: "🎯" },
    { key: "all", label: "All Jobs", icon: "📋" },
    { key: "shortlist", label: "Shortlist", icon: "⭐" },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Top nav ── */}
      <header className="border-b border-line px-4 sm:px-6 py-3 flex items-center justify-between animate-slide-down">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold tracking-tight">
            <span className="text-amber">Job</span>Match BD
          </h1>

          {/* Desktop tabs */}
          <nav className="hidden sm:flex gap-1 ml-4">
            {TABS.map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => setTab(t.key)}
                className={`text-sm px-3 py-1.5 rounded-card transition-colors flex items-center gap-1.5 ${
                  tab === t.key
                    ? "bg-surface2 text-ink"
                    : "text-muted hover:text-ink"
                }`}
              >
                <span className="text-xs">{t.icon}</span>
                {t.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {/* Profile button */}
          <button
            type="button"
            onClick={() => setSidebarOpen((v) => !v)}
            className="flex items-center gap-2 text-sm text-muted hover:text-ink transition-colors py-1.5 px-3 rounded-card border border-line hover:border-ink"
          >
            <span className="w-5 h-5 rounded-full bg-amber/20 border border-amber/30 flex items-center justify-center text-[10px] font-bold text-amber">
              {(profile.name || "U").charAt(0).toUpperCase()}
            </span>
            <span className="hidden sm:inline font-medium truncate max-w-[120px]">
              {profile.name || "Your Profile"}
            </span>
          </button>
        </div>
      </header>

      {/* Mobile tabs */}
      <div className="sm:hidden flex border-b border-line">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className={`flex-1 text-sm py-2.5 text-center transition-colors border-b-2 ${
              tab === t.key
                ? "border-amber text-ink"
                : "border-transparent text-muted"
            }`}
          >
            <span className="mr-1">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Main content area ── */}
      <div className="flex-1 flex relative">
        {/* Sidebar overlay (profile panel) */}
        {sidebarOpen && (
          <>
            <div
              className="fixed inset-0 bg-black/40 z-30 sm:hidden"
              onClick={() => setSidebarOpen(false)}
            ></div>
            <aside className="fixed right-0 top-0 h-full w-80 bg-surface border-l border-line z-40 p-6 overflow-y-auto animate-slide-down sm:animate-fade-in">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-sm font-semibold text-ink">Your Profile</h2>
                <button
                  type="button"
                  onClick={() => setSidebarOpen(false)}
                  className="text-muted hover:text-ink text-lg leading-none"
                >
                  ×
                </button>
              </div>

              {editing ? (
                <ProfileForm
                  profile={profile}
                  onSaved={(saved) => {
                    handleSaved(saved);
                    setEditing(false);
                  }}
                />
              ) : (
                <div className="flex flex-col gap-4">
                  <div>
                    <p className="text-sm font-semibold text-ink">
                      {profile.name || "Your profile"}
                    </p>
                    {profile.education && (
                      <p className="text-xs text-muted mt-1">
                        {profile.education}
                      </p>
                    )}
                  </div>

                  {profile.skills && (
                    <div>
                      <p className="text-xs text-muted mb-2">Skills</p>
                      <div className="flex flex-wrap gap-1.5">
                        {profile.skills
                          .split(",")
                          .filter((s) => s.trim())
                          .map((skill) => (
                            <span
                              key={skill.trim()}
                              className="text-xs font-mono px-2 py-0.5 rounded-pill bg-surface2 text-ink border border-line"
                            >
                              {skill.trim()}
                            </span>
                          ))}
                      </div>
                    </div>
                  )}

                  {profile.experience && (
                    <div>
                      <p className="text-xs text-muted mb-1">Experience</p>
                      <p className="text-xs text-ink leading-relaxed">
                        {profile.experience}
                      </p>
                    </div>
                  )}

                  {profile.location && (
                    <div>
                      <p className="text-xs text-muted mb-1">Location</p>
                      <p className="text-xs text-ink">{profile.location}</p>
                    </div>
                  )}

                  {profile.email && (
                    <div>
                      <p className="text-xs text-muted mb-1">Email alerts</p>
                      <p className="text-xs text-ink break-all">{profile.email}</p>
                      <p className="text-[10px] text-muted/70 mt-1">
                        You'll get an email when new jobs match your profile.
                      </p>
                    </div>
                  )}

                  <div className="flex flex-col gap-2 pt-2 border-t border-line">
                    <button
                      type="button"
                      onClick={() => setEditing(true)}
                      className="text-xs text-muted hover:text-ink underline decoration-line underline-offset-4 self-start"
                    >
                      Edit profile
                    </button>
                    <button
                      type="button"
                      onClick={handleLogout}
                      className="text-xs text-coral/70 hover:text-coral underline decoration-line underline-offset-4 self-start"
                    >
                      Start over
                    </button>
                  </div>
                </div>
              )}
            </aside>
          </>
        )}

        {/* Main feed area */}
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 max-w-4xl mx-auto w-full page-enter">
          {tab === "feed" && <JobFeed profileId={profile.id} />}
          {tab === "all" && <BrowseJobs profileId={profile.id} />}
          {tab === "shortlist" && <Shortlist profileId={profile.id} />}
        </main>
      </div>
    </div>
  );
}
