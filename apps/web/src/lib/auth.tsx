"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { loginUser, registerUser, fetchMe, type AuthUser } from "@/lib/api";

// ── Types ──────────────────────────────────────────────────────────

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, pan: string, name: string) => Promise<void>;
  signOut: () => void;
}

// ── Token helpers ───────────────────────────────────────────────────

const TOKEN_KEY = "taxstox_token";

function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// ── Context ────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount: try to restore session from stored token
  useEffect(() => {
    const token = getToken();
    if (token) {
      fetchMe()
        .then((u) => setUser(u))
        .catch(() => clearToken())
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const result = await loginUser(email, password);
    saveToken(result.access_token);
    setUser(result.user);
  }, []);

  const signUp = useCallback(async (email: string, password: string, pan: string, name: string) => {
    const result = await registerUser(email, password, pan, name);
    saveToken(result.access_token);
    setUser(result.user);
  }, []);

  const signOut = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ───────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth() must be used within <AuthProvider>");
  return ctx;
}
