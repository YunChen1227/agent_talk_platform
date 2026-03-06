"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { createAgent, listAgents, startMatching, deleteAgent, getAgentResult } from "@/lib/api";
import Link from "next/link";

interface AgentResult {
  status: string;
  session: {
    id: string;
    status: string;
    created_at: string;
  } | null;
  other_agent_name: string | null;
  messages: { sender: string; content: string; timestamp: string }[];
  result: {
    verdict: string;
    summary: string;
    reason: string;
  } | null;
  contact: string | null;
}

export default function Home() {
  const [user, setUser] = useState<any>(null);
  const [agentName, setAgentName] = useState("");
  const [agents, setAgents] = useState<any[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedResult, setSelectedResult] = useState<AgentResult | null>(null);
  const [selectedAgentName, setSelectedAgentName] = useState("");
  const [loadingResult, setLoadingResult] = useState(false);
  const [notifiedAgents, setNotifiedAgents] = useState<Set<string>>(new Set());
  const router = useRouter();

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (!storedUser) {
      router.push("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);

    listAgents(userData.id).then(data => {
      if (Array.isArray(data)) setAgents(data);
    });

    const interval = setInterval(() => {
      listAgents(userData.id).then(data => {
        if (Array.isArray(data)) setAgents(data);
      });
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Detect newly completed agents for notification
  useEffect(() => {
    const doneAgents = agents.filter(a => a.status === "DONE");
    const newNotifications: string[] = [];
    doneAgents.forEach(a => {
      if (!notifiedAgents.has(a.id)) {
        newNotifications.push(a.id);
      }
    });
    if (newNotifications.length > 0) {
      setNotifiedAgents(prev => {
        const next = new Set(prev);
        newNotifications.forEach(id => next.add(id));
        return next;
      });
    }
  }, [agents]);

  const fetchAgents = async () => {
    if (!user) return;
    try {
      const data = await listAgents(user.id);
      if (Array.isArray(data)) {
        setAgents(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    router.push("/login");
  };

  const handleCreateAgent = async () => {
    if (!user || !agentName.trim()) return;
    try {
      await createAgent(user.id, agentName);
      setAgentName("");
      setIsCreating(false);
      fetchAgents();
    } catch (e) {
      alert("Error creating agent");
    }
  };

  const handleMatch = async (id: string) => {
    try {
      await startMatching(id);
      fetchAgents();
    } catch (e) {
      alert("Error starting match");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this agent?")) return;
    try {
      const success = await deleteAgent(id);
      if (success) {
        fetchAgents();
      } else {
        alert("Failed to delete agent");
      }
    } catch (e) {
      alert("Error deleting agent");
    }
  };

  const handleViewResult = async (agent: any) => {
    setLoadingResult(true);
    setSelectedAgentName(agent.name);
    try {
      const data = await getAgentResult(agent.id);
      setSelectedResult(data);
    } catch (e) {
      alert("Error loading result");
    } finally {
      setLoadingResult(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "IDLE": return "bg-green-500";
      case "MATCHING": return "bg-blue-500";
      case "PAIRED": return "bg-yellow-500";
      case "DONE": return "bg-purple-500";
      default: return "bg-gray-500";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "IDLE": return "Idle";
      case "MATCHING": return "Matching...";
      case "PAIRED": return "In Conversation";
      case "DONE": return "Result Ready";
      default: return status;
    }
  };

  if (!user) return null;

  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-100">
      <div className="w-full max-w-6xl flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold text-black">AgentMatch Platform</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-700">Welcome, {user.username}</span>
          <button
            onClick={handleLogout}
            className="text-red-500 hover:underline"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="w-full max-w-6xl mb-8">
        {!isCreating ? (
          <button
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-blue-700 shadow-md transition-colors"
            onClick={() => setIsCreating(true)}
          >
            + Create New AI
          </button>
        ) : (
          <div className="bg-white p-6 rounded-lg shadow-md max-w-md">
            <h2 className="text-xl font-bold mb-4 text-black">Create New Agent</h2>
            <div className="flex gap-2">
              <input
                className="flex-1 p-2 border rounded text-black"
                placeholder="Agent Name"
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
              />
              <button
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                onClick={handleCreateAgent}
              >
                Create
              </button>
              <button
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
                onClick={() => setIsCreating(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="w-full max-w-6xl">
        <h2 className="text-2xl font-bold mb-6 text-black">Your Agents</h2>
        {agents.length === 0 ? (
          <p className="text-gray-500 text-lg">No agents found. Create one to get started!</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className={`bg-white p-6 rounded-lg shadow-md border flex flex-col justify-between ${
                  agent.status === "DONE"
                    ? "border-purple-400 ring-2 ring-purple-200"
                    : "border-gray-200"
                }`}
              >
                <div>
                  <h3 className="text-xl font-bold text-gray-800 mb-2">{agent.name}</h3>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`inline-block w-3 h-3 rounded-full ${getStatusColor(agent.status)}`}></span>
                    <span className="text-sm text-gray-600 tracking-wide">{getStatusLabel(agent.status)}</span>
                  </div>

                  {agent.status === "DONE" && (
                    <div className="bg-purple-50 border border-purple-200 rounded-md p-3 mb-2">
                      <p className="text-purple-800 text-sm font-medium">
                        Negotiation complete! Click below to see the result.
                      </p>
                    </div>
                  )}

                  {agent.status === "PAIRED" && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-2">
                      <p className="text-yellow-800 text-sm font-medium">
                        Your agent is currently in a conversation...
                      </p>
                    </div>
                  )}

                  {agent.status === "MATCHING" && (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-2">
                      <p className="text-blue-800 text-sm font-medium">
                        Looking for a match...
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-100">
                  <div className="flex gap-2">
                    <Link
                      href={`/agent/${agent.id}`}
                      className="bg-blue-100 text-blue-700 px-3 py-1.5 rounded hover:bg-blue-200 text-sm font-medium transition-colors"
                    >
                      Edit
                    </Link>
                    {agent.status === "IDLE" && (
                      <button
                        onClick={() => handleDelete(agent.id)}
                        className="bg-red-100 text-red-700 px-3 py-1.5 rounded hover:bg-red-200 text-sm font-medium transition-colors"
                      >
                        Delete
                      </button>
                    )}
                  </div>

                  {agent.status === "IDLE" && (
                    <button
                      className="bg-purple-600 text-white px-3 py-1.5 rounded text-sm hover:bg-purple-700 transition-colors"
                      onClick={() => handleMatch(agent.id)}
                    >
                      Match
                    </button>
                  )}

                  <div className="flex gap-2">
                    {agent.status === "DONE" && (
                      <button
                        className="bg-green-600 text-white px-3 py-1.5 rounded text-sm hover:bg-green-700 transition-colors"
                        onClick={() => handleMatch(agent.id)}
                      >
                        Re-Match
                      </button>
                    )}
                    {(agent.status === "DONE" || agent.status === "PAIRED") && (
                      <button
                        className="bg-purple-600 text-white px-3 py-1.5 rounded text-sm hover:bg-purple-700 transition-colors"
                        onClick={() => handleViewResult(agent)}
                      >
                        View Result
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Result Modal */}
      {(selectedResult || loadingResult) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0">
              <h2 className="text-xl font-bold text-gray-800">
                {selectedAgentName} — Match Details
              </h2>
              <button
                onClick={() => { setSelectedResult(null); }}
                className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                &times;
              </button>
            </div>

            {loadingResult ? (
              <div className="p-12 text-center text-gray-500">Loading...</div>
            ) : selectedResult && (
              <div className="overflow-y-auto flex-1 p-6 space-y-6">
                {/* Verdict Banner */}
                {selectedResult.result && (
                  <div className={`rounded-lg p-4 ${
                    selectedResult.result.verdict === "CONSENSUS"
                      ? "bg-green-50 border border-green-300"
                      : "bg-red-50 border border-red-300"
                  }`}>
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`text-2xl`}>
                        {selectedResult.result.verdict === "CONSENSUS" ? "✅" : "❌"}
                      </span>
                      <span className={`text-lg font-bold ${
                        selectedResult.result.verdict === "CONSENSUS" ? "text-green-800" : "text-red-800"
                      }`}>
                        {selectedResult.result.verdict === "CONSENSUS" ? "Match Successful!" : "No Match"}
                      </span>
                    </div>
                    <p className={`text-sm ${
                      selectedResult.result.verdict === "CONSENSUS" ? "text-green-700" : "text-red-700"
                    }`}>
                      {selectedResult.result.summary}
                    </p>
                    <p className={`text-xs mt-2 ${
                      selectedResult.result.verdict === "CONSENSUS" ? "text-green-600" : "text-red-600"
                    }`}>
                      Reason: {selectedResult.result.reason}
                    </p>
                  </div>
                )}

                {/* Contact Info */}
                {selectedResult.contact && (
                  <div className="bg-blue-50 border border-blue-300 rounded-lg p-4">
                    <h3 className="text-sm font-bold text-blue-800 mb-1">Contact Information</h3>
                    <p className="text-blue-900 text-lg font-mono">{selectedResult.contact}</p>
                    {selectedResult.other_agent_name && (
                      <p className="text-blue-600 text-xs mt-1">Matched with: {selectedResult.other_agent_name}</p>
                    )}
                  </div>
                )}

                {/* Session Status (when still ongoing) */}
                {!selectedResult.result && selectedResult.session && (
                  <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4">
                    <p className="text-yellow-800 font-medium">
                      Session is still in progress ({selectedResult.session.status})
                    </p>
                  </div>
                )}

                {/* Conversation History */}
                {selectedResult.messages && selectedResult.messages.length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-gray-600 uppercase tracking-wide mb-3">
                      Conversation ({selectedResult.messages.length} messages)
                    </h3>
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {selectedResult.messages.map((msg, i) => (
                        <div
                          key={i}
                          className={`flex ${msg.sender === "self" ? "justify-end" : "justify-start"}`}
                        >
                          <div
                            className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                              msg.sender === "self"
                                ? "bg-purple-100 text-purple-900"
                                : "bg-gray-100 text-gray-900"
                            }`}
                          >
                            <div className="text-xs font-medium mb-1 opacity-60">
                              {msg.sender === "self" ? selectedAgentName : (selectedResult.other_agent_name || "Other")}
                            </div>
                            <div className="whitespace-pre-wrap">{msg.content}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
