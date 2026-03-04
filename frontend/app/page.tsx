"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createAgent, listAgents, startMatching } from "@/lib/api";

export default function Home() {
  const [user, setUser] = useState<any>(null);
  const [agentName, setAgentName] = useState("");
  const [agents, setAgents] = useState<any[]>([]);
  const router = useRouter();

  useEffect(() => {
    // Check authentication
    const storedUser = localStorage.getItem("user");
    if (!storedUser) {
      router.push("/login");
      return;
    }
    const userData = JSON.parse(storedUser);
    setUser(userData);

    // Initial fetch with user ID
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
    if (!user) return;
    try {
      await createAgent(user.id, agentName);
      setAgentName("");
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

  if (!user) return null;

  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-100">
      <div className="w-full max-w-4xl flex justify-between items-center mb-8">
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
      
      <div className="w-full max-w-2xl bg-white p-6 rounded-lg shadow-md mb-8 text-black">
        <h2 className="text-2xl font-bold mb-4">Your Profile</h2>
        <p className="mb-2"><strong>Demand:</strong> {user.raw_demand}</p>
        <p className="mb-2"><strong>Tags:</strong> {user.tags?.join(", ")}</p>
      </div>

      <div className="w-full max-w-2xl bg-white p-6 rounded-lg shadow-md mb-8 text-black">
        <h2 className="text-2xl font-bold mb-4">Create Agent</h2>
        <div className="flex gap-2">
          <input
            className="flex-1 p-2 border rounded"
            placeholder="Agent Name"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
          />
          <button
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
            onClick={handleCreateAgent}
          >
            Spawn Agent
          </button>
        </div>
      </div>

      <div className="w-full max-w-2xl bg-white p-6 rounded-lg shadow-md text-black">
        <h2 className="text-2xl font-bold mb-4">Active Agents</h2>
        {agents.length === 0 ? (
          <p className="text-gray-500">No agents found.</p>
        ) : (
          agents.map((agent) => (
            <div key={agent.id} className="border-b py-2 flex justify-between items-center last:border-0">
              <div>
                <p className="font-bold">{agent.name}</p>
                <p className="text-sm text-gray-500">Status: {agent.status}</p>
              </div>
              {agent.status === "IDLE" && (
                <button
                  className="bg-purple-500 text-white px-3 py-1 rounded text-sm hover:bg-purple-600"
                  onClick={() => handleMatch(agent.id)}
                >
                  Start Matching
                </button>
              )}
              {agent.status === "MATCHING" && (
                <span className="text-blue-500 font-bold text-sm">Searching...</span>
              )}
              {agent.status === "BUSY" && (
                <span className="text-yellow-600 font-bold text-sm">Negotiating...</span>
              )}
            </div>
          ))
        )}
      </div>
    </main>
  );
}
