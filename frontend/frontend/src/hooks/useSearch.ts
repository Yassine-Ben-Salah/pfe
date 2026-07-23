import { useState, useCallback } from 'react';
import { searchRapports } from '../api/client';
import type { SearchRequest, SearchResponse } from '../types/api';

interface UseSearchReturn {
  results: SearchResponse | null;
  loading: boolean;
  error: string | null;
  search: (req: SearchRequest) => Promise<void>;
  clear: () => void;
}

export function useSearch(): UseSearchReturn {
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (req: SearchRequest) => {
    setLoading(true);
    setError(null);
    try {
      const data = await searchRapports(req);
      setResults(data);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Erreur lors de la recherche';
      setError(msg);
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return { results, loading, error, search, clear };
}
