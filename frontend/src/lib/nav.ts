import { Activity, Archive, FileText, Layers, Tools } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export type NavItem = {
  id: 'dashboard' | 'waterBodies' | 'diagnostics' | 'journal' | 'media';
  label: string;
  icon: LucideIcon;
};

export const siteMeta = {
  title: 'EcoBiome — Simulateur d’écosystèmes aquatiques'
};

export const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Tableau de bord', icon: Activity },
  { id: 'waterBodies', label: 'Milieux aquatiques', icon: Layers },
  { id: 'diagnostics', label: 'Diagnostics', icon: Tools },
  { id: 'journal', label: 'Journal scientifique', icon: FileText },
  { id: 'media', label: 'Galerie média', icon: Archive }
];
