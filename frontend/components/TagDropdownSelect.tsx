"use client";
import { useState, useEffect, useRef, useMemo } from "react";
import { PlazaTagCategory, PlazaTag } from "@/lib/api";

interface FlatTag {
  id: string;
  name: string;
  categoryName: string;
  categoryId: string;
  parentId?: string;
  parentName?: string;
  depth: number;
  hasChildren: boolean;
}

function buildFlatList(
  categories: PlazaTagCategory[],
  filterCategorySlugs?: string[]
): FlatTag[] {
  const displayed = filterCategorySlugs
    ? categories.filter((c) => filterCategorySlugs.includes(c.slug))
    : categories;

  const result: FlatTag[] = [];
  for (const cat of displayed) {
    for (const tag of cat.tags) {
      result.push({
        id: tag.id,
        name: tag.name,
        categoryName: cat.name,
        categoryId: cat.id,
        depth: 0,
        hasChildren: tag.children.length > 0,
      });
      for (const child of tag.children) {
        result.push({
          id: child.id,
          name: child.name,
          categoryName: cat.name,
          categoryId: cat.id,
          parentId: tag.id,
          parentName: tag.name,
          depth: 1,
          hasChildren: child.children.length > 0,
        });
        for (const grandchild of child.children) {
          result.push({
            id: grandchild.id,
            name: grandchild.name,
            categoryName: cat.name,
            categoryId: cat.id,
            parentId: child.id,
            parentName: child.name,
            depth: 2,
            hasChildren: false,
          });
        }
      }
    }
  }
  return result;
}

