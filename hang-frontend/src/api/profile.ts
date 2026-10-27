import { apiFetch } from "./client";

const JSON_HEADERS = { "Content-Type": "application/json" };

export async function get_user_profile_info(userId?: number) {
  const res = await apiFetch(userId ? `/api/users/profile/${userId}` : "/api/users/profile");
  if (!res.ok) return null;
  return res.json();
}

export async function update_profile_info(formData: unknown) {
  const res = await apiFetch("/api/users/profile", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(formData),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function upload_pictures(formData: FormData) {
  const res = await apiFetch("/api/users/profile/upload-image", { method: "POST", body: formData });
  if (!res.ok) return null;
  return res.json();
}

export async function report_user(userId: number, reason: string, message?: string | null) {
  const res = await apiFetch("/api/users/profile/report-create", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ reported_user_id: userId, reason, message: message || null }),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function block_user(userId: number) {
  const res = await apiFetch("/api/users/profile/block", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ blocked_user_id: userId }),
  });
  if (!res.ok) return null;
  return res.json();
}
