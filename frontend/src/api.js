export const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function req(path, opts = {}, adminKey) {
  const headers = { "Content-Type": "application/json", ...(adminKey ? { "X-Admin-Key": adminKey } : {}) };
  const res = await fetch(API + path, { ...opts, headers });
  if (!res.ok) throw new Error(`${res.status} ${(await res.text()).slice(0, 160)}`);
  return res.json();
}

export const ask = (query) => req("/ask", { method: "POST", body: JSON.stringify({ query }) });
export const sendFeedback = (query_id, helpful) =>
  req("/feedback", { method: "POST", body: JSON.stringify({ query_id, helpful }) });
export const getStats = () => req("/stats");
export const getQuestions = (status, key) =>
  req(`/admin/questions?${status ? `status=${status}&` : ""}limit=100`, {}, key);
export const resolveQuestion = (payload, key) =>
  req("/admin/resolve", { method: "POST", body: JSON.stringify(payload) }, key);
export const addKnowledge = (payload, key) =>
  req("/admin/knowledge", { method: "POST", body: JSON.stringify(payload) }, key);

export const INTENTS = [
  "Admission", "Fees", "Exam_Results", "Timetable_Schedule", "Hostel_Accommodation", "Transport_Bus",
  "Placement", "Scholarship", "Documents_Certificates", "Faculty_Department", "Cafeteria_Food",
  "Location_Directions", "Library_Facilities", "Attendance_Leave", "Complaint_Support",
];
export const pretty = (s) => (s || "").replace(/_/g, " ");
