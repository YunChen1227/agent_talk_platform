"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { createSkill } from "@/lib/api";
import { useDraft } from "@/lib/useDraft";

const DRAFT_KEY = "draft:skill:new";

export default function CreateSkillPage() {
  const [user, setUser] = useState<{ id: string } | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();
  const draftRestored = useRef(false);

  const draftState = { name, description };
  const { draft, clearDraft, hasDraft } = useDraft(DRAFT_KEY, draftState, !!user, user?.id);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (!stored) {
      router.push("/login");
      return;
    }
    setUser(JSON.parse(stored));
  }, [router]);

  useEffect(() => {
    if (!draftRestored.current && hasDraft && draft && typeof draft.name === "string") {
      draftRestored.current = true;
      setName(draft.name);
      setDescription(typeof draft.description === "string" ? draft.description : "");
    }
  }, [hasDraft, draft]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !name.trim()) return;
    setSubmitting(true);
    try {
      await createSkill({
        user_id: user.id,
        name: name.trim(),
        description: description.trim() || undefined,
      });
      clearDraft();
      router.back();
    } catch (err: any) {
      alert(err.response?.data?.detail ?? "Failed to create skill");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    clearDraft();
    router.back();
  };

  if (!user) return null;

  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-100">
      <div className="w-full max-w-4xl mb-8">
        <button
          type="button"
          onClick={() => router.back()}
          className="text-blue-500 hover:underline flex items-center gap-1 mb-4"
        >
          <span>&larr;</span>
          <span>Back</span>
        </button>
        <h1 className="text-4xl font-bold text-black mt-2">Create New Skill</h1>
      </div>

      <div className="w-full max-w-4xl bg-white p-6 rounded-lg shadow-md">
        <form onSubmit={handleCreate} className="space-y-6">
          <div>
            <label className="block font-bold mb-2 text-gray-800">Name</label>
            <input
              className="w-full p-3 border border-gray-300 rounded-lg text-black focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., Search assistant"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block font-bold mb-2 text-gray-800">
              Description
              <span className="block text-sm font-normal text-gray-500">
                Optional. What this skill does.
              </span>
            </label>
            <textarea
              className="w-full p-3 border border-gray-300 rounded-lg text-black h-32 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Describe the skill..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div className="flex gap-3 pt-4 border-t border-gray-100">
            <button
              type="submit"
              disabled={submitting || !name.trim()}
              className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {submitting ? "Creating..." : "Create Skill"}
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300 font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
