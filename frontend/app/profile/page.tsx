"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { listMedia, uploadMedia, deleteMedia, setAvatar, API_URL } from "@/lib/api";

export default function ProfilePage() {
  const [user, setUser] = useState<any>(null);
  const [media, setMedia] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const router = useRouter();

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
    listMedia(user.id).then(setMedia).catch(console.error);
  }, [user?.id]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user) return;
    setUploading(true);
    try {
      await uploadMedia(user.id, file);
      const list = await listMedia(user.id);
      setMedia(list);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleSetAvatar = async (mediaId: string) => {
    if (!user) return;
    try {
      await setAvatar(user.id, mediaId);
      const u = { ...user, avatar_url: `/media/${mediaId}/file` };
      localStorage.setItem("user", JSON.stringify(u));
      setUser(u);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to set avatar");
    }
  };

  const handleDelete = async (mediaId: string) => {
    if (!user || !confirm("Delete this file?")) return;
    try {
      await deleteMedia(mediaId, user.id);
      setMedia((prev) => prev.filter((m) => m.id !== mediaId));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Delete failed");
    }
  };

  if (!user) return null;

  return (
    <main className="flex min-h-screen flex-col items-center p-8 bg-gray-100">
      <div className="w-full max-w-4xl flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-black">Profile & Media</h1>
        <Link href="/" className="text-blue-600 hover:underline">Back to Dashboard</Link>
      </div>
      <Link href="/shop" className="block w-full max-w-4xl mb-6 bg-white rounded-lg shadow p-6 border-2 border-transparent hover:border-purple-400 hover:shadow-md transition-all group">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🛍</span>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 group-hover:text-purple-700 transition-colors">My Shop</h2>
              <p className="text-sm text-gray-500">Manage your products, set prices, and link them to agents</p>
            </div>
          </div>
          <span className="text-gray-400 group-hover:text-purple-600 text-xl transition-colors">→</span>
        </div>
      </Link>
      <div className="w-full max-w-4xl bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Avatar</h2>
        {user.avatar_url && (
          <img src={API_URL + user.avatar_url} alt="Avatar" className="w-20 h-20 rounded-full object-cover border mb-2" />
        )}
        <p className="text-sm text-gray-600 mb-4">Set avatar by clicking &quot;Set as avatar&quot; on an image below.</p>
      </div>
      <div className="w-full max-w-4xl bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">My Media</h2>
        <label className="inline-block bg-blue-600 text-white px-4 py-2 rounded cursor-pointer hover:bg-blue-700 mb-4">
          {uploading ? "Uploading..." : "Upload photo/video"}
          <input type="file" accept="image/*,video/*" className="hidden" onChange={handleUpload} disabled={uploading} />
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {media.map((m) => (
            <div key={m.id} className="border rounded p-2">
              {m.file_type === "image" ? (
                <img src={API_URL + (m.url || `/media/${m.id}/file`)} alt={m.original_filename} className="w-full h-24 object-cover rounded" />
              ) : (
                <div className="w-full h-24 bg-gray-200 rounded flex items-center justify-center text-sm">Video</div>
              )}
              <p className="text-xs truncate mt-1">{m.original_filename}</p>
              <div className="flex gap-1 mt-2">
                {m.file_type === "image" && (
                  <button type="button" onClick={() => handleSetAvatar(m.id)} className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">Set as avatar</button>
                )}
                <button type="button" onClick={() => handleDelete(m.id)} className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded">Delete</button>
              </div>
            </div>
          ))}
        </div>
        {media.length === 0 && <p className="text-gray-500">No media yet. Upload a photo or video.</p>}
      </div>
    </main>
  );
}
