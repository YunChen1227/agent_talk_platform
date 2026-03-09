import axios from "axios";

const API_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const listAgents = async (userId: string) => {
  const res = await api.get(`/agents/?user_id=${userId}`);
  return res.data;
};

export const createAgent = async (
  userId: string, 
  name: string, 
  description?: string, 
  systemPrompt?: string, 
  openingRemark?: string
) => {
  const res = await api.post("/agents/", { 
    user_id: userId, 
    name,
    description,
    system_prompt: systemPrompt,
    opening_remark: openingRemark
  });
  return res.data;
};

export const getAgent = async (id: string) => {
  const res = await api.get(`/agents/${id}`);
  return res.data;
};

export const updateAgent = async (id: string, data: any) => {
  const res = await api.put(`/agents/${id}`, data);
  return res.data;
};

export const deleteAgent = async (id: string) => {
  try {
    await api.delete(`/agents/${id}`);
    return true;
  } catch (e) {
    return false;
  }
};

export const startMatching = async (id: string) => {
  const res = await api.post(`/agents/${id}/match`);
  return res.data;
};

export const stopMatching = async (id: string) => {
  const res = await api.post(`/agents/${id}/stop-matching`);
  return res.data;
};

export const getAgentResult = async (id: string, sessionId?: string) => {
  const query = sessionId ? `?session_id=${sessionId}` : "";
  const res = await api.get(`/agents/${id}/result${query}`);
  return res.data;
};

export const shareContact = async (id: string, sessionId?: string) => {
  const query = sessionId ? `?session_id=${sessionId}` : "";
  const res = await api.post(`/agents/${id}/share-contact${query}`);
  return res.data;
};

export const getActiveSessions = async (userId: string) => {
  const res = await api.get(`/sessions/active?user_id=${userId}`);
  return res.data;
};

export const getCompletedSessions = async (userId: string) => {
  const res = await api.get(`/sessions/completed?user_id=${userId}`);
  return res.data;
};

export const getSessionDetails = async (sessionId: string) => {
  const res = await api.get(`/sessions/${sessionId}`);
  return res.data;
};

export const getLatestJudge = async (sessionId: string) => {
  const res = await api.get(`/sessions/${sessionId}/latest-judge`);
  return res.data;
};

export const terminateSession = async (sessionId: string, userId: string) => {
  const res = await api.post(`/sessions/${sessionId}/terminate?user_id=${userId}`);
  return res.data;
};

export const getSystemStatus = async () => {
  const res = await api.get("/api/status");
  return res.data;
};

export const toggleLlmMatcher = async (enabled: boolean) => {
  const res = await api.post(`/api/config/llm-matcher?enabled=${enabled}`);
  return res.data;
};
