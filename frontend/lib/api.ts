const API_URL = "http://localhost:8000";

export async function createUser(raw_demand: string, contact?: string) {
  const res = await fetch(`${API_URL}/users/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_demand, contact }),
  });
  return res.json();
}

export async function createAgent(user_id: string, name: string) {
  const res = await fetch(`${API_URL}/agents/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, name }),
  });
  return res.json();
}

export async function listAgents(user_id: string) {
  const res = await fetch(`${API_URL}/agents/?user_id=${user_id}`);
  return res.json();
}

export async function getAgent(agent_id: string) {
  const res = await fetch(`${API_URL}/agents/${agent_id}`);
  return res.json();
}

export async function updateAgent(agent_id: string, data: { name?: string; system_prompt?: string; opening_remark?: string }) {
  const res = await fetch(`${API_URL}/agents/${agent_id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function startMatching(agent_id: string) {
  const res = await fetch(`${API_URL}/agents/${agent_id}/match`, {
    method: "POST",
  });
  return res.json();
}

export async function deleteAgent(agent_id: string) {
  const res = await fetch(`${API_URL}/agents/${agent_id}`, {
    method: "DELETE",
  });
  return res.status === 204;
}

export async function getAgentResult(agent_id: string) {
  const res = await fetch(`${API_URL}/agents/${agent_id}/result`);
  return res.json();
}

export async function getActiveSessions(user_id: string) {
  const res = await fetch(`${API_URL}/sessions/active?user_id=${user_id}`);
  return res.json();
}

export async function getSessionDetails(session_id: string) {
  const res = await fetch(`${API_URL}/sessions/${session_id}`);
  return res.json();
}

export async function getLatestJudge(session_id: string) {
  const res = await fetch(`${API_URL}/sessions/${session_id}/latest-judge`);
  return res.json();
}
