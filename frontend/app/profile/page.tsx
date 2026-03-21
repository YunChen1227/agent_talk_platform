"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  listMedia,
  uploadMedia,
  deleteMedia,
  setAvatar,
  getUserProfile,
  updateUserProfile,
  getUserPreferences,
  updateUserPreferences,
  getPlazaTags,
  API_URL,
  UserProfile,
  UserPreferences,
  PlazaTagCategory,
} from "@/lib/api";

const GENDER_OPTIONS = [
  { value: "", label: "未设置" },
  { value: "male", label: "男" },
  { value: "female", label: "女" },
  { value: "other", label: "其他" },
  { value: "prefer_not_to_say", label: "不愿透露" },
];

function TagInput({
  tags,
  onChange,
  placeholder,
}: {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder: string;
}) {
  const [input, setInput] = useState("");

  const addTag = () => {
    const trimmed = input.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed]);
    }
    setInput("");
  };

  return (
    <div className="flex flex-wrap gap-1.5 items-center">
      {tags.map((tag) => (
        <span
          key={tag}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 text-sm border border-purple-100"
        >
          {tag}
          <button
            type="button"
            onClick={() => onChange(tags.filter((t) => t !== tag))}
            className="text-purple-400 hover:text-purple-700 leading-none"
          >
            &times;
          </button>
        </span>
      ))}
      <div className="inline-flex items-center gap-1">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addTag();
            }
          }}
          placeholder={placeholder}
          className="border border-gray-300 rounded-lg px-2.5 py-1 text-sm w-28 focus:ring-2 focus:ring-purple-300 focus:border-transparent outline-none"
        />
        <button
          type="button"
          onClick={addTag}
          className="text-sm px-2 py-1 rounded-lg bg-purple-100 text-purple-700 hover:bg-purple-200"
        >
          +
        </button>
      </div>
    </div>
  );
}

type PrefState = "neutral" | "like" | "dislike";

function PreferenceTagButton({
  name,
  state,
  onClick,
}: {
  name: string;
  state: PrefState;
  onClick: () => void;
}) {
  const base = "px-3 py-1 rounded-full text-sm font-medium transition-colors border cursor-pointer select-none";
  const styles: Record<PrefState, string> = {
    neutral: "bg-white border-gray-300 text-gray-700 hover:bg-gray-50",
    like: "bg-green-100 border-green-400 text-green-800",
    dislike: "bg-red-100 border-red-400 text-red-800 line-through",
  };
  const icons: Record<PrefState, string> = {
    neutral: "",
    like: " \u2764",
    dislike: " \u2717",
  };

  return (
    <button type="button" onClick={onClick} className={`${base} ${styles[state]}`}>
      {name}{icons[state]}
    </button>
  );
}

