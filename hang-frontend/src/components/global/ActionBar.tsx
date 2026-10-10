import { useNavigate } from "react-router-dom";
import { logout } from "../../api/auth";
import { useToast } from "./ToastProvider";
import Button from "./Button";

export default function ActionBar() {
  const navigate = useNavigate();
  const { showToast } = useToast();

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
        Conversations
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
