"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { uploadPDFs } from "@/lib/api";
import { setState } from "@/lib/store";

export default function UploadPage() {
  const router = useRouter();
  const form16Ref = useRef<HTMLInputElement>(null);
  const aisRef = useRef<HTMLInputElement>(null);

  const [pan, setPan] = useState("");
  const [dob, setDob] = useState("");
  const [form16File, setForm16File] = useState<File | null>(null);
  const [aisFile, setAisFile] = useState<File | null>(null);
  const [form16Password, setForm16Password] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);

  async function handleUpload() {
    setError("");

    if (!pan || pan.length !== 10) {
      setError("Please enter a valid 10-character PAN.");
      return;
    }
    if (!dob || dob.length !== 8) {
      setError("Please enter DOB in DDMMYYYY format.");
      return;
    }
    if (!form16File && !aisFile) {
      setError("Please upload at least one PDF (Form 16 or AIS).");
      return;
    }

    setLoading(true);
    setProgress(20);

    try {
      const result = await uploadPDFs(pan, dob, form16File, aisFile, form16Password || undefined);
      setProgress(80);

      if (result.status === "parsed") {
        setState({
          sessionId: result.session_id,
          pan,
          dob,
          step: "questions",
          uploadResult: result as unknown as Record<string, unknown>,
        });

        // Navigate to questions
        router.push(`/questions?session=${result.session_id}`);
        setProgress(100);
      } else if (result.password_required) {
        setError(
          `PDF password required. ${result.password_hint || "Please enter the Form 16 password."}`
        );
        setProgress(0);
      } else {
        setError("Failed to parse PDFs. Please check your files and try again.");
        setProgress(0);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed. Check your connection.");
      setProgress(0);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-3">
          File your ITR in <span className="text-emerald-600">2 minutes</span>
        </h1>
        <p className="text-gray-500 text-lg">
          2 documents. 5 yes/no questions. Download validated ITR JSON.
        </p>
      </div>

      {/* Progress */}
      {loading && (
        <div className="mb-6">
          <Progress value={progress} className="h-2" />
          <p className="text-xs text-gray-400 mt-2 text-center">
            {progress < 50
              ? "Parsing PDFs..."
              : progress < 90
                ? "Classifying capital gains..."
                : "Optimizing regime..."}
          </p>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Upload Your Documents</CardTitle>
          <CardDescription>
            Your data never leaves memory. No financial data is stored on disk.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* PAN + DOB */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="pan">PAN</Label>
              <Input
                id="pan"
                placeholder="CFFPM4503N"
                maxLength={10}
                value={pan}
                onChange={(e) => setPan(e.target.value.toUpperCase())}
                className="font-mono uppercase"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dob">Date of Birth</Label>
              <Input
                id="dob"
                placeholder="DDMMYYYY"
                maxLength={8}
                value={dob}
                onChange={(e) => setDob(e.target.value.replace(/\D/g, ""))}
                className="font-mono"
              />
              <p className="text-[10px] text-gray-400">AIS password = PAN(lower) + DOB</p>
            </div>
          </div>

          <Separator />

          {/* Form 16 Upload */}
          <div className="space-y-3">
            <Label className="text-base">Form 16 (PDF)</Label>
            <div className="flex items-center gap-3">
              <Input
                ref={form16Ref}
                type="file"
                accept=".pdf"
                onChange={(e) => setForm16File(e.target.files?.[0] || null)}
                className="flex-1 file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:bg-emerald-50 file:text-emerald-700 file:text-sm file:font-medium"
              />
              {form16File && (
                <span className="text-xs text-emerald-600 font-medium whitespace-nowrap">✓ Selected</span>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="f16pwd" className="text-xs text-gray-500">
                Form 16 Password (if encrypted)
              </Label>
              <Input
                id="f16pwd"
                type="text"
                placeholder="Usually your PAN — auto-tried if blank"
                value={form16Password}
                onChange={(e) => setForm16Password(e.target.value)}
                className="text-sm"
              />
              <p className="text-[10px] text-gray-400">
                We auto-try: PAN (UPPER), PAN (lower), PAN + FY
              </p>
            </div>
          </div>

          <Separator />

          {/* AIS Upload */}
          <div className="space-y-3">
            <Label className="text-base">Annual Information Statement — AIS (PDF)</Label>
            <div className="flex items-center gap-3">
              <Input
                ref={aisRef}
                type="file"
                accept=".pdf"
                onChange={(e) => setAisFile(e.target.files?.[0] || null)}
                className="flex-1 file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:bg-emerald-50 file:text-emerald-700 file:text-sm file:font-medium"
              />
              {aisFile && (
                <span className="text-xs text-emerald-600 font-medium whitespace-nowrap">✓ Selected</span>
              )}
            </div>
            <p className="text-[10px] text-gray-400">
              Password auto-computed from your PAN + DOB. No manual entry needed.
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Submit */}
          <Button
            onClick={handleUpload}
            disabled={loading}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white h-12 text-lg"
          >
            {loading ? "Processing..." : "Start Filing →"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
