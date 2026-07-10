import { useNavigate } from "react-router-dom";

export type Conversation = {
    conversation_id: number;
    other_user_id: number;
    other_user_name: string;
    other_user_img_url: string | null;
    last_message: string | null; 
    last_message_at: string | null;
    unread_count: number;
    updated_at: string;
};

type Props = {
    conversations?: Conversation[] | null;
    onSelect?: (conversation: Conversation) => void;
};

export default function ConversationCard({
    conversations,
    onSelect,
}: Props) {
    const conversationList = conversations ?? [];
    return (
        <div className="w-2/5 h-full flex flex-col p-3 bg-[#181818] rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.45)] overflow-y-auto gap-2">
            {conversationList.length === 0 ? (
                <div className="text-center text-white/40 text-sm py-10">
                    No conversations yet
                </div>
            ) : (
                conversationList.map((conversation) => (
                    <ConversationRow
                        key={conversation.conversation_id}
                        conversation={conversation}
                        onClick={() => onSelect?.(conversation)}
                    />
                ))
            )}
        </div>
    );
}

function ConversationRow({
    conversation,
    onClick,
}: {
    conversation: any;
    onClick?: () => void;
}) {
    const navigate = useNavigate();

    return (
        <div
            onClick={onClick}
            className="flex items-center gap-3 p-3 rounded-xl bg-[#222] hover:bg-[#2a2a2a] active:scale-[0.99] transition cursor-pointer"
        >
            <img
                onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/profile/${conversation.other_user_id}`);
                }}
                src={conversation.other_user_img_url}
                alt={conversation.other_user_name}
                className="w-10 h-10 rounded-full object-cover border border-white/10 cursor-pointer"
            />

            <div className="flex flex-col flex-1 min-w-0">
                <div className="flex items-center justify-between">
                    <span className="text-white text-sm font-medium truncate">
                        {conversation.other_user_name}
                    </span>

                    {conversation.unread_count > 0 && (
                        <span className="bg-[#e50914] text-white text-[11px] px-2 py-[2px] rounded-full min-w-[20px] text-center">
                            {conversation.unread_count}
                        </span>
                    )}
                </div>

                <span className="text-xs text-white/50 truncate">
                    {conversation.last_message || "No messages yet"}
                </span>
            </div>
        </div>
    );
}