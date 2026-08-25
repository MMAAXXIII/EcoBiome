import { useState } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { Topbar } from '@/components/Topbar';
import { DashboardView } from '@/views/DashboardView';
import { WaterBodiesView } from '@/views/WaterBodiesView';
import { DiagnosticsView } from '@/views/DiagnosticsView';
import { JournalView } from '@/views/JournalView';
import { MediaView } from '@/views/MediaView';
import { NitrogenView } from '@/views/NitrogenView';
import type { ViewKey } from '@/lib/nav';
import type { WaterBody } from '@/lib/types';

export default function App() {
  const [activeView, setActiveView] = useState<ViewKey>('dashboard');
  const [collapsed, setCollapsed] = useState(false);
  const [selectedWaterBody, setSelectedWaterBody] = useState<WaterBody | null>(null);

  const navigateToWaterBody = (wb: WaterBody) => {
    setSelectedWaterBody(wb);
    setActiveView('waterbodies');
  };

  const handleNavigate = (view: ViewKey) => {
    setActiveView(view);
    if (view !== 'waterbodies') setSelectedWaterBody(null);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        activeView={activeView}
        onNavigate={handleNavigate}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Topbar activeView={activeView} />
        <main className="flex-1 overflow-y-auto">
          {activeView === 'dashboard' && (
            <DashboardView
              onNavigateToWaterBody={navigateToWaterBody}
              onNavigateToView={(v) => handleNavigate(v)}
            />
          )}
          {activeView === 'waterbodies' && (
            <WaterBodiesView
              initialWaterBody={selectedWaterBody}
              onClearInitial={() => setSelectedWaterBody(null)}
            />
          )}
          {activeView === 'diagnostics' && <DiagnosticsView />}
          {activeView === 'journal' && <JournalView />}
          {activeView === 'media' && <MediaView />}
          {activeView === 'nitrogen' && <NitrogenView />}
        </main>
      </div>
    </div>
  );
}
