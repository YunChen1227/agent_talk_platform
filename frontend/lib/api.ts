import axios from "axios";

const API_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export { API_URL };

export const listAgents = async (userId: string) => {
  const res = await api.get(`/agents/?user_id=${userId}`);
  return res.data;
};

export const createAgent = async (
  userId: string, 
  name: string, 
  description?: string, 
  systemPrompt?: string, 
  openingRemark?: string,
  linkedProductIds?: string[]
) => {
  const res = await api.post("/agents/", { 
    user_id: userId, 
    name,
    description,
    system_prompt: systemPrompt,
    opening_remark: openingRemark,
    linked_product_ids: linkedProductIds,
  });
  return res.data;
};

export const getAgent = async (id: string) => {
  const res = await api.get(`/agents/${id}`);
  return res.data;
};

export const listPlazaAgents = async (
  userId: string,
  tags?: string,
  search?: string
) => {
  const params = new URLSearchParams({ user_id: userId });
  if (tags) params.set("tags", tags);
  if (search) params.set("search", search);
  const res = await api.get(`/agents/plaza?${params.toString()}`);
  return res.data;
};

export const createDirectSession = async (
  myAgentId: string,
  targetAgentId: string
) => {
  const res = await api.post("/sessions/direct", {
    my_agent_id: myAgentId,
    target_agent_id: targetAgentId,
  });
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

// Media
export const uploadMedia = async (userId: string, file: File) => {
  const form = new FormData();
  form.append("user_id", userId);
  form.append("file", file);
  const res = await api.post("/media/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};

export const listMedia = async (userId: string) => {
  const res = await api.get(`/media/?user_id=${userId}`);
  return res.data;
};

export const deleteMedia = async (mediaId: string, userId: string) => {
  await api.delete(`/media/${mediaId}?user_id=${userId}`);
};

export const setAvatar = async (userId: string, mediaId: string) => {
  const res = await api.post("/media/avatar", { user_id: userId, media_id: mediaId });
  return res.data;
};

// Shop
export const listProducts = async (userId: string) => {
  const res = await api.get(`/shop/products?user_id=${userId}`);
  return res.data;
};

export const createProduct = async (data: {
  user_id: string;
  name: string;
  description?: string;
  price: number | string;
  currency?: string;
  image_ids?: string[];
  cover_image_id?: string;
  linked_agent_ids?: string[];
}) => {
  const res = await api.post("/shop/products", data);
  return res.data;
};

export const getProduct = async (productId: string, userId: string) => {
  const res = await api.get(`/shop/products/${productId}?user_id=${userId}`);
  return res.data;
};

export const updateProduct = async (
  productId: string,
  userId: string,
  data: Partial<{
    name: string;
    description: string;
    price: number | string;
    currency: string;
    image_ids: string[];
    cover_image_id: string;
    status: string;
    linked_agent_ids: string[];
  }>
) => {
  const res = await api.put(`/shop/products/${productId}?user_id=${userId}`, data);
  return res.data;
};

export const deleteProduct = async (productId: string, userId: string) => {
  await api.delete(`/shop/products/${productId}?user_id=${userId}`);
};

export const linkProductToAgent = async (
  productId: string,
  userId: string,
  agentId: string
) => {
  const res = await api.post(`/shop/products/${productId}/link-agent`, {
    user_id: userId,
    agent_id: agentId,
  });
  return res.data;
};

export const unlinkProductFromAgent = async (
  productId: string,
  userId: string,
  agentId: string
) => {
  const res = await api.post(`/shop/products/${productId}/unlink-agent`, {
    user_id: userId,
    agent_id: agentId,
  });
  return res.data;
};
