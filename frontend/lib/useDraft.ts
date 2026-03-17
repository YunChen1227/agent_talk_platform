"use client";

import { useState, useEffect, useCallback, useRef } from "react";

const isClient = typeof window !== "undefined";

/**
 * localStorage-based draft: save/restore/clear.
 *
 * @param key        localStorage key
 * @param currentState  current form state to auto-save
 * @param enabled    auto-save only when true
 * @param userId     current user id; draft is only restored if it belongs to this user
 */
export function useDraft<T extends Record<string, unknown>>(
  key: string,
  currentState: T,
  enabled: boolean,
  userId?: string | null
) {
  const [draft, setDraft] = useState<T | null>(() => {
    if (!isClient || !userId) return null;
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (parsed._userId && parsed._userId !== userId) return null;
      return parsed as T;
    } catch {
      return null;
    }
  });
  const hasDraft = draft !== null;
  const lastSavedRef = useRef<string>("");
  const clearedRef = useRef(false);

  useEffect(() => {
    if (!userId || !isClient) return;
    try {
      const raw = localStorage.getItem(key);
      if (!raw) { setDraft(null); return; }
      const parsed = JSON.parse(raw);
      if (parsed._userId && parsed._userId !== userId) {
        setDraft(null);
        return;
      }
      setDraft(parsed as T);
    } catch {
      setDraft(null);
    }
  }, [key, userId]);

  const clearDraft = useCallback(() => {
    clearedRef.current = true;
    if (isClient) localStorage.removeItem(key);
    setDraft(null);
    lastSavedRef.current = "";
  }, [key]);

  useEffect(() => {
    if (!enabled || !isClient || clearedRef.current) return;
    if (!userId) return;
    try {
      const toSave = { ...currentState, _userId: userId, savedAt: Date.now() };
      const str = JSON.stringify(toSave);
      if (str !== lastSavedRef.current) {
        lastSavedRef.current = str;
        localStorage.setItem(key, str);
      }
    } catch {
      /* ignore */
    }
  });

  return { draft, clearDraft, hasDraft };
}
