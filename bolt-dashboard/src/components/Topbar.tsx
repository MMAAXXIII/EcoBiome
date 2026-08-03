import { NAV_ITEMS, type ViewKey } from '@/lib/nav';
import { Search, Bell, Activity } from 'lucide-react';

interface TopbarProps {
  activeView: ViewKey;
}

export function Topbar({ activeView }: TopbarProps) {
  const current = NAV_ITEMS.find((n) => n.key === activeView);

  return (
    <header className="h-16 shrink-0 border-b border-night-700/40 bg-night-900/40 backdrop-blur-md px-6 flex items-center justify-between gap-4">
      <div>
        <h1 className="font-display font-bold text-white text-xl tracking-tight">{current?.label}</h1>
      </div>

      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Rechercher..."
            className="w-48 lg:w-64 pl-9 pr-3 py-2 rounded-xl bg-night-850/60 border border-night-700 text-sm text-slate-300 placeholder-slate-500 focus:outline-none focus:border-teal-500/40 focus:ring-1 focus:ring-teal-500/20 transition-all"
          />
        </div>

        {/* Live indicator */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/20">
          <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
          <span className="text-xs font-medium text-teal-300">Système actif</span>
        </div>

        {/* Notifications */}
        <button className="relative p-2 rounded-xl text-slate-400 hover:text-white hover:bg-night-700/40 transition-all">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-coral-500" />
        </button>

        {/* Activity */}
        <button className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-night-700/40 transition-all">
          <Activity className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
