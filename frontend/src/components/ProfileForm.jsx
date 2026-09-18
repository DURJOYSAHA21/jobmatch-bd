import { useRef, useState } from "react";

import { api } from "../api";

const FIELDS = [
  { key: "name", label: "Name", type: "input", placeholder: "Your name" },
  {
    key: "email",
    label: "Email (for match alerts)",
    type: "input",
    inputType: "email",
    placeholder: "you@example.com",
    hint: "When new jobs match your profile, we'll email you here.",
  },
  { key: "education", label: "Education", type: "input", placeholder: "e.g. CSE, BSc in Computer Science" },
  {
    key: "skills",
    label: "Skills",
    type: "textarea",
    placeholder: "Python, C#, ASP.NET Core, SQL, Machine Learning",
  },
  {
    key: "interests",
    label: "Interests",
    type: "textarea",
    placeholder: "AI, NLP, Backend Development",
  },
  {
    key: "experience",
    label: "Experience",
    type: "textarea",
    placeholder: "ML research, .NET projects, 2 years backend development",
  },
  { key: "location", label: "Location", type: "input", placeholder: "Dhaka" },
];

export default function ProfileForm({ profile, onSaved }) {
  const [form, setForm] = useState({
    name: "",
    email: "",
    education: "",
    skills: "",
    interests: "",
    experience: "",
    location: "",
    ...(profile || {}),
  });
  const [saving, setSaving] = useState(false);
  const [cvStatus, setCvStatus] = useState(null);
  const fileInputRef = useRef(null);

  const update = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const saved = profile?.id
        ? await api.updateProfile(profile.id, form)
        : await api.createProfile(form);
      onSaved(saved);
    } catch (err) {
      setCvStatus({ type: "error", message: err.message });
    } finally {
      setSaving(false);
    }
  };

  const handleCvUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // If no profile yet, create one first
    let profileId = profile?.id;
    if (!profileId) {
      setCvStatus({ type: "loading", message: "Creating profile..." });
      try {
        const newProfile = await api.createProfile(form);
        profileId = newProfile.id;
      } catch (err) {
        setCvStatus({ type: "error", message: err.message });
        return;
      }
    }

    setCvStatus({ type: "loading", message: "Analyzing your CV..." });
    try {
      const result = await api.uploadCV(profileId, file);
      const refreshed = await api.getProfile(profileId);
      setForm(refreshed);
      onSaved(refreshed);
      setCvStatus({
        type: "success",
        message: `Found ${result.skills.length} skill${result.skills.length === 1 ? "" : "s"} in your CV.`,
      });
    } catch (err) {
      setCvStatus({ type: "error", message: err.message });
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {/* CV upload section — always visible */}
      <div className="border border-line rounded-card p-4 flex flex-col gap-2 bg-surface2/30">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-base">📄</span>
          <span className="text-xs font-semibold text-ink">
            Upload CV (PDF)
          </span>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          onChange={handleCvUpload}
          className="text-xs text-muted file:mr-3 file:py-1.5 file:px-3 file:rounded-card
                     file:border-0 file:bg-amber/10 file:text-amber file:text-xs file:font-medium
                     hover:file:bg-amber/20 file:cursor-pointer cursor-pointer file:transition-colors"
        />
        {cvStatus?.type === "loading" && (
          <div className="flex items-center gap-2 animate-fade-in">
            <div className="w-3 h-3 border border-amber border-t-transparent rounded-full animate-spin-slow"></div>
            <p className="text-xs text-muted">{cvStatus.message}</p>
          </div>
        )}
        {cvStatus?.type === "success" && (
          <p className="text-xs text-teal animate-fade-in">✓ {cvStatus.message}</p>
        )}
        {cvStatus?.type === "error" && (
          <p className="text-xs text-coral animate-fade-in">✗ {cvStatus.message}</p>
        )}
        <p className="text-[10px] text-muted/60">
          Skills and education will be auto-extracted and merged into your profile.
        </p>
      </div>

      {/* Divider */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-px bg-line"></div>
        <span className="text-[10px] text-muted font-mono uppercase tracking-widest">
          or fill in manually
        </span>
        <div className="flex-1 h-px bg-line"></div>
      </div>

      {/* Manual form fields */}
      {FIELDS.map(({ key, label, type, placeholder, inputType, hint }) => (
        <label key={key} className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted">{label}</span>
          {type === "textarea" ? (
            <textarea
              value={form[key] ?? ""}
              onChange={(e) => update(key, e.target.value)}
              placeholder={placeholder}
              rows={2}
              className="text-sm resize-none w-full"
            />
          ) : (
            <input
              type={inputType || "text"}
              value={form[key] ?? ""}
              onChange={(e) => update(key, e.target.value)}
              placeholder={placeholder}
              className="text-sm w-full"
            />
          )}
          {hint && (
            <span className="text-[10px] text-muted/70">{hint}</span>
          )}
        </label>
      ))}

      <button
        type="submit"
        disabled={saving}
        className="mt-1 bg-amber text-base font-semibold text-sm py-2.5 rounded-card
                   hover:bg-amber-dim transition-colors disabled:opacity-50"
      >
        {saving ? "Saving..." : profile?.id ? "Update profile" : "Find my matches"}
      </button>
    </form>
  );
}
