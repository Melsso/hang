import Button from "../global/Button";

export default function SwipeAction({ onSwipe }: { onSwipe: (swipeType: string) => void }) {
  return (
    <div className="flex items-center justify-center gap-6 w-3/4 py-4 rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.45)]">
      <Button
        className="px-5 py-3 rounded-xl bg-[#222] text-white font-medium hover:bg-[#2a2a2a] active:scale-95 transition"
        onClick={() => onSwipe("pass")}
      >
        Pass
      </Button>

      <Button
        className="px-5 py-3 rounded-xl bg-[#e50914] text-white font-medium hover:bg-[#f6121d] active:scale-95 transition"
        onClick={() => onSwipe("super-like")}
      >
        Super Like
      </Button>

      <Button
        className="px-5 py-3 rounded-xl bg-[#222] text-white font-medium hover:bg-[#2a2a2a] active:scale-95 transition"
        onClick={() => onSwipe("like")}
      >
        Like
      </Button>
    </div>
  );
}
