import { useNavigate } from "react-router-dom";
import Button from "../components/global/Button";

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center p-6">
      <h1 className="text-6xl font-bold">Find Your Match</h1>
      <p className="mt-60 mb-5">Swipe. Connect. Chat. Meet people that actually fit you.</p>
      <div className="flex p-2 gap-5">
        <Button className="btn-primary" onClick={() => navigate("/login")}>
          Login
        </Button>
        <Button className="btn-secondary" onClick={() => navigate("/register")}>
          Register
        </Button>
      </div>
    </div>
  );
}
