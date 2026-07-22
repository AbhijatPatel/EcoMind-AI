import { Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing.jsx";
import Calculator from "./pages/Calculator.jsx";
import Chat from "./pages/Chat.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Challenges from "./pages/Challenges.jsx";
import Profile from "./pages/Profile.jsx";
import Auth from "./pages/Auth.jsx";
import ComingSoon from "./pages/ComingSoon.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/calculator" element={<Calculator />} />
      <Route path="/chat" element={<Chat />} />
      <Route path="/challenges" element={<Challenges />} />
      <Route path="/profile" element={<Profile />} />
      <Route path="/login" element={<Auth />} />
      <Route path="/register" element={<Auth />} />
      <Route path="*" element={<ComingSoon title="Page not found" />} />
    </Routes>
  );
}
