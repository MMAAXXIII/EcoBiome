import { Atom, Droplet, Waves, Fish, Leaf, Microscope, BookOpen, Images, LayoutDashboard, type LucideIcon } from 'lucide-react';

export type ViewKey = 'dashboard' | 'waterbodies' | 'diagnostics' | 'journal' | 'media' | 'nitrogen';

export interface NavItem {
  key: ViewKey;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { key: 'dashboard', label: 'Tableau de bord', icon: LayoutDashboard },
  { key: 'waterbodies', label: 'Milieux aquatiques', icon: Waves },
  { key: 'diagnostics', label: 'Diagnostics', icon: Microscope },
  { key: 'nitrogen', label: "Cycle de l'azote", icon: Atom },
  { key: 'journal', label: 'Journal scientifique', icon: BookOpen },
  { key: 'media', label: 'Galerie média', icon: Images },
];

export const ORGANISM_ICONS: Record<string, LucideIcon> = {
  plant: Leaf,
  bacteria: Microscope,
  microfauna: Droplet,
  animal: Fish,
};
