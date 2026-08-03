import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import type {
  WaterBody, Measurement, Diagnostic, JournalEntry, MediaItem, Organism, Metric,
} from '@/lib/types';

export function useWaterBodies() {
  const [data, setData] = useState<WaterBody[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    const { data: rows, error: err } = await supabase
      .from('water_bodies')
      .select('*')
      .order('created_at', { ascending: true });
    if (err) setError(err.message);
    else setData(rows ?? []);
    setLoading(false);
  }, []);

  useEffect(() => { refetch(); }, [refetch]);
  return { data, loading, error, refetch };
}

export function useMeasurements(waterBodyId: string | null) {
  const [data, setData] = useState<Measurement[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    if (!waterBodyId) { setData([]); setLoading(false); return; }
    setLoading(true);
    const { data: rows, error } = await supabase
      .from('measurements')
      .select('*')
      .eq('water_body_id', waterBodyId)
      .order('recorded_at', { ascending: true });
    if (error) console.error(error);
    else setData(rows ?? []);
    setLoading(false);
  }, [waterBodyId]);

  useEffect(() => { refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useAllMeasurements() {
  const [data, setData] = useState<Measurement[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    const { data: rows, error } = await supabase
      .from('measurements')
      .select('*')
      .order('recorded_at', { ascending: true });
    if (error) console.error(error);
    else setData(rows ?? []);
    setLoading(false);
  }, []);

  useEffect(() => { refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useDiagnostics() {
  const [data, setData] = useState<Diagnostic[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    const { data: rows, error } = await supabase
      .from('diagnostics')
      .select('*')
      .order('created_at', { ascending: false });
    if (error) console.error(error);
    else setData(rows ?? []);
    setLoading(false);
  }, []);

  useEffect(() => { refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useDiagnosticFindings(diagnosticId: string | null) {
  const [data, setData] = useState<{ id: string; severity: string; metric: string; observation: string; explanation: string; causal_chain: string[] }[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    if (!diagnosticId) { setData([]); setLoading(false); return; }
    setLoading(true);
    const { data: rows, error } = await supabase
      .from('diagnostic_findings')
      .select('*')
      .eq('diagnostic_id', diagnosticId);
    if (error) console.error(error);
    else setData(rows ?? []);
    setLoading(false);
  }, [diagnosticId]);

  useEffect(() => { refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useJournal() {
  const [data, setData] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    const { data: rows, error } = await supabase
      .from('journal_entries')
      .select('*')
      .order('created_at', { ascending: false });
    if (error) console.error(error);
    else setData(rows ?? []);
    setLoading(false);
  }, []);

  useEffect(() => { refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useMedia() {
  const [data, setData] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    const { data: rows, error } = await supabase
      .from('media_items')
      .select('*')
      .order('created_at', { ascending: false });
    if (error) console.error(error);
    else setData(rows ?? []);
    setLoading(false);
  }, []);

  useEffect(() => { refetch(); }, [refetch]);
  return { data, loading, refetch };
}

export function useOrganisms(waterBodyId: string | null) {
  const [data, setData] = useState<Organism[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    if (!waterBodyId) { setData([]); setLoading(false); return; }
    setLoading(true);
    const { data: rows, error } = await supabase
      .from('organisms')
      .select('*')
      .eq('water_body_id', waterBodyId)
      .order('kind', { ascending: true });
    if (error) console.error(error);
    else setData(rows ?? []);
    setLoading(false);
  }, [waterBodyId]);

  useEffect(() => { refetch(); }, [refetch]);
  return { data, loading, refetch };
}

// Helper: get latest value per metric for a water body
export function getLatestByMetric(measurements: Measurement[]): Record<Metric, number | null> {
  const result = {} as Record<Metric, number | null>;
  const sorted = [...measurements].sort((a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime());
  for (const m of sorted) {
    if (result[m.metric] === undefined) {
      result[m.metric] = m.value;
    }
  }
  return result;
}

// Helper: get time series for a specific metric
export function getMetricSeries(measurements: Measurement[], metric: Metric): number[] {
  return measurements
    .filter((m) => m.metric === metric)
    .sort((a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime())
    .map((m) => m.value);
}
