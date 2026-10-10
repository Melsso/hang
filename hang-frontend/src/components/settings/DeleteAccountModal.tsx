import { deleteAccount } from "../../api/settings";
import { useNavigate } from "react-router-dom";
import { useToast } from "../global/ToastProvider";

export default function DeleteAccountModal() {
    const navigate = useNavigate();
    const { showToast } = useToast();

    async function handleDelete() {
        const result = await deleteAccount();
        if (!result) {
            showToast("Could not delete account, try again later.", "error");
            return;
        }
        showToast("Account deleted.", "success");
        navigate("/");
    }

    return (
        <>
            <h2 className="text-2xl font-bold text-[#ff5c5c] mb-4">
                Delete Account
            </h2>

            <div className="bg-[#241313] border border-[#e50914]/30 rounded-xl p-4 mb-5">
                <p className="text-white/80">
                    This action is irreversible.
                </p>

                <p className="text-white/50 text-sm mt-2">
                    Your account, conversations and profile data
                    will be permanently deleted.
                </p>
            </div>

            <button
                onClick={handleDelete}
                className="bg-[#e50914] hover:bg-[#f6121d] px-5 py-3 rounded-xl text-white"
            >
                Permanently Delete Account
            </button>
        </>
    );
}
