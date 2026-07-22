import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import Nav from "../components/Nav.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { streamChat, ApiError } from "../services/api.js";

const STARTER_PROMPTS = [
  "I use my car 20km daily. Is that bad?",
  "How much difference does going vegetarian actually make?",
  "What's one realistic change I could make this week?",
];

function MessageBubble({ role, content, isStreaming }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser ? "bg-bark text-fog rounded-br-sm" : "bg-paper border border-mist text-bark rounded-bl-sm"
        }`}
      >
        {content}
        {isStreaming && (
          <span className="inline-block w-1.5 h-4 bg-verdigris ml-0.5 align-middle animate-pulse" />
        )}
      </div>
    </div>
  );
}

export default function Chat() {
  const { loggedIn } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || isStreaming) return;

    setError("");
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: trimmed }, { role: "assistant", content: "" }]);
    setIsStreaming(true);

    streamChat(trimmed, {
      onChunk: (chunk) => {
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          next[next.length - 1] = { ...last, content: last.content + chunk };
          return next;
        });
      },
      onDone: () => {
        setIsStreaming(false);
      },
      onError: (err) => {
        // Failed before any streaming started (e.g. AI not configured, not
        // logged in) — drop the empty placeholder bubble and show a real
        // error instead of leaving a blank assistant message.
        setMessages((prev) => prev.slice(0, -1));
        setError(err instanceof ApiError ? err.message : "Couldn't reach EcoMind AI. Please try again.");
        setIsStreaming(false);
      },
    });
  }

  if (!loggedIn) {
    return (
      <div>
        <Nav />
        <div className="max-w-md mx-auto px-6 py-24 text-center">
          <p className="font-mono text-xs uppercase tracking-widest text-moss mb-4">AI chat</p>
          <h1 className="font-display text-3xl text-bark mb-3">Log in to chat with EcoMind AI</h1>
          <p className="text-bark/60 mb-8">
            Chat is tied to your account so it can reference your carbon assessments — unlike the
            calculator, which you can try as a guest.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center rounded-full bg-verdigris text-fog text-sm font-medium px-7 py-3.5 hover:bg-verdigris-dark transition-colors"
          >
            Log in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      <Nav />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-6 py-8">
          {messages.length === 0 ? (
            <div className="text-center py-16">
              <p className="font-mono text-xs uppercase tracking-widest text-moss mb-4">AI chat</p>
              <h1 className="font-display text-2xl text-bark mb-8">
                Ask EcoMind AI anything about your impact.
              </h1>
              <div className="flex flex-col gap-3 max-w-sm mx-auto">
                {STARTER_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => sendMessage(prompt)}
                    className="text-left text-sm text-bark/70 bg-paper border border-mist rounded-xl px-4 py-3 hover:border-verdigris transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((m, i) => (
                <MessageBubble
                  key={i}
                  role={m.role}
                  content={m.content}
                  isStreaming={isStreaming && i === messages.length - 1 && m.role === "assistant"}
                />
              ))}
              <div ref={bottomRef} />
            </div>
          )}

          {error && (
            <p className="text-sm text-copper-dark bg-copper/10 border border-copper/30 rounded-lg px-4 py-3 mt-4">
              {error}
            </p>
          )}
        </div>
      </div>

      <div className="border-t border-mist bg-fog/95 backdrop-blur">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(input);
          }}
          className="max-w-2xl mx-auto px-6 py-4 flex gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your footprint…"
            disabled={isStreaming}
            className="flex-1 rounded-full border border-mist bg-paper px-5 py-3 text-sm text-bark focus:border-verdigris transition-colors disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="inline-flex items-center justify-center rounded-full bg-verdigris text-fog text-sm font-medium px-6 py-3 hover:bg-verdigris-dark transition-colors disabled:opacity-40"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
