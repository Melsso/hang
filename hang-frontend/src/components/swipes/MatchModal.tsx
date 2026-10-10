import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import defaultUserImage from "../../assets/default_user.png";

type Props = {
  name: string;
  imageUrl?: string | null;
  onClose: () => void;
};

export default function MatchModal({ name, imageUrl, onClose }: Props) {
  const navigate = useNavigate();

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      onClick={onClose}
    >
      <motion.div
        className="flex flex-col items-center gap-5 rounded-2xl bg-[#181818] p-8 shadow-[0_8px_32px_rgba(0,0,0,0.65)]"
        initial={{ scale: 0.6, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 260, damping: 18 }}
        onClick={(e) => e.stopPropagation()}
      >
        <motion.h2
          className="text-4xl font-bold text-[#e50914]"
          initial={{ y: -10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.15 }}
        >
          It's a match!
        </motion.h2>

        <motion.img
          src={imageUrl ?? defaultUserImage}
          alt={name}
          className="h-40 w-40 rounded-full border-4 border-[#e50914] object-cover"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
        />

        <p className="text-white/70">You and {name} liked each other.</p>

        <div className="flex gap-3">
          <button
            type="button"
            className="rounded-xl bg-[#222] px-5 py-3 text-white hover:bg-[#2a2a2a]"
            onClick={onClose}
          >
            Keep swiping
          </button>
          <button
            type="button"
            className="rounded-xl bg-[#e50914] px-5 py-3 text-white hover:bg-[#f6121d]"
            onClick={() => navigate("/conversations")}
          >
            Send a message
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
