import { useState, useEffect } from "react";
import { getBlockedUsers, unblockUser } from "../../api/settings";
import { useToast } from "../global/ToastProvider";
import ModalRow from "./SettingsModal";

export default function BlockedUsersModal() {
    const [users, setUsers] = useState<any[]>([]);
    const { showToast } = useToast();

    useEffect(() => {
        loadBlockedUsers();
    }, []);

    function formatDate(date: string) {
        return new Date(date).toLocaleString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    async function loadBlockedUsers() {
        const data = await getBlockedUsers();
        if (!data) {
            showToast("Something went wrong, try again later.", "error");
            return;
        }
        setUsers(data);
    }

    return (
        <>
            <h2 className="text-2xl font-bold text-white mb-6">
                Blocked Users
            </h2>

            <div className="space-y-3">
                {users.map((user) => (
                    <ModalRow key={user.user_id}>
                        <div>
                            <div className="text-white">
                                {user.first_name} {user.last_name}
                            </div>

                            <div className="text-white/50 text-sm">
                                Blocked on {formatDate(user.created_at)}
                            </div>
                        </div>

                        <button
                            className="bg-[#e50914] px-4 py-2 rounded-lg text-white hover:bg-[#f6121d]"
                            onClick={async () => {
                                const success = await unblockUser(user.user_id);
                                if (!success) {
                                    showToast("Something went wrong, try again later.", "error");
                                    return;
                                }
                                setUsers(prev =>
                                    prev.filter(u => u.user_id !== user.user_id)
                                );
                            }}
                        >
                            Unblock
                        </button>
                    </ModalRow>
                ))}
            </div>
        </>
    );
}