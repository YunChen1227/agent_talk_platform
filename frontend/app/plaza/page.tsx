"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  listAgents,
  createDirectSession,
  getPlazaTags,
  searchPlazaAgents,
  PlazaTagCategory,
  PlazaTag,
  PlazaAgent,
  PlazaSearchResponse,
  PlazaMatchDetail,
} from "@/lib/api";

interface SimpleAgent {
  id: string;
  name: string;
}

const MATCH_STATUS_CONFIG: Record<
  string,
  { label: string; className: string }
> = {
  CONSENSUS: {
    label: "\u2713 达成一致",
    className: "bg-green-100 text-green-800",
  },
  CHATTING: {
    label: "\u25CF 聊天中",
    className: "bg-yellow-100 text-yellow-800",
  },
  DEADLOCK: {
    label: "\u2717 未达成一致",
    className: "bg-gray-200 text-gray-600",
  },
};

function MatchStatusBadge({ status }: { status: string }) {
  const config = MATCH_STATUS_CONFIG[status];
  if (!config) return null;
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}
    >
      {config.label}
    </span>
  );
}

function TagButton({
  tag,
  isSelected,
  onClick,
}: {
  tag: PlazaTag;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
        isSelected
          ? "bg-purple-600 text-white shadow-sm"
          : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400"
      }`}
    >
      {tag.name}
      {tag.children.length > 0 && !isSelected && (
        <span className="ml-0.5 text-gray-400">+</span>
      )}
    </button>
  );
}

export default function PlazaPage() {
  const [user, setUser] = useState<any>(null);
  const [tagCategories, setTagCategories] = useState<PlazaTagCategory[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<Set<string>>(new Set());
  const [expandedParentIds, setExpandedParentIds] = useState<Set<string>>(
    new Set()
  );
  const [searchInput, setSearchInput] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [searchResult, setSearchResult] = useState<PlazaSearchResponse | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const [myAgents, setMyAgents] = useState<SimpleAgent[]>([]);
  const [modalAgent, setModalAgent] = useState<PlazaAgent | null>(null);
  const [step, setStep] = useState<"detail" | "pick_agent">("detail");
  const [starting, setStarting] = useState(false);
  const router = useRouter();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (!stored) {
      router.push("/login");
      return;
    }
    setUser(JSON.parse(stored));
  }, [router]);

  useEffect(() => {
    getPlazaTags()
      .then(setTagCategories)
      .catch(() => setTagCategories([]));
  }, []);

  useEffect(() => {
    if (!user?.id) return;
    listAgents(user.id).then((data: SimpleAgent[]) =>
      setMyAgents(Array.isArray(data) ? data : [])
    );
  }, [user?.id]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setDebouncedQuery(searchInput.trim());
      setPage(1);
    }, 500);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchInput]);

  const doSearch = useCallback(async () => {
    if (!user?.id) return;
    setLoading(true);
    try {
      const tagIdArr = Array.from(selectedTagIds);
      const result = await searchPlazaAgents(user.id, {
        tagIds: tagIdArr.length > 0 ? tagIdArr : undefined,
        q: debouncedQuery || undefined,
        page,
        pageSize,
      });
      setSearchResult(result);
    } catch {
      setSearchResult(null);
    } finally {
      setLoading(false);
    }
  }, [user?.id, selectedTagIds, debouncedQuery, page, pageSize]);

  useEffect(() => {
    doSearch();
  }, [doSearch]);

  const toggleTag = (tagId: string, hasChildren: boolean) => {
    setSelectedTagIds((prev) => {
      const next = new Set(prev);
      if (next.has(tagId)) next.delete(tagId);
      else next.add(tagId);
      return next;
    });
    if (hasChildren) {
      setExpandedParentIds((prev) => {
        const next = new Set(prev);
        if (next.has(tagId)) next.delete(tagId);
        else next.add(tagId);
        return next;
      });
    }
    setPage(1);
  };

  const toggleChildTag = (tagId: string) => {
    setSelectedTagIds((prev) => {
      const next = new Set(prev);
      if (next.has(tagId)) next.delete(tagId);
      else next.add(tagId);
      return next;
    });
    setPage(1);
  };

  const openModal = (agent: PlazaAgent) => {
    setModalAgent(agent);
    setStep("detail");
  };

  const closeModal = () => {
    setModalAgent(null);
    setStep("detail");
  };

  const handleStartChatClick = () => {
    setStep("pick_agent");
  };

  const handleSelectMyAgent = async (myAgentId: string) => {
    if (!modalAgent || !user) return;
    setStarting(true);
    try {
      await createDirectSession(myAgentId, modalAgent.id);
      closeModal();
      router.push("/");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to start chat");
    } finally {
      setStarting(false);
    }
  };

  const agents = searchResult?.items ?? [];
  const total = searchResult?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  if (!user) return null;

  return (
    <main className="flex min-h-screen flex-col items-center p-8 bg-gray-50">
      {/* Header */}
      <div className="w-full max-w-6xl flex flex-wrap justify-between items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Agent Plaza</h1>
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative">
            <input
              type="text"
              placeholder="搜索 Agent..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-56 focus:ring-2 focus:ring-purple-400 focus:border-transparent outline-none"
            />
            <svg
              className="absolute left-2.5 top-2.5 w-4 h-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <Link
            href="/"
            className="text-purple-600 hover:underline font-medium text-sm"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>

      {/* Tag Categories - two-level hierarchy */}
      {tagCategories.length > 0 && (
        <div className="w-full max-w-6xl mb-6 space-y-3">
          {tagCategories.map((cat) => (
            <div key={cat.id} className="space-y-1.5">
              {/* Category row: label + root tags */}
              <div className="flex items-start gap-2">
                <span className="text-sm font-medium text-gray-500 min-w-[3.5rem] pt-1 text-right shrink-0">
                  {cat.name}:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {cat.tags.map((tag) => (
                    <TagButton
                      key={tag.id}
                      tag={tag}
                      isSelected={selectedTagIds.has(tag.id)}
                      onClick={() =>
                        toggleTag(tag.id, tag.children.length > 0)
                      }
                    />
                  ))}
                </div>
              </div>

              {/* Expanded children row(s) */}
              {cat.tags
                .filter(
                  (tag) =>
                    tag.children.length > 0 && expandedParentIds.has(tag.id)
                )
                .map((parent) => (
                  <div key={`children-${parent.id}`} className="flex items-start gap-2 ml-2">
                    <span className="text-xs text-gray-400 min-w-[3.5rem] pt-1.5 text-right shrink-0">
                      {parent.name}
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {parent.children.map((child) => (
                        <button
                          key={child.id}
                          type="button"
                          onClick={() => toggleChildTag(child.id)}
                          className={`px-2.5 py-0.5 rounded-full text-xs font-medium transition-colors ${
                            selectedTagIds.has(child.id)
                              ? "bg-purple-500 text-white shadow-sm"
                              : "bg-gray-50 border border-gray-200 text-gray-600 hover:bg-gray-100 hover:border-gray-300"
                          }`}
                        >
                          {child.name}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
          ))}
        </div>
      )}

      {/* Result Count */}
      {!loading && searchResult && (
        <div className="w-full max-w-6xl mb-3 text-sm text-gray-500">
          共 {total} 个 Agent
          {debouncedQuery && (
            <span>
              {" "}
              · 搜索 &quot;{debouncedQuery}&quot;
            </span>
          )}
          {selectedTagIds.size > 0 && (
            <span> · {selectedTagIds.size} 个标签过滤</span>
          )}
        </div>
      )}

      {/* Agent Grid */}
      {loading ? (
        <p className="text-gray-500 py-12">Loading...</p>
      ) : agents.length === 0 ? (
        <p className="text-gray-500 py-12">
          No agents found. Try different keywords or tags.
        </p>
      ) : (
        <div className="w-full max-w-6xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <button
              key={agent.id}
              type="button"
              onClick={() => openModal(agent)}
              className="bg-white rounded-xl shadow-sm p-5 border border-gray-200 hover:border-purple-400 hover:shadow-md transition-all text-left flex flex-col gap-2"
            >
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-lg font-bold text-gray-800 leading-tight">
                  {agent.name}
                </h3>
                <MatchStatusBadge status={agent.match_status} />
              </div>

              {agent.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {agent.tags.map((t) => (
                    <span
                      key={t.id}
                      className="text-xs px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-100"
                    >
                      {t.name}
                    </span>
                  ))}
                </div>
              )}

              {agent.opening_remark && (
                <p className="text-sm text-gray-500 line-clamp-2">
                  {agent.opening_remark}
                </p>
              )}

              {agent.search_score != null && agent.search_score > 0 && (
                <div className="text-xs text-gray-400 mt-auto">
                  相关度: {(agent.search_score * 100).toFixed(0)}%
                </div>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="w-full max-w-6xl flex justify-center items-center gap-4 mt-8">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            上一页
          </button>
          <span className="text-sm text-gray-600">
            第 {page}/{totalPages} 页
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            下一页
          </button>
        </div>
      )}

      {/* Modal */}
      {modalAgent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0">
              <h2 className="text-lg font-bold text-gray-800">
                {step === "detail" ? modalAgent.name : "选择你的 Agent"}
              </h2>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                &times;
              </button>
            </div>

            <div className="p-6 overflow-y-auto">
              {step === "detail" && (
                <div className="space-y-4">
                  {modalAgent.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {modalAgent.tags.map((t) => (
                        <span
                          key={t.id}
                          className="text-xs px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-100"
                        >
                          {t.name}
                        </span>
                      ))}
                    </div>
                  )}

                  {modalAgent.opening_remark && (
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-sm text-gray-600 italic">
                        &ldquo;{modalAgent.opening_remark}&rdquo;
                      </p>
                    </div>
                  )}

                  <div>
                    <MatchStatusBadge status={modalAgent.match_status} />
                  </div>

                  {modalAgent.match_details.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-gray-700">
                        匹配历史
                      </h4>
                      {modalAgent.match_details.map(
                        (d: PlazaMatchDetail, i: number) => (
                          <div
                            key={i}
                            className="flex items-center justify-between text-sm bg-gray-50 rounded px-3 py-2"
                          >
                            <span className="text-gray-700">
                              {d.my_agent_name}
                            </span>
                            <div className="flex items-center gap-2">
                              <MatchStatusBadge status={d.status} />
                              <span className="text-xs text-gray-400">
                                {new Date(d.created_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={handleStartChatClick}
                    className="w-full bg-purple-600 text-white py-2.5 rounded-lg font-medium hover:bg-purple-700 transition-colors"
                  >
                    Start Chat
                  </button>
                </div>
              )}

              {step === "pick_agent" && (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">
                    使用你的哪个 Agent 与{" "}
                    <strong>{modalAgent.name}</strong> 对话？
                  </p>
                  {myAgents.length === 0 ? (
                    <p className="text-gray-500 text-sm py-4">
                      你还没有 Agent。请先在 Dashboard 创建一个。
                    </p>
                  ) : (
                    <ul className="space-y-2">
                      {myAgents.map((a) => (
                        <li key={a.id}>
                          <button
                            type="button"
                            onClick={() => handleSelectMyAgent(a.id)}
                            disabled={starting}
                            className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:bg-purple-50 hover:border-purple-300 transition-colors disabled:opacity-50"
                          >
                            {a.name}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
