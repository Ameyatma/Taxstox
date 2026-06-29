/** Lightweight state management for the filing flow. */

export interface AppState {
  sessionId: string | null;
  pan: string;
  dob: string;
  step: "upload" | "questions" | "summary";
  uploadResult: Record<string, unknown> | null;
  questions: Question[] | null;
  regimeRecommended: string | null;
  taxSummary: Record<string, unknown> | null;
  itrExport: Record<string, unknown> | null;
}

type Question = {
  id: string;
  text: string;
  type: string;
  sub_questions?: Question[];
  impact?: string;
};

// In-memory store (reset on page reload — by design, no persistent financial data)
let store: AppState = {
  sessionId: null,
  pan: "",
  dob: "",
  step: "upload",
  uploadResult: null,
  questions: null,
  regimeRecommended: null,
  taxSummary: null,
  itrExport: null,
};

type Listener = () => void;
const listeners = new Set<Listener>();

export function getState(): AppState {
  return store;
}

export function setState(partial: Partial<AppState>) {
  store = { ...store, ...partial };
  listeners.forEach((fn) => fn());
}

export function subscribe(fn: Listener): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function reset() {
  store = {
    sessionId: null,
    pan: "",
    dob: "",
    step: "upload",
    uploadResult: null,
    questions: null,
    regimeRecommended: null,
    taxSummary: null,
    itrExport: null,
  };
  listeners.forEach((fn) => fn());
}
