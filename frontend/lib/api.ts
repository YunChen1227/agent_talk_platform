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

export async function startMatching(agent_id: string) {
  const res = await fetch(`${API_URL}/agents/${agent_id}/match`, {
    method: "POST",
  });
  return res.json();
}
