export type KpiCard = {
  title: string;
  value: string;
  status: 'stable' | 'caution' | 'critical';
  description: string;
};

export type Metric = {
  label: string;
  value: string;
  ideal: string;
  status: 'ideal' | 'warning' | 'critical';
  sparkline: number[];
};

export type WaterBody = {
  id: string;
  name: string;
  category: string;
  volume: string;
  fill: number;
  updated: string;
  status: 'Stable' | 'Vigilance' | 'Critique';
  summary: string;
  keyValues: Record<string, string>;
};

export type Diagnostic = {
  name: string;
  summary: string;
  confidence: string;
  date: string;
};

export type JournalEntry = {
  title: string;
  tags: string[];
  summary: string;
  source: string;
};

export type MediaItem = {
  title: string;
  category: string;
  status: string;
};
