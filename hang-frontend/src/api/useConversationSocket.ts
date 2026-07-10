import { useEffect, useRef } from "react";

type IncomingEvent =
    | { type: "message"; message: any }
    | { type: "typing"; conversation_id: number; user_id: number; is_typing: boolean }
    | { type: "ping"; }
    | { type: "read"; conversation_id: number; user_id: number };

export function useConversationsSocket(onMessage: (event: IncomingEvent) => void) {
    const socketRef = useRef<WebSocket | null>(null);
    const onMessageRef = useRef(onMessage);

    useEffect(() => {
        onMessageRef.current = onMessage;
    }, [onMessage]);

    useEffect(() => {
        const socket = new WebSocket("ws://localhost:8000/api/ws/conversations");

        socketRef.current = socket;

        socket.onopen = () => {
            console.log("socket connected");
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessageRef.current(data);
            } catch (e) {
                console.error("bad socket message", e);
            }
        };

        socket.onclose = () => {
            console.log("socket disconnected");
        };

        socket.onerror = (err) => {
            console.error("socket error", err);
        };

        return () => {
            socket.close();
            socketRef.current = null;
        };
    }, []);

    const send = (payload: any) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify(payload));
        }
    };

    return { socketRef, send };
}