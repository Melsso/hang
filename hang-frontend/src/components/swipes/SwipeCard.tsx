import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { useState } from "react";
import type { ProfileImage } from "../profile/ProfileImagePanel";
import defaultUserImage from "../../assets/default_user.png";

export type SwipeProfile = {
  user_id: number;
  first_name: string;
  bio: string;
  interests: string[];
  gender: string;
  images: ProfileImage[];
};

type ProfileCardProps = {
  profile?: SwipeProfile;
  onSwipe?: (dir: "like" | "pass" | "super-like") => void;
};

const DEFAULT_IMAGE_URL = defaultUserImage;

export default function ProfileCard({ profile, onSwipe }: ProfileCardProps) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const rotate = useTransform(x, [-200, 200], [-15, 15]);
  const opacity = useTransform(x, [-200, 0, 200], [0.8, 1, 0.8]);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const imageCount = profile?.images?.length || 0;
  const hasImages = imageCount > 0;

  const prevImage = () => {
    if (imageCount <= 1) return;
    setSelectedIndex((prev) => (prev === 0 ? imageCount - 1 : prev - 1));
  };
  const nextImage = () => {
    if (imageCount <= 1) return;
    setSelectedIndex((prev) => (prev === imageCount - 1 ? 0 : prev + 1));
  };

  const isEmpty = !profile;

  const swipe = (dir: "like" | "pass" | "super-like") => {
    const targetX = dir === "like" ? 600 : dir === "pass" ? -600 : 0;
    const targetY = dir === "super-like" ? -600 : 0;

    animate(x, targetX, { duration: 0.25 });
    animate(y, targetY, { duration: 0.25 });

    setTimeout(() => {
      onSwipe?.(dir);
      x.set(0);
      y.set(0);
    }, 250);
  };

  return (
    <motion.div
      className="flex w-full rounded-2xl overflow-hidden bg-[#181818] shadow-[0_10px_40px_rgba(0,0,0,0.55)]"
      style={{ x, y, rotate, opacity }}
      drag={!isEmpty}
      dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={isEmpty ? 0 : 0.7}
      animate={{ opacity: 1, scale: 1 }}
      initial={{ opacity: 0, scale: 0.95 }}
      onDragEnd={(_, info) => {
        if (isEmpty) return;

        const dx = info.offset.x;
        const dy = info.offset.y;

        if (dx > 120) return swipe("like");
        if (dx < -120) return swipe("pass");
        if (dy < -120) return swipe("super-like");

        animate(x, 0, { duration: 0.2 });
        animate(y, 0, { duration: 0.2 });
      }}
    >
      <div className="relative w-3/5 h-96 bg-black">
        {isEmpty ? (
          <div className="w-full h-full flex items-center justify-center bg-[#111] text-white/40 text-sm">
            No more profiles
          </div>
        ) : (
          <img
            src={hasImages ? profile.images[selectedIndex].image_url : DEFAULT_IMAGE_URL}
            className="w-full h-full object-cover"
            alt={profile.first_name}
          />
        )}
        {hasImages && imageCount > 1 && (
          <>
            <button
              type="button"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={(e) => {
                e.stopPropagation();
                prevImage();
              }}
              className="
                                absolute left-3 top-1/2 -translate-y-1/2
                                w-10 h-10 rounded-full
                                bg-black/60 text-white
                                hover:bg-black/80
                                z-20
                            "
            >
              ←
            </button>

            <button
              type="button"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={(e) => {
                e.stopPropagation();
                nextImage();
              }}
              className="
                                absolute right-3 top-1/2 -translate-y-1/2
                                w-10 h-10 rounded-full
                                bg-black/60 text-white
                                hover:bg-black/80
                                z-20
                            "
            >
              →
            </button>
          </>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
      </div>

      <div className="w-2/5 flex flex-col justify-center gap-4 p-6">
        {isEmpty ? (
          <div className="text-center text-white/60 text-lg">No more profiles</div>
        ) : (
          <>
            <div className="text-2xl font-semibold text-white text-center">
              {profile.first_name}
            </div>

            <div className="text-sm text-white/70 text-center">{profile.bio}</div>

            <div className="flex flex-wrap justify-center gap-2">
              {profile.interests.map((i) => (
                <span key={i} className="px-3 py-1 text-xs rounded-full bg-[#222] text-white/70">
                  {i}
                </span>
              ))}
            </div>
          </>
        )}
      </div>
    </motion.div>
  );
}
