"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  getAgent,
  updateAgent,
  listProducts,
  listSkills,
  createProduct,
  createSkill,
  getPlazaTags,
  createPlazaTag,
  PlazaTagCategory,
} from "@/lib/api";
import TagDropdownSelect from "@/components/TagDropdownSelect";

interface Item {
  id: string;
  name: string;
}

function MultiSelectWithCreate({
  label,
  items,
  selectedIds,
  onToggle,
  onCreate,
  createPlaceholder,
}: {
  label: string;
  items: Item[];
  selectedIds: string[];
  onToggle: (id: string) => void;
  onCreate: (name: string) => Promise<void>;
  createPlaceholder: string;
}) {
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setCreating(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleCreate = async () => {
    if (!newName.trim() || submitting) return;
    setSubmitting(true);
    try {
      await onCreate(newName.trim());
      setNewName("");
      setCreating(false);
    } finally {
      setSubmitting(false);
    }
  };

  const selected = items.filter((i) => selectedIds.includes(i.id));

  return (
    <div ref={ref} className="relative">
      <label className="block font-bold mb-2">{label}</label>
      <div
        className="w-full min-h-[44px] p-2 border border-gray-300 rounded-lg cursor-pointer flex flex-wrap gap-1.5 items-center focus-within:ring-2 focus-within:ring-blue-500"
        onClick={() => setOpen(!open)}
      >
        {selected.length === 0 && (
          <span className="text-gray-400 text-sm">Click to select…</span>
        )}
        {selected.map((item) => (
          <span
            key={item.id}
            className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-1 rounded-full flex items-center gap-1"
          >
            {item.name}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onToggle(item.id);
              }}
              className="hover:text-blue-600"
            >
              ×
            </button>
          </span>
        ))}
      </div>

      {open && (
        <div className="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {items.map((item) => {
            const isSelected = selectedIds.includes(item.id);
            return (
              <div
                key={item.id}
                className={`px-3 py-2 cursor-pointer hover:bg-gray-50 flex items-center gap-2 text-sm ${
                  isSelected ? "bg-blue-50" : ""
                }`}
                onClick={() => onToggle(item.id)}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  readOnly
                  className="rounded text-blue-600"
                />
                <span className="text-gray-800">{item.name}</span>
              </div>
            );
          })}

          {items.length === 0 && !creating && (
            <div className="px-3 py-2 text-sm text-gray-400">
              No items yet.
            </div>
          )}

          <div className="border-t border-gray-100">
            {creating ? (
              <div className="p-2 flex gap-2">
                <input
                  autoFocus
                  className="flex-1 p-1.5 border border-gray-300 rounded text-sm text-black"
                  placeholder={createPlaceholder}
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleCreate();
                    }
                    if (e.key === "Escape") setCreating(false);
                  }}
                  onClick={(e) => e.stopPropagation()}
                />
                <button
                  type="button"
                  disabled={submitting || !newName.trim()}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCreate();
                  }}
                  className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {submitting ? "…" : "Add"}
                </button>
              </div>
            ) : (
              <div
                className="px-3 py-2 cursor-pointer hover:bg-gray-50 flex items-center gap-2 text-sm text-blue-600 font-medium"
                onClick={(e) => {
                  e.stopPropagation();
                  setCreating(true);
                }}
              >
                <span className="text-lg leading-none">+</span>
                <span>Create new</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function AgentDetail({ params }: { params: { id: string } }) {
  const [agent, setAgent] = useState<any>(null);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [openingRemark, setOpeningRemark] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const [user, setUser] = useState<any>(null);
  const [products, setProducts] = useState<Item[]>([]);
  const [skills, setSkills] = useState<Item[]>([]);
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([]);
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);

  const [tagCategories, setTagCategories] = useState<PlazaTagCategory[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<Set<string>>(new Set());
  const [selectedIntentIds, setSelectedIntentIds] = useState<Set<string>>(
    new Set()
  );

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  useEffect(() => {
    getPlazaTags()
      .then(setTagCategories)
      .catch(() => setTagCategories([]));
  }, []);

  useEffect(() => {
    getAgent(params.id).then((data) => {
      if (data) {
        setAgent(data);
        setSystemPrompt(data.system_prompt);
        setOpeningRemark(data.opening_remark || "");
        setName(data.name);
        setSelectedProductIds(data.linked_product_ids || []);
        setSelectedSkillIds(data.linked_skill_ids || []);
        if (data.catalog_tags && Array.isArray(data.catalog_tags)) {
          setSelectedTagIds(
            new Set(data.catalog_tags.map((t: any) => t.id))
          );
        }
        if (
          data.match_intent_tag_ids &&
          Array.isArray(data.match_intent_tag_ids)
        ) {
          setSelectedIntentIds(new Set(data.match_intent_tag_ids));
        }
      }
      setLoading(false);
    });
  }, [params.id]);

  useEffect(() => {
    if (!user) return;
    loadItems(user.id);
  }, [user]);

  const loadItems = async (userId: string) => {
    try {
      const [prods, sklls] = await Promise.all([
        listProducts(userId),
        listSkills(userId),
      ]);
      setProducts(prods.map((p: any) => ({ id: p.id, name: p.name })));
      setSkills(sklls.map((s: any) => ({ id: s.id, name: s.name })));
    } catch {
      /* ignore */
    }
  };

  const toggleId = (
    id: string,
    selected: string[],
    setSelected: (ids: string[]) => void
  ) => {
    setSelected(
      selected.includes(id)
        ? selected.filter((x) => x !== id)
        : [...selected, id]
    );
  };

  const toggleTagId = (tagId: string) => {
    setSelectedTagIds((prev) => {
      const next = new Set(prev);
      if (next.has(tagId)) next.delete(tagId);
      else next.add(tagId);
      return next;
    });
  };

  const toggleIntentId = (tagId: string) => {
    setSelectedIntentIds((prev) => {
      const next = new Set(prev);
      if (next.has(tagId)) next.delete(tagId);
      else next.add(tagId);
      return next;
    });
  };

  const handleCreateTag = async (name: string, categoryId: string) => {
    try {
      const newTag = await createPlazaTag(name, categoryId);
      const cats = await getPlazaTags();
      setTagCategories(cats);
      setSelectedTagIds((prev) => new Set([...prev, newTag.id]));
    } catch {
      alert("Failed to create tag");
    }
  };

  const handleCreateIntentTag = async (name: string, categoryId: string) => {
    try {
      const newTag = await createPlazaTag(name, categoryId);
      const cats = await getPlazaTags();
      setTagCategories(cats);
      setSelectedIntentIds((prev) => new Set([...prev, newTag.id]));
    } catch {
      alert("Failed to create tag");
    }
  };

  const handleCreateProduct = async (name: string) => {
    if (!user) return;
    const prod = await createProduct({ user_id: user.id, name, price: 0 });
    const newItem = { id: prod.id, name: prod.name };
    setProducts((prev) => [...prev, newItem]);
    setSelectedProductIds((prev) => [...prev, prod.id]);
  };

  const handleCreateSkill = async (name: string) => {
    if (!user) return;
    const sk = await createSkill({ user_id: user.id, name });
    const newItem = { id: sk.id, name: sk.name };
    setSkills((prev) => [...prev, newItem]);
    setSelectedSkillIds((prev) => [...prev, sk.id]);
  };

  const handleSave = async () => {
    try {
      await updateAgent(params.id, {
        name,
        system_prompt: systemPrompt,
        opening_remark: openingRemark,
        linked_product_ids: selectedProductIds,
        linked_skill_ids: selectedSkillIds,
        tag_ids: Array.from(selectedTagIds),
        match_intent_tag_ids: Array.from(selectedIntentIds),
      });
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

      <div className="w-full max-w-4xl bg-white p-6 rounded-lg shadow-md text-black space-y-5">
        <div>
          <label className="block font-bold mb-2">Agent Name</label>
          <input
            className="w-full p-2 border rounded"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div>
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

        <div>
          <label className="block font-bold mb-2">
            System Prompt (Persona)
          </label>
          <p className="text-sm text-gray-500 mb-2">
            This is the core instruction set for your AI agent. You can modify
            its personality, goals, and negotiation strategy here.
          </p>
          <textarea
            className="w-full h-96 p-2 border rounded font-mono text-sm"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
          />
        </div>

        {tagCategories.length > 0 && (
          <>
            <TagDropdownSelect
              categories={tagCategories}
              selectedTagIds={selectedIntentIds}
              onToggle={toggleIntentId}
              label="匹配意图 (Match Intent)"
              placeholder="搜索意图标签..."
              filterCategorySlugs={["intent"]}
              onCreateTag={handleCreateIntentTag}
            />
            <TagDropdownSelect
              categories={tagCategories}
              selectedTagIds={selectedTagIds}
              onToggle={toggleTagId}
              label="Tags (标签)"
              placeholder="搜索标签..."
              onCreateTag={handleCreateTag}
            />
          </>
        )}

        <MultiSelectWithCreate
          label="Linked Products"
          items={products}
          selectedIds={selectedProductIds}
          onToggle={(id) =>
            toggleId(id, selectedProductIds, setSelectedProductIds)
          }
          onCreate={handleCreateProduct}
          createPlaceholder="New product name"
        />

        <MultiSelectWithCreate
          label="Linked Skills"
          items={skills}
          selectedIds={selectedSkillIds}
          onToggle={(id) =>
            toggleId(id, selectedSkillIds, setSelectedSkillIds)
          }
          onCreate={handleCreateSkill}
          createPlaceholder="New skill name"
        />

        <div className="flex justify-end pt-4 border-t border-gray-100">
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
