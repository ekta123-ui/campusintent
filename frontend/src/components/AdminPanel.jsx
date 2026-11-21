import { useCallback, useEffect, useState } from "react";
import { INTENTS, addKnowledge, getQuestions, pretty, resolveQuestion } from "../api.js";

function Item({ q, adminKey, onDone, index }) {
  const [answer, setAnswer] = useState("");
  const [intent, setIntent] = useState(INTENTS.includes(q.intent) ? q.intent : "Faculty_Department");
  const [err, setErr] = useState("");

  async function save() {
    try {
      await resolveQuestion({ query_id: q.query_id, answer, intent }, adminKey);
      onDone();
    } catch (e) { setErr(e.message); }
  }

  return (
    <div className="qitem" style={{ "--q-index": index }}>
      <div className="row">
        <strong>{q.query}</strong>
        <span className="chip muted">asked {q.count}×</span>
        <span className="chip warn">{q.status}</span>
      </div>
      <p className="muted">Predicted intent: {pretty(q.intent)} ({Math.round(q.confidence * 100)}%) · Helpful {q.up} · Needs review {q.down}</p>
      <textarea rows={3} placeholder="Write the correct answer…" value={answer} onChange={(e) => setAnswer(e.target.value)} />
      <div className="row">
        <select value={intent} onChange={(e) => setIntent(e.target.value)}>
          {INTENTS.map((i) => <option key={i} value={i}>{pretty(i)}</option>)}
        </select>
        <button disabled={answer.trim().length < 3} onClick={save}>Add to knowledge base</button>
      </div>
      {err && <p className="err">{err}</p>}
    </div>
  );
}

export default function AdminPanel({ onChanged }) {
  const [adminKey, setAdminKey] = useState("");
  const [filter, setFilter] = useState("unanswered");
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const [faq, setFaq] = useState({ question: "", answer: "", intent: "Admission" });
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    setErr("");
    try { setItems(await getQuestions(filter === "all" ? "" : filter, adminKey)); }
    catch (e) { setItems([]); setErr(e.message); }
  }, [filter, adminKey]);
  useEffect(() => { load(); }, [load]);

  async function addFaq() {
    try {
      await addKnowledge(faq, adminKey);
      setMsg("Added to the knowledge base.");
      setFaq({ ...faq, question: "", answer: "" });
      onChanged?.();
    } catch (e) { setMsg(e.message); }
  }

  return (
    <section className="chat staff-panel">
      <div className="row">
        <input type="password" placeholder="Admin key (only if ADMIN_KEY is set on the server)" value={adminKey}
               onChange={(e) => setAdminKey(e.target.value)} />
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="unanswered">Unanswered</option>
          <option value="needs_review">Needs review</option>
          <option value="resolved">Resolved</option>
          <option value="answered">Answered</option>
          <option value="all">All</option>
        </select>
        <button onClick={load}>Refresh</button>
      </div>
      {err && <p className="err">{err}</p>}
      {items.length === 0 && !err && <p className="muted">Nothing here. Ask a new question in the student chat and it will appear.</p>}
      {items.map((q, index) => <Item key={q.query_id} q={q} adminKey={adminKey} index={index} onDone={() => { load(); onChanged?.(); }} />)}

      <h3>Add an FAQ directly</h3>
      <input placeholder="Question" value={faq.question} onChange={(e) => setFaq({ ...faq, question: e.target.value })} />
      <textarea rows={3} placeholder="Answer" value={faq.answer} onChange={(e) => setFaq({ ...faq, answer: e.target.value })} />
      <div className="row">
        <select value={faq.intent} onChange={(e) => setFaq({ ...faq, intent: e.target.value })}>
          {INTENTS.map((i) => <option key={i} value={i}>{pretty(i)}</option>)}
        </select>
        <button disabled={faq.question.length < 3 || faq.answer.length < 3} onClick={addFaq}>Add FAQ</button>
      </div>
      {msg && <p className="muted">{msg}</p>}
    </section>
  );
}
