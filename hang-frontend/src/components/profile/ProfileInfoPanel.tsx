import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useToast } from "../global/ToastProvider";
import CountrySelect from "./CountrySelect";
import InterestsSelect from "./InterestsSelect";
import InterestedIn from "./InterestedIn";

import { report_user, block_user } from "../../api/profile";

export type ProfileData = {
    user_id?: number;
    first_name: string;
    last_name: string;
    bio: string;
    country: string;
    birthdate?: string | null;
    gender: string;
    interested_in: string;
    interests: string[];
};

type Props = {
    profile: ProfileData;
    form: ProfileData;
    setForm: React.Dispatch<React.SetStateAction<ProfileData>>;
    setEditMode: React.Dispatch<React.SetStateAction<boolean>>;
    onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
    onCancel: () => void;
    editMode: boolean;
    isOwnProfile: boolean;
};

type ProfileModalState = | null | "block" | "report";

function ProfileInfoView({ profile }: { profile: ProfileData }) {
    return (
        <div className="flex flex-col gap-6">
            <div>
                <h2 className="text-sm text-white/50 mb-2">Country</h2>
                <p className="text-white/80">{profile.country}</p>
            </div>

            <div>
                <h2 className="text-sm text-white/50 mb-2">Interested In</h2>
                <p className="text-white/80">{profile.interested_in}</p>
            </div>

            <div>
                <h2 className="text-sm text-white/50 mb-3">Interests</h2>
                <div className="flex flex-wrap gap-2">
                    {profile.interests.map((interest) => (
                        <span
                            key={interest}
                            className="px-3 py-1 rounded-full text-xs bg-[#222] text-white/80"
                        >
                            {interest}
                        </span>
                    ))}
                </div>
            </div>

            <div>
                <h2 className="text-sm text-white/50 mb-2">Bio</h2>
                <p className="text-white/80">{profile.bio}</p>
            </div>
        </div>
    );
}

function ProfileInfoEdit({
    form,
    setForm,
    onSubmit,
    onCancel,
}: {
    form: ProfileData;
    setForm: React.Dispatch<React.SetStateAction<ProfileData>>;
    onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
    onCancel: () => void;
}) {
    return (
        <form className="flex flex-col gap-5" onSubmit={onSubmit}>
            <div className="flex flex-col gap-2">
                <label className="text-sm text-white/60">First Name</label>
                <input
                    value={form.first_name}
                    onChange={(e) =>
                        setForm((prev) => ({
                            ...prev,
                            first_name: e.target.value,
                        }))
                    }
                    className="px-4 py-3 rounded-xl bg-[#222] text-white"
                />
            </div>
            
            <div className="flex flex-col gap-2">
                <label className="text-sm text-white/60">Birthdate</label>
                <input
                    type="date"
                    value={form.birthdate ?? ""}
                    onChange={(e) => setForm((prev) => ({ ...prev, birthdate: e.target.value }))}
                    className="px-4 py-3 rounded-xl bg-[#222] text-white"
                />
            </div>
            
            <CountrySelect
                value={form.country}
                onChange={(value) =>
                    setForm((prev) => ({
                        ...prev,
                        country: value,
                    }))
                }
            />

            <InterestedIn
                value={form.interested_in}
                setValue={(value) =>
                    setForm((prev) => ({
                        ...prev,
                        interested_in: value,
                    }))
                }
            />
            
            <InterestsSelect
                value={form.interests}
                onChange={(values) =>
                    setForm((prev) => ({
                        ...prev,
                        interests: values,
                    }))
                }
            />

            <div className="flex flex-col gap-2">
                <label className="text-sm text-white/60">Bio</label>
                <textarea
                    rows={5}
                    value={form.bio}
                    onChange={(e) =>
                        setForm((prev) => ({
                            ...prev,
                            bio: e.target.value,
                        }))
                    }
                    className="px-4 py-3 rounded-xl bg-[#222] text-white resize-none"
                />
            </div>

            <div className="flex gap-3 mt-2">
                <button
                    type="submit"
                    className="flex-1 py-3 rounded-xl bg-[#e50914] text-white font-medium"
                >
                    Save Changes
                </button>

                <button
                    type="button"
                    className="flex-1 py-3 rounded-xl bg-[#222] text-white"
                    onClick={onCancel}
                >
                    Cancel
                </button>
            </div>
        </form>
    );
}

