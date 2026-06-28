"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { exportITR, type TaxSummaryData, type ExportData } from "@/lib/api";
import { getState } from "@/lib/store";

function SummaryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session") || getState().sessionId;

  const [summary, setSummary] = useState<TaxSummaryData | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportData, setExportData] = useState<ExportData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const cached = getState().taxSummary;
    if (cached) {
      setSummary(cached as unknown as TaxSummaryData);
    }
  }, []);

  async function handleExport() {
    setExporting(true);
    setError("");
    try {
      const data = await exportITR(sessionId!);
      setExportData(data);

      // Auto-download
      const blob = new Blob([JSON.stringify(data.json_data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = data.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExporting(false);
    }
  }

  if (!summary) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-20 text-center">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-3/4 mx-auto" />
          <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto" />
          <div className="h-64 bg-gray-200 rounded mt-8" />
        </div>
        <p className="text-gray-500 mt-8">Computing your optimized tax...</p>
      </div>
    );
  }

  const balancePayable = Number(summary.balance_payable || 0);
  const regimeSavings = Number(summary.regime_savings || 0);

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-bold text-center mb-2">Your Tax Summary</h1>
      <p className="text-gray-500 text-center mb-8">FY 2025-26 (AY 2026-27)</p>

      {/* Regime Badge */}
      <div className="flex justify-center mb-8">
        <Badge className="text-base px-4 py-2 bg-emerald-100 text-emerald-800 border-emerald-300">
          {summary.regime === "new" ? "NEW REGIME" : "OLD REGIME"} —{" "}
          {regimeSavings > 0
            ? `Saves ₹${regimeSavings.toLocaleString("en-IN")}`
            : "Optimal choice"}
        </Badge>
      </div>

      {/* Income */}
      <Card className="mb-4">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">📊 Income</CardTitle>
        </CardHeader>
        <CardContent>
          {Object.entries(summary.income).map(([label, amount]) => (
            <div key={label} className="flex justify-between py-2 text-sm">
              <span className="text-gray-600">{label}</span>
              <span className="font-mono font-medium">₹{Number(amount).toLocaleString("en-IN")}</span>
            </div>
          ))}
          <Separator className="my-2" />
          <div className="flex justify-between py-2 text-sm font-semibold">
            <span>Gross Total</span>
            <span className="font-mono">
              ₹{Object.values(summary.income)
                .reduce((sum, v) => sum + Number(v), 0)
                .toLocaleString("en-IN")}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Deductions */}
      <Card className="mb-4">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">📉 Deductions</CardTitle>
        </CardHeader>
        <CardContent>
          {Object.entries(summary.deductions).length > 0 ? (
            Object.entries(summary.deductions).map(([label, amount]) => (
              <div key={label} className="flex justify-between py-2 text-sm">
                <span className="text-gray-600">{label}</span>
                <span className="font-mono">₹{Number(amount).toLocaleString("en-IN")}</span>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-400">No deductions applicable (New Regime)</p>
          )}
          <Separator className="my-2" />
          <div className="flex justify-between py-2 font-semibold text-base">
            <span>💰 Taxable Income</span>
            <span className="font-mono">₹{Number(summary.taxable_income).toLocaleString("en-IN")}</span>
          </div>
        </CardContent>
      </Card>

      {/* Tax Computation */}
      <Card className="mb-4">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">🧮 Tax Computation</CardTitle>
        </CardHeader>
        <CardContent>
          {Object.entries(summary.tax_breakdown).map(([label, amount]) => (
            <div key={label} className="flex justify-between py-2 text-sm">
              <span className="text-gray-600">{label}</span>
              <span className="font-mono">₹{Number(amount).toLocaleString("en-IN")}</span>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Payments */}
      <Card className="mb-8">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">💳 Payments</CardTitle>
        </CardHeader>
        <CardContent>
          {Object.entries(summary.payments).map(([label, amount]) => (
            <div key={label} className="flex justify-between py-2 text-sm">
              <span className="text-gray-600">{label}</span>
              <span className="font-mono">₹{Number(amount).toLocaleString("en-IN")}</span>
            </div>
          ))}
          <Separator className="my-2" />
          <div className="flex justify-between py-3 text-lg font-bold">
            <span className={balancePayable > 0 ? "text-red-600" : "text-emerald-600"}>
              {balancePayable > 0 ? "Balance Payable" : "Refund Due"}
            </span>
            <span
              className={`font-mono ${balancePayable > 0 ? "text-red-600" : "text-emerald-600"}`}
            >
              ₹{Math.abs(balancePayable).toLocaleString("en-IN")}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Export */}
      <div className="space-y-3">
        {error && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
            {error}
          </div>
        )}

        {exportData?.validation_warnings && exportData.validation_warnings.length > 0 && (
          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-sm text-amber-800">
            <p className="font-medium mb-1">Validation Warnings:</p>
            <ul className="list-disc list-inside space-y-1">
              {exportData.validation_warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        <Button
          onClick={handleExport}
          disabled={exporting}
          className="w-full bg-emerald-600 hover:bg-emerald-700 text-white h-14 text-lg"
        >
          {exporting ? "Building JSON..." : "📥 Download ITR JSON"}
        </Button>

        {exportData && exportData.validation_passed && (
          <p className="text-center text-sm text-emerald-600 font-medium">
            ✅ Validation passed — ready to upload to ITR Portal
          </p>
        )}

        <Button
          onClick={() => router.push("/")}
          variant="outline"
          className="w-full mt-4"
        >
          Start New Filing
        </Button>
      </div>

      {/* Post-Export Instructions (abbreviated) */}
      <Card className="mt-8 border-blue-200 bg-blue-50/30">
        <CardHeader>
          <CardTitle className="text-base">📋 What To Do Next</CardTitle>
          <CardDescription>
            After downloading your JSON, follow these steps on the ITR Portal:
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
            <li>Go to <strong>incometax.gov.in</strong> → Login</li>
            <li>e-File → Income Tax Return → File ITR</li>
            <li>Select <strong>Assessment Year 2026-27</strong></li>
            <li>Select <strong>ITR-2</strong> → Prepare &amp; Submit Online</li>
            <li>Click <strong>&ldquo;Import JSON&rdquo;</strong> → Select your downloaded file</li>
            <li>Verify the pre-filled data → Submit</li>
            <li>Pay any balance tax via e-Pay → e-Verify with Aadhaar OTP</li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
}

export default function SummaryPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-2xl mx-auto px-6 py-20 text-center text-gray-500">
          Loading...
        </div>
      }
    >
      <SummaryContent />
    </Suspense>
  );
}
