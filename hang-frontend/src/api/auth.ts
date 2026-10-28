import { apiFetch } from "./client";

export async function getSession() {
  const res = await apiFetch("/api/auth/session");
  if (!res.ok) return null;
  return res.json();
}

export async function login(email: string, password: string) {
  const res = await apiFetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function logout() {
  const res = await apiFetch("/api/auth/logout", { method: "POST" });
  if (!res.ok) throw new Error("Logout failed");
  return res.json();
}

export async function register(data: Record<string, unknown>) {
  const res = await apiFetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Registration failed");
  return res.json();
}
