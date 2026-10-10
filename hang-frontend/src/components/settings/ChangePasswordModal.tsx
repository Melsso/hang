import { useState } from "react";
import { changePassword } from "../../api/settings";
import { useToast } from "../global/ToastProvider";

export default function ChangePasswordModal({onClose}: {onClose: () => void;}) {
    const [oldPassword, setOldPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const { showToast } = useToast();

    async function handleSubmit() {
        const result = await changePassword(oldPassword, newPassword);
        if (!result) {
            showToast("Could not change password, try again later.", "error");
            return;
        }
        showToast("Password updated.", "success");
        onClose();
    }

    return (
        <>
            <h2 className="text-2xl font-bold text-white mb-6">
                Change Password
            </h2>

            <div className="space-y-4">
                <input
                    type="password"
                    placeholder="Current Password"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    className="w-full bg-[#222] rounded-xl p-3 text-white"
                />

                <input
                    type="password"
                    placeholder="New Password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full bg-[#222] rounded-xl p-3 text-white"
                />

                <button
                    onClick={handleSubmit}
                    className="bg-[#e50914] hover:bg-[#f6121d] px-5 py-3 rounded-xl text-white"
                >
                    Change Password
                </button>
            </div>
        </>
    );
}
