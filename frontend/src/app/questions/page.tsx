"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
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

  useEffect(() => {
    if (!sessionId) {
      router.push("/");
      return;
    }
    loadQuestions();
  }, [sessionId]);

  async function loadQuestions() {
    try {
      const data = await processPDFs(sessionId!);
      setQuestionsData(data);
      setState({ questions: data.questions as unknown as never[], regimeRecommended: data.regime_recommended });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process PDFs");
    } finally {
      setLoading(false);
    }
  }

  function setAnswer(id: string, value: string) {
    setAnswers((prev) => ({ ...prev, [id]: value }));
  }

  function isVisible(question: Question): boolean {
    if (!question.depends_on) return true;
    const parentAnswer = answers[question.depends_on];
    return parentAnswer === question.depends_on_answer;
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
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-20 text-center">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-3/4 mx-auto" />
          <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto" />
          <div className="h-32 bg-gray-200 rounded mt-8" />
        </div>
        <p className="text-gray-500 mt-8">Classifying capital gains & optimizing your regime...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-20 text-center">
        <Card>
          <CardContent className="py-10">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={() => router.push("/")} variant="outline">
              Start Over
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!questionsData) return null;

  const { questions, regime_recommended, regime_savings } = questionsData;
  const savings = Number(regime_savings || 0);

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      {/* Regime Banner */}
      <Card className="mb-8 border-emerald-200 bg-emerald-50/50">
        <CardContent className="py-4 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-emerald-800">
              Recommended:{" "}
              <span className="uppercase">
                {regime_recommended === "new" ? "New Regime" : "Old Regime"}
              </span>
            </p>
            <p className="text-xs text-emerald-600 mt-1">
              {savings > 0
                ? `Saves you ₹${savings.toLocaleString("en-IN")} vs ${regime_recommended === "new" ? "Old" : "New"} Regime`
                : "Both regimes yield the same tax"}
            </p>
          </div>
          <Badge variant="outline" className="text-emerald-700 border-emerald-300">
            Auto-Optimized
          </Badge>
        </CardContent>
      </Card>

      {/* Questions */}
      <div className="space-y-6">
        {questions.map((q, i) => (
          <Card key={q.id}>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <span className="flex items-center justify-center w-7 h-7 rounded-full bg-emerald-100 text-emerald-700 text-sm font-bold">
                  {i + 1}
                </span>
                {q.text}
              </CardTitle>
              {q.impact && <CardDescription>{q.impact}</CardDescription>}
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Yes/No Toggle */}
              <div className="flex gap-3">
                <Button
                  variant={answers[q.id] === "yes" ? "default" : "outline"}
                  className={answers[q.id] === "yes" ? "bg-emerald-600 hover:bg-emerald-700" : ""}
                  onClick={() => setAnswer(q.id, "yes")}
                >
                  Yes
                </Button>
                <Button
                  variant={answers[q.id] === "no" ? "default" : "outline"}
                  className={answers[q.id] === "no" ? "bg-gray-600 hover:bg-gray-700" : ""}
                  onClick={() => setAnswer(q.id, "no")}
                >
                  No
                </Button>
              </div>

              {/* Sub-questions (conditional) */}
              {answers[q.id] === "yes" &&
                q.sub_questions?.map((sq) => (
                  <div key={sq.id} className="ml-9 p-4 bg-gray-50 rounded-lg space-y-2">
                    <Label htmlFor={sq.id}>{sq.text}</Label>
                    {sq.impact && <p className="text-[10px] text-gray-400">{sq.impact}</p>}
                    <Input
                      id={sq.id}
                      type={sq.type === "number" || sq.type === "text" ? (sq.type === "number" ? "number" : "text") : "text"}
                      placeholder={sq.type === "number" ? "₹ Amount" : sq.type === "text" ? "Enter text" : ""}
                      value={answers[sq.id] || ""}
                      onChange={(e) => setAnswer(sq.id, e.target.value)}
                    />
                  </div>
                ))}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Submit */}
      <div className="mt-8">
        <Button
          onClick={handleSubmit}
          disabled={submitting}
          className="w-full bg-emerald-600 hover:bg-emerald-700 text-white h-12 text-lg"
        >
          {submitting ? "Computing Tax..." : "Compute My Tax →"}
        </Button>
        <p className="text-center text-xs text-gray-400 mt-3">
          Answering &ldquo;No&rdquo; to all is perfectly fine. We auto-detect everything else.
        </p>
      </div>
    </div>
  );
}

export default function QuestionsPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-2xl mx-auto px-6 py-20 text-center text-gray-500">
          Loading...
        </div>
      }
    >
      <QuestionsContent />
    </Suspense>
  );
}
