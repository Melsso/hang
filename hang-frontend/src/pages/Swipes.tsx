import { useState, useEffect } from "react";
import { useToast } from "../components/global/ToastProvider";

import ActionBar from "../components/global/ActionBar";
import ProfileCard from "../components/swipes/SwipeCard";
import SwipeAction from "../components/swipes/SwipeAction";
import { get_swipe_profiles, swipe_action } from "../api/swipes";
import type { SwipeProfile } from "../components/swipes/SwipeCard";

export default function Swipes() {
  const [profiles, setProfiles] = useState<SwipeProfile[] | null>(null);
  const [index, setIndex] = useState(0);
  const { showToast } = useToast();

  useEffect(() => {
    async function load() {
      const feed = await get_swipe_profiles();
      if (feed.status === "incomplete") {
        showToast("Please complete your profile.", "info");
        setProfiles([]);
        return;
      }
      if (feed.status === "error") {
        showToast("Something went wrong, try again later.", "error");
        setProfiles([]);
        return;
      }
      setProfiles(feed.profiles);
    }
    load();
  }, [showToast]);

  if (profiles === null) {
    return <div>Loading...</div>;
  }

  const currentProfile = profiles[index];
  const isEmpty = index >= profiles.length;

  const handleSwipe = async (swipeType: string) => {
    if (isEmpty) return;
    const profile = profiles[index];
    try {
      const result = await swipe_action(profile.user_id, swipeType);
      if (result == null) {
        showToast("Something went wrong, try again later.", "error");
        return;
      }
      if (index + 1 >= profiles.length) {
        const feed = await get_swipe_profiles();
        if (feed.status === "ok") {
          setProfiles(feed.profiles);
          setIndex(0);
          return;
        }
      }
      setIndex((prev) => prev + 1);
    } catch {
      showToast("Something went wrong, try again later.", "error");
    }
  };

  return (
    <div className="w-3/4 h-[70vh] flex flex-col items-center justify-center gap-10">
      <ActionBar />

      <ProfileCard
        key={index}
        profile={isEmpty ? undefined : currentProfile}
        onSwipe={handleSwipe}
      />

      <SwipeAction onSwipe={handleSwipe} />
    </div>
  );
}
