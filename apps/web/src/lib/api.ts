/** TaxStox API client — communicates with the FastAPI backend. */

/** Resolve the backend base path for API calls.
 *
 *  API calls are always issued against the *same origin* (`/api/v1/...`) and are
 *  proxied to the FastAPI backend by the rewrites in `next.config.ts`. This is
 *  required for cookie-based auth: the Google OAuth callback mints httpOnly
 *  session cookies on the frontend domain (taxstox.com), and those cookies are
 *  only transmitted on same-origin requests — a cross-origin backend such as
 *  `*.run.app` would never receive them. */
export function getApiBase(): string {
  return "/api/v1";
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
    await fetch(`${getApiBase()}/auth/logout`, { method: "POST", credentials: "include" });
  } catch {
    // Ignore logout errors
  }
  if (onUnauthorized) onUnauthorized();
}

// ── Helpers ────────────────────────────────────────────

// Get the access token from localStorage (set during Google OAuth handoff).
function getAccessTokenFromLocalStorage(): string | null {
  return localStorage.getItem("taxstox_access_token");
}

// Shared fetch wrapper with credentials and optional auth header
async function fetchApi(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  // Get token from localStorage (temporary handoff mechanism)
  const token = getAccessTokenFromLocalStorage();
  
  const headers = new Headers(options.headers ?? {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  // Handle 401 responses globally
  if (res.status === 401) {
    handleUnauthorized();
  }

  return res;
}

// ── Auth Types ───────────────────────────────────────────

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

// ── Tax Processing Types ───────────────────────────────────

export interface UploadResponseData {
  session_id: string;
  status: string;
  password_hint?: string;
}

export interface Question {
  id: string;
  text: string;
  impact?: string;
  depends_on?: string;
  depends_on_answer?: string;
  sub_questions?: SubQuestion[];
  type?: "text" | "number";
}

export interface SubQuestion {
  id: string;
  text: string;
  impact?: string;
  type?: "text" | "number";
}

export interface QuestionsResponseData {
  questions: Question[];
  regime_recommended: string;
  regime_savings?: number;
}

export interface HoldingPosition {
  symbol: string;
  isin?: string;
  quantity: number;
  buy_price: number;
  current_price: number;
  day_change_pct?: number;
  unrealized_pnl?: number;
  rating?: string;
  composite_score?: number;
  catalyst?: string;
}

export interface PortfolioItem {
  symbol: string;
  name: string;
  quantity: number;
  added_at?: string;
  rating?: string;
  catalyst?: string;
}

export interface Recommendation {
  symbol: string;
  name: string;
  target_price?: number;
  recommendation?: "buy" | "sell" | "hold";
  rating?: string;
  composite_score?: number;
  catalyst?: string;
}

export interface TaxHarvestingData {
  holdings: HoldingPosition[];
  realized_stcg?: number;
  total_potential_savings?: number;
  opportunities?: any[];
}

export interface TaxInsightsData {
  updates?: TaxUpdateItem[];
  deadlines?: TaxDeadlineItem[];
  tips?: TaxTipItem[];
  facts?: TaxFactItem[];
  last_synced?: string;
}

export interface TaxUpdateItem {
  id: string;
  title: string;
  summary_short: string;
  category: string;
  published_date: string;
  source_url?: string;
  source?: string;
}

export interface TaxDeadlineItem {
  id: string;
  title: string;
  date: string;
  description?: string;
}

export interface TaxTipItem {
  id: string;
  text: string;
}

export interface TaxFactItem {
  id: string;
  title: string;
  description: string;
  icon?: string;
}

export interface TaxSummaryData {
  taxable_income?: Record<string, number>;
  deductions?: Record<string, number>;
  payments?: Record<string, number>;
  balance_payable?: number;
  regime_savings?: number;
  regime?: "old" | "new";
  old_regime_breakdown?: Record<string, number>;
  new_regime_breakdown?: Record<string, number>;
  income?: Record<string, number>;
  tax_breakdown?: Record<string, number>;
}

export interface ExportData {
  downloadUrl?: string;
  json_data?: any;
  filename: string;
  validation_passed?: boolean;
  validation_warnings?: string[];
}

// ── Auth API ─────────────────────────────────────────────

export async function loginUser(email: string, password: string): Promise<TokenResponse> {
  const res = await fetchApi(`${getApiBase()}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Login failed");
  }

  return res.json();
}

export async function registerUser(
  email: string,
  password: string,
  pan: string,
  name: string,
  dob?: string
): Promise<TokenResponse> {
  const res = await fetchApi(`${getApiBase()}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, pan, name, dob }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Registration failed");
  }

  return res.json();
}

export async function fetchMe(): Promise<AuthUser> {
  const res = await fetchApi(`${getApiBase()}/auth/me`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch user");
  }

  return res.json();
}

export async function uploadFile(
  file: File,
  uploadType: string,
  metadata: Record<string, string> = {}
): Promise<{ sessionId: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("uploadType", uploadType);
  for (const [key, value] of Object.entries(metadata)) {
    formData.append(key, value);
  }

  const res = await fetchApi(`${getApiBase()}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Upload failed");
  }

  return res.json();
}

// ── Tax API ──────────────────────────────────────────────

export async function saveTaxReturn(
  sessionId: string,
  taxData: Record<string, unknown>
): Promise<{ success: boolean }> {
  const res = await fetchApi(`${getApiBase()}/tax/${sessionId}/return`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(taxData),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to save tax return");
  }

  return res.json();
}

export async function exportTaxReturn(
  sessionId: string,
  format: string = "json"
): Promise<{ downloadUrl: string }> {
  const res = await fetchApi(`${getApiBase()}/tax/${sessionId}/export/${format}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to export tax return");
  }

  return res.json();
}

export async function exportITR(
  sessionId: string,
  format: string = "json"
): Promise<ExportData> {
  const res = await fetchApi(`${getApiBase()}/tax/${sessionId}/export/${format}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to export ITR");
  }

  return res.json();
}

export async function fetchPortfolio(): Promise<PortfolioItem[]> {
  const res = await fetchApi(`${getApiBase()}/portfolio`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch portfolio");
  }

  return res.json();
}

export async function fetchRecommendations(): Promise<Recommendation[]> {
  const res = await fetchApi(`${getApiBase()}/recommendations`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch recommendations");
  }

  return res.json();
}

export async function fetchTaxInsights(): Promise<TaxInsightsData> {
  const res = await fetchApi(`${getApiBase()}/tax-insights`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch tax insights");
  }

  return res.json();
}

export async function getTaxHarvesting(sessionId: string): Promise<TaxHarvestingData> {
  const res = await fetchApi(`${getApiBase()}/tax/harvesting/${sessionId}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to get tax harvesting");
  }

  return res.json();
}

export async function processPDFs(
  sessionId: string
): Promise<QuestionsResponseData> {
  const formData = new FormData();
  formData.append("sessionId", sessionId);

  const res = await fetchApi(`${getApiBase()}/process-pdfs`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to process PDFs");
  }

  return res.json();
}

export async function submitAnswers(
  sessionId: string,
  answers: Record<string, string>
): Promise<TaxSummaryData> {
  const res = await fetchApi(`${getApiBase()}/answers/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(answers),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to submit answers");
  }

  return res.json();
}

export async function uploadBrokerPL(
  file: File,
  sessionId: string,
  password?: string
): Promise<UploadResponseData> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("sessionId", sessionId);
  if (password) {
    formData.append("password", password);
  }

  const res = await fetchApi(`${getApiBase()}/upload-broker-pl`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to upload broker PL");
  }

  return res.json();
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
    formData.append("form16_file", form16File);
  }
  if (aisFile) {
    formData.append("ais_file", aisFile);
  }
  if (form16Password) {
    formData.append("form16_password", form16Password);
  }

  const res = await fetchApi(`${getApiBase()}/upload-pdfs`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to upload PDFs");
  }

  return res.json();
}
