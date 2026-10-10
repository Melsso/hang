import Button from "../global/Button";
import { useEffect, useRef, useState } from "react";

type MessagePreview = {
    message_id: number;
    sender_id: number;
    content: string;
    created_at: string;
    is_read: boolean;
};

export type MessageListResponse = {
    conversation_id: number;
    current_user_id: number;
    typing?: boolean;
    messages: MessagePreview[];
    next_cursor: number | null;
    has_more: boolean;
};

type Props = {
    data: MessageListResponse | null;
    onSend?: (text: string) => void;
    onTyping?: (text: string) => void;
    onLoadMore?: (cursor: number) => Promise<void>;
};

function MessageItem({
    message,
    isMine,
    showStatus,
}: {
    message: MessagePreview;
    isMine: boolean;
    showStatus: boolean;
}) {
    return (
        <div
            className={`flex flex-col gap-1 ${
                isMine ? "items-end" : "items-start"
            }`}
        >
            <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl text-white ${
                    isMine ? "bg-[#e50914]" : "bg-[#222]"
                }`}
            >
                {message.content}
            </div>

            {showStatus && (
                <div className="text-xs text-white/40">
                    {message.is_read ? "Read" : "Sent"}
                </div>
            )}
        </div>
    );
}

function MessageInput({onSend, onTyping}: {
    onSend?: (text: string) => void;
    onTyping?: (text: string) => void;
}) {
    const [text, setText] = useState("");
    return (
        <div className="flex gap-3 p-4 bg-[#141414] border-t border-white/5 rounded-b-2xl">
            <input
                value={text}
                onChange={(e) => {
                    setText(e.target.value);
                    onTyping?.(e.target.value);
                }}
                onKeyDown={(e) => {
                    if (e.key === "Enter") {
                        e.preventDefault();
                        if (!text.trim()) return;

                        onSend?.(text);
                        setText("");
                    }
                }}
                type="text"
                placeholder="Type a message..."
                className="flex-1 px-4 py-3 rounded-xl bg-[#222] text-white placeholder-white/40 border border-transparent focus:border-[#e50914] focus:bg-[#262626] outline-none transition"
            />

            <Button
                className="px-6 rounded-xl font-medium bg-[#e50914] text-white hover:bg-[#f6121d] active:scale-[0.98] transition"
                onClick={() => {
                    if (!text.trim()) return;
                    onSend?.(text);
                    setText("");
                }}
            >
                Send
            </Button>
        </div>
    );
}

export default function ChatCard({
    data,
    onSend,
    onTyping,
    onLoadMore,
}: Props) {
    const messages = data?.messages ?? [];
    const currentUserId = data?.current_user_id;
    const lastMessageId = messages[messages.length - 1]?.message_id;
    const containerRef = useRef<HTMLDivElement | null>(null);
    const [loadingMore, setLoadingMore] = useState(false);

    const handleScroll = async () => {
        const el = containerRef.current;
        if (!el || !data) return;

        if (el.scrollTop < 80) {
            if (!data.has_more || loadingMore) return;
            setLoadingMore(true);
            await onLoadMore?.(data.next_cursor!);
            setLoadingMore(false);
        }
    };

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        
        el.addEventListener("scroll", handleScroll);
        return () => el.removeEventListener("scroll", handleScroll);
    }, [data, loadingMore]);

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;

        el.scrollTop = el.scrollHeight;
    }, [data?.conversation_id]);

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        const messages = data?.messages;
        if (!messages || messages.length === 0) return;
        const lastMessage = messages[messages.length - 1];
        const isMine = lastMessage.sender_id === data.current_user_id;
        const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;

        if (isMine || isNearBottom) {
            requestAnimationFrame(() => {
                el.scrollTop = el.scrollHeight;
            });
        }
    }, [data?.messages?.length]);

    return (
        <div className="flex flex-col h-full w-[700px] bg-[#181818] rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.45)]">
            <div
                ref={containerRef}
                className="flex-1 overflow-y-auto p-6 flex flex-col gap-4"
            >
                {!data ? (
                    <div className="text-center text-white/40 text-sm">
                        Select a conversation
                    </div>
                ) : messages.length === 0 ? (
                    <div className="text-center text-white/40 text-sm">
                        No messages yet
                    </div>
                ) : (
                    messages.map((message) => (
                        <MessageItem
                            key={message.message_id}
                            message={message}
                            isMine={message.sender_id === currentUserId}
                            showStatus={message.message_id === lastMessageId}
                        />
                    ))
                )}

                {loadingMore && (
                    <div className="text-center text-white/30 text-xs">
                        Loading more...
                    </div>
                )}
            </div>
 
            {data?.typing && (
                <div className="text-sm text-white/50 px-6 pb-2">
                    typing...
                </div>
            )}
            <MessageInput onSend={onSend} onTyping={onTyping} />
        </div>
    );
}