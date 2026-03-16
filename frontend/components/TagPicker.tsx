"use client";
import { useState } from "react";
import { PlazaTagCategory } from "@/lib/api";

export default function TagPicker({
  categories,
  selectedTagIds,
  onToggle,
  required,
  filterCategorySlugs,
}: {
  categories: PlazaTagCategory[];
  selectedTagIds: Set<string>;
  onToggle: (tagId: string) => void;
  required?: boolean;
  filterCategorySlugs?: string[];
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

  const displayed = filterCategorySlugs
    ? categories.filter((c) => filterCategorySlugs.includes(c.slug))
    : categories;

  return (
    <div>
      <label className="block font-bold mb-2 text-gray-800">
        Tags (标签)
        {required && <span className="text-red-500 ml-1">*</span>}
        <span className="block text-sm font-normal text-gray-500">
          {required
            ? "请至少选择 1 个标签"
            : "可选标签，不选则由 AI 自动提取"}
        </span>
      </label>
      <div className="border border-gray-300 rounded-lg p-3 space-y-2.5 bg-gray-50">
        {displayed.map((cat) => (
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
