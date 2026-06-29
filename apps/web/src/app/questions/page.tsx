"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { processPDFs, submitAnswers, type Question, type QuestionsResponseData } from "@/lib/api";
import { getState, setState } from "@/lib/store";

function QuestionsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session") || getState().sessionId;

  const [questionsData, setQuestionsData] = useState<QuestionsResponseData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [currentStep, setCurrentStep] = useState(0);
  const [errorId, setErrorId] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) { router.push("/"); return; }
    loadQuestions();
  }, [sessionId]);

  async function loadQuestions() {
    try {
      const data = await processPDFs(sessionId!);
      setQuestionsData(data);
      setState({ questions: data.questions as never[], regimeRecommended: data.regime_recommended });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process PDFs");
    } finally {
      setLoading(false);
    }
  }

  function setAnswer(id: string, value: string) {
    setAnswers((prev) => ({ ...prev, [id]: value }));
  }

  function isVisible(q: Question): boolean {
    if (!q.depends_on) return true;
    return answers[q.depends_on] === q.depends_on_answer;
  }

  async function handleSubmit() {
    setSubmitting(true);
    setError("");
    try {
      const result = await submitAnswers(sessionId!, answers);
      setState({ step: "summary", taxSummary: result as unknown as Record<string, unknown> });
      router.push(`/summary?session=${sessionId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to compute tax");
      setSubmitting(false);
    }
  }

  // ── Loading State — matches design skeleton ──
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="text-center space-y-4 animate-in fade-in">
          <div className="w-16 h-16 rounded-full bg-[#eff4ff] mx-auto flex items-center justify-center">
            <span className="material-symbols-outlined text-[#003366] text-3xl animate-spin">sync</span>
          </div>
          <h2 className="text-xl font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Classifying Your Data</h2>
          <p className="text-sm text-[#434652]">Analyzing income sources & optimizing your regime...</p>
        </div>
      </div>
    );
  }

  // ── Error State ──
  if (error || !questionsData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="text-center space-y-4 max-w-md px-6">
          <div className="w-16 h-16 rounded-full bg-[#ffdad6] mx-auto flex items-center justify-center">
            <span className="material-symbols-outlined text-[#991B1B] text-3xl">error</span>
          </div>
          <h2 className="text-xl font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Processing Error</h2>
          <p className="text-sm text-[#434652]">{error || "Could not load questions."}</p>
          <button onClick={() => router.push("/")} className="px-6 py-3 bg-[#003366] text-white rounded-lg font-semibold" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
            Start Over
          </button>
        </div>
      </div>
    );
  }

  const { questions, regime_recommended, regime_savings } = questionsData;
  const savings = Number(regime_savings || 0);
  const visibleQuestions = questions.filter(isVisible);
  const totalSteps = visibleQuestions.length;
  const currentQ = visibleQuestions[currentStep];
  const isLast = currentStep >= totalSteps - 1;

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col">
      {/* Progress bar — matches smart-questionnaire/code.html */}
      <div className="sticky top-16 z-30 bg-white border-b border-[#E2E8F0] px-6 py-3">
        <div className="max-w-[640px] mx-auto flex items-center justify-between">
          <div className="flex-1 flex gap-1.5 h-1">
            {visibleQuestions.map((_, i) => (
              <div key={i} className={`flex-1 rounded-full transition-all ${i <= currentStep ? "bg-[#F57C00]" : "bg-[#E2E8F0]"}`} />
            ))}
          </div>
          <span className="ml-4 text-[11px] font-bold text-[#F57C00] uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
            Step {currentStep + 1} of {totalSteps}
          </span>
        </div>
      </div>

      {/* Main Wizard */}
      <main className="flex-grow flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-[640px] space-y-6">

          {/* Regime Savings Badge */}
          {currentStep === 0 && (
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-[11px] font-bold uppercase tracking-wider animate-in fade-in ${savings > 0 ? "bg-green-50 text-[#166534] border-green-100" : "bg-[#eff4ff] text-[#003366] border-[#c3c6d4]"}`} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              <span className="material-symbols-outlined text-sm">{savings > 0 ? "trending_down" : "check_circle"}</span>
              {savings > 0 ? `Potential Tax Savings: ₹${savings.toLocaleString("en-IN")}` : "Optimal Regime Selected"}
            </div>
          )}

          {/* Question Card */}
          <div key={currentQ.id} className="bg-white border border-[#E2E8F0] rounded-xl p-8 shadow-sm animate-in slide-in-from-right-4 duration-300">
            {/* Question number */}
            <span className="text-[11px] font-bold text-[#F57C00] uppercase tracking-widest" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              Question {currentStep + 1} of {totalSteps}
            </span>

            {/* Headline */}
            <h1 className="text-xl font-semibold text-[#0b1c30] mt-3 mb-2 leading-snug" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              {currentQ.text}
            </h1>
            {currentQ.impact && (
              <p className="text-sm text-[#434652] mb-6">{currentQ.impact}</p>
            )}

            {/* Yes/No Toggle — matches design exactly */}
            <div className="grid grid-cols-2 gap-4 mt-6">
              {/* Yes */}
              <label className={`group relative cursor-pointer ${answers[currentQ.id] === "yes" ? "active" : ""}`}>
                <input type="radio" name={currentQ.id} className="sr-only peer"
                  checked={answers[currentQ.id] === "yes"} onChange={() => setAnswer(currentQ.id, "yes")} />
                <div className={`flex flex-col items-center justify-center p-6 border-2 rounded-xl transition-all
                  ${answers[currentQ.id] === "yes"
                    ? "border-[#003366] bg-[#eff4ff]"
                    : "border-[#E2E8F0] bg-white hover:border-[#003366]"}`}>
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 transition-colors
                    ${answers[currentQ.id] === "yes" ? "bg-[#0d47a1] text-white" : "bg-[#eff4ff] text-[#003178]"}`}>
                    <span className="material-symbols-outlined">home</span>
                  </div>
                  <span className="text-lg font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Yes</span>
                </div>
              </label>

              {/* No */}
              <label className={`group relative cursor-pointer ${answers[currentQ.id] === "no" ? "active" : ""}`}>
                <input type="radio" name={currentQ.id} className="sr-only peer"
                  checked={answers[currentQ.id] === "no"} onChange={() => setAnswer(currentQ.id, "no")} />
                <div className={`flex flex-col items-center justify-center p-6 border-2 rounded-xl transition-all
                  ${answers[currentQ.id] === "no"
                    ? "border-[#003366] bg-[#eff4ff]"
                    : "border-[#E2E8F0] bg-white hover:border-[#003366]"}`}>
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 transition-colors
                    ${answers[currentQ.id] === "no" ? "bg-[#0d47a1] text-white" : "bg-[#eff4ff] text-[#003178]"}`}>
                    <span className="material-symbols-outlined">close</span>
                  </div>
                  <span className="text-lg font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>No</span>
                </div>
              </label>
            </div>

            {/* Sub-questions (when Yes) */}
            {answers[currentQ.id] === "yes" && currentQ.sub_questions?.length && (
              <div className="mt-6 space-y-4 animate-in slide-in-from-top-2 duration-300">
                {currentQ.sub_questions.filter(isVisible).map((sq) => (
                  <div key={sq.id} className="p-4 bg-[#F8FAFC] rounded-lg border border-[#E2E8F0] space-y-2">
                    <label className="text-sm font-medium text-[#0b1c30]">{sq.text}</label>
                    {sq.impact && <p className="text-[10px] text-[#737783]">{sq.impact}</p>}
                    <input
                      type={sq.type === "number" ? "number" : "text"}
                      placeholder={sq.type === "number" ? "₹ Amount" : "Enter value"}
                      value={answers[sq.id] || ""}
                      onChange={(e) => setAnswer(sq.id, e.target.value)}
                      className="w-full px-4 py-2.5 bg-white border border-[#E2E8F0] rounded text-sm focus:border-[#003366] focus:ring-1 focus:ring-[#003366] outline-none transition-all"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex justify-between items-center px-2">
            <button onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
              disabled={currentStep === 0}
              className="flex items-center gap-1.5 px-5 py-2.5 text-[11px] font-bold text-[#003178] uppercase tracking-wider hover:bg-[#eff4ff] rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              <span className="material-symbols-outlined text-base">arrow_back</span> Back
            </button>

            {isLast ? (
              <button onClick={handleSubmit} disabled={submitting}
                className="bg-[#003366] text-white px-8 py-3 rounded-lg text-[11px] font-bold uppercase tracking-wider flex items-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-md disabled:opacity-50"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                {submitting ? "Computing..." : "Compute My Tax"}
                <span className="material-symbols-outlined text-base">arrow_forward</span>
              </button>
            ) : (
              <button onClick={() => setCurrentStep(currentStep + 1)}
                className="bg-[#003366] text-white px-8 py-3 rounded-lg text-[11px] font-bold uppercase tracking-wider flex items-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-md"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                Next Step
                <span className="material-symbols-outlined text-base">arrow_forward</span>
              </button>
            )}
          </div>

          {/* Expert Tip */}
          <div className="flex items-start gap-4 p-5 bg-white border border-dashed border-[#c3c6d4] rounded-xl">
            <div className="w-10 h-10 rounded-full bg-[#0d47a1] flex-shrink-0 flex items-center justify-center text-white text-sm font-bold">CA</div>
            <div className="space-y-1">
              <p className="text-xs italic text-[#434652]">
                {currentQ.id === "rent"
                  ? "\"If you live with parents but pay them rent via bank transfer, you can still claim this deduction! Make sure to have a valid rent agreement.\""
                  : "\"Answer honestly — there are no wrong answers. Saying 'No' to all is perfectly fine. We auto-detect everything from your PDFs.\""}
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Error toast */}
      {error && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-5 py-3 bg-[#ffdad6] border border-red-200 rounded-lg text-sm text-[#93000a] flex items-center gap-2 shadow-lg">
          <span className="material-symbols-outlined text-base">error</span>
          {error}
        </div>
      )}
    </div>
  );
}

export default function QuestionsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] text-sm text-[#434652]">Loading...</div>
    }>
      <QuestionsContent />
    </Suspense>
  );
}
