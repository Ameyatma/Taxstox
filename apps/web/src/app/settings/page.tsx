"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { fetchMe, type AuthUser } from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading, signOut } = useAuth();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Form state
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showCurrentPwd, setShowCurrentPwd] = useState(false);
  const [showNewPwd, setShowNewPwd] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/auth?redirect=/settings");
      return;
    }
    if (isAuthenticated) loadProfile();
  }, [isAuthenticated, authLoading]);

  async function loadProfile() {
    try {
      const u = await fetchMe();
      setUser(u);
      setName(u.name);
      setEmail(u.email);
    } catch {
      setError("Failed to load profile");
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveProfile() {
    setSaving(true); setMessage(""); setError("");
    try {
      const token = localStorage.getItem("taxstox_token");
      const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${base}/auth/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ name }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Update failed");
      }
      setMessage("Profile updated successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleChangePassword() {
    if (!currentPassword || !newPassword) {
      setError("Both fields are required to change password.");
      return;
    }
    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters.");
      return;
    }
    setSaving(true); setMessage(""); setError("");
    try {
      const token = localStorage.getItem("taxstox_token");
      const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${base}/auth/change-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Password change failed");
      }
      setMessage("Password changed successfully.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password change failed");
    } finally {
      setSaving(false);
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="w-16 h-16 rounded-full bg-[#eff4ff] mx-auto flex items-center justify-center">
          <span className="material-symbols-outlined text-[#003366] text-3xl animate-spin">sync</span>
        </div>
      </div>
    );
  }

  const inputClass = "w-full px-4 py-3 bg-white border border-[#E2E8F0] rounded-lg text-sm focus:border-[#003366] focus:ring-1 focus:ring-[#003366] outline-none transition-all";
  const labelClass = "text-[11px] font-bold text-[#434652] uppercase tracking-wider block mb-1";

  return (
    <div className="min-h-screen bg-[#F8FAFC] pb-16">
      {/* Header */}
      <div className="bg-white border-b border-[#E2E8F0]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-10 py-6">
          <h1 className="text-2xl font-bold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Account Settings</h1>
          <p className="text-sm text-[#434652] mt-1">Manage your profile and security preferences.</p>
        </div>
      </div>

      <div className="max-w-[720px] mx-auto px-6 md:px-10 py-8 space-y-8">
        {/* Profile Info */}
        <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 space-y-5">
          <h2 className="text-sm font-bold text-[#003366] uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Profile Information</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Full Name</label>
              <input value={name} onChange={e => setName(e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Email Address</label>
              <input value={email} disabled className={`${inputClass} bg-[#F8FAFC] text-[#737783] cursor-not-allowed`} />
              <p className="text-[10px] text-[#737783] mt-1">Email cannot be changed. Contact support.</p>
            </div>
            <div>
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>PAN</label>
              <input value={user?.pan || ""} disabled className={`${inputClass} bg-[#F8FAFC] text-[#737783] cursor-not-allowed font-mono uppercase`} />
            </div>
            <div>
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Account Created</label>
              <input value="" placeholder="—" disabled className={`${inputClass} bg-[#F8FAFC] text-[#737783] cursor-not-allowed`} />
            </div>
          </div>

          <button
            onClick={handleSaveProfile}
            disabled={saving}
            className="bg-[#003366] text-white px-6 py-3 rounded-lg text-sm font-bold hover:opacity-90 transition-all disabled:opacity-50"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>

        {/* Change Password */}
        <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 space-y-5">
          <h2 className="text-sm font-bold text-[#003366] uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Change Password</h2>

          <div className="space-y-4">
            <div>
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Current Password</label>
              <div className="relative">
                <input
                  type={showCurrentPwd ? "text" : "password"}
                  value={currentPassword}
                  onChange={e => setCurrentPassword(e.target.value)}
                  className={inputClass}
                  placeholder="Enter current password"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPwd(!showCurrentPwd)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[#737783] text-xl cursor-pointer"
                >
                  {showCurrentPwd ? "visibility" : "visibility_off"}
                </button>
              </div>
            </div>
            <div>
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>New Password</label>
              <div className="relative">
                <input
                  type={showNewPwd ? "text" : "password"}
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  className={inputClass}
                  placeholder="Min. 8 characters"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPwd(!showNewPwd)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[#737783] text-xl cursor-pointer"
                >
                  {showNewPwd ? "visibility" : "visibility_off"}
                </button>
              </div>
            </div>
          </div>

          <button
            onClick={handleChangePassword}
            disabled={saving}
            className="bg-[#F57C00] text-white px-6 py-3 rounded-lg text-sm font-bold hover:bg-[#E67600] transition-all disabled:opacity-50"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            {saving ? "Changing..." : "Change Password"}
          </button>
        </div>

        {/* Messages */}
        {message && (
          <div className="p-4 rounded-xl bg-green-50 border border-green-200 flex items-start gap-3 text-sm text-[#166534]">
            <span className="material-symbols-outlined shrink-0 mt-0.5">check_circle</span>
            {message}
          </div>
        )}
        {error && (
          <div className="p-4 rounded-xl bg-[#ffdad6] border border-red-200 flex items-start gap-3 text-sm text-[#93000a]">
            <span className="material-symbols-outlined shrink-0 mt-0.5">error</span>
            {error}
          </div>
        )}

        {/* Logout */}
        <div className="bg-white border border-[#ffdad6] rounded-xl p-6 text-center space-y-3">
          <p className="text-sm text-[#991B1B] font-semibold">Want to sign out?</p>
          <button
            onClick={() => { signOut(); router.push("/"); }}
            className="px-6 py-2.5 bg-[#991B1B] text-white rounded-lg text-sm font-bold hover:opacity-90 transition-all"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
