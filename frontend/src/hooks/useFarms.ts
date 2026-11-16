import { useApi } from './useApi';
import { getFarms, getFarmData } from '../services/api';
import type { Farm, DataRecord } from '../types';

export function useFarms() {
  return useApi<Farm[]>(() => getFarms(), [], { pollMs: 30000 });
}

export function useFarmData(farmId: string, start?: string, end?: string) {
  return useApi<DataRecord[]>(
    () => getFarmData(farmId, start, end),
    [farmId, start, end]
  );
}

export default useFarms;
