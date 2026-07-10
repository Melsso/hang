export async function get_user_conversations() {
    const res = await fetch("/api/conversations", {
        credentials: "include",
    });
    if (!res.ok) return null;
    return res.json();
}

export async function get_conversation_messages(conv_id: number, cursor?: number | null) {
    const url = new URL(`/api/conversations/${conv_id}/messages`, window.location.origin);
    if (cursor) {
        url.searchParams.set("before_message_id", String(cursor));
    }
    const res = await fetch(url.toString(), {
        credentials: "include",
    });
    if (!res.ok) return null;
    return res.json();
}