"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createAgent } from "@/lib/api";

export default function CreateAgentPage() {
  const [user, setUser] = useState<any>(null);
  const [agentName, setAgentName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

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
      await createAgent(user.id, agentName.trim());
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
      </div>

      <div className="w-full max-w-4xl bg-white p-6 rounded-lg shadow-md">
        <div className="mb-6">
          <label className="block font-bold mb-2 text-gray-800">Agent Name</label>
          <input
            className="w-full p-3 border border-gray-300 rounded-lg text-black focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter a name for your agent"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
          />
        </div>

        <div className="flex gap-3">
          <button
            className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleCreate}
            disabled={!agentName.trim() || isSubmitting}
          >
            {isSubmitting ? "Creating..." : "Create"}
          </button>
          <Link
            href="/"
            className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300 text-center"
          >
            Cancel
          </Link>
        </div>
      </div>
    </main>
  );
}
