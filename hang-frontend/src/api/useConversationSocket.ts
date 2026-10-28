import { useEffect, useRef, useState } from "react";
import { getSession } from "./auth";
import { handleUnauthorized } from "./client";

const BASE_DELAY_MS = 1000;
const MAX_DELAY_MS = 30000;

export type SocketMessage = {
  message_id: number;
  conversation_id: number;
  sender_id: number;
  content: string;
  created_at: string;
  is_read: boolean;
};

type IncomingEvent =
  | { type: "match"; conversation_id: number; user_id: number; name: string }
  | { type: "message"; message: SocketMessage }
  | { type: "typing"; conversation_id: number; user_id: number; is_typing: boolean }
  | { type: "ping" }
  | { type: "read"; conversation_id: number; user_id: number }
  | { type: "ready" }
  | { type: "error"; conversation_id: number; reason: string };

export function useConversationsSocket(
  onMessage: (event: IncomingEvent) => void,
  onReconnect?: () => void
) {
  const socketRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  const onReconnectRef = useRef(onReconnect);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    onMessageRef.current = onMessage;
    onReconnectRef.current = onReconnect;
  }, [onMessage, onReconnect]);

  useEffect(() => {
    let disposed = false;
    let attempt = 0;
    let everReady = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const scheduleReconnect = () => {
      const cap = Math.min(MAX_DELAY_MS, BASE_DELAY_MS * 2 ** attempt);
      const delay = cap * (0.5 + Math.random() * 0.5); // jitter: 50-100% of the cap
      attempt += 1;
      timer = setTimeout(connect, delay);
    };

    const onClosed = async () => {
      let authenticated = true;
      try {
        const session = await getSession();
        authenticated = !!session?.authenticated;
      } catch {
        // server unreachable (restart, network): keep retrying
      }
      if (disposed) return;
      if (!authenticated) {
        handleUnauthorized();
        return;
      }
      scheduleReconnect();
    };

    function connect() {
      if (disposed) return;
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      const socket = new WebSocket(`${proto}://${window.location.host}/api/ws/conversations`);
      socketRef.current = socket;

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "ping") {
            socket.send(JSON.stringify({ type: "pong" }));
            return;
          }
          if (data.type === "ready") {
            attempt = 0;
            setConnected(true);
            if (everReady) onReconnectRef.current?.();
            everReady = true;
          }
          onMessageRef.current(data);
        } catch (e) {
          console.error("bad socket message", e);
        }
      };
      socket.onerror = (err) => console.error("socket error", err);
      socket.onclose = () => {
        if (socketRef.current === socket) socketRef.current = null;
        if (disposed) return;
        setConnected(false);
        void onClosed();
      };
    }

    connect();

    return () => {
      disposed = true;
      if (timer) clearTimeout(timer);
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, []);

  const send = (payload: Record<string, unknown>) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(payload));
      return true;
    }
    return false;
  };

  return { socketRef, send, connected };
}
