"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { listPlazaAgents, listAgents, createDirectSession } from "@/lib/api";

interface PlazaAgent {
  id: string;
  name: string;
  tags: string[];
  user_id: string;
  status?: string;
}

export default function PlazaPage() {
  const [user, setUser] = useState<any>(null);
  const [agents, setAgents] = useState<PlazaAgent[]>([]);
  const [myAgents, setMyAgents] = useState<PlazaAgent[]>([]);
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [modalAgent, setModalAgent] = useState<PlazaAgent | null>(null);
  const [step, setStep] = useState<"detail" | "pick_agent">("detail");
  const [starting, setStarting] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (!stored) {
      router.push("/login");
      return;
    }
    setUser(JSON.parse(stored));
  }, [router]);

  useEffect(() => {
    if (!user?.id) return;
    setLoading(true);
    const tagsParam =
      selectedTags.size > 0 ? Array.from(selectedTags).join(",") : undefined;
    const searchParam = searchInput.trim() || undefined;
    listPlazaAgents(user.id, tagsParam, searchParam)
      .then((data: PlazaAgent[]) => setAgents(Array.isArray(data) ? data : []))
      .catch(() => setAgents([]))
      .finally(() => setLoading(false));
  }, [user?.id, selectedTags, searchInput]);

  useEffect(() => {
    if (!user?.id) return;
    listAgents(user.id).then((data: PlazaAgent[]) =>
      setMyAgents(Array.isArray(data) ? data : [])
    );
  }, [user?.id]);

  const allTags = useMemo(() => {
    const set = new Set<string>();
    agents.forEach((a) => (a.tags || []).forEach((t: string) => set.add(t)));
    return Array.from(set).sort();
  }, [agents]);

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
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

  if (!user) return null;

  return (
    <main className="flex min-h-screen flex-col items-center p-8 bg-gray-100">
      <div className="w-full max-w-5xl flex flex-wrap justify-between items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold text-black">Agent Plaza</h1>
        <div className="flex items-center gap-3 flex-wrap">
          <input
            type="text"
            placeholder="Search by name..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm w-48"
          />
          <Link
            href="/"
            className="text-blue-600 hover:underline font-medium"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>

      {allTags.length > 0 && (
        <div className="w-full max-w-5xl mb-4 flex flex-wrap gap-2">
          {allTags.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => toggleTag(tag)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedTags.has(tag)
                  ? "bg-purple-600 text-white"
                  : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : agents.length === 0 ? (
        <p className="text-gray-500">No agents to show. Try changing filters or search.</p>
      ) : (
        <div className="w-full max-w-5xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <button
              key={agent.id}
              type="button"
              onClick={() => openModal(agent)}
              className="bg-white rounded-lg shadow p-6 border border-gray-200 hover:border-purple-400 hover:shadow-md transition-all text-left"
            >
              <h3 className="text-xl font-bold text-gray-800 mb-2">
                {agent.name}
              </h3>
              <div className="flex flex-wrap gap-1">
                {(agent.tags || []).map((t: string) => (
                  <span
                    key={t}
                    className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>
      )}

      {modalAgent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-bold text-gray-800">
                {step === "detail" ? modalAgent.name : "Choose your agent"}
              </h2>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                &times;
              </button>
            </div>
            <div className="p-6">
              {step === "detail" && (
                <>
                  <p className="text-sm text-gray-600 mb-4">
                    Tags: {(modalAgent.tags || []).join(", ") || "—"}
                  </p>
                  <button
                    type="button"
                    onClick={handleStartChatClick}
                    className="w-full bg-purple-600 text-white py-2 rounded-lg font-medium hover:bg-purple-700 transition-colors"
                  >
                    Start Chat
                  </button>
                </>
              )}
              {step === "pick_agent" && (
                <>
                  <p className="text-sm text-gray-600 mb-4">
                    Chat with <strong>{modalAgent.name}</strong> using:
                  </p>
                  {myAgents.length === 0 ? (
                    <p className="text-gray-500 text-sm">
                      You have no agents. Create one from the dashboard first.
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
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
