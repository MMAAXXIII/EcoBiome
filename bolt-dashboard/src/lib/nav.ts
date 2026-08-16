import {
  BookOpen,
  DatabaseZap,
  Droplet,
  Fish,
  FileText,
  Images,
  LayoutDashboard,
  Leaf,
  Microscope,
  Waves,
  type LucideIcon,
} from 'lucide-react';

export type ViewKey =
  | 'dashboard'
  | 'waterbodies'
  | 'collector'
  | 'diagnostics'
  | 'journal'
  | 'media'
  | 'glossary';

export interface NavItem {
  key: ViewKey;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  {
    key: 'dashboard',
    label: 'Tableau de bord',
    icon: LayoutDashboard,
  },
  {
    key: 'waterbodies',
    label: 'Milieux aquatiques',
    icon: Waves,
  },
  {
    key: 'collector',
    label: 'Collector',
    icon: DatabaseZap,
  },
  {
    key: 'diagnostics',
    label: 'Diagnostics',
    icon: Microscope,
  },
  {
    key: 'journal',
    label: 'Journal scientifique',
    icon: BookOpen,
  },
  {
    key: 'media',
    label: 'Galerie média',
    icon: Images,
  },
  {
    key: 'glossary',
    label: 'Lexique scientifique',
    icon: FileText,
  },
];

export const ORGANISM_ICONS: Record<string, LucideIcon> = {
  plant: Leaf,
  bacteria: Microscope,
  microfauna: Droplet,
  animal: Fish,
};
