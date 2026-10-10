import { useNavigate } from "react-router-dom";
import { Trash2 } from "lucide-react";
import defaultUserImage from "../../assets/default_user.png";

const DEFAULT_IMAGE_URL = defaultUserImage;

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
  onDelete?: (conversation: Conversation) => void;
};

export default function ConversationCard({ conversations, onSelect, onDelete }: Props) {
  const conversationList = conversations ?? [];
  return (
    <div className="w-2/5 h-full flex flex-col p-3 bg-[#181818] rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.45)] overflow-y-auto gap-2">
      {conversationList.length === 0 ? (
        <div className="text-center text-white/40 text-sm py-10">No conversations yet</div>
      ) : (
        conversationList.map((conversation) => (
          <ConversationRow
            key={conversation.conversation_id}
            conversation={conversation}
            onClick={() => onSelect?.(conversation)}
            onDelete={() => onDelete?.(conversation)}
          />
        ))
      )}
    </div>
  );
}

function ConversationRow({
  conversation,
  onClick,
  onDelete,
}: {
  conversation: Conversation;
  onClick?: () => void;
  onDelete?: () => void;
}) {
  const navigate = useNavigate();

  return (
    <div
      onClick={onClick}
      className="group flex items-center gap-3 p-3 rounded-xl bg-[#222] hover:bg-[#2a2a2a] active:scale-[0.99] transition cursor-pointer"
    >
      <div className="relative shrink-0">
        <img
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/profile/${conversation.other_user_id}`);
          }}
          src={conversation.other_user_img_url ?? DEFAULT_IMAGE_URL}
          alt={conversation.other_user_name}
          className="w-10 h-10 rounded-full object-cover border border-white/10 cursor-pointer"
        />

        {conversation.unread_count > 0 && (
          <span className="absolute -top-1 -right-1 bg-[#e50914] text-white text-[10px] leading-none px-[5px] py-[3px] rounded-full min-w-[18px] text-center border-2 border-[#222]">
            {conversation.unread_count}
          </span>
        )}
      </div>

      <div className="flex flex-col flex-1 min-w-0">
        <span className="text-white text-sm font-medium truncate">
          {conversation.other_user_name}
        </span>

        <span className="text-xs text-white/50 truncate">
          {conversation.last_message || "No messages yet"}
        </span>
      </div>

      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onDelete?.();
        }}
        aria-label={`Delete conversation with ${conversation.other_user_name}`}
        className="shrink-0 p-2 rounded-full text-white/30 hover:text-white hover:bg-white/10 transition"
      >
        <Trash2 size={16} />
      </button>
    </div>
  );
}
