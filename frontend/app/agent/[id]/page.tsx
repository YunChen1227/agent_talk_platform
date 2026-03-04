"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAgent, updateAgent } from "@/lib/api";

export default function AgentDetail({ params }: { params: { id: string } }) {
  const [agent, setAgent] = useState<any>(null);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [openingRemark, setOpeningRemark] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    getAgent(params.id).then((data) => {
      if (data) {
        setAgent(data);
        setSystemPrompt(data.system_prompt);
        setOpeningRemark(data.opening_remark || "");
        setName(data.name);
      }
      setLoading(false);
    });
  }, [params.id]);

  const handleSave = async () => {
    try {
      await updateAgent(params.id, { name, system_prompt: systemPrompt, opening_remark: openingRemark });
      alert("Agent updated successfully!");
    } catch (e) {
      alert("Error updating agent");
    }
  };

  if (loading) return <div className="p-24 text-black">Loading...</div>;
  if (!agent) return <div className="p-24 text-black">Agent not found</div>;

  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-100">
      <div className="w-full max-w-4xl mb-8">
        <button
          onClick={() => router.back()}
          className="text-blue-500 hover:underline mb-4"
        >
          &larr; Back to Dashboard
        </button>
        <h1 className="text-4xl font-bold text-black">Edit Agent Persona</h1>
      </div>

      <div className="w-full max-w-4xl bg-white p-6 rounded-lg shadow-md text-black">
        <div className="mb-4">
          <label className="block font-bold mb-2">Agent Name</label>
          <input
            className="w-full p-2 border rounded"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div className="mb-4">
          <label className="block font-bold mb-2">Opening Remark</label>
          <p className="text-sm text-gray-500 mb-2">
            The first message your agent will send when a match is found.
          </p>
          <textarea
            className="w-full h-24 p-2 border rounded font-mono text-sm"
            value={openingRemark}
            onChange={(e) => setOpeningRemark(e.target.value)}
          />
        </div>

        <div className="mb-4">
          <label className="block font-bold mb-2">System Prompt (Persona)</label>
          <p className="text-sm text-gray-500 mb-2">
            This is the core instruction set for your AI agent. You can modify its personality, goals, and negotiation strategy here.
          </p>
          <textarea
            className="w-full h-96 p-2 border rounded font-mono text-sm"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
          />
        </div>

        <div className="flex justify-end">
          <button
            className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600"
            onClick={handleSave}
          >
            Save Changes
          </button>
        </div>
      </div>
    </main>
  );
}
