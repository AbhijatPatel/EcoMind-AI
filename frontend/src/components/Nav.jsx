import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";

const LINKS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/calculator", label: "Calculator" },
  { to: "/chat", label: "Chat" },
  { to: "/challenges", label: "Challenges" },
];

export default function Nav() {
  const { loggedIn } = useAuth();

  return (
    <header className="sticky top-0 z-40 backdrop-blur bg-fog/85 border-b border-mist">
      <nav className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-2 group">
          <span className="w-7 h-7 rounded-full bg-copper relative overflow-hidden flex-shrink-0">
            <span className="absolute inset-1 rounded-full bg-verdigris opacity-80 group-hover:opacity-100 transition-opacity" />
          </span>
          <span className="font-display text-lg text-bark">EcoMind AI</span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `font-body text-sm transition-colors ${
                  isActive ? "text-bark font-medium" : "text-bark/60 hover:text-bark"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>

        <div className="flex items-center gap-3">
          {loggedIn ? (
            <Link
              to="/profile"
              className="hidden sm:inline-block text-sm text-bark/70 hover:text-bark transition-colors"
            >
              Profile
            </Link>
          ) : (
            <Link
              to="/login"
              className="hidden sm:inline-block text-sm text-bark/70 hover:text-bark transition-colors"
            >
              Log in
            </Link>
          )}
          <Link
            to="/calculator"
            className="inline-flex items-center rounded-full bg-bark text-fog text-sm font-medium px-5 py-2.5 hover:bg-verdigris-dark transition-colors"
          >
            Get your score
          </Link>
        </div>
      </nav>
    </header>
  );
}
