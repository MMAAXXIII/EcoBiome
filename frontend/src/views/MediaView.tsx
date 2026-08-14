import { useState, useMemo } from 'react';
import { useMedia, useWaterBodies } from '@/lib/hooks';
import { Images, X, Calendar, Droplets } from 'lucide-react';
import type { MediaItem } from '@/lib/types';

export function MediaView() {
  const { data: media, loading } = useMedia();
  const { data: waterBodies } = useWaterBodies();
  const [selected, setSelected] = useState<MediaItem | null>(null);
  const [filterWb, setFilterWb] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!filterWb) return media;
    return media.filter((m) => m.water_body_id === filterWb);
  }, [media, filterWb]);

  if (loading) {
    return <div className="p-6 space-y-4"><div className="skeleton h-96" /></div>;
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <p className="text-sm text-slate-400">{media.length} médias dans la bibliothèque</p>

      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          onClick={() => setFilterWb(null)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${!filterWb ? 'bg-teal-500/15 text-teal-300 border border-teal-500/20' : 'bg-night-850/40 text-slate-400 border border-transparent hover:text-white'}`}
        >
          Tous les milieux
        </button>
        {waterBodies.map((wb) => (
          <button
            key={wb.id}
            onClick={() => setFilterWb(wb.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filterWb === wb.id ? 'bg-teal-500/15 text-teal-300 border border-teal-500/20' : 'bg-night-850/40 text-slate-400 border border-transparent hover:text-white'}`}
          >
            {wb.name}
          </button>
        ))}
      </div>

      {/* Masonry grid */}
      <div className="columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-4 space-y-4">
        {filtered.map((item) => (
          <button
            key={item.id}
            onClick={() => setSelected(item)}
            className="block w-full break-inside-avoid mb-4 group relative rounded-2xl overflow-hidden surface surface-hover"
          >
            <div className="overflow-hidden">
              <img
                src={item.url}
                alt={item.caption}
                loading="lazy"
                className="w-full h-auto object-cover transition-transform duration-500 group-hover:scale-105"
              />
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-night-950/90 via-night-950/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="absolute bottom-0 left-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
              <p className="text-sm font-medium text-white">{item.title}</p>
              <p className="text-xs text-slate-300 line-clamp-1">{item.caption}</p>
            </div>
          </button>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="surface p-12 flex flex-col items-center justify-center text-center">
          <Images className="w-12 h-12 text-slate-600 mb-4" />
          <p className="text-slate-400">Aucun média pour ce filtre</p>
        </div>
      )}

      {/* Lightbox */}
      {selected && (
        <div
          onClick={() => setSelected(null)}
          className="fixed inset-0 z-50 bg-night-950/90 backdrop-blur-md flex items-center justify-center p-6 animate-fade-in"
        >
          <button className="absolute top-4 right-4 p-2 rounded-xl bg-night-800/60 text-slate-400 hover:text-white transition-colors" onClick={() => setSelected(null)}>
            <X className="w-5 h-5" />
          </button>
          <div className="max-w-4xl w-full" onClick={(e) => e.stopPropagation()}>
            <img src={selected.url} alt={selected.caption} className="w-full rounded-2xl" />
            <div className="mt-4 surface p-5">
              <h3 className="font-display font-bold text-white text-lg mb-1">{selected.title}</h3>
              <p className="text-sm text-slate-400 mb-3">{selected.caption}</p>
              <div className="flex items-center gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {new Date(selected.created_at).toLocaleDateString('fr-FR')}</span>
                {selected.water_body_id && (
                  <span className="flex items-center gap-1">
                    <Droplets className="w-3 h-3" />
                    {waterBodies.find((w) => w.id === selected.water_body_id)?.name ?? 'Milieu inconnu'}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
