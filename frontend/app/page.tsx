"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createAgent, listAgents, startMatching, deleteAgent } from "@/lib/api";
import Link from "next/link";

export default function Home() {
  const [user, setUser] = useState<any>(null);
  const [agentName, setAgentName] = useState("");
  const [agents, setAgents] = useState<any[]>([]);
  const [isCreating, setIsCreating] = useState(false);
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
              <div key={agent.id} className="bg-white p-6 rounded-lg shadow-md border border-gray-200 flex flex-col justify-between h-48">
                <div>
                  <h3 className="text-xl font-bold text-gray-800 mb-2">{agent.name}</h3>
                  <div className="flex items-center gap-2 mb-4">
                    <span className={`inline-block w-3 h-3 rounded-full ${
                      agent.status === 'IDLE' ? 'bg-green-500' : 
                      agent.status === 'MATCHING' ? 'bg-blue-500' : 'bg-yellow-500'
                    }`}></span>
                    <span className="text-sm text-gray-600 uppercase tracking-wide">{agent.status}</span>
                  </div>
                </div>
                
                <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-100">
                  <div className="flex gap-2">
                    <Link 
                      href={`/agent/${agent.id}`}
                      className="bg-blue-100 text-blue-700 px-3 py-1.5 rounded hover:bg-blue-200 text-sm font-medium transition-colors"
                    >
                      View
                    </Link>
                    <button
                      onClick={() => handleDelete(agent.id)}
                      className="bg-red-100 text-red-700 px-3 py-1.5 rounded hover:bg-red-200 text-sm font-medium transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                  
                  {agent.status === "IDLE" && (
                    <button
                      className="bg-purple-600 text-white px-3 py-1.5 rounded text-sm hover:bg-purple-700 transition-colors"
                      onClick={() => handleMatch(agent.id)}
                    >
                      Match
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
