import { apiFetch } from "./client";

export type Notifications = { new_matches: number; unread_messages: number };

export async function get_notifications(): Promise<Notifications | null> {
  const res = await apiFetch("/api/conversations/notifications");
  if (!res.ok) return null;
  return res.json();
}

export async function get_user_conversations() {
  const res = await apiFetch("/api/conversations");
  if (!res.ok) return null;
  return res.json();
}

export async function get_conversation_messages(conv_id: number, cursor?: number | null) {
  const url = new URL(`/api/conversations/${conv_id}/messages`, window.location.origin);
  if (cursor) url.searchParams.set("before_message_id", String(cursor));
  const res = await apiFetch(url.pathname + url.search);
  if (!res.ok) return null;
  return res.json();
}

export async function delete_conversation(conversationId: number): Promise<boolean> {
  const res = await apiFetch(`/api/conversations/delete/${conversationId}`, { method: "POST" });
  return res.ok;
}
