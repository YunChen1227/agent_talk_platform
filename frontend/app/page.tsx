"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { listAgents, startMatching, stopMatching, deleteAgent, getAgentResult, getActiveSessions, getCompletedSessions, getSessionDetails, getLatestJudge, terminateSession, getSystemStatus, toggleLlmMatcher, shareContact, API_URL } from "@/lib/api";
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
  my_contact_shared: boolean;
}

interface ActiveSession {
  session_id: string;
  my_agent_name: string;
  my_agent_id: string;
  opponent_agent_name: string;
  opponent_agent_id: string;
  status: string;
}

interface CompletedSession {
  session_id: string;
  my_agent_name: string;
  my_agent_id: string;
  opponent_agent_name: string;
  opponent_agent_id: string;
  status: string;
  verdict: string | null;
}

export default function Home() {
  const [user, setUser] = useState<any>(null);
  const [agents, setAgents] = useState<any[]>([]);
  const [selectedResult, setSelectedResult] = useState<AgentResult | null>(null);
  const [selectedAgentName, setSelectedAgentName] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [loadingResult, setLoadingResult] = useState(false);
  const [sharingContact, setSharingContact] = useState(false);
  const [activeSessions, setActiveSessions] = useState<ActiveSession[]>([]);
  const [completedSessions, setCompletedSessions] = useState<CompletedSession[]>([]);
  const [selectedChat, setSelectedChat] = useState<ActiveSession | null>(null);
  const [chatMessages, setChatMessages] = useState<{ sender: string; content: string; timestamp: string }[]>([]);
  const [chatJudge, setChatJudge] = useState<{ verdict: string; summary: string; reason: string } | null>(null);
  const [loadingChat, setLoadingChat] = useState(false);
  const [terminating, setTerminating] = useState(false);
  const [isDevMode, setIsDevMode] = useState(false);
  const [useLlmMatcher, setUseLlmMatcher] = useState(false);
  const [selectedResultSessionId, setSelectedResultSessionId] = useState("");
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
    getActiveSessions(userData.id).then(data => {
      if (Array.isArray(data)) setActiveSessions(data);
    });
    getCompletedSessions(userData.id).then(data => {
      if (Array.isArray(data)) setCompletedSessions(data);
    });
    
    // Check system status
    getSystemStatus().then(status => {
      setIsDevMode(status.mode === "dev");
      setUseLlmMatcher(status.use_llm_matcher);
    });

    const interval = setInterval(() => {
      listAgents(userData.id).then(data => {
        if (Array.isArray(data)) setAgents(data);
      });
      getActiveSessions(userData.id).then(data => {
        if (Array.isArray(data)) setActiveSessions(data);
      });
      getCompletedSessions(userData.id).then(data => {
        if (Array.isArray(data)) setCompletedSessions(data);
      });
    }, 5000);
    return () => clearInterval(interval);
  }, []);

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

  const fetchSessions = async () => {
    if (!user) return;
    try {
      const [activeData, completedData] = await Promise.all([
        getActiveSessions(user.id),
        getCompletedSessions(user.id),
      ]);
      if (Array.isArray(activeData)) setActiveSessions(activeData);
      if (Array.isArray(completedData)) setCompletedSessions(completedData);
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    router.push("/login");
  };

  const handleMatch = async (id: string) => {
    try {
      await startMatching(id);
      fetchAgents();
      fetchSessions();
    } catch (e) {
      alert("Error starting match");
    }
  };

  const handleStopMatching = async (id: string) => {
    try {
      await stopMatching(id);
      fetchAgents();
    } catch (e) {
      alert("Error stopping match");
    }
  };

  const handleDelete = async (agent: any) => {
    let confirmMessage = "Are you sure you want to delete this agent?";
    
    if (agent.status === "PAIRED") {
      confirmMessage = "This agent is currently chatting! Deleting it will terminate the active conversation for BOTH parties. Are you sure you want to proceed?";
    } else if (agent.status === "MATCHING") {
      confirmMessage = "This agent is currently looking for a match. Deleting it will cancel the request. Proceed?";
    }

    if (!confirm(confirmMessage)) return;

    try {
      const success = await deleteAgent(agent.id);
      if (success) {
        fetchAgents();
        fetchSessions();
        // If we deleted the agent currently open in chat modal, close it
        if (selectedChat && selectedChat.my_agent_id === agent.id) {
          setSelectedChat(null);
        }
      } else {
        alert("Failed to delete agent");
      }
    } catch (e) {
      alert("Error deleting agent");
    }
  };

  const refreshChat = useCallback(async (session: ActiveSession) => {
    try {
      const [detailRes, judgeRes] = await Promise.all([
        getSessionDetails(session.session_id),
        getLatestJudge(session.session_id),
      ]);
      const history = detailRes.history || [];
      const messages = history.map((m: { sender_id: string; content: string; timestamp: string }) => ({
        sender: m.sender_id === session.my_agent_id ? "self" : "other",
        content: m.content,
        timestamp: m.timestamp,
      }));
      setChatMessages(messages);
      setChatJudge(judgeRes);
    } catch (_) {}
  }, []);

  const handleOpenChat = async (session: ActiveSession) => {
    setSelectedChat(session);
    setLoadingChat(true);
    await refreshChat(session);
    setLoadingChat(false);
  };

  const handleTerminate = async () => {
    if (!selectedChat || !user) return;
    if (!confirm("Are you sure you want to terminate this conversation? This will mark it as a DEADLOCK.")) return;
    
    setTerminating(true);
    try {
      await terminateSession(selectedChat.session_id, user.id);
      alert("Conversation terminated.");
      setSelectedChat(null); // Close modal
      fetchAgents(); // Refresh list
      fetchSessions();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Error terminating session");
    } finally {
      setTerminating(false);
    }
  };
  
  const handleToggleLlmMatcher = async () => {
    const newState = !useLlmMatcher;
    try {
      await toggleLlmMatcher(newState);
      setUseLlmMatcher(newState);
    } catch (e) {
      alert("Failed to toggle LLM Matcher");
    }
  };

  // Refresh chat modal when open
  useEffect(() => {
    if (!selectedChat) return;
    const t = setInterval(() => refreshChat(selectedChat), 3000);
    return () => clearInterval(t);
  }, [selectedChat, refreshChat]);

  const handleViewResult = async (session: CompletedSession) => {
    setLoadingResult(true);
    setSelectedAgentName(session.my_agent_name);
    setSelectedAgentId(session.my_agent_id);
    setSelectedResultSessionId(session.session_id);
    try {
      const data = await getAgentResult(session.my_agent_id, session.session_id);
      setSelectedResult(data);
    } catch (e) {
      alert("Error loading result");
    } finally {
      setLoadingResult(false);
    }
  };

  const handleShareContact = async () => {
    if (!selectedAgentId || !selectedResultSessionId) return;
    if (!confirm("确认向对方展示你的联系方式吗？")) return;
    setSharingContact(true);
    try {
      await shareContact(selectedAgentId, selectedResultSessionId);
      const data = await getAgentResult(selectedAgentId, selectedResultSessionId);
      setSelectedResult(data);
      fetchSessions();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Failed to share contact");
    } finally {
      setSharingContact(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "MATCHING": return "bg-blue-500";
      default: return "bg-green-500";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "MATCHING": return "Matching...";
      default: return "Idle";
    }
  };

  if (!user) return null;

  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-100">
      <div className="w-full max-w-6xl flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold text-black">AgentMatch Platform</h1>
        <div className="flex items-center gap-4">
          {isDevMode && (
            <div className="flex items-center gap-2 bg-gray-200 px-3 py-1 rounded-full">
              <span className="text-xs font-bold text-gray-600 uppercase">Dev Mode</span>
              <button 
                onClick={handleToggleLlmMatcher}
                className={`text-xs px-2 py-0.5 rounded transition-colors ${
                  useLlmMatcher 
                    ? "bg-green-500 text-white hover:bg-green-600" 
                    : "bg-red-500 text-white hover:bg-red-600"
                }`}
              >
                AI Match: {useLlmMatcher ? "ON" : "OFF"}
              </button>
            </div>
          )}
          <Link href="/profile" className="text-gray-700 hover:underline">
            Welcome, {user.username}
          </Link>
          <Link href="/plaza" className="text-purple-600 font-medium hover:underline">
            Agent Plaza
          </Link>
          {user.avatar_url && (
            <img src={API_URL + user.avatar_url} alt="Avatar" className="w-8 h-8 rounded-full object-cover border border-gray-300" />
          )}
          <button
            onClick={handleLogout}
            className="text-red-500 hover:underline"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="w-full max-w-6xl mb-8">
        <Link
          href="/agent/new"
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-blue-700 shadow-md transition-colors"
        >
          + Create New AI
        </Link>
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
                className="bg-white p-6 rounded-lg shadow-md border flex flex-col justify-between border-gray-200"
              >
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-xl font-bold text-gray-800">{agent.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-bold text-white ${getStatusColor(agent.status)}`}>
                      {getStatusLabel(agent.status)}
                    </span>
                  </div>

                  {agent.status === "MATCHING" && (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-2">
                      <p className="text-blue-800 text-sm font-medium">
                        Looking for matches...
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
                    <button
                      onClick={() => handleDelete(agent)}
                      className="bg-red-100 text-red-700 px-3 py-1.5 rounded hover:bg-red-200 text-sm font-medium transition-colors"
                    >
                      Delete
                    </button>
                  </div>

                  {agent.status !== "MATCHING" && (
                    <button
                      className="bg-purple-600 text-white px-3 py-1.5 rounded text-sm hover:bg-purple-700 transition-colors"
                      onClick={() => handleMatch(agent.id)}
                    >
                      Start Match
                    </button>
                  )}
                  {agent.status === "MATCHING" && (
                    <button
                      className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm hover:bg-gray-800 transition-colors"
                      onClick={() => handleStopMatching(agent.id)}
                    >
                      Stop Match
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="w-full max-w-6xl mt-10">
        <h2 className="text-2xl font-bold mb-4 text-black">Active Sessions</h2>
        {activeSessions.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-gray-500">No active conversations. Start matching to begin.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activeSessions.map((session) => (
              <button
                key={session.session_id}
                onClick={() => handleOpenChat(session)}
                className="w-full text-left bg-white border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-center justify-between">
                  <p className="text-gray-900 font-medium">
                    {session.my_agent_name} ↔ {session.opponent_agent_name}
                  </p>
                  <span className={`text-xs px-2 py-1 rounded-full font-bold ${
                    session.status === "JUDGING"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-yellow-100 text-yellow-700"
                  }`}>
                    {session.status}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="w-full max-w-6xl mt-10">
        <h2 className="text-2xl font-bold mb-4 text-black">Completed Sessions</h2>
        {completedSessions.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-gray-500">No completed sessions yet.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {completedSessions.map((session) => (
              <div
                key={session.session_id}
                className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between"
              >
                <div>
                  <p className="text-gray-900 font-medium">
                    {session.my_agent_name} ↔ {session.opponent_agent_name}
                  </p>
                  <span className={`inline-block text-xs px-2 py-1 rounded-full font-bold mt-2 ${
                    session.verdict === "CONSENSUS"
                      ? "bg-green-100 text-green-700"
                      : "bg-red-100 text-red-700"
                  }`}>
                    {session.verdict || session.status}
                  </span>
                </div>
                <button
                  className="bg-purple-600 text-white px-3 py-1.5 rounded text-sm hover:bg-purple-700 transition-colors"
                  onClick={() => handleViewResult(session)}
                >
                  View Result
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Chat Modal (live conversation) */}
      {selectedChat && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0">
              <div className="flex items-center gap-4">
                <h2 className="text-xl font-bold text-gray-800">
                  {selectedChat.my_agent_name} ↔ {selectedChat.opponent_agent_name}
                </h2>
                {selectedChat.status === "ACTIVE" && (
                  <button
                    onClick={handleTerminate}
                    disabled={terminating}
                    className="bg-red-100 text-red-700 px-3 py-1 rounded text-xs font-bold hover:bg-red-200 transition-colors disabled:opacity-50"
                  >
                    {terminating ? "Terminating..." : "Terminate"}
                  </button>
                )}
              </div>
              <button
                onClick={() => setSelectedChat(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                &times;
              </button>
            </div>
            {loadingChat ? (
              <div className="p-12 text-center text-gray-500">Loading...</div>
            ) : (
              <div className="overflow-y-auto flex-1 p-6 space-y-6">
                {chatJudge && (
                  <div className={`rounded-lg p-4 ${
                    chatJudge.verdict === "CONSENSUS"
                      ? "bg-green-50 border border-green-300"
                      : chatJudge.verdict === "DEADLOCK"
                      ? "bg-red-50 border border-red-300"
                      : "bg-gray-50 border border-gray-300"
                  }`}>
                    <h3 className="text-sm font-bold text-gray-600 uppercase mb-2">Latest Judge</h3>
                    <p className="font-medium">{chatJudge.verdict}</p>
                    {chatJudge.summary && <p className="text-sm mt-1">{chatJudge.summary}</p>}
                    {chatJudge.reason && <p className="text-xs mt-1 text-gray-600">Reason: {chatJudge.reason}</p>}
                  </div>
                )}
                {!chatJudge && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <p className="text-gray-600 text-sm">对话进行中，尚未裁判</p>
                  </div>
                )}
                <div>
                  <h3 className="text-sm font-bold text-gray-600 uppercase tracking-wide mb-3">Conversation</h3>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {chatMessages.map((msg, i) => (
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
                            {msg.sender === "self" ? selectedChat.my_agent_name : selectedChat.opponent_agent_name}
                          </div>
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

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
                onClick={() => { setSelectedResult(null); setSelectedAgentId(""); setSelectedResultSessionId(""); }}
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

                {/* Final Outcome */}
                {selectedResult.result?.verdict === "CONSENSUS" && selectedResult.result.final_outcome && (
                  <div className="bg-emerald-50 border border-emerald-300 rounded-lg p-4">
                    <h3 className="text-sm font-bold text-emerald-800 mb-2">Final Agreed Outcome</h3>
                    <p className="text-emerald-900 text-sm whitespace-pre-wrap">
                      {selectedResult.result.final_outcome}
                    </p>
                  </div>
                )}

                {/* Contact Consent & Info */}
                {selectedResult.result?.verdict === "CONSENSUS" && (
                  <div className="space-y-3">
                    {!selectedResult.my_contact_shared ? (
                      <div className="bg-amber-50 border border-amber-300 rounded-lg p-4">
                        <h3 className="text-sm font-bold text-amber-800 mb-2">Share Your Contact</h3>
                        <p className="text-amber-700 text-sm mb-3">
                          You need to opt in before your contact details are shared with your match.
                        </p>
                        <button
                          onClick={handleShareContact}
                          disabled={sharingContact}
                          className="bg-amber-600 text-white px-3 py-1.5 rounded text-sm hover:bg-amber-700 transition-colors disabled:opacity-50"
                        >
                          {sharingContact ? "Sharing..." : "Share My Contact"}
                        </button>
                      </div>
                    ) : (
                      <div className="bg-green-50 border border-green-300 rounded-lg p-4">
                        <p className="text-green-800 text-sm font-medium">You have shared your contact.</p>
                      </div>
                    )}

                    {selectedResult.contact ? (
                      <div className="bg-blue-50 border border-blue-300 rounded-lg p-4">
                        <h3 className="text-sm font-bold text-blue-800 mb-1">Contact Information</h3>
                        <p className="text-blue-900 text-lg font-mono">{selectedResult.contact}</p>
                        {selectedResult.other_agent_name && (
                          <p className="text-blue-600 text-xs mt-1">Matched with: {selectedResult.other_agent_name}</p>
                        )}
                      </div>
                    ) : (
                      <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
                        <p className="text-gray-700 text-sm">Waiting for opponent to share their contact...</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Session Status */}
                {!selectedResult.result && selectedResult.session && (
                  selectedResult.session.status === "ACTIVE" || selectedResult.session.status === "JUDGING" ? (
                    <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4">
                      <p className="text-yellow-800 font-medium">
                        Session is still in progress ({selectedResult.session.status})
                      </p>
                    </div>
                  ) : selectedResult.session.status === "TERMINATED" ? (
                    <div className="bg-red-50 border border-red-300 rounded-lg p-4">
                      <p className="text-red-800 font-medium">
                        Session ended — no agreement was reached (DEADLOCK).
                      </p>
                    </div>
                  ) : (
                    <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
                      <p className="text-gray-700 font-medium">
                        Session ended ({selectedResult.session.status}).
                      </p>
                    </div>
                  )
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
