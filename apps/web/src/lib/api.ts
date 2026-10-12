/** TaxStox API client — communicates with the FastAPI backend. */

/** Resolve the backend base URL. Use this for any direct fetch so we never
 *  duplicate the `NEXT_PUBLIC_API_URL || localhost` fallback across files. */
export function getApiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
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
): Promise<{ downloadUrl: string }> {
  const res = await fetchApi(`${getApiBase()}/tax/${sessionId}/export/${format}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to export ITR");
  }

  return res.json();
}

export async function fetchPortfolio(
  userId: string
): Promise<{ holdings: Array<{ symbol: string; name: string; quantity: number }> }> {
  const res = await fetchApi(`${getApiBase()}/portfolio/${userId}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch portfolio");
  }

  return res.json();
}

export async function fetchRecommendations(
  userId: string
): Promise<{ recommendations: Array<{ symbol: string; name: string; type: string }> }> {
  const res = await fetchApi(`${getApiBase()}/recommendations/${userId}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch recommendations");
  }

  return res.json();
}

export async function fetchTaxInsights(
  userId: string
): Promise<{ insights: Array<{ type: string; value: string }> }> {
  const res = await fetchApi(`${getApiBase()}/tax-insights/${userId}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch tax insights");
  }

  return res.json();
}

export async function getTaxHarvesting(
  userId: string
): Promise<{ harvesting: Array<{ symbol: string; gainLoss: string }> }> {
  const res = await fetchApi(`${getApiBase()}/tax/harvesting/${userId}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to get tax harvesting");
  }

  return res.json();
}

export async function processPDFs(
  sessionId: string,
  files: File[]
): Promise<{ processed: boolean }> {
  const formData = new FormData();
  files.forEach(file => formData.append("files", file));
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
): Promise<{ success: boolean }> {
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
  sessionId: string,
  file: File
): Promise<{ success: boolean }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("sessionId", sessionId);

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
  sessionId: string,
  files: File[]
): Promise<{ success: boolean }> {
  const formData = new FormData();
  files.forEach(file => formData.append("files", file));
  formData.append("sessionId", sessionId);

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
