import { useState } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { Topbar } from '@/components/Topbar';
import { CollectorView } from '@/views/CollectorView';
import { DashboardView } from '@/views/DashboardView';
import { DiagnosticsView } from '@/views/DiagnosticsView';
import { JournalView } from '@/views/JournalView';
import { MediaView } from '@/views/MediaView';
import { ScientificGlossaryView } from '@/views/ScientificGlossaryView';
import { getGlossaryEntryForMetric } from '@/lib/scientificGlossary';
import { WaterBodiesView } from '@/views/WaterBodiesView';
import type { ViewKey } from '@/lib/nav';
import type { Metric, WaterBody } from '@/lib/types';

export default function App() {
  const [activeView, setActiveView] = useState<ViewKey>('dashboard');
  const [collapsed, setCollapsed] = useState(false);
  const [selectedWaterBody, setSelectedWaterBody] =
    useState<WaterBody | null>(null);
  const [glossaryEntryId, setGlossaryEntryId] = useState<string | null>(null);

  const navigateToWaterBody = (waterBody: WaterBody) => {
    setSelectedWaterBody(waterBody);
    setActiveView('waterbodies');
  };

  const navigateToGlossaryMetric = (metric: Metric) => {
    const entry = getGlossaryEntryForMetric(metric);
    setGlossaryEntryId(entry?.id ?? null);
    setSelectedWaterBody(null);
    setActiveView('glossary');
  };

  const handleNavigate = (view: ViewKey) => {
    setActiveView(view);
    if (view !== 'waterbodies') {
      setSelectedWaterBody(null);
    }
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
              onNavigateToView={(view) => handleNavigate(view)}
            />
          )}
          {activeView === 'waterbodies' && (
            <WaterBodiesView
              initialWaterBody={selectedWaterBody}
              onClearInitial={() => setSelectedWaterBody(null)}
              onOpenGlossaryForMetric={navigateToGlossaryMetric}
            />
          )}
          {activeView === 'collector' && <CollectorView />}
          {activeView === 'diagnostics' && <DiagnosticsView />}
          {activeView === 'journal' && <JournalView />}
          {activeView === 'media' && <MediaView />}
          {activeView === 'glossary' && (
            <ScientificGlossaryView
              initialEntryId={glossaryEntryId}
              onInitialEntryHandled={() => setGlossaryEntryId(null)}
            />
          )}
        </main>
      </div>
    </div>
  );
}