export default function TagDropdownSelect({
  categories,
  selectedTagIds,
  onToggle,
  label,
  required,
  placeholder = "搜索标签...",
  filterCategorySlugs,
  onCreateTag,
}: {
  categories: PlazaTagCategory[];
  selectedTagIds: Set<string>;
  onToggle: (tagId: string) => void;
  label: string;
  required?: boolean;
  placeholder?: string;
  filterCategorySlugs?: string[];
  onCreateTag?: (name: string, categoryId: string) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const allTags = useMemo(
    () => buildFlatList(categories, filterCategorySlugs),
    [categories, filterCategorySlugs]
  );

  const displayedCategories = useMemo(
    () =>
      filterCategorySlugs
        ? categories.filter((c) => filterCategorySlugs.includes(c.slug))
        : categories,
    [categories, filterCategorySlugs]
  );

  const defaultCategoryId = displayedCategories[0]?.id;

  const isSearching = search.trim().length > 0;
  const searchLower = search.trim().toLowerCase();

  const searchResults = useMemo(() => {
    if (!isSearching) return [];
    return allTags.filter((t) => t.name.toLowerCase().includes(searchLower));
  }, [allTags, isSearching, searchLower]);

  const hasExactMatch = useMemo(() => {
    if (!isSearching) return true;
    return allTags.some((t) => t.name.toLowerCase() === searchLower);
  }, [allTags, isSearching, searchLower]);

  const selectedTags = useMemo(
    () => allTags.filter((t) => selectedTagIds.has(t.id)),
    [allTags, selectedTagIds]
  );

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleCreate = async () => {
    if (!search.trim() || !onCreateTag || !defaultCategoryId || creating)
      return;
    setCreating(true);
    try {
      await onCreateTag(search.trim(), defaultCategoryId);
      setSearch("");
    } finally {
      setCreating(false);
    }
  };

  const depthPadding = (depth: number) => {
    if (depth === 0) return "0.75rem";
    if (depth === 1) return "2rem";
    return "3.25rem";
  };

  const renderTagRow = (tag: FlatTag) => {
    const isSelected = selectedTagIds.has(tag.id);
    return (
      <div
        key={tag.id}
        className={`py-2 cursor-pointer hover:bg-gray-50 flex items-center gap-2 text-sm ${
          isSelected ? "bg-purple-50" : ""
        }`}
        style={{ paddingLeft: depthPadding(tag.depth), paddingRight: "0.75rem" }}
        onClick={() => onToggle(tag.id)}
      >
        <input
          type="checkbox"
          checked={isSelected}
          readOnly
          className="rounded text-purple-600 shrink-0"
        />
        <span className={`${tag.depth === 0 ? "font-medium text-gray-800" : "text-gray-700"}`}>
          {tag.name}
        </span>
        {tag.hasChildren && (
          <svg
            className={`w-3.5 h-3.5 ml-auto text-gray-400 transition-transform ${
              isSelected ? "rotate-90" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        )}
      </div>
    );
  };

  const renderCascadeView = () => {
    return displayedCategories.map((cat) => {
      const l1Tags = allTags.filter(
        (t) => t.categoryId === cat.id && t.depth === 0
      );
      if (l1Tags.length === 0) return null;

      return (
        <div key={cat.id}>
          <div className="px-3 py-1.5 text-xs font-semibold text-gray-400 uppercase bg-gray-50 sticky top-0 z-10">
            {cat.name}
          </div>
          {l1Tags.map((l1) => {
            const l1Selected = selectedTagIds.has(l1.id);
            const l2Children = allTags.filter(
              (t) => t.parentId === l1.id && t.depth === 1
            );

            return (
              <div key={l1.id}>
                {renderTagRow(l1)}
                {l1Selected &&
                  l2Children.map((l2) => {
                    const l2Selected = selectedTagIds.has(l2.id);
                    const l3Children = allTags.filter(
                      (t) => t.parentId === l2.id && t.depth === 2
                    );

                    return (
                      <div key={l2.id}>
                        {renderTagRow(l2)}
                        {l2Selected && l3Children.map((l3) => renderTagRow(l3))}
                      </div>
                    );
                  })}
              </div>
            );
          })}
        </div>
      );
    });
  };

  const renderSearchView = () => {
    const grouped = new Map<string, FlatTag[]>();
    for (const t of searchResults) {
      if (!grouped.has(t.categoryName)) grouped.set(t.categoryName, []);
      grouped.get(t.categoryName)!.push(t);
    }

    return (
      <>
        {searchResults.length === 0 && (
          <div className="px-3 py-2 text-sm text-gray-400">
            没有匹配的标签
          </div>
        )}
        {displayedCategories.map((cat) => {
          const tags = grouped.get(cat.name);
          if (!tags) return null;
          return (
            <div key={cat.id}>
              <div className="px-3 py-1.5 text-xs font-semibold text-gray-400 uppercase bg-gray-50 sticky top-0 z-10">
                {cat.name}
              </div>
              {tags.map((tag) => {
                const isSelected = selectedTagIds.has(tag.id);
                return (
                  <div
                    key={tag.id}
                    className={`px-3 py-2 cursor-pointer hover:bg-gray-50 flex items-center gap-2 text-sm ${
                      isSelected ? "bg-purple-50" : ""
                    }`}
                    onClick={() => onToggle(tag.id)}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      readOnly
                      className="rounded text-purple-600 shrink-0"
                    />
                    <span className="text-gray-800">{tag.name}</span>
                    {tag.parentName && (
                      <span className="text-xs text-gray-400 ml-auto">
                        {tag.parentName}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          );
        })}
      </>
    );
  };

  return (
    <div ref={ref} className="relative">
      <label className="block font-bold mb-2 text-gray-800">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      <div
        className="w-full min-h-[44px] p-2 border border-gray-300 rounded-lg cursor-pointer flex items-center gap-2 focus-within:ring-2 focus-within:ring-blue-500"
        onClick={() => {
          setOpen((v) => !v);
          if (!open) setTimeout(() => inputRef.current?.focus(), 0);
        }}
      >
        {onCreateTag ? (
          <svg
            className="w-4 h-4 text-gray-400 shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        ) : null}
        {!onCreateTag && selectedTags.length > 0 && !open ? (
          <div className="flex-1 flex flex-wrap gap-1">
            {selectedTags.map((tag) => (
              <span
                key={tag.id}
                className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  tag.depth === 0
                    ? "bg-purple-100 text-purple-800"
                    : "bg-indigo-50 text-indigo-700"
                }`}
              >
                {tag.name}
              </span>
            ))}
          </div>
        ) : (
          <input
            ref={inputRef}
            type="text"
            className="flex-1 outline-none text-sm text-black bg-transparent"
            placeholder={!onCreateTag && selectedTags.length > 0 ? "筛选标签..." : placeholder}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              if (!open) setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                setOpen(false);
                setSearch("");
              }
            }}
          />
        )}
        <svg
          className={`w-4 h-4 text-gray-400 shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </div>

      {selectedTags.length > 0 && (onCreateTag || open) && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {selectedTags.map((tag) => (
            <span
              key={tag.id}
              className={`text-xs font-medium px-2.5 py-1 rounded-full flex items-center gap-1 ${
                tag.depth === 0
                  ? "bg-purple-100 text-purple-800"
                  : "bg-indigo-50 text-indigo-700"
              }`}
            >
              {tag.depth > 0 && (
                <span className="text-[10px] opacity-60">{tag.parentName} ›</span>
              )}
              {tag.name}
              <button
                type="button"
                onClick={() => onToggle(tag.id)}
                className="hover:opacity-70 ml-0.5"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {required && selectedTagIds.size === 0 && (
        <p className="text-xs text-red-500 mt-1">请至少选择一个一级标签</p>
      )}

      {open && (
        <div className="absolute z-30 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-y-auto">
          {isSearching ? renderSearchView() : renderCascadeView()}

          {isSearching && !hasExactMatch && onCreateTag && defaultCategoryId && (
            <div className="border-t border-gray-100">
              <div
                className="px-3 py-2.5 cursor-pointer hover:bg-gray-50 flex items-center gap-2 text-sm text-purple-600 font-medium"
                onClick={(e) => {
                  e.stopPropagation();
                  handleCreate();
                }}
              >
                <span className="text-lg leading-none">+</span>
                <span>
                  {creating ? "创建中..." : `创建 "${search.trim()}"`}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
