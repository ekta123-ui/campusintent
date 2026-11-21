import { useCallback, useEffect, useState } from "react";
import ChatBox from "./components/ChatBox.jsx";
import AdminPanel from "./components/AdminPanel.jsx";
import StatsBar from "./components/StatsBar.jsx";
import { getStats } from "./api.js";

export default function App() {
  const [tab, setTab] = useState("chat");
  const [stats, setStats] = useState(null);

  const refresh = useCallback(() => getStats().then(setStats).catch(() => setStats(null)), []);
  useEffect(() => { refresh(); }, [refresh]);

  return (
    <main className="page">
      <header className="site-header">
        <h1>CampusIntent</h1>
        <p>LangChain RAG helpdesk - MCA lab project</p>
      </header>
      <StatsBar stats={stats} />
      <nav className="tabs">
        <button className={tab === "chat" ? "active" : ""} onClick={() => setTab("chat")}>Student chat</button>
        <button className={tab === "admin" ? "active" : ""} onClick={() => setTab("admin")}>
          Staff panel{stats && stats.unanswered > 0 ? ` (${stats.unanswered})` : ""}
        </button>
      </nav>
      <div className="tab-content" key={tab}>
        {tab === "chat" ? <ChatBox onAsked={refresh} /> : <AdminPanel onChanged={refresh} />}
      </div>
      <footer className="site-footer">Built by [Your Name] - MCA (AI &amp; ML)</footer>
    </main>
  );
}
