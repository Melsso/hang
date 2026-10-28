const PUBLIC_PATHS = new Set(["/", "/login", "/register"]);
const EXEMPT_API = [
  "/api/auth/login",
  "/api/auth/register",
  "/api/auth/session",
  "/api/auth/logout",
];

let redirect: (url: string) => void = (url) => window.location.assign(url);
let redirecting = false;

export function setRedirect(fn: (url: string) => void) {
  redirect = fn;
}

export function resetUnauthorizedGuard() {
  redirecting = false;
}

export function handleUnauthorized() {
  if (redirecting || PUBLIC_PATHS.has(window.location.pathname)) return;
  redirecting = true;
  redirect("/login?expired=1");
}

export async function apiFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const res = await fetch(input, { credentials: "include", ...init });
  if (res.status === 401) {
    const path = new URL(input, window.location.origin).pathname;
    if (!EXEMPT_API.includes(path)) handleUnauthorized();
  }
  return res;
}
