import { useState, useEffect, useCallback } from 'react';
import { checkHealth } from '../api/client';

export type HealthStatus = 'checking' | 'online' | 'offline';

export function useHealthCheck(intervalMs = 15000): {
  status: HealthStatus;
  check: () => void;
} {
  const [status, setStatus] = useState<HealthStatus>('checking');

  const check = useCallback(async () => {
    setStatus('checking');
    const ok = await checkHealth();
    setStatus(ok ? 'online' : 'offline');
  }, []);

  useEffect(() => {
    check();
    const id = setInterval(check, intervalMs);
    return () => clearInterval(id);
  }, [check, intervalMs]);

  return { status, check };
}
