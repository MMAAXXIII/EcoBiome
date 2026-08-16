import { useCallback, useEffect, useState } from 'react';
import {
  getAllMeasurements,
  getDiagnosticFindings,
  getDiagnostics,
  getEcology,
  getEquipment,
  getGuidance,
  getJournal,
  getMeasurements,
  getMedia,
  getOrganisms,
  getWaterBodies,
} from '@/lib/api';
import type {
  Diagnostic,
  EcologySnapshot,
  EquipmentItem,
  ExperienceLevel,
  GuidanceSnapshot,
  JournalEntry,
  Measurement,
  MediaItem,
  Metric,
  Organism,
  WaterBody,
} from '@/lib/types';

export function useWaterBodies() {
  const [data, setData] = useState<WaterBody[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getWaterBodies());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useMeasurements(waterBodyId: string | null) {
  const [data, setData] = useState<Measurement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!waterBodyId) {
      setData([]);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setData(await getMeasurements(waterBodyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [waterBodyId]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useAllMeasurements() {
  const [data, setData] = useState<Measurement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getAllMeasurements());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useDiagnostics() {
  const [data, setData] = useState<Diagnostic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getDiagnostics());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useDiagnosticFindings(diagnosticId: string | null) {
  const [data, setData] = useState<Array<{
    id: string;
    severity: string;
    metric: string;
    observation: string;
    explanation: string;
    causal_chain: string[];
  }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!diagnosticId) {
      setData([]);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setData(await getDiagnosticFindings(diagnosticId));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [diagnosticId]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useJournal() {
  const [data, setData] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getJournal());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useMedia() {
  const [data, setData] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getMedia());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useEcology(waterBodyId: string | null) {
  const [data, setData] = useState<EcologySnapshot>({
    livestock: [],
    plants: [],
    water_sources: [],
    substrate_layers: [],
    feed_products: [],
    known_livestock_biomass_g: 0,
    operation_count: 0,
    feeding_event_count: 0,
    derived_indicators: {},
    recent_operations: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!waterBodyId) {
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setData(await getEcology(waterBodyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [waterBodyId]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useGuidance(
  waterBodyId: string | null,
  level: ExperienceLevel,
) {
  const [data, setData] = useState<GuidanceSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!waterBodyId) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setData(await getGuidance(waterBodyId, level));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [level, waterBodyId]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useEquipment(waterBodyId: string | null) {
  const [data, setData] = useState<EquipmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!waterBodyId) {
      setData([]);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setData(await getEquipment(waterBodyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [waterBodyId]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useOrganisms(waterBodyId: string | null) {
  const [data, setData] = useState<Organism[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!waterBodyId) {
      setData([]);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setData(await getOrganisms(waterBodyId));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [waterBodyId]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function getLatestByMetric(
  measurements: Measurement[],
): Record<Metric, number | null> {
  const result = {} as Record<Metric, number | null>;
  const sorted = [...measurements].sort(
    (a, b) =>
      new Date(b.recorded_at).getTime() -
      new Date(a.recorded_at).getTime(),
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
        new Date(a.recorded_at).getTime() -
        new Date(b.recorded_at).getTime(),
    )
    .map((measurement) => measurement.value);
}
