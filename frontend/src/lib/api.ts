/** TaxStox API client — communicates with the FastAPI backend. */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

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

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Upload failed");
  }

  return res.json();
}

export async function processPDFs(sessionId: string): Promise<QuestionsResponseData> {
  const res = await fetch(`${API_BASE}/process/${sessionId}`, {
    method: "POST",
  });

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
  const res = await fetch(`${API_BASE}/answers/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, answers }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to compute tax");
  }

  return res.json();
}

export async function exportITR(sessionId: string): Promise<ExportData> {
  const res = await fetch(`${API_BASE}/export/${sessionId}`, {
    method: "POST",
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Export failed");
  }

  return res.json();
}
