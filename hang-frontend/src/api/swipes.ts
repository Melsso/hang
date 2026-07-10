export async function get_swipe_profiles() {
    const res = await fetch("/api/swipes/home", {
        credentials: "include",
        cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
}

export async function swipe_action(to_user_id: number, swipe_type: string) {
    const res = await fetch("/api/swipes/swipe-action", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            to_user_id,
            swipe_type,
        }),
    });
    if (!res.ok) return null;
    return res.json();
}