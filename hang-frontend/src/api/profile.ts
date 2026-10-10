export async function get_user_profile_info(userId?: number) {
    const url = userId ? `/api/users/profile/${userId}` : `/api/users/profile`;
    const res = await fetch(url, {
        credentials: "include",
    });
    if (!res.ok) return null;
    return res.json();
}

export async function update_profile_info(formData: unknown) {
    const res = await fetch("/api/users/profile", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
    });
    if (!res.ok) return null;
    return res.json();
}

export async function upload_pictures(formData: FormData) {
    const res = await fetch("/api/users/profile/upload-image", {
        method: "POST",
        credentials: "include",
        body: formData,
    });
    if (!res.ok) return null;
    return res.json();
}

export async function report_user(userId: number, reason: string, message?: string | null) {
    const res = await fetch("/api/users/profile/report-create", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            reported_user_id: userId,
            reason: reason,
            message: message || null,
        }),
    });
    if (!res.ok) return null;
    return res.json();
}

export async function block_user(userId: number) {
    const res = await fetch("/api/users/profile/block", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({blocked_user_id: userId}),     
    });
    if (!res.ok) return null;
    return res.json();
}
