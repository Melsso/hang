import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useToast } from "../components/global/ToastProvider";

import ProfileImagePanel from "../components/profile/ProfileImagePanel";
import ProfileInfoPanel from "../components/profile/ProfileInfoPanel";
import ActionBar from "../components/global/ActionBar";

import {
    get_user_profile_info,
    upload_pictures,
    update_profile_info,
} from "../api/profile";

function getChangedFields(original: any, updated: any) {
    const diff: any = {};
    for (const key in updated) {
        const originalValue = original?.[key];
        const updatedValue = updated?.[key];
        if (JSON.stringify(originalValue) !== JSON.stringify(updatedValue))diff[key] = updatedValue;
    }
    return diff;
}

export default function Profile() {
    const { userId } = useParams();
    const { showToast } = useToast();

    const isOwnProfile = !userId;

    const [editMode, setEditMode] = useState(false);
    const [profile, setProfile] = useState<any | null>(null);
    const [form, setForm] = useState<any | null>(null);
    const [imageOrder, setImageOrder] = useState<any[]>([]);
    const [deletedImages, setDeletedImages] = useState<number[]>([]);
    const [loading, setLoading] = useState(true);

    const loadProfile = async () => {
        setLoading(true);

        const data = userId
            ? await get_user_profile_info(Number(userId))
            : await get_user_profile_info();

        if (!data) {
            setLoading(false);
            showToast("Something went wrong, try again later.", "error")
            return;
        }

        setProfile(data);
        setForm(data);
        setImageOrder(data.images);
        setLoading(false);

        if (!isOwnProfile) setEditMode(false);
    };

    useEffect(() => {
        loadProfile();
    }, [userId]);

    if (loading || !profile || !form) {
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
        } catch (err) {
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
            showToast("Failed to save image order");
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
                    setForm={setForm}
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