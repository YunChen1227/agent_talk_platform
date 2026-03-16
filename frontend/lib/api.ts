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

export interface CatalogTag {
  id: string;
  name: string;
  slug: string;
  category_id: string;
  parent_id?: string | null;
}

export const createAgent = async (
  userId: string,
  name: string,
  description?: string,
  systemPrompt?: string,
  openingRemark?: string,
  linkedProductIds?: string[],
  linkedSkillIds?: string[],
  tagIds?: string[],
  matchIntentTagIds?: string[]
) => {
  const res = await api.post("/agents/", {
    user_id: userId,
    name,
    description,
    system_prompt: systemPrompt,
    opening_remark: openingRemark,
    linked_product_ids: linkedProductIds,
    linked_skill_ids: linkedSkillIds,
    tag_ids: tagIds,
    match_intent_tag_ids: matchIntentTagIds,
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

// Plaza (new structured search)
export interface PlazaTag {
  id: string;
  name: string;
  slug: string;
  children: PlazaTag[];
}

export interface PlazaTagCategory {
  id: string;
  name: string;
  slug: string;
  tags: PlazaTag[];
}

export interface PlazaAgentTag {
  id: string;
  name: string;
  slug: string;
  category_id: string;
  parent_id?: string | null;
}

export interface PlazaMatchDetail {
  my_agent_id: string;
  my_agent_name: string;
  session_id: string;
  status: string;
  created_at: string;
}

export interface PlazaAgent {
  id: string;
  name: string;
  tags: PlazaAgentTag[];
  opening_remark?: string;
  match_status: string;
  match_details: PlazaMatchDetail[];
  search_score?: number;
}

export interface PlazaSearchResponse {
  total: number;
  page: number;
  page_size: number;
  items: PlazaAgent[];
}

export const getPlazaTags = async (): Promise<PlazaTagCategory[]> => {
  const res = await api.get("/plaza/tags");
  return res.data;
};

export const createPlazaTag = async (
  name: string,
  categoryId: string
): Promise<PlazaTag> => {
  const res = await api.post("/plaza/tags", {
    name,
    category_id: categoryId,
  });
  return res.data;
};

export const searchPlazaAgents = async (
  userId: string,
  options?: {
    tagIds?: string[];
    q?: string;
    page?: number;
    pageSize?: number;
  }
): Promise<PlazaSearchResponse> => {
  const params = new URLSearchParams({ user_id: userId });
  if (options?.tagIds && options.tagIds.length > 0) {
    params.set("tag_ids", options.tagIds.join(","));
  }
  if (options?.q) params.set("q", options.q);
  if (options?.page) params.set("page", String(options.page));
  if (options?.pageSize) params.set("page_size", String(options.pageSize));
  const res = await api.get(`/plaza/search?${params.toString()}`);
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
  tag_ids?: string[];
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
    tag_ids: string[];
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

// Skills
export const listSkills = async (userId: string) => {
  const res = await api.get(`/skills/?user_id=${userId}`);
  return res.data;
};

export const createSkill = async (data: {
  user_id: string;
  name: string;
  description?: string;
}) => {
  const res = await api.post("/skills/", data);
  return res.data;
};

export const updateSkill = async (
  skillId: string,
  userId: string,
  data: Partial<{ name: string; description: string }>
) => {
  const res = await api.put(`/skills/${skillId}?user_id=${userId}`, data);
  return res.data;
};

export const deleteSkill = async (skillId: string, userId: string) => {
  await api.delete(`/skills/${skillId}?user_id=${userId}`);
};
