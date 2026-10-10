export default function SettingsRow({
  title,
  description,
  danger = false,
  onClick,
}: {
  title: string;
  description: string;
  danger?: boolean;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={`
                flex items-center justify-between
                p-5 rounded-xl cursor-pointer transition
                border border-transparent
                ${
                  danger
                    ? "bg-[#241313] hover:bg-[#311717] hover:border-[#e50914]/40"
                    : "bg-[#222] hover:bg-[#2a2a2a] hover:border-white/10"
                }
            `}
    >
      <div className="flex flex-col">
        <span className={`font-medium ${danger ? "text-[#ff5c5c]" : "text-white"}`}>{title}</span>

        <span className="text-sm text-white/50">{description}</span>
      </div>

      <span className="text-white/30 text-xl">→</span>
    </div>
  );
}
