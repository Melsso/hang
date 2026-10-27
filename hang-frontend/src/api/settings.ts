import { apiFetch } from "./client";

const JSON_HEADERS = { "Content-Type": "application/json" };

async function post(path: string, body?: unknown) {
  const res = await apiFetch(path, {
    method: "POST",
    headers: body === undefined ? undefined : JSON_HEADERS,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) return null;
  return res.json();
}

async function get(path: string) {
  const res = await apiFetch(path);
  if (!res.ok) return null;
  return res.json();
}

export const getBlockedUsers = () => get("/api/settings/blocks");
export const getReports = () => get("/api/settings/reports");
export const unblockUser = (userId: number) =>
  post("/api/settings/unblock", { blocked_user_id: userId });
export const deleteReport = (reportId: number) =>
  post("/api/settings/report-delete", { reported_user_id: reportId });
export const changePassword = (oldPassword: string, newPassword: string) =>
  post("/api/settings/change-password", { old_password: oldPassword, new_password: newPassword });
export const deleteAccount = () => post("/api/settings/delete-account");
