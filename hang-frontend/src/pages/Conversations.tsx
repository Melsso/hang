import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

import { get_user_conversations, get_conversation_messages, delete_conversation } from "../api/conversations";
import { useConversationsSocket } from "../api/useConversationSocket";
import { useToast } from "../components/global/ToastProvider";

import type { Conversation } from "../components/conversations/ConversationCard";
import type { MessageListResponse } from "../components/conversations/ChatCard";

import ActionBar from "../components/global/ActionBar";
import ConversationCard from "../components/conversations/ConversationCard";
import ChatCard from "../components/conversations/ChatCard";

export default function Conversations() {
    const [conversations, setConversations] = useState<Conversation[] | null>(null);
    const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
    const [messageData, setMessageData] = useState<MessageListResponse | null>(null);
    const typingRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const activeConversationRef = useRef<number | null>(null);
    const { showToast } = useToast();
    const navigate = useNavigate();

    const sendRef = useRef<(payload: Record<string, unknown>) => void>(() => {});   
    const { send } = useConversationsSocket((event) => {
        if (event.type === "message") {
            const { message } = event;
            const conversation_id = message.conversation_id;
            const activeId = activeConversationRef.current;
            const isActive = activeId === conversation_id;
            const isSender = message.sender_id === messageData?.current_user_id;
            
            setConversations((prev) =>
                prev?.map((c) => {
                    if (c.conversation_id !== conversation_id) return c;

                    return {
                        ...c,
                        last_message: message.content,
                        unread_count: isActive ? 0 : c.unread_count + 1,
                    };
                }) ?? null
            );

            setMessageData((prev) => {
                if (!prev) return prev;
                if (prev.conversation_id !== conversation_id) return prev;

                return {
                    ...prev,
                    messages: [...prev.messages, message],
                };
            });
            if (isActive && !isSender) {
                sendRef.current({ type: "read", conversation_id });
            }
        }

        if (event.type === "typing") {
            const { conversation_id, is_typing, user_id } = event;

            if (
                !selectedConversation ||
                selectedConversation.conversation_id !== conversation_id
            ) return;

            if (user_id === messageData?.current_user_id) return;

            setMessageData((prev) => {
                if (!prev) return prev;
                if (prev.conversation_id !== conversation_id) return prev;

                return {
                    ...prev,
                    typing: is_typing,
                };
            });
        }

        if (event.type === "read") {
            const { conversation_id } = event;

            setMessageData((prev) => {
                if (!prev) return prev;
                if (prev.conversation_id !== conversation_id) return prev;

                const updated = [...prev.messages];
                if (updated.length === 0) return prev;

                const lastIndex = updated.length - 1;

                updated[lastIndex] = {
                    ...updated[lastIndex],
                    is_read: true,
                };

                return {
                    ...prev,
                    messages: updated,
                };
            });
        }
    });

    useEffect(() => {
        async function load() {
            const data = await get_user_conversations();
            if (!data) {
                showToast("Could not load conversations, try again later.");
                navigate("/swipes");
                return;
            }
            setConversations(data);
        }
        load();
    }, [navigate, showToast]);

    const handleSelectConversation = async (conv: Conversation) => {
        activeConversationRef.current = conv.conversation_id;
        const msgs = await get_conversation_messages(conv.conversation_id);
        if (!msgs) {
            showToast("Could not fetch messages, try again later.");
            return ;
        }
        setSelectedConversation(conv);
        setMessageData(msgs);
        setConversations((prev) =>
            prev?.map((c) =>
                c.conversation_id === conv.conversation_id
                    ? { ...c, unread_count: 0 }
                    : c
            ) ?? null
        );
        send({
            type: "read",
            conversation_id: conv.conversation_id,
        });
    };

    const handleDeleteConversation = async (conv: Conversation) => {
        const previousConversations = conversations;
        const wasActive = activeConversationRef.current === conv.conversation_id;

        setConversations((prev) =>
            prev?.filter((c) => c.conversation_id !== conv.conversation_id) ?? null
        );

        if (wasActive) {
            activeConversationRef.current = null;
            setSelectedConversation(null);
            setMessageData(null);
        }

        try {
            const ok = await delete_conversation(conv.conversation_id);
            if (!ok) {
                showToast("Could not delete conversation, try again later.", "error");
                setConversations(previousConversations);
            }
            else{
                showToast("Conversation deleted", "success")
            }
        } catch {
            showToast("Could not delete conversation, try again later.", "error");
            setConversations(previousConversations);
        }
    };

    const handleSend = (text: string) => {
        if (!selectedConversation) return;
        send({
            type: "message",
            conversation_id: selectedConversation.conversation_id,
            content: text,
        });
    };

    const handleTyping = () => {
        if (!selectedConversation) return;
        send({
            type: "typing",
            conversation_id: selectedConversation.conversation_id,
            is_typing: true,
        });

        if (typingRef.current) clearTimeout(typingRef.current);
        typingRef.current = setTimeout(() => {
            send({
                type: "typing",
                conversation_id: selectedConversation.conversation_id,
                is_typing: false,
            });
        }, 800);
    };

    const handleLoadMore = async (cursor: number) => {
        if (!selectedConversation) return;
        const nextPage = await get_conversation_messages(selectedConversation.conversation_id, cursor);
        if (!nextPage) return;
        setMessageData((prev) => {
            if (!prev) return nextPage;
            const merged = [...nextPage.messages, ...prev.messages];
            const deduped = Array.from(
                new Map(merged.map((m) => [m.message_id, m])).values()
            );
            return {...nextPage, messages: deduped};
        });
    };

    if (conversations === null) {
        return <div>Loading...</div>;
    }

    return (
        <div className="w-3/4 h-[70vh] flex flex-col items-center justify-center gap-10">
            <ActionBar />

            <div className="flex w-full h-full gap-5">
                <ConversationCard
                    conversations={conversations}
                    onSelect={
                        handleSelectConversation
                    }
                    onDelete={handleDeleteConversation}
                />

                <ChatCard
                    data={messageData}
                    onSend={handleSend}
                    onTyping={handleTyping}
                    onLoadMore={handleLoadMore}
                />
            </div>
        </div>
    );
}