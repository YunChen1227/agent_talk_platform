"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { listProducts, createProduct, updateProduct, deleteProduct, getShopTags, createShopTag, PlazaTagCategory } from "@/lib/api";
import TagDropdownSelect from "@/components/TagDropdownSelect";
import { useDraft } from "@/lib/useDraft";

const DRAFT_KEY_PRODUCT_CREATE = "draft:product:create";

export default function ShopPage() {
  const [user, setUser] = useState<any>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [tagCategories, setTagCategories] = useState<PlazaTagCategory[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<Set<string>>(new Set());
  const router = useRouter();
  const draftRestored = useRef(false);

  const draftState = {
    name,
    description,
    price,
    selectedTagIds: Array.from(selectedTagIds),
  };
  const draftEnabled = showForm && !editingId;
  const { draft, clearDraft, hasDraft } = useDraft(
    DRAFT_KEY_PRODUCT_CREATE,
    draftState,
    draftEnabled,
    user?.id
  );

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (!stored) {
      router.push("/login");
      return;
    }
    setUser(JSON.parse(stored));
  }, [router]);

  useEffect(() => {
    if (!user?.id) return;
    listProducts(user.id).then(setProducts).catch(console.error);
  }, [user?.id]);

  useEffect(() => {
    getShopTags().then(setTagCategories).catch(() => setTagCategories([]));
  }, []);

  useEffect(() => {
    if (!draftRestored.current && hasDraft && draft && user) {
      draftRestored.current = true;
      const d = draft as { name?: string; description?: string; price?: string; selectedTagIds?: string[] };
      if (typeof d.name === "string") setName(d.name);
      if (typeof d.description === "string") setDescription(d.description);
      if (typeof d.price === "string") setPrice(d.price);
      if (Array.isArray(d.selectedTagIds)) setSelectedTagIds(new Set(d.selectedTagIds));
      setShowForm(true);
      setEditingId(null);
    }
  }, [hasDraft, draft, user]);

  const resetForm = () => {
    setName("");
    setDescription("");
    setPrice("");
    setSelectedTagIds(new Set());
    setEditingId(null);
    setShowForm(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !name || !price) return;
    setSubmitting(true);
    try {
      await createProduct({
        user_id: user.id,
        name,
        description: description || undefined,
        price: parseFloat(price) || 0,
        currency: "CNY",
        tag_ids: selectedTagIds.size > 0 ? Array.from(selectedTagIds) : undefined,
      });
      clearDraft();
      resetForm();
      const list = await listProducts(user.id);
      setProducts(list);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to create product");
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartEdit = (p: any) => {
    setEditingId(p.id);
    setName(p.name || "");
    setDescription(p.description || "");
    setPrice(String(p.price ?? ""));
    setSelectedTagIds(new Set(p.tag_ids || []));
    setShowForm(true);
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !editingId || !name || !price) return;
    setSubmitting(true);
    try {
      await updateProduct(editingId, user.id, {
        name,
        description: description || undefined,
        price: parseFloat(price) || 0,
        tag_ids: Array.from(selectedTagIds),
      });
      clearDraft();
      resetForm();
      const list = await listProducts(user.id);
      setProducts(list);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to update product");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (productId: string) => {
    if (!user || !confirm("Delete this product?")) return;
    try {
      await deleteProduct(productId, user.id);
      setProducts((prev) => prev.filter((p) => p.id !== productId));
      if (editingId === productId) resetForm();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Delete failed");
    }
  };

  const toggleTagId = (tagId: string) => {
    setSelectedTagIds((prev) => {
      const next = new Set(prev);
      if (next.has(tagId)) next.delete(tagId);
      else next.add(tagId);
      return next;
    });
  };

  const handleCreateTag = async (name: string, categoryId: string) => {
    try {
      const newTag = await createShopTag(name, categoryId);
      const cats = await getShopTags();
      setTagCategories(cats);
      setSelectedTagIds((prev) => new Set([...prev, newTag.id]));
    } catch {
      alert("Failed to create tag");
    }
  };

  const handleCancelForm = () => {
    clearDraft();
    resetForm();
  };

  const handleNewClick = () => {
    if (editingId) resetForm();
    setShowForm(true);
    setEditingId(null);
  };

  if (!user) return null;

  const isEditing = editingId !== null;

  return (
    <main className="flex min-h-screen flex-col items-center p-8 bg-gray-100">
      <div className="w-full max-w-4xl flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => router.back()}
            className="text-blue-500 hover:underline flex items-center gap-1"
          >
            <span>&larr;</span>
            <span>Back</span>
          </button>
          <h1 className="text-2xl font-bold text-black">My Shop</h1>
        </div>
        <div className="flex gap-4 items-center">
          <button
            type="button"
            onClick={showForm ? handleCancelForm : handleNewClick}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
          >
            {showForm ? "Cancel" : "+ New product"}
          </button>
        </div>
      </div>

      {showForm ? (
        <div className="w-full max-w-4xl bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">
            {isEditing ? "Edit product" : "Create product"}
          </h2>
          <form onSubmit={isEditing ? handleUpdate : handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 block w-full border rounded px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="mt-1 block w-full border rounded px-3 py-2"
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Price (CNY)</label>
              <input
                type="number"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="mt-1 block w-full border rounded px-3 py-2"
                required
              />
            </div>
            {tagCategories.length > 0 && (
              <TagDropdownSelect
                categories={tagCategories}
                selectedTagIds={selectedTagIds}
                onToggle={toggleTagId}
                label="Tags (标签)"
                placeholder="搜索商品标签..."
                filterCategorySlugs={["category", "condition", "product_type", "target"]}
                onCreateTag={handleCreateTag}
              />
            )}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={submitting}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting
                  ? (isEditing ? "Saving..." : "Creating...")
                  : (isEditing ? "Save Changes" : "Create")}
              </button>
              <button
                type="button"
                onClick={handleCancelForm}
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300"
              >
                {isEditing ? "Cancel Edit" : "Cancel"}
              </button>
            </div>
          </form>
        </div>
      ) : (

      <div className="w-full max-w-4xl">
        <h2 className="text-lg font-semibold mb-4">Your products</h2>
        {products.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-6 text-gray-500">No products. Create one to get started.</div>
        ) : (
          <div className="grid gap-4">
            {products.map((p) => (
              <div
                key={p.id}
                className={`bg-white rounded-lg shadow p-4 flex justify-between items-center ${
                  editingId === p.id ? "ring-2 ring-blue-400" : ""
                }`}
              >
                <div>
                  <p className="font-medium text-gray-900">{p.name}</p>
                  {p.description && <p className="text-sm text-gray-600">{p.description}</p>}
                  <p className="text-sm text-gray-500">{p.price} {p.currency} · Status: {p.status}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => handleStartEdit(p)}
                    className="bg-blue-100 text-blue-700 px-3 py-1 rounded text-sm hover:bg-blue-200"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(p.id)}
                    className="bg-red-100 text-red-700 px-3 py-1 rounded text-sm hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      )}
    </main>
  );
}
