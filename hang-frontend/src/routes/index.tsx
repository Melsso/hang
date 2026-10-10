import { BrowserRouter, Routes, Route } from "react-router-dom";
import RequireAuth from "../components/global/RequireAuth";

import Landing from "../pages/Landing";
import Login from "../pages/Login";
import Register from "../pages/Register";
import Swipes from "../pages/Swipes";
import Profile from "../pages/Profile";
import Conversations from "../pages/Conversations";
import Settings from "../pages/Settings";

export default function AppRoutes() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Landing />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route element={<RequireAuth />}>
                    <Route path="/swipes" element={<Swipes />} />
                    <Route path="/profile/:userId?" element={<Profile />} />
                    <Route path="/conversations" element={<Conversations />} />
                    <Route path="/settings" element={<Settings />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}