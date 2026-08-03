import type { Diagnostic, JournalEntry, KpiCard, Metric, MediaItem, WaterBody } from './types';

export const kpis: KpiCard[] = [
  { title: 'Milieux aquatiques', value: '4', status: 'stable', description: 'Écosystèmes actifs gérés' },
  { title: 'Stables', value: '2', status: 'stable', description: 'Systèmes dans la plage idéale' },
  { title: 'En vigilance', value: '1', status: 'caution', description: 'Intervention recommandée' },
  { title: 'Critiques', value: '1', status: 'critical', description: 'Action urgente requise' }
];

export const metrics: Metric[] = [
  { label: 'Température', value: '28.16°C', ideal: '24–27°C', status: 'warning', sparkline: [26.9, 27.3, 27.8, 28.1, 28.3, 28.5, 28.16] },
  { label: 'pH', value: '7.87', ideal: '7.8–8.4', status: 'ideal', sparkline: [7.8, 7.82, 7.84, 7.86, 7.88, 7.87, 7.87] },
  { label: 'Ammonium', value: '0.05mg/L', ideal: '0–0.05mg/L', status: 'ideal', sparkline: [0.02, 0.03, 0.04, 0.05, 0.05, 0.05, 0.05] },
  { label: 'Nitrites', value: '0.09mg/L', ideal: '0–0.05mg/L', status: 'warning', sparkline: [0.02, 0.03, 0.05, 0.07, 0.08, 0.08, 0.09] },
  { label: 'Nitrates', value: '14.88mg/L', ideal: '0–20mg/L', status: 'ideal', sparkline: [11.2, 12.0, 12.8, 13.4, 14.0, 14.4, 14.88] },
  { label: 'Oxygène', value: '7.87mg/L', ideal: '7–10mg/L', status: 'ideal', sparkline: [7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.87] },
  { label: 'Phosphate', value: '0.30mg/L', ideal: '0–0.3mg/L', status: 'ideal', sparkline: [0.18, 0.22, 0.26, 0.28, 0.29, 0.30, 0.30] },
  { label: 'Fer', value: '0.05mg/L', ideal: '0.05–0.1mg/L', status: 'ideal', sparkline: [0.04, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05] },
  { label: 'CO₂', value: '12.44mg/L', ideal: '5–15mg/L', status: 'ideal', sparkline: [11.0, 11.6, 12.0, 12.2, 12.4, 12.4, 12.44] },
  { label: 'GH', value: '11.42°dH', ideal: '6–12°dH', status: 'ideal', sparkline: [10.0, 10.5, 10.8, 11.0, 11.2, 11.4, 11.42] },
  { label: 'KH', value: '8.19°dH', ideal: '5–10°dH', status: 'ideal', sparkline: [7.2, 7.5, 7.7, 8.0, 8.1, 8.2, 8.19] }
];

export const waterBodies: WaterBody[] = [
  {
    id: 'reef-01',
    name: 'Récif Corallien Principal',
    category: 'aquarium',
    volume: '450 L',
    fill: 72,
    updated: '03/08/2026',
    status: 'Vigilance',
    summary: 'Pic de nitrites détecté: le cycle de l’azote n’est pas encore stabilisé.',
    keyValues: { 'Niveau du bassin': '72%', 'Organismes': 'coraux, poissons, bactéries' }
  },
  {
    id: 'japanese-pond',
    name: 'Bassin Japonais',
    category: 'pond',
    volume: '1200 L',
    fill: 88,
    updated: '03/08/2026',
    status: 'Stable',
    summary: 'Un écosystème paisible avec des plantes d’eau et une filtration douce.',
    keyValues: { 'Dureté GH/KH': '10°dH / 8°dH', 'Température': '24°C' }
  },
  {
    id: 'aquaponics-north',
    name: 'Système Aquaponique Nord',
    category: 'aquaponic',
    volume: '800 L',
    fill: 64,
    updated: '03/08/2026',
    status: 'Critique',
    summary: 'Chute critique d’oxygène dissous et pH bas. Risque immédiat pour les animaux.',
    keyValues: { 'pH': '6.8', 'Oxygène': '5.4mg/L' }
  },
  {
    id: 'nano-biorama',
    name: 'Nano Aquatique Biorama',
    category: 'aquarium',
    volume: '60 L',
    fill: 90,
    updated: '03/08/2026',
    status: 'Stable',
    summary: 'Nano-aquarium stable avec population de crevettes en bonne santé.',
    keyValues: { 'Plantes': 'mousse, cryptocoryne', 'État': 'stable' }
  }
];

export const diagnostics: Diagnostic[] = [
  {
    name: 'Nano Aquatique Biorama',
    summary: 'Nano-aquarium stable. Population de crevettes en bonne santé.',
    confidence: '97%',
    date: '02/08/2026'
  },
  {
    name: 'Système Aquaponique Nord',
    summary: 'Chute critique d’oxygène dissous et pH bas. Risque immédiat pour les tilapias.',
    confidence: '91%',
    date: '02/08/2026'
  },
  {
    name: 'Récif Corallien Principal',
    summary: 'Pic de nitrites détecté: le cycle de l’azote n’est pas encore stabilisé. Surveiller l’ammonium et les bactéries nitrifiantes.',
    confidence: '78%',
    date: '01/08/2026'
  },
  {
    name: 'Bassin Japonais',
    summary: 'Tous les paramètres sont dans les plages optimales. Écosystème équilibré.',
    confidence: '95%',
    date: '31/07/2026'
  }
];

export const journalEntries: JournalEntry[] = [
  {
    title: 'Interactions racines-poissons dans les systèmes aquaponiques',
    tags: ['aquaponie', 'plantes', 'bactéries'],
    summary: 'Notes sur les cycles d’azote et l’équilibre entre la nutrition des plantes et la qualité de l’eau.',
    source: 'Article scientifique'
  },
  {
    title: 'Stratégies de stabilisation des nitrites',
    tags: ['nitrites', 'filtration', 'microfaune'],
    summary: 'Analyse des approches de culture bactérienne pour accélérer le cycle de l’azote.',
    source: 'Documentation interne'
  },
  {
    title: 'Gestion des niveaux de CO₂ dans un récif',
    tags: ['CO₂', 'corail', 'aération'],
    summary: 'Observation des seuils critiques et des meilleures pratiques de dégazage.',
    source: 'Transcription YouTube'
  }
];

export const mediaItems: MediaItem[] = [
  { title: 'Vue nocturne du récif', category: 'Photo', status: 'Publié' },
  { title: 'Coupe transversale du bassin', category: 'Illustration', status: 'Brouillon' },
  { title: 'Diagramme de cycle de l’azote', category: 'Graphique', status: 'Publié' },
  { title: 'Journal de bord du nano-aquarium', category: 'Photo', status: 'Publié' }
];
