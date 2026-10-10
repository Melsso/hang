export async function getBlockedUsers() {
  const res = await fetch("/api/settings/blocks", {
    credentials: "include",
  });
  if (!res.ok) return null;
  return res.json();
}

export async function getReports() {
  const res = await fetch("/api/settings/reports", {
    credentials: "include",
  });
  if (!res.ok) return null;
  return res.json();
}

export async function unblockUser(userId: number) {
  const res = await fetch("/api/settings/unblock", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ blocked_user_id: userId }),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function deleteReport(reportId: number) {
  const res = await fetch("/api/settings/report-delete", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reported_user_id: reportId }),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function changePassword(oldPassword: string, newPassword: string) {
  const res = await fetch("/api/settings/change-password", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function deleteAccount() {
  const res = await fetch("/api/settings/delete-account", {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) return null;
  return res.json();
}
