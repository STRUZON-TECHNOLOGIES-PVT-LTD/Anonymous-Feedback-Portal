import type {
  AdminInfo,
  FeedbackSubmitPayload,
  PowChallenge,
  Question,
  Stats,
  SubmissionDetail,
  SubmissionListResponse,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore parse failure, keep statusText
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  getQuestions: () => request<Question[]>("/api/questions"),

  getPowChallenge: () => request<PowChallenge>("/api/pow-challenge"),

  submitFeedback: (payload: FeedbackSubmitPayload) =>
    request("/api/feedback", { method: "POST", body: JSON.stringify(payload) }),

  adminLogin: (username: string, password: string) =>
    request<AdminInfo>("/api/admin/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  adminLogout: () => request("/api/admin/logout", { method: "POST" }),

  adminMe: () => request<AdminInfo>("/api/admin/me"),

  listSubmissions: (page: number, pageSize = 20) =>
    request<SubmissionListResponse>(`/api/admin/submissions?page=${page}&page_size=${pageSize}`),

  getSubmission: (id: string) => request<SubmissionDetail>(`/api/admin/submissions/${id}`),

  getStats: () => request<Stats>("/api/admin/stats"),
};

export { ApiError };
