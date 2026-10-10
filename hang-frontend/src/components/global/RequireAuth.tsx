import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { getSession } from "../../api/auth";

type AuthState = "loading" | "authed" | "anon";

export default function RequireAuth() {
  const [state, setState] = useState<AuthState>("loading");

  useEffect(() => {
    let cancelled = false;
    getSession().then((session) => {
      if (!cancelled) setState(session?.authenticated ? "authed" : "anon");
    });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state === "loading") return <div>Loading...</div>;
  if (state === "anon") return <Navigate to="/login" replace />;
  return <Outlet />;
}
