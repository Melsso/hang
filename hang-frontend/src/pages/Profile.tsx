import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useToast } from "../components/global/ToastProvider";

import ProfileImagePanel from "../components/profile/ProfileImagePanel";
import ProfileInfoPanel from "../components/profile/ProfileInfoPanel";
import ActionBar from "../components/global/ActionBar";

import type { ProfileData } from "../components/profile/ProfileInfoPanel";
import type { ProfileImage } from "../components/profile/ProfileImagePanel";

import {
    get_user_profile_info,
    upload_pictures,
    update_profile_info,
} from "../api/profile";

type FullProfile = ProfileData & { images: ProfileImage[] };

function getChangedFields(
    original: Record<string, unknown>,
    updated: Record<string, unknown>
) {
    const diff: Record<string, unknown> = {};
    for (const key in updated) {
        const originalValue = original?.[key];
        const updatedValue = updated?.[key];
        if (JSON.stringify(originalValue) !== JSON.stringify(updatedValue)) {
            diff[key] = updatedValue;
        }
    }
    return diff;
}

function ProfileView({ userId }: { userId?: string }) {
    const { showToast } = useToast();

    const isOwnProfile = !userId;

    const [editMode, setEditMode] = useState(false);
    const [profile, setProfile] = useState<FullProfile | null>(null);
    const [form, setForm] = useState<ProfileData | null>(null);
    const [imageOrder, setImageOrder] = useState<ProfileImage[]>([]);
    const [deletedImages, setDeletedImages] = useState<number[]>([]);

    const setFormData: React.Dispatch<React.SetStateAction<ProfileData>> = (
        value
    ) =>
        setForm((prev) => {
            if (prev === null) return prev;
            return typeof value === "function" ? value(prev) : value;
        });

    const fetchProfile = (): Promise<FullProfile | null> =>
        get_user_profile_info(userId ? Number(userId) : undefined);

    const applyProfile = (data: FullProfile) => {
        setProfile(data);
        setForm(data);
        setImageOrder(data.images);
    };

    // used for reloads after upload/save (called from handlers, not from an effect)
    const loadProfile = async () => {
        try {
            const data = await fetchProfile();
            if (!data) {
                showToast("Something went wrong, try again later.", "error");
                return;
            }
            applyProfile(data);
        } catch {
            showToast("Something went wrong, try again later.", "error");
        }
    };

    // initial load: state is only set after the await, so no synchronous setState in the effect
    useEffect(() => {
        let cancelled = false;
        (async () => {
            const data = await get_user_profile_info(
                userId ? Number(userId) : undefined
            );
            if (cancelled) return;
            if (!data) {
                showToast("Something went wrong, try again later.", "error");
                return;
            }
            setProfile(data);
            setForm(data);
            setImageOrder(data.images);
        })();
        return () => {
            cancelled = true;
        };
    }, [userId, showToast]);

    if (!profile || !form) {
        return <div>Loading...</div>;
    }

    const handleUploadImages = async (
        e: React.ChangeEvent<HTMLInputElement>
    ) => {
        const files = e.target.files;
        if (!files?.length) return;

        const formData = new FormData();
        for (const file of files) {
            formData.append("files", file);
        }
        try {
            const result = await upload_pictures(formData);

            if (!result) {
                showToast("Upload failed");
                return;
            }

            await loadProfile();
            showToast("Images uploaded");
            e.target.value = "";
        } catch {
            showToast("Upload failed");
        }
    };

    const handleSubmitProfile = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        if (!isOwnProfile) return;
        const updatedForm = {
            ...form,
            images: imageOrder.map((img, index) => ({
                ...img,
                position: index,
            })),
            deleted_images: deletedImages,
        };
        const diff = getChangedFields(profile, updatedForm);
        const result = await update_profile_info(diff);
        if (!result) {
            showToast("Could not update profile");
            return;
        }

        setEditMode(false);
        showToast("Profile updated");
        setDeletedImages([]);
        await loadProfile();
    };

    const handleCancelEdit = () => {
        setForm(profile);
        setImageOrder(profile.images);
        setEditMode(false);
        setDeletedImages([]);
    };

    return (
        <div className="w-3/4 h-[70vh] flex flex-col items-center justify-center gap-10">
            <ActionBar />

            <div className="w-full h-full flex rounded-2xl overflow-hidden bg-[#111]">
                <ProfileImagePanel
                    key={profile.images.map((i) => i.image_id).join(",")}
                    images={profile.images}
                    imageOrder={imageOrder}
                    setImageOrder={setImageOrder}
                    editMode={editMode}
                    canEdit={isOwnProfile}
                    onUploadImages={handleUploadImages}
                    deletedImages={deletedImages}
                    setDeletedImages={setDeletedImages}
                />

                <ProfileInfoPanel
                    profile={profile}
                    form={form}
                    setForm={setFormData}
                    editMode={editMode}
                    setEditMode={setEditMode}
                    onSubmit={handleSubmitProfile}
                    onCancel={handleCancelEdit}
                    isOwnProfile={isOwnProfile}
                />
            </div>
        </div>
    );
}

export default function Profile() {
    const { userId } = useParams();
    return <ProfileView key={userId ?? "me"} userId={userId} />;
}