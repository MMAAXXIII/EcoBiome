import { NAV_ITEMS, type ViewKey } from '@/lib/nav';
import { Droplets } from 'lucide-react';

interface SidebarProps {
  activeView: ViewKey;
  onNavigate: (view: ViewKey) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export function Sidebar({ activeView, onNavigate, collapsed, onToggleCollapse }: SidebarProps) {
  return (
    <aside className={`${collapsed ? 'w-16' : 'w-64'} shrink-0 transition-all duration-300 flex flex-col border-r border-night-700/40 bg-night-900/40 backdrop-blur-md`}>
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-night-700/40">
        <button onClick={onToggleCollapse} className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center shadow-glow shrink-0">
            <Droplets className="w-5 h-5 text-night-950" />
          </div>
          {!collapsed && (
            <div className="text-left">
              <p className="font-display font-bold text-white text-sm leading-tight">EcoBiome</p>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Simulateur aquatique</p>
            </div>
          )}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.key;
          return (
            <button
              key={item.key}
              onClick={() => onNavigate(item.key)}
              className={`nav-item w-full ${isActive ? 'nav-item-active' : ''} ${collapsed ? 'justify-center px-0' : ''}`}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-4.5 h-4.5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-3 border-t border-night-700/40">
          <div className="surface p-3">
            <p className="text-xs text-slate-400 leading-relaxed">
              Modéliser les interactions entre l'eau, le substrat, les plantes, les bactéries, la microfaune et les animaux.
            </p>
          </div>
        </div>
      )}
    </aside>
  );
}
