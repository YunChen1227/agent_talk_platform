"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createAgent } from "@/lib/api";

export default function CreateAgentPage() {
  const [user, setUser] = useState<any>(null);
  const [agentName, setAgentName] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [openingRemark, setOpeningRemark] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  // In dev mode, default to FREE tier behavior for now
  // Ideally this comes from user.tier
  const isPaidUser = false; 

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (!storedUser) {
      router.push("/login");
      return;
    }
    setUser(JSON.parse(storedUser));
  }, [router]);

  const handleCreate = async () => {
    if (!user || !agentName.trim()) return;
    setIsSubmitting(true);
    try {
      await createAgent(
        user.id, 
        agentName.trim(),
        isPaidUser ? description : undefined,
        !isPaidUser ? systemPrompt : undefined,
        !isPaidUser ? openingRemark : undefined
      );
      router.push("/");
    } catch (e) {
      alert("Error creating agent");
      setIsSubmitting(false);
    }
  };

  if (!user) return null;

  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-100">
      <div className="w-full max-w-4xl mb-8">
        <Link
          href="/"
          className="text-blue-500 hover:underline mb-4 inline-block"
        >
          &larr; Back to Dashboard
        </Link>
        <h1 className="text-4xl font-bold text-black mt-2">Create New Agent</h1>
        <p className="text-gray-600 mt-2">
          {isPaidUser ? "Paid Tier: AI Auto-Generation" : "Free Tier: Manual Configuration"}
        </p>
      </div>

      <div className="w-full max-w-4xl bg-white p-6 rounded-lg shadow-md space-y-6">
        <div>
          <label className="block font-bold mb-2 text-gray-800">Agent Name</label>
          <input
            className="w-full p-3 border border-gray-300 rounded-lg text-black focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Alice the Buyer"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
          />
        </div>

        {isPaidUser ? (
          <div>
            <label className="block font-bold mb-2 text-gray-800">
              Agent Description
              <span className="block text-sm font-normal text-gray-500">
                Describe personality, preferences, needs, and speaking style. Our AI will generate the rest.
              </span>
            </label>
            <textarea
              className="w-full p-3 border border-gray-300 rounded-lg text-black h-40 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., I am a tech enthusiast looking for a high-end laptop. I am detail-oriented, polite but firm on price. I prefer concise answers."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        ) : (
          <>
            <div>
              <label className="block font-bold mb-2 text-gray-800">
                System Prompt
                <span className="block text-sm font-normal text-gray-500">
                  Define exactly how your agent should behave.
                </span>
              </label>
              <textarea
                className="w-full p-3 border border-gray-300 rounded-lg text-black h-40 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                placeholder="You are a helpful assistant..."
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
              />
            </div>
            <div>
              <label className="block font-bold mb-2 text-gray-800">
                Opening Remark
                <span className="block text-sm font-normal text-gray-500">
                  The first message your agent will send to start the conversation.
                </span>
              </label>
              <input
                className="w-full p-3 border border-gray-300 rounded-lg text-black focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Hello! I am looking for..."
                value={openingRemark}
                onChange={(e) => setOpeningRemark(e.target.value)}
              />
            </div>
          </>
        )}

        <div className="flex gap-3 pt-4 border-t border-gray-100">
          <button
            className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            onClick={handleCreate}
            disabled={
              !agentName.trim() || 
              (isPaidUser && !description.trim()) ||
              (!isPaidUser && (!systemPrompt.trim() || !openingRemark.trim())) ||
              isSubmitting
            }
          >
            {isSubmitting ? "Creating..." : "Create Agent"}
          </button>
          <Link
            href="/"
            className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300 text-center font-medium"
          >
            Cancel
          </Link>
        </div>
      </div>
    </main>
  );
}
