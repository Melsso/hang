export async function getSession() {
    const res = await fetch("/api/auth/session", {
        credentials: "include",
    });
    if (!res.ok) return null;
    return res.json();
}

export async function login(email: string, password: string) {
    const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ email, password }),
    });
    if (!res.ok) return null;
    return res.json();
}

export async function logout() {
    const res = await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
    });
    if (!res.ok) throw new Error("Logout failed");
    return res.json();
}

export async function register(data: Record<string, unknown>) {
    const res = await fetch(
        "/api/auth/register",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        }
    );
    if (!res.ok) throw new Error("Registration failed");
    return res.json();
}
