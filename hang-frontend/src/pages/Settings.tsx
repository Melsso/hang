import { useState } from "react";
import ActionBar from "../components/global/ActionBar";
import SettingsModal from "../components/settings/ModalRow";
import BlockedUsersModal from "../components/settings/BlockedUsersModal";
import ReportsModal from "../components/settings/ReportsModal";
import ChangePasswordModal from "../components/settings/ChangePasswordModal";
import DeleteAccountModal from "../components/settings/DeleteAccountModal";
import SettingsRow from "../components/settings/SettingsRow";

export type SettingsModal =
  null | "blocked-users" | "reports" | "change-password" | "delete-account";

export default function Settings() {
  const [activeModal, setActiveModal] = useState<SettingsModal>(null);

  return (
    <div className="w-3/4 h-[70vh] flex flex-col items-center justify-center gap-10">
      <ActionBar />

      <div className="w-full h-full bg-[#181818] rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.45)] p-8 overflow-y-auto">
        <div className="space-y-8">
          <section>
            <h2 className="text-white/60 uppercase tracking-wider text-sm mb-3">Safety</h2>

            <div className="space-y-3">
              <SettingsRow
                title="Blocked Users"
                description="Manage users you've blocked."
                onClick={() => setActiveModal("blocked-users")}
              />

              <SettingsRow
                title="Reports"
                description="View reports you've submitted."
                onClick={() => setActiveModal("reports")}
              />
            </div>
          </section>

          <section>
            <h2 className="text-white/60 uppercase tracking-wider text-sm mb-3">Account</h2>

            <div className="space-y-3">
              <SettingsRow
                title="Change Password"
                description="Update your account password."
                onClick={() => setActiveModal("change-password")}
              />

              <SettingsRow
                title="Delete Account"
                description="Permanently remove your account and data."
                danger
                onClick={() => setActiveModal("delete-account")}
              />
            </div>
          </section>
        </div>
      </div>
      {activeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => setActiveModal(null)}
          />

          <div className="relative z-10 w-[700px] max-h-[80vh] overflow-y-auto bg-[#181818] rounded-2xl p-6 shadow-[0_8px_32px_rgba(0,0,0,0.65)]">
            <button
              onClick={() => setActiveModal(null)}
              className="absolute top-4 right-4 text-white/50 hover:text-white transition"
            >
              ✕
            </button>

            {activeModal === "blocked-users" && <BlockedUsersModal />}

            {activeModal === "reports" && <ReportsModal />}

            {activeModal === "change-password" && (
              <ChangePasswordModal onClose={() => setActiveModal(null)} />
            )}

            {activeModal === "delete-account" && <DeleteAccountModal />}
          </div>
        </div>
      )}
    </div>
  );
}
