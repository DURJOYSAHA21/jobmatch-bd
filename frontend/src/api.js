const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  createProfile: (payload) =>
    request("/profile", { method: "POST", body: JSON.stringify(payload) }),

  updateProfile: (id, payload) =>
    request(`/profile/${id}`, { method: "PUT", body: JSON.stringify(payload) }),

  getProfile: (id) => request(`/profile/${id}`),

  uploadCV: (id, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/profile/${id}/cv`, { method: "POST", body: form });
  },

  seedJobs: () => request("/jobs/seed", { method: "POST" }),

  fetchJobs: (source) => {
    const params = source ? `?source=${source}` : "";
    return request(`/jobs/fetch${params}`, { method: "POST" });
  },

  getJobCount: () => request("/jobs/count"),

  getAllJobs: (limit = 500) => request(`/jobs?skip=0&limit=${limit}`),

  clearJobs: () => request("/jobs/clear", { method: "DELETE" }),

  getMatches: (profileId) => request(`/match/${profileId}`),

  shortlistJob: (profileId, jobId, status = "shortlisted") =>
    request("/shortlist", {
      method: "POST",
      body: JSON.stringify({ profile_id: profileId, job_id: jobId, status }),
    }),

  getShortlist: (profileId) => request(`/shortlist/${profileId}`),
};
