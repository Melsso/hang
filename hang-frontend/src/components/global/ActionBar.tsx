import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { logout } from "../../api/auth";
import { get_notifications } from "../../api/conversations";
import { useToast } from "./ToastProvider";
import Button from "./Button";

export default function ActionBar() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { showToast } = useToast();
  const [hasNotifications, setHasNotifications] = useState(false);

  useEffect(() => {
    let cancelled = false;
    get_notifications().then((n) => {
      if (!cancelled) {
        setHasNotifications(!!n && n.new_matches + n.unread_messages > 0);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogout = async () => {
    const result = await logout();
    if (!result) {
      showToast("Something went wrong.", "error");
      return;
    }
    navigate("/login");
  };

  return (
    <div className="action-bar">
      <Button className="btn-secondary" onClick={() => navigate("/swipes")}>
        Home
      </Button>
      <Button className="btn-secondary" onClick={() => navigate("/profile")}>
        Profile
      </Button>
      <Button className="btn-secondary" onClick={() => navigate("/conversations")}>
        <span className="relative">
          Conversations
          {hasNotifications && pathname !== "/conversations" && (
            <span
              aria-label="New activity"
              className="absolute -top-1 -right-3 h-2.5 w-2.5 rounded-full bg-[#e50914]"
            />
          )}
        </span>
      </Button>
      <Button className="btn-secondary" onClick={() => navigate("/settings")}>
        Settings
      </Button>
      <Button className="btn-secondary" onClick={handleLogout}>
        Log-Out
      </Button>
    </div>
  );
}
