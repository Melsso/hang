import { useEffect, useRef } from "react";

export type SocketMessage = {
  message_id: number;
  conversation_id: number;
  sender_id: number;
  content: string;
  created_at: string;
  is_read: boolean;
};

type IncomingEvent =
  | { type: "message"; message: SocketMessage }
  | { type: "typing"; conversation_id: number; user_id: number; is_typing: boolean }
  | { type: "ping" }
  | { type: "read"; conversation_id: number; user_id: number }
  | { type: "ready" }
  | { type: "error"; conversation_id: number; reason: string };

export function useConversationsSocket(onMessage: (event: IncomingEvent) => void) {
  const socketRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
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
        onMessageRef.current(data);
      } catch (e) {
        console.error("bad socket message", e);
      }
    };
    socket.onerror = (err) => console.error("socket error", err);

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, []);

  const send = (payload: Record<string, unknown>) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(payload));
    }
  };

  return { socketRef, send };
}
