import { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
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
            const data = await get_swipe_profiles();
            if (!data) {
                showToast("Something went wrong, try again later.", "error");
                return;
            }
            setProfiles(data);
        }
        load();
    }, []);

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
            setIndex(prev => prev + 1);
        } catch (err) {
            showToast("Something went wrong, try again later.", "error");
        }
    };

    return (
        <div className="w-3/4 h-[70vh] flex flex-col items-center justify-center gap-10">
            <ActionBar />

            <AnimatePresence mode="wait">
                <ProfileCard
                    key={index}
                    profile={isEmpty ? undefined : currentProfile}
                    onSwipe={handleSwipe}
                />
            </AnimatePresence>

            <SwipeAction onSwipe={handleSwipe} />
        </div>
    );
}