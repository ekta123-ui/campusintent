import { useEffect, useRef, useState } from "react";
import AnswerCard from "./AnswerCard.jsx";
import { ask } from "../api.js";

const EXAMPLES = [
  "How do I get a bonafide certificate?",
  "Is bus facility available from Sohna?",
  "What time does the canteen open?",
  "Is there a robotics club in the college?",
];

export default function ChatBox({ onAsked }) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  async function send(text) {
    const q = (text ?? query).trim();
    if (!q || loading) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setQuery("");
    setLoading(true);
    try {
      const data = await ask(q);
      setMessages((m) => [...m, { role: "bot", result: data }]);
      onAsked?.();
    } catch (err) {
      setMessages((m) => [...m, { role: "error", text: `Could not reach the API (${err.message}). Is the backend running?` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="chat student-chat">
      <div className="examples">
        {EXAMPLES.map((e) => <button key={e} onClick={() => send(e)}>{e}</button>)}
      </div>
      <div className="messages">
        {messages.length === 0 && <p className="muted">Ask a question about admission, fees, exams, hostel, transport, cafeteria, placements and more.</p>}
        {messages.map((m, i) =>
          m.role === "user" ? <div key={i} className="bubble user">{m.text}</div>
          : m.role === "bot" ? <div key={i} className="bubble bot"><AnswerCard r={m.result} /></div>
          : <div key={i} className="bubble error">{m.text}</div>
        )}
        {loading && (
          <div className="bubble bot loading-bubble" aria-label="Searching">
            <span className="typing-dots" aria-hidden="true"><i /><i /><i /></span>
            <div className="loading-steps" aria-hidden="true">
              <span>Understand</span>
              <span>Retrieve</span>
              <span>Answer</span>
            </div>
          </div>
        )}
        <div ref={end} />
      </div>
      <div className="input">
        <input value={query} onChange={(e) => setQuery(e.target.value)}
               onKeyDown={(e) => e.key === "Enter" && send()} placeholder="Type your college question…" />
        <button onClick={() => send()} disabled={loading}>Send</button>
      </div>
    </section>
  );
}
