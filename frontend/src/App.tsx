import { type ComponentType, useMemo, useState } from 'react';
import { Search, Settings, Sparkles } from 'lucide-react';
import { navItems, NavItem } from './lib/nav';
import { DashboardView } from './views/DashboardView';
import { WaterBodiesView } from './views/WaterBodiesView';
import { DiagnosticsView } from './views/DiagnosticsView';
import { JournalView } from './views/JournalView';
import { MediaView } from './views/MediaView';

const viewComponents: Record<NavItem['id'], ComponentType> = {
  dashboard: DashboardView,
  waterBodies: WaterBodiesView,
  diagnostics: DiagnosticsView,
  journal: JournalView,
  media: MediaView
};

function App() {
  const [active, setActive] = useState<NavItem['id']>('dashboard');
  const ActiveView = viewComponents[active];

  const activeItem = useMemo(
    () => navItems.find((item) => item.id === active),
    [active]
  );

  return (
    <div className="min-h-screen bg-ecobiome-background text-ecobiome-text">
      <div className="mx-auto flex min-h-screen max-w-[1600px] gap-6 px-4 py-5 lg:px-8">
        <aside className="hidden w-80 flex-col rounded-3xl border border-ecobiome-border bg-ecobiome-surface p-6 shadow-panel lg:flex">
          <div className="mb-10 flex items-center gap-4">
            <div className="grid h-14 w-14 place-items-center rounded-3xl bg-ecobiome-accent/15 text-ecobiome-accent shadow-glow">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-ecobiome-accent/75">EcoBiome</p>
              <h1 className="text-xl font-semibold text-ecobiome-text">Simulateur aquatique</h1>
            </div>
          </div>

          <p className="mb-8 text-sm leading-6 text-slate-300">
            Modélise les interactions entre l'eau, le substrat, les plantes, les bactéries, la microfaune et les animaux.
          </p>

          <nav className="space-y-2">
            {navItems.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setActive(item.id)}
                className={`flex w-full items-center gap-3 rounded-3xl px-4 py-3 text-left transition ${
                  active === item.id
                    ? 'bg-ecobiome-accent/15 text-ecobiome-text shadow-glow'
                    : 'text-slate-300 hover:bg-white/5 hover:text-ecobiome-text'
                }`}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>

          <div className="mt-auto rounded-3xl border border-white/5 bg-white/5 p-4 text-sm text-slate-300">
            <p className="font-semibold text-ecobiome-text">EcoBiome Night</p>
            <p className="mt-2 text-xs text-slate-400">Dashboard web inspiré de votre simulateur d'écosystèmes aquatiques.</p>
          </div>
        </aside>

        <div className="flex-1 flex-col space-y-6">
          <header className="flex items-center justify-between rounded-3xl border border-ecobiome-border bg-ecobiome-surface p-5 shadow-panel">
            <div>
              <p className="text-sm uppercase tracking-[0.25em] text-ecobiome-accent/75">Dashboard</p>
              <h2 className="mt-2 text-2xl font-semibold text-ecobiome-text">{activeItem?.label ?? 'EcoBiome'}</h2>
            </div>
            <div className="flex items-center gap-3">
              <button className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 transition hover:bg-white/10">
                <Search className="h-4 w-4" />
                Rechercher
              </button>
              <button className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-ecobiome-surfaceAlt text-ecobiome-text transition hover:bg-ecobiome-surface">
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </header>

          <main className="space-y-6">
            <ActiveView />
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;