export default function ProfileInfoPanel({
    profile,
    form,
    editMode,
    setForm,
    setEditMode,
    onSubmit,
    onCancel,
    isOwnProfile,
}: Props) {
    const navigate = useNavigate();
    const { showToast } = useToast();
    const [modal, setModal] = useState<ProfileModalState>(null);
    const [reportForm, setReportForm] = useState({
        reason: "",
        info: "",
    });

    const handleBlock = async () => {
        if (!profile.user_id) return;
        const result = await block_user(profile.user_id);
        if (!result) {
            showToast("Could not block user, try again later", "error");
            return;
        }
        showToast("User blocked.", "success");
        setModal(null);
        setTimeout(() => {
            navigate("/profile");
        }, 150);
    };
    const handleReport = async () => {
        if (!profile.user_id) return;
        const result = await report_user(profile.user_id, reportForm.reason, reportForm.info);
        if (!result) {
            showToast("Could not report user, try again later.", "error");
            return;
        }
        showToast("User reported.", "success");
        setReportForm({ reason: "", info: "" });
        setModal(null);
    };

    return (
        <div className="w-1/2 flex flex-col p-8 text-white max-h-screen overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-semibold">
                    {profile.first_name}
                </h1>

                {isOwnProfile && !editMode && (
                    <button
                        className="px-4 py-2 rounded-xl bg-[#e50914] text-white font-medium"
                        onClick={() => setEditMode(true)}
                    >
                        Edit Profile
                    </button>
                )}
                {!isOwnProfile && (
                    <div className="flex gap-3">
                        <button 
                            className="px-4 py-2 rounded-xl bg-yellow-600 text-white font-medium"
                            onClick={() => {setModal("report")}}
                        >
                            Report User
                        </button>

                        <button 
                            className="px-4 py-2 rounded-xl bg-[#e50914] text-white font-medium"
                            onClick={() => {setModal("block")}}
                        >
                            Block User
                        </button>
                    </div>
                )}
            </div>

            {editMode ? (
                <ProfileInfoEdit
                    form={form}
                    setForm={setForm}
                    onSubmit={onSubmit}
                    onCancel={onCancel}
                />
            ) : (
                <ProfileInfoView profile={profile} />
            )}
    
            {modal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
                    <div className="bg-[#181818] p-6 rounded-xl w-[420px] text-white">

                        {modal === "block" && (
                            <div className="flex flex-col gap-4">
                                <h2 className="text-xl font-semibold">
                                    Block user?
                                </h2>

                                <p className="text-white/60 text-sm">
                                    This user will no longer be able to interact with you.
                                </p>

                                <div className="flex gap-3 mt-4">
                                    <button
                                        className="flex-1 py-2 rounded bg-[#222]"
                                        onClick={() => setModal(null)}
                                    >
                                        Cancel
                                    </button>

                                    <button
                                        className="flex-1 py-2 rounded bg-red-600"
                                        onClick={handleBlock}
                                    >
                                        Block
                                    </button>
                                </div>
                            </div>
                        )}

                        {modal === "report" && (
                            <div className="flex flex-col gap-4">
                                <h2 className="text-xl font-semibold">
                                    Report user
                                </h2>

                                <input
                                    placeholder="Reason"
                                    value={reportForm.reason}
                                    onChange={(e) =>
                                        setReportForm((p) => ({
                                            ...p,
                                            reason: e.target.value,
                                        }))
                                    }
                                    className="px-4 py-2 rounded bg-[#222] text-white"
                                />

                                <textarea
                                    placeholder="Additional info"
                                    value={reportForm.info}
                                    onChange={(e) =>
                                        setReportForm((p) => ({
                                            ...p,
                                            info: e.target.value,
                                        }))
                                    }
                                    className="px-4 py-2 rounded bg-[#222] text-white resize-none h-24"
                                />

                                <div className="flex gap-3 mt-2">
                                    <button
                                        className="flex-1 py-2 rounded bg-[#222]"
                                        onClick={() => setModal(null)}
                                    >
                                        Cancel
                                    </button>

                                    <button
                                        className="flex-1 py-2 rounded bg-yellow-600"
                                        onClick={handleReport}
                                    >
                                        Submit
                                    </button>
                                </div>
                            </div>
                        )}

                    </div>
                </div>
            )}
        </div>
    );
}