"use client";

import { useCallback } from "react";
import { useLocalStorage } from "./useLocalStorage";

export interface QueryRecord {
  id: string;
  query: string;
  timestamp: number;
  responseSnippet?: string;
}

const HISTORY_KEY = "floatchat_query_history";
const MAX_HISTORY = 20;

export function useQueryHistory() {
  const { value: history, setValue: setHistory } = useLocalStorage<QueryRecord[]>(
    HISTORY_KEY,
    []
  );

  const addToHistory = useCallback(
    (query: string, responseSnippet?: string) => {
      const record: QueryRecord = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        query: query.trim(),
        timestamp: Date.now(),
        responseSnippet: responseSnippet?.slice(0, 120),
      };
      setHistory((prev) => [record, ...prev.filter((r) => r.query !== query.trim())].slice(0, MAX_HISTORY));
    },
    [setHistory]
  );

  const removeFromHistory = useCallback(
    (id: string) => {
      setHistory((prev) => prev.filter((r) => r.id !== id));
    },
    [setHistory]
  );

  const clearHistory = useCallback(() => {
    setHistory([]);
  }, [setHistory]);

  return { history, addToHistory, removeFromHistory, clearHistory } as const;
}
