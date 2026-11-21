import { useState } from "react";
import { pretty, sendFeedback } from "../api.js";

const STATUS = {
  answered: ["Answered from knowledge base", "ok"],
  unanswered: ["New question saved for staff", "warn"],
  out_of_scope: ["Not a college question", "muted"],
  unclear: ["Could you rephrase?", "muted"],
};

export default function AnswerCard({ r }) {
  const [voted, setVoted] = useState(null);
  const [label, tone] = STATUS[r.status] || [r.status, "muted"];
  const entities = Object.entries(r.entities || {});

  async function vote(helpful) {
    setVoted(helpful);
    try { await sendFeedback(r.query_id, helpful); } catch { /* ignore */ }
  }

  return (
    <div className="result">
      <div className="row">
        <span className={`chip ${tone}`}>{label}</span>
        <span className="badge">{pretty(r.intent)}</span>
        <span className="conf">{Math.round(r.confidence * 100)}%</span>
        {r.generator === "claude" && <span className="chip muted">written by Claude</span>}
      </div>
      <p className="reply">{r.answer}</p>
      {r.department && r.status !== "answered" && <p className="dept">Contact: <strong>{r.department}</strong></p>}
      {entities.length > 0 && (
        <p className="ents">{entities.map(([k, v]) => <span key={k} className="ent">{k}: {v}</span>)}</p>
      )}
      {r.status === "unanswered" && r.times_asked > 1 && (
        <p className="muted">{r.times_asked} students have asked this. It is at the top of the staff queue.</p>
      )}
      {r.status === "unanswered" && r.related?.length > 0 && (
        <details>
          <summary>Related questions</summary>
          <ul>{r.related.map((x, i) => <li key={i}>{x.question}</li>)}</ul>
        </details>
      )}
      {r.sources?.length > 0 && (
        <details>
          <summary>Sources ({r.sources.length})</summary>
          <ul>
            {r.sources.map((s) => (
              <li key={s.kb_id}>
                <strong>{s.question}</strong> <span className="muted">(match {Math.round(s.score * 100)}%, {s.source})</span>
              </li>
            ))}
          </ul>
        </details>
      )}
      {r.query_id && (
        <div className="feedback">
          {voted === null ? (
            <>
              <span className="muted">Was this helpful?</span>
              <button onClick={() => vote(true)}>Yes</button>
              <button onClick={() => vote(false)}>No</button>
            </>
          ) : (
            <span className="muted feedback-thanks">{voted ? "Thanks for the feedback." : "Thanks, staff will review this answer."}</span>
          )}
        </div>
      )}
    </div>
  );
}
