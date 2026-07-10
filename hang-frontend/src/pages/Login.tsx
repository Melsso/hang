import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/global/ToastProvider";
import { login } from "../api/auth";
import Button from "../components/global/Button";

export default function Login() {
    const navigate = useNavigate();
    const { showToast } = useToast();
    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        const formData = new FormData(e.currentTarget);
        const email = formData.get("email") as string;
        const password = formData.get("password") as string;

        const result = await login(email, password);

        if (!result) {
            showToast("Login failed.", "error");
            return;
        }
        navigate("/swipes");
    };

    return (
        // <div className="card-container">
        <div className="w-2/5 h-[60vh] flex flex-col items-center justify-start gap-4 border border-[rgba(255,255,255,0.06)] rounded-lg p-6 bg-[#111111]">
            <h2 className="card-header">Login</h2>

            
            <form onSubmit={handleSubmit} className="login-form">
                <input type="email" name="email" placeholder="Email" />
                <input type="password" name="password" placeholder="Password" />
                <Button type="submit">Login</Button>
            </form>

            <Button
                className="oauth-btn"
                onClick={() => {
                    window.location.href = "/api/auth/login/google";
                }}
            >
                Continue with Google
            </Button>

            <Button className="redir-btn" onClick={() => navigate("/register")}>
                Don't have an account?
            </Button>
        </div>
    );
}