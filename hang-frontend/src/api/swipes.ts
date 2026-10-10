import type { SwipeProfile } from "../components/swipes/SwipeCard";

export type SwipeFeed =
  { status: "ok"; profiles: SwipeProfile[] } | { status: "incomplete" } | { status: "error" };

export async function get_swipe_profiles(): Promise<SwipeFeed> {
  const res = await fetch("/api/swipes/home", {
    credentials: "include",
    cache: "no-store",
  });
  if (res.status === 403) return { status: "incomplete" };
  if (!res.ok) return { status: "error" };
  return { status: "ok", profiles: await res.json() };
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
      swipe_type: swipe_type.replace("-", "_"),
    }),
  });
  if (!res.ok) return null;
  return res.json();
}
