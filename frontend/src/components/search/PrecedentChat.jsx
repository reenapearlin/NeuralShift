import { useState } from "react";
import toast from "react-hot-toast";
import { MessageCircle, Send } from "lucide-react";
import { chatPrecedents } from "../../api/searchApi";

const PrecedentChat = () => {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);

  const onSend = async () => {
    const text = prompt.trim();
    if (!text) {
      return;
    }
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", text }]);
    setPrompt("");
    try {
      const response = await chatPrecedents(text, 5);
      const list = response.results || [];
      const summary =
        list.length > 0
          ? `Found ${list.length} similar precedents from live scraping.`
          : "No matching precedents found.";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: summary,
          results: list,
        },
      ]);
    } catch (error) {
      const message = error?.message || "Unable to fetch precedents right now.";
      toast.error(message);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: message },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
      <div className="mb-4 flex items-center gap-2">
        <MessageCircle className="h-5 w-5 text-amber-300" />
        <h3 className="text-lg font-bold text-white">AI Precedent Chat</h3>
      </div>
      <p className="mb-4 text-sm text-slate-400">
        Ask in plain language. The assistant scrapes and ranks precedents by similarity.
      </p>

      <div className="mb-4 max-h-80 space-y-3 overflow-y-auto rounded-lg border border-slate-700/50 bg-slate-900/40 p-3">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400">Start by asking a legal precedent question.</p>
        )}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`rounded-lg px-3 py-2 text-sm ${
              msg.role === "user" ? "bg-amber-400/20 text-amber-100" : "bg-slate-700/40 text-slate-200"
            }`}
          >
            <p>{msg.text}</p>
            {msg.role === "assistant" && Array.isArray(msg.results) && msg.results.length > 0 && (
              <ul className="mt-2 space-y-1">
                {msg.results.map((item) => (
                  <li key={item.url}>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-amber-300 hover:underline"
                    >
                      {item.title}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              onSend();
            }
          }}
          className="w-full rounded-lg border border-slate-600/50 bg-slate-800/50 px-4 py-2.5 text-white outline-none focus:border-amber-400"
          placeholder="Type your legal query..."
        />
        <button
          type="button"
          onClick={onSend}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-amber-400 to-amber-500 px-4 py-2.5 font-semibold text-slate-900 disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
          {loading ? "Sending..." : "Send"}
        </button>
      </div>
    </section>
  );
};

export default PrecedentChat;