export default function ProfilePage() {
  const [user, setUser] = useState<any>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [media, setMedia] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savingPrefs, setSavingPrefs] = useState(false);

  // Profile form state
  const [displayName, setDisplayName] = useState("");
  const [gender, setGender] = useState("");
  const [birthday, setBirthday] = useState("");
  const [location, setLocation] = useState("");
  const [bio, setBio] = useState("");
  const [personality, setPersonality] = useState<string[]>([]);
  const [hobbies, setHobbies] = useState<string[]>([]);
  const [occupation, setOccupation] = useState("");
  const [website, setWebsite] = useState("");

  // Tag preferences
  const [tagCategories, setTagCategories] = useState<PlazaTagCategory[]>([]);
  const [likedTagIds, setLikedTagIds] = useState<Set<string>>(new Set());
  const [dislikedTagIds, setDislikedTagIds] = useState<Set<string>>(new Set());
  const [expandedParentIds, setExpandedParentIds] = useState<Set<string>>(new Set());

  const router = useRouter();

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (!stored) {
      router.push("/login");
      return;
    }
    setUser(JSON.parse(stored));
  }, [router]);

  const loadProfile = useCallback(async (userId: string) => {
    try {
      const p = await getUserProfile(userId);
      setProfile(p);
      setDisplayName(p.display_name || "");
      setGender(p.gender || "");
      setBirthday(p.birthday || "");
      setLocation(p.location || "");
      setBio(p.bio || "");
      setPersonality(p.personality || []);
      setHobbies(p.hobbies || []);
      setOccupation(p.occupation || "");
      setWebsite(p.website || "");
    } catch {
      // Profile endpoint may return 404 for fresh users -- that's OK
    }
  }, []);

  const loadPreferences = useCallback(async (userId: string) => {
    try {
      const prefs = await getUserPreferences(userId);
      setLikedTagIds(new Set(prefs.liked_tag_ids));
      setDislikedTagIds(new Set(prefs.disliked_tag_ids));
    } catch {
      // No prefs yet
    }
  }, []);

  useEffect(() => {
    if (!user?.id) return;
    loadProfile(user.id);
    listMedia(user.id).then(setMedia).catch(console.error);
    loadPreferences(user.id);
    getPlazaTags().then(setTagCategories).catch(() => setTagCategories([]));
  }, [user?.id, loadProfile, loadPreferences]);

  const handleSaveProfile = async () => {
    if (!user) return;
    setSaving(true);
    try {
      const updated = await updateUserProfile(user.id, {
        display_name: displayName || null,
        gender: gender || null,
        birthday: birthday || null,
        location: location || null,
        bio: bio || null,
        personality: personality.length > 0 ? personality : null,
        hobbies: hobbies.length > 0 ? hobbies : null,
        occupation: occupation || null,
        website: website || null,
      });
      setProfile(updated);
      // Sync avatar_url / display_name back to localStorage
      const storedUser = JSON.parse(localStorage.getItem("user") || "{}");
      storedUser.avatar_url = updated.avatar_url;
      storedUser.display_name = updated.display_name;
      localStorage.setItem("user", JSON.stringify(storedUser));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleSavePreferences = async () => {
    if (!user) return;
    setSavingPrefs(true);
    try {
      await updateUserPreferences(
        user.id,
        Array.from(likedTagIds),
        Array.from(dislikedTagIds)
      );
    } catch (err: any) {
      alert(err.response?.data?.detail || "Save preferences failed");
    } finally {
      setSavingPrefs(false);
    }
  };

  const cycleTagPref = (tagId: string) => {
    if (likedTagIds.has(tagId)) {
      // like -> dislike
      setLikedTagIds((prev) => { const n = new Set(prev); n.delete(tagId); return n; });
      setDislikedTagIds((prev) => new Set(prev).add(tagId));
    } else if (dislikedTagIds.has(tagId)) {
      // dislike -> neutral
      setDislikedTagIds((prev) => { const n = new Set(prev); n.delete(tagId); return n; });
    } else {
      // neutral -> like
      setLikedTagIds((prev) => new Set(prev).add(tagId));
    }
  };

  const getTagPrefState = (tagId: string): PrefState => {
    if (likedTagIds.has(tagId)) return "like";
    if (dislikedTagIds.has(tagId)) return "dislike";
    return "neutral";
  };

  const toggleExpand = (parentId: string) => {
    setExpandedParentIds((prev) => {
      const n = new Set(prev);
      if (n.has(parentId)) n.delete(parentId);
      else n.add(parentId);
      return n;
    });
  };

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

  const handleDelete = async (mediaId: string) => {
    if (!user || !confirm("Delete this file?")) return;
    try {
      await deleteMedia(mediaId, user.id);
      setMedia((prev) => prev.filter((m) => m.id !== mediaId));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Delete failed");
    }
  };

  const handleSetAvatar = async (mediaId: string) => {
    if (!user) return;
    try {
      const result = await setAvatar(user.id, mediaId);
      const storedUser = JSON.parse(localStorage.getItem("user") || "{}");
      storedUser.avatar_url = result.avatar_url;
      localStorage.setItem("user", JSON.stringify(storedUser));
      setUser({ ...user, avatar_url: result.avatar_url });
      if (profile) setProfile({ ...profile, avatar_url: result.avatar_url });
    } catch (err: any) {
      alert(err.response?.data?.detail || "Set avatar failed");
    }
  };

  if (!user) return null;

  return (
    <main className="flex min-h-screen flex-col items-center p-8 bg-gray-100">
      <div className="w-full max-w-4xl flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-black">Profile</h1>
        <Link href="/" className="text-blue-600 hover:underline">
          Back to Dashboard
        </Link>
      </div>

      {/* Header Card: Avatar + Name */}
      <div className="w-full max-w-4xl bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center gap-5">
          <div className="shrink-0">
            {(profile?.avatar_url || user.avatar_url) ? (
              <img
                src={API_URL + (profile?.avatar_url || user.avatar_url)}
                alt="Avatar"
                className="w-20 h-20 rounded-full object-cover border-2 border-purple-200"
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-purple-100 flex items-center justify-center text-3xl text-purple-400">
                {(displayName || user.username || "?").charAt(0).toUpperCase()}
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-bold text-gray-900 truncate">
              {displayName || user.username}
            </h2>
            <p className="text-sm text-gray-500">@{user.username}</p>
            {bio && <p className="text-sm text-gray-600 mt-1 line-clamp-2">{bio}</p>}
          </div>
        </div>
      </div>

      {/* Basic Info Card */}
      <div className="w-full max-w-4xl bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-900">基本信息</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">昵称</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="设置昵称"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-300 focus:border-transparent outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">性别</label>
            <select
              value={gender}
              onChange={(e) => setGender(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-300 focus:border-transparent outline-none bg-white"
            >
              {GENDER_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">生日</label>
            <input
              type="date"
              value={birthday}
              onChange={(e) => setBirthday(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-300 focus:border-transparent outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">所在地</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="城市或地区"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-300 focus:border-transparent outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">职业</label>
            <input
              type="text"
              value={occupation}
              onChange={(e) => setOccupation(e.target.value)}
              placeholder="你的职业"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-300 focus:border-transparent outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">个人网站</label>
            <input
              type="url"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="https://"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-300 focus:border-transparent outline-none"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">个人简介</label>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="介绍一下自己..."
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-300 focus:border-transparent outline-none resize-none"
            />
          </div>
        </div>
      </div>

      {/* Personality & Hobbies Card */}
      <div className="w-full max-w-4xl bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-900">性格 & 兴趣</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">性格标签</label>
            <TagInput tags={personality} onChange={setPersonality} placeholder="添加性格..." />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">兴趣爱好</label>
            <TagInput tags={hobbies} onChange={setHobbies} placeholder="添加爱好..." />
          </div>
        </div>
      </div>

      {/* Save Profile Button */}
      <div className="w-full max-w-4xl mb-6 flex justify-end">
        <button
          type="button"
          onClick={handleSaveProfile}
          disabled={saving}
          className="px-6 py-2.5 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50"
        >
          {saving ? "保存中..." : "保存个人信息"}
        </button>
      </div>

      {/* Tag Preferences Card */}
      <div className="w-full max-w-4xl bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-2 text-gray-900">Agent 标签偏好</h2>
        <p className="text-sm text-gray-500 mb-4">
          点击切换标签状态：<span className="text-green-700 font-medium">喜欢</span>{" "}
          → <span className="text-red-700 font-medium line-through">不喜欢</span>{" "}
          → 中立。喜欢的标签在广场优先展示，不喜欢的标签会被过滤。
        </p>

        {tagCategories.length === 0 ? (
          <p className="text-gray-400 text-sm">暂无标签分类</p>
        ) : (
          <div className="space-y-4">
            {tagCategories.map((cat) => (
              <div key={cat.id} className="space-y-2">
                <div className="flex items-start gap-2">
                  <span className="text-sm font-medium text-gray-500 min-w-[4rem] pt-1 text-right shrink-0">
                    {cat.name}:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {cat.tags.map((tag) => (
                      <div key={tag.id} className="inline-flex flex-col">
                        <PreferenceTagButton
                          name={tag.name}
                          state={getTagPrefState(tag.id)}
                          onClick={() => {
                            cycleTagPref(tag.id);
                            if (tag.children.length > 0) toggleExpand(tag.id);
                          }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
                {cat.tags
                  .filter((tag) => tag.children.length > 0 && expandedParentIds.has(tag.id))
                  .map((parent) => (
                    <div key={`children-${parent.id}`} className="flex items-start gap-2 ml-4">
                      <span className="text-xs text-gray-400 min-w-[4rem] pt-1.5 text-right shrink-0">
                        {parent.name}
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {parent.children.map((child) => (
                          <PreferenceTagButton
                            key={child.id}
                            name={child.name}
                            state={getTagPrefState(child.id)}
                            onClick={() => cycleTagPref(child.id)}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            ))}
          </div>
        )}

        {/* Preference summary */}
        {(likedTagIds.size > 0 || dislikedTagIds.size > 0) && (
          <div className="mt-4 pt-4 border-t border-gray-100 flex gap-6 text-sm">
            {likedTagIds.size > 0 && (
              <span className="text-green-700">
                {likedTagIds.size} 个喜欢
              </span>
            )}
            {dislikedTagIds.size > 0 && (
              <span className="text-red-700">
                {dislikedTagIds.size} 个不喜欢
              </span>
            )}
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={handleSavePreferences}
            disabled={savingPrefs}
            className="px-6 py-2.5 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            {savingPrefs ? "保存中..." : "保存标签偏好"}
          </button>
        </div>
      </div>

      {/* My Shop Card */}
      <Link
        href="/shop"
        className="block w-full max-w-4xl mb-6 bg-white rounded-lg shadow p-6 border-2 border-transparent hover:border-purple-400 hover:shadow-md transition-all group"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🛍</span>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 group-hover:text-purple-700 transition-colors">
                My Shop
              </h2>
              <p className="text-sm text-gray-500">
                Manage your products, set prices, and link them to agents
              </p>
            </div>
          </div>
          <span className="text-gray-400 group-hover:text-purple-600 text-xl transition-colors">
            →
          </span>
        </div>
      </Link>

      {/* My Media Card */}
      <div className="w-full max-w-4xl bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">My Media</h2>
        <label className="inline-block bg-blue-600 text-white px-4 py-2 rounded cursor-pointer hover:bg-blue-700 mb-4">
          {uploading ? "Uploading..." : "Upload photo/video"}
          <input
            type="file"
            accept="image/*,video/*"
            className="hidden"
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {media.map((m) => (
            <div key={m.id} className="border rounded p-2">
              {m.file_type === "image" ? (
                <img
                  src={API_URL + (m.url || `/media/${m.id}/file`)}
                  alt={m.original_filename}
                  className="w-full h-24 object-cover rounded"
                />
              ) : (
                <div className="w-full h-24 bg-gray-200 rounded flex items-center justify-center text-sm">
                  Video
                </div>
              )}
              <p className="text-xs truncate mt-1">{m.original_filename}</p>
              <div className="flex gap-1 mt-2">
                {m.file_type === "image" && (
                  <button
                    type="button"
                    onClick={() => handleSetAvatar(m.id)}
                    className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded"
                  >
                    Set as avatar
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => handleDelete(m.id)}
                  className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
        {media.length === 0 && (
          <p className="text-gray-500">No media yet. Upload a photo or video.</p>
        )}
      </div>
    </main>
  );
}
