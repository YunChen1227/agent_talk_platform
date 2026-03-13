"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  createAgent,
  listProducts,
  listSkills,
  createProduct,
  createSkill,
  getPlazaTags,
  PlazaTagCategory,
  PlazaTag,
} from "@/lib/api";

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
      <label className="block font-bold mb-2 text-gray-800">{label}</label>
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

function TagPicker({
  categories,
  selectedTagIds,
  onToggle,
  required,
}: {
  categories: PlazaTagCategory[];
  selectedTagIds: Set<string>;
  onToggle: (tagId: string) => void;
  required?: boolean;
}) {
  const [expandedParents, setExpandedParents] = useState<Set<string>>(
    new Set()
  );

  const toggleExpand = (parentId: string) => {
    setExpandedParents((prev) => {
      const next = new Set(prev);
      if (next.has(parentId)) next.delete(parentId);
      else next.add(parentId);
      return next;
    });
  };

  return (
    <div>
      <label className="block font-bold mb-2 text-gray-800">
        Tags (标签)
        {required && (
          <span className="text-red-500 ml-1">*</span>
        )}
        <span className="block text-sm font-normal text-gray-500">
          {required
            ? "请至少选择 1 个标签，用于在 Plaza 中被搜索和分类展示"
            : "可选标签，不选则由 AI 自动提取"}
        </span>
      </label>
      <div className="border border-gray-300 rounded-lg p-3 space-y-2.5 bg-gray-50">
        {categories.map((cat) => (
          <div key={cat.id} className="space-y-1.5">
            <div className="flex items-start gap-2">
              <span className="text-sm font-medium text-gray-500 min-w-[3.5rem] pt-0.5 text-right shrink-0">
                {cat.name}:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {cat.tags.map((tag) => {
                  const hasKids = tag.children.length > 0;
                  const isSelected = selectedTagIds.has(tag.id);
                  return (
                    <button
                      key={tag.id}
                      type="button"
                      onClick={() => {
                        onToggle(tag.id);
                        if (hasKids) toggleExpand(tag.id);
                      }}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                        isSelected
                          ? "bg-purple-600 text-white shadow-sm"
                          : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-100 hover:border-gray-400"
                      }`}
                    >
                      {tag.name}
                      {hasKids && !isSelected && (
                        <span className="ml-0.5 text-gray-400">+</span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
            {cat.tags
              .filter(
                (tag) =>
                  tag.children.length > 0 && expandedParents.has(tag.id)
              )
              .map((parent) => (
                <div
                  key={`children-${parent.id}`}
                  className="flex items-start gap-2 ml-2"
                >
                  <span className="text-xs text-gray-400 min-w-[3.5rem] pt-1 text-right shrink-0">
                    {parent.name}
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {parent.children.map((child) => (
                      <button
                        key={child.id}
                        type="button"
                        onClick={() => onToggle(child.id)}
                        className={`px-2.5 py-0.5 rounded-full text-xs font-medium transition-colors ${
                          selectedTagIds.has(child.id)
                            ? "bg-purple-500 text-white shadow-sm"
                            : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-100 hover:border-gray-300"
                        }`}
                      >
                        {child.name}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        ))}
      </div>
      {required && selectedTagIds.size === 0 && (
        <p className="text-xs text-red-500 mt-1">请至少选择一个标签</p>
      )}
    </div>
  );
}

export default function CreateAgentPage() {
  const [user, setUser] = useState<any>(null);
  const [agentName, setAgentName] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [openingRemark, setOpeningRemark] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const [products, setProducts] = useState<Item[]>([]);
  const [skills, setSkills] = useState<Item[]>([]);
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([]);
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);

  const [tagCategories, setTagCategories] = useState<PlazaTagCategory[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<Set<string>>(new Set());

  const isPaidUser = false;

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (!storedUser) {
      router.push("/login");
      return;
    }
    const u = JSON.parse(storedUser);
    setUser(u);
    loadItems(u.id);
  }, [router]);

  useEffect(() => {
    getPlazaTags()
      .then(setTagCategories)
      .catch(() => setTagCategories([]));
  }, []);

  const loadItems = async (userId: string) => {
    try {
      const [prods, sklls] = await Promise.all([
        listProducts(userId),
        listSkills(userId),
      ]);
      setProducts(prods.map((p: any) => ({ id: p.id, name: p.name })));
      setSkills(sklls.map((s: any) => ({ id: s.id, name: s.name })));
    } catch {
      /* ignore load errors */
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

  const handleCreate = async () => {
    if (!user || !agentName.trim()) return;
    if (!isPaidUser && selectedTagIds.size === 0) return;
    setIsSubmitting(true);
    try {
      const tagIdArr =
        selectedTagIds.size > 0 ? Array.from(selectedTagIds) : undefined;
      await createAgent(
        user.id,
        agentName.trim(),
        isPaidUser ? description : undefined,
        !isPaidUser ? systemPrompt : undefined,
        !isPaidUser ? openingRemark : undefined,
        selectedProductIds.length > 0 ? selectedProductIds : undefined,
        selectedSkillIds.length > 0 ? selectedSkillIds : undefined,
        tagIdArr
      );
      router.push("/");
    } catch (e) {
      alert("Error creating agent");
      setIsSubmitting(false);
    }
  };

  const isFormValid = isPaidUser
    ? agentName.trim() && description.trim()
    : agentName.trim() &&
      systemPrompt.trim() &&
      openingRemark.trim() &&
      selectedTagIds.size > 0;

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
          {isPaidUser
            ? "Paid Tier: AI Auto-Generation"
            : "Free Tier: Manual Configuration"}
        </p>
      </div>

      <div className="w-full max-w-4xl bg-white p-6 rounded-lg shadow-md space-y-6">
        <div>
          <label className="block font-bold mb-2 text-gray-800">
            Agent Name
          </label>
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
                Describe personality, preferences, needs, and speaking style.
                Our AI will generate the rest.
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
                  The first message your agent will send to start the
                  conversation.
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

        {tagCategories.length > 0 && (
          <TagPicker
            categories={tagCategories}
            selectedTagIds={selectedTagIds}
            onToggle={toggleTagId}
            required={!isPaidUser}
          />
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

        <div className="flex gap-3 pt-4 border-t border-gray-100">
          <button
            className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            onClick={handleCreate}
            disabled={!isFormValid || isSubmitting}
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
