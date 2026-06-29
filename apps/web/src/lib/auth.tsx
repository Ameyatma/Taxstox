"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";

// ── Types ──────────────────────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string;
  pan: string;
  name: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  signIn: (user: AuthUser) => void;
  signUp: (user: AuthUser) => void;
  signOut: () => void;
}

// ── Context ────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

// ── localStorage keys ──────────────────────────────────────────────

const SESSION_KEY = "taxstox_session";
const USERS_KEY = "taxstox_users";

// ── Mock auth helpers (swap for real API later) ─────────────────────

export function getStoredUsers(): (AuthUser & { password: string })[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY) || "[]");
  } catch {
    return [];
  }
}

function storeUser(user: AuthUser & { password: string }) {
  const users = getStoredUsers();
  users.push(user);
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

export function findUserByPan(pan: string): (AuthUser & { password: string }) | undefined {
  return getStoredUsers().find((u) => u.pan.toUpperCase() === pan.toUpperCase());
}

function createSession(user: AuthUser) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

function getSession(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

function generateId(): string {
  return crypto.randomUUID?.() ?? Math.random().toString(36).slice(2);
}

// ── Provider ───────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // Hydrate from localStorage on mount
  useEffect(() => {
    const session = getSession();
    if (session) setUser(session);
    setLoading(false);
  }, []);

  const signIn = useCallback((authUser: AuthUser) => {
    setUser(authUser);
    createSession(authUser);
  }, []);

  const signUp = useCallback(
    (formData: { pan: string; dob: string; name: string; email: string; password: string }) => {
      // Check if PAN already registered
      if (findUserByPan(formData.pan)) {
        throw new Error("An account with this PAN already exists.");
      }

      const newUser: AuthUser & { password: string } = {
        id: generateId(),
        email: formData.email,
        pan: formData.pan.toUpperCase(),
        name: formData.name,
        password: formData.password, // Mock — plain text for now
      };

      storeUser(newUser);
      const { password: _, ...publicUser } = newUser;
      setUser(publicUser);
      createSession(publicUser);
    },
    [],
  );

  const signOut = useCallback(() => {
    setUser(null);
    clearSession();
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
