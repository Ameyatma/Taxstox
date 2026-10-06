/** TaxStox API client — communicates with the FastAPI backend. */

// Single source of truth for the backend base URL. Every fetch in the app
// must route through here so the API origin is configured in exactly one place.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/** Resolve the backend base URL. Use this for any direct fetch so we never
 *  duplicate the `NEXT_PUBLIC_API_URL || localhost` fallback across files. */
export function getApiBase(): string {
  return API_BASE;
}

/** Optional handler for 401 Unauthorized responses from authenticated endpoints.
 *  AuthProvider sets this to clear token and redirect to /auth. */
export let onUnauthorized: (() => void) | null = null;

/** Register a global handler invoked when any API call receives a 401.
 *  AuthProvider sets this to clear token and redirect to /auth. */
export function setOnUnauthorized(fn: (() => void) | null) {
  onUnauthorized = fn;
}

// Shared 401 handler — clears cookies on the backend via logout endpoint.
async function handleUnauthorized() {
  try {
    await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
  } catch {
    // Ignore logout errors
  }
  if (onUnauthorized) onUnauthorized();
}

// ── Helpers ──────────────────────────────────────────────────

// No localStorage token handling — tokens are managed via httpOnly cookies.

// ── Auth Types ───────────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string;
  pan: string;
  name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

// ── Shared fetch wrapper with credentials ────────────────────

async function fetchApi(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const res = await fetch(url, {
    ...options,
    credentials: "include",
  });
  if (res.status === 401) {
    await handleUnauthorized();
  }
  return res;
}

// ── Auth API ─────────────────────────────────────────────────

export async function registerUser(
  email: string, password: string, pan: string, name: string, dob?: string
): Promise<TokenResponse> {
  const res = await fetchApi(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, pan, name, dob: dob || "" }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

export async function loginUser(email: string, password: string): Promise<TokenResponse> {
  const res = await fetchApi(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }
  return res.json();
}

export async function fetchMe(): Promise<AuthUser> {
  const res = await fetchApi(`${API_BASE}/auth/me`);
  if (res.status === 401) {
    throw new Error("Session expired");
  }
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

// ── ITR Types ────────────────────────────────────────────────

export interface UploadResponseData {
  session_id: string;
  status: string;
  data_summary?: Record<string, string | number>;
  password_required: boolean;
  password_hint?: string;
}

export interface Question {
  id: string;
  text: string;
  type: "yes_no" | "number" | "dropdown" | "text";
  sub_questions?: Question[];
  impact: string;
  depends_on?: string;
  depends_on_answer?: string;
}

export interface QuestionsResponseData {
  itr_type: string;
  regime_recommended: "old" | "new";
  regime_savings: string;
  income_summary: Record<string, string | number>;
  questions: Question[];
}

export interface TaxSummaryData {
  income: Record<string, string>;
  deductions: Record<string, string>;
  taxable_income: string;
  tax_breakdown: Record<string, string>;
  payments: Record<string, string>;
  balance_payable: string;
  regime: "old" | "new";
  regime_savings: string;
  filing_deadline: string;
}

export interface ExportData {
  filename: string;
  json_data: Record<string, unknown>;
  validation_passed: boolean;
  validation_warnings: string[];
}

export async function uploadPDFs(
  pan: string,
  dob: string,
  form16File?: File | null,
  aisFile?: File | null,
  form16Password?: string
): Promise<UploadResponseData> {
  const formData = new FormData();
  formData.append("pan", pan);
  formData.append("dob", dob);

  if (form16File) {
    formData.append("form16_pdf", form16File);
  }
  if (aisFile) {
    formData.append("ais_pdf", aisFile);
  }
  if (form16Password) {
    formData.append("form16_password", form16Password);
  }

  const res = await fetchApi(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (res.status === 401) {
    throw new Error("Session expired");
  }

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Upload failed");
  }

  return res.json();
}

export async function processPDFs(sessionId: string): Promise<QuestionsResponseData> {
  const res = await fetchApi(`${API_BASE}/process/${sessionId}`, {
    method: "POST",
  });

  if (res.status === 401) {
    throw new Error("Session expired");
  }

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Processing failed");
  }

  return res.json();
}

export async function submitAnswers(
  sessionId: string,
  answers: Record<string, string>
): Promise<TaxSummaryData> {
  const res = await fetchApi(`${API_BASE}/answers/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, answers }),
  });

  if (res.status === 401) {
    throw new Error("Session expired");
  }

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to compute tax");
  }

  return res.json();
}

export async function exportITR(sessionId: string): Promise<ExportData> {
  const res = await fetchApi(`${API_BASE}/export/${sessionId}`, {
    method: "POST",
  });

  if (res.status === 401) {
    throw new Error("Session expired");
  }

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Export failed");
  }

  return res.json();
}

// ── Dashboard API ────────────────────────────────────────────

export interface DashboardStats {
  total_filings: number;
  total_refunds: string;
  total_tax_saved: string;
  filed_count: number;
  draft_count: number;
  days_remaining: number;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  href: string;
  primary?: boolean;
}

export interface FilingRecord {
  id: string;
  assessment_year: string;
  itr_type: string;
  regime: string | null;
  gross_income: string | null;
  tax_paid: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TaxCalendarEvent {
  date: string;
  title: string;
  type: string;
}

export interface DashboardData {
  stats: DashboardStats;
  quick_actions: QuickAction[];
  filings: FilingRecord[];
  tax_calendar: TaxCalendarEvent[];
  user_name: string;
}

export async function fetchDashboard(): Promise<DashboardData> {
  const res = await fetchApi(`${API_BASE}/dashboard`);
  if (!res.ok) throw new Error("Failed to load dashboard");
  return res.json();
}

export async function fetchFilings(): Promise<FilingRecord[]> {
  const res = await fetchApi(`${API_BASE}/filings`);
  if (!res.ok) throw new Error("Failed to load filings");
  return res.json();
}

// ── Tax Updates & Insights API ────────────────────────────────

export interface TaxUpdateItem {
  id: string;
  title: string;
  summary_short: string;
  what_changed: string;
  who_affected: string;
  action_required: string;
  category: string;
  effective_date: string;
  published_date: string;
  source: string;
  source_url: string;
  is_active: boolean;
  created_at: string;
}

export interface TaxDeadlineItem {
  id: string;
  title: string;
  date: string;
  description: string;
  category: string;
  is_active: boolean;
}

export interface TaxTipItem {
  id: string;
  text: string;
  sort_order: number;
  is_active: boolean;
}

export interface TaxFactItem {
  id: string;
  title: string;
  description: string;
  icon: string;
  sort_order: number;
  is_active: boolean;
}

export interface TaxInsightsData {
  updates: TaxUpdateItem[];
  deadlines: TaxDeadlineItem[];
  tips: TaxTipItem[];
  facts: TaxFactItem[];
  last_synced: string | null;
}

export async function fetchTaxInsights(): Promise<TaxInsightsData> {
  const res = await fetchApi(`${API_BASE}/tax/insights`);
  if (!res.ok) throw new Error("Failed to load tax insights");
  return res.json();
}