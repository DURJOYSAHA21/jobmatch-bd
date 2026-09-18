import { useRef, useState } from "react";

import { api } from "../api";

const FEATURES = [
  {
    icon: "🧠",
    title: "Semantic Matching",
    desc: "Goes beyond keywords — understands what your skills actually mean.",
  },
  {
    icon: "📊",
    title: "Skill Analysis",
    desc: "Extracts and maps your skills against job requirements automatically.",
  },
  {
    icon: "💡",
    title: "Smart Explanations",
    desc: "See exactly why each job matched — not just a percentage.",
  },
];

export default function LandingPage({ onProfileReady, onManualEntry }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadPhase, setUploadPhase] = useState(""); // creating | parsing | done
  const [parsedResult, setParsedResult] = useState(null);
  const [pendingProfile, setPendingProfile] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const processFile = async (file) => {
    if (!file) return;
    if (file.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File too large. Please upload a PDF under 10MB.");
      return;
    }

    setError(null);
    setUploading(true);

    try {
      // Step 1: Create a blank profile
      setUploadPhase("creating");
      const profile = await api.createProfile({
        name: "",
        education: "",
        skills: "",
        interests: "",
        experience: "",
        location: "",
      });

      // Step 2: Upload CV to that profile
      setUploadPhase("parsing");
      const result = await api.uploadCV(profile.id, file);

      // Step 3: Fetch the updated profile (with extracted skills merged in)
      const updatedProfile = await api.getProfile(profile.id);

      setUploadPhase("done");
      setParsedResult(result);
      setPendingProfile(updatedProfile);
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
      setUploading(false);
      setUploadPhase("");
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    processFile(file);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    processFile(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleContinue = () => {
    if (pendingProfile) {
      onProfileReady(pendingProfile);
    }
  };

  // ── Uploading / parsing state ──
  if (uploading && uploadPhase !== "done") {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="text-center animate-fade-in">
          <div className="relative w-20 h-20 mx-auto mb-6">
            <div className="absolute inset-0 border-2 border-line rounded-full"></div>
            <div className="absolute inset-0 border-2 border-amber border-t-transparent rounded-full animate-spin-slow"></div>
            <span className="absolute inset-0 flex items-center justify-center text-2xl">
              {uploadPhase === "creating" ? "📄" : "🔍"}
            </span>
          </div>
          <h2 className="text-lg font-semibold text-ink mb-2">
            {uploadPhase === "creating"
              ? "Setting up your profile..."
              : "Analyzing your CV..."}
          </h2>
          <p className="text-sm text-muted max-w-xs mx-auto">
            {uploadPhase === "creating"
              ? "Creating your profile to store the results."
              : "Extracting skills, education, and experience from your CV."}
          </p>
          <div className="progress-bar w-48 mx-auto mt-6">
            <div className="progress-bar-fill bg-amber"></div>
          </div>
        </div>
      </div>
    );
  }

  // ── Parsed result — show what we found ──
  if (uploading && uploadPhase === "done" && parsedResult) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-lg animate-scale-in">
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-teal/10 border border-teal/30 flex items-center justify-center text-2xl">
              ✅
            </div>
            <h2 className="text-xl font-semibold text-ink mb-2">
              CV Analyzed Successfully
            </h2>
            <p className="text-sm text-muted">
              Here's what we extracted from your resume.
            </p>
          </div>

          <div className="bg-surface border border-line rounded-card p-6 space-y-5">
            {/* Skills found */}
            {parsedResult.skills.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted mb-2">
                  Skills Found ({parsedResult.skills.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {parsedResult.skills.map((skill) => (
                    <span
                      key={skill}
                      className="text-xs font-mono px-2.5 py-1 rounded-pill bg-teal/10 text-teal border border-teal/30"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Education guess */}
            {parsedResult.education_guess && (
              <div>
                <p className="text-xs font-medium text-muted mb-1">
                  Education
                </p>
                <p className="text-sm text-ink">
                  {parsedResult.education_guess}
                </p>
              </div>
            )}

            {/* CV text preview */}
            {parsedResult.raw_text_preview && (
              <div>
                <p className="text-xs font-medium text-muted mb-1">
                  CV Preview
                </p>
                <p className="text-xs text-muted leading-relaxed line-clamp-4 bg-surface2 rounded-card p-3">
                  {parsedResult.raw_text_preview}
                </p>
              </div>
            )}

            {parsedResult.skills.length === 0 && (
              <div className="text-center py-4">
                <p className="text-sm text-muted">
                  We couldn't extract specific skills from your CV. You can add
                  them manually after continuing.
                </p>
              </div>
            )}
          </div>

          <div className="flex flex-col gap-3 mt-6">
            <button
              type="button"
              onClick={handleContinue}
              className="w-full bg-amber text-base font-semibold text-sm py-3 rounded-card
                         hover:bg-amber-dim transition-colors animate-pulse-glow"
            >
              See My Job Matches →
            </button>
            <button
              type="button"
              onClick={() => onProfileReady(pendingProfile, true)}
              className="w-full text-sm text-muted hover:text-ink py-2 transition-colors"
            >
              Edit my profile first
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Main landing page ──
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="px-6 py-4 flex items-center justify-between animate-slide-down">
        <div className="flex items-baseline gap-2">
          <h1 className="text-lg font-semibold tracking-tight">
            <span className="text-amber">Job</span>Match BD
          </h1>
        </div>
        <button
          type="button"
          onClick={onManualEntry}
          className="text-xs text-muted hover:text-ink font-medium py-1.5 px-3 rounded-card border border-line hover:border-ink transition-colors"
        >
          Build profile manually
        </button>
      </header>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12 hero-grid relative">
        {/* Background gradient orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-amber/5 rounded-full blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-teal/5 rounded-full blur-[100px] pointer-events-none"></div>

        <div className="relative z-10 w-full max-w-2xl text-center">
          {/* Headline */}
          <div className="animate-slide-up mb-10">
            <p className="text-xs font-mono text-amber tracking-widest uppercase mb-4">
              NLP-Powered Job Discovery
            </p>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-ink leading-tight mb-4">
              Find Jobs That
              <br />
              <span className="bg-gradient-to-r from-amber to-teal bg-clip-text text-transparent animate-gradient">
                Actually Match You
              </span>
            </h2>
            <p className="text-base text-muted max-w-lg mx-auto leading-relaxed">
              Upload your CV and our semantic engine will rank open positions
              against your real skills — not just keywords.
            </p>
          </div>

          {/* Upload zone */}
          <div
            className={`drop-zone p-8 sm:p-10 cursor-pointer mb-8 animate-slide-up ${
              dragging ? "dragging" : ""
            }`}
            style={{ animationDelay: "100ms" }}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              onChange={handleFileSelect}
              className="hidden"
            />

            <div className="animate-float mb-4">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-amber/10 border border-amber/20 flex items-center justify-center text-3xl">
                📄
              </div>
            </div>

            <p className="text-base font-semibold text-ink mb-1">
              Drop your CV here or click to browse
            </p>
            <p className="text-sm text-muted">
              PDF files only · Max 10MB
            </p>

            {error && (
              <p className="text-sm text-coral mt-3 animate-fade-in">
                {error}
              </p>
            )}
          </div>

          {/* Feature cards */}
          <div
            className="grid grid-cols-1 sm:grid-cols-3 gap-4 stagger-children animate-slide-up"
            style={{ animationDelay: "200ms" }}
          >
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="glass-card rounded-card p-4 text-center animate-slide-up"
              >
                <span className="text-2xl mb-2 block">{f.icon}</span>
                <p className="text-sm font-semibold text-ink mb-1">
                  {f.title}
                </p>
                <p className="text-xs text-muted leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-4 text-center">
        <p className="text-xs text-muted/50 font-mono">
          JobMatch BD · Semantic job matching for Bangladesh
        </p>
      </footer>
    </div>
  );
}
