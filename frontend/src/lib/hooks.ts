import { useState, useEffect, useCallback } from 'react';
import type {
  WaterBody, Measurement, Diagnostic, JournalEntry, MediaItem, Organism, Metric,
} from '@/lib/types';

const API_BASE = '/api';

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: 'application/json' },
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`EcoBiome API ${response.status}: ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export function useWaterBodies() {
  const [data, setData] = useState<WaterBody[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchJson<WaterBody[]>('/water-bodies'));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refetch(); }, [refetch]);
  return { data, loading, error, refetch };
}

export function useMeasurements(waterBodyId: string | null) {
  const [data, setData] = useState<Measurement[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    if (!waterBodyId) {
      setData([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      setData(
        await fetchJson<Measurement[]>(
          `/measurements?water_body_id=${encodeURIComponent(waterBodyId)}`,
        ),
      );
    } catch (err) {
      console.error(err);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [waterBodyId]);

  useEffect(() => { void refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useAllMeasurements() {
  const [data, setData] = useState<Measurement[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fetchJson<Measurement[]>('/measurements'));
    } catch (err) {
      console.error(err);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useDiagnostics() {
  const [data, setData] = useState<Diagnostic[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fetchJson<Diagnostic[]>('/diagnostics'));
    } catch (err) {
      console.error(err);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useDiagnosticFindings(diagnosticId: string | null) {
  const [data, setData] = useState<{
    id: string;
    severity: string;
    metric: string;
    observation: string;
    explanation: string;
    causal_chain: string[];
  }[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    if (!diagnosticId) {
      setData([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      setData(
        await fetchJson(
          `/diagnostic-findings?diagnostic_id=${encodeURIComponent(diagnosticId)}`,
        ),
      );
    } catch (err) {
      console.error(err);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [diagnosticId]);

  useEffect(() => { void refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useJournal() {
  const [data, setData] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fetchJson<JournalEntry[]>('/journal'));
    } catch (err) {
      console.error(err);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useMedia() {
  const [data, setData] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fetchJson<MediaItem[]>('/media'));
    } catch (err) {
      console.error(err);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useOrganisms(waterBodyId: string | null) {
  const [data, setData] = useState<Organism[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    if (!waterBodyId) {
      setData([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      setData(
        await fetchJson<Organism[]>(
          `/organisms?water_body_id=${encodeURIComponent(waterBodyId)}`,
        ),
      );
    } catch (err) {
      console.error(err);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [waterBodyId]);

  useEffect(() => { void refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function getLatestByMetric(
  measurements: Measurement[],
): Record<Metric, number | null> {
  const result = {} as Record<Metric, number | null>;
  const sorted = [...measurements].sort(
    (a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime(),
  );

  for (const measurement of sorted) {
    if (result[measurement.metric] === undefined) {
      result[measurement.metric] = measurement.value;
    }
  }

  return result;
}

export function getMetricSeries(
  measurements: Measurement[],
  metric: Metric,
): number[] {
  return measurements
    .filter((measurement) => measurement.metric === metric)
    .sort(
      (a, b) =>
        new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime(),
    )
    .map((measurement) => measurement.value);
}
