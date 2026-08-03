# EcoBiome

EcoBiome est un simulateur open source d'écosystèmes aquatiques.

## Objectif

Modéliser les interactions entre :

- l'eau ;
- le substrat ;
- les bactéries ;
- les plantes ;
- la microfaune ;
- les animaux ;
- les cycles biogéochimiques.

Le projet est actuellement en phase de conception scientifique et logicielle.

## Web Dashboard Prototype

Le dépôt intègre désormais un prototype d'interface web dans le dossier `frontend/`.
Ce frontend a été fusionné dans `main` avec le PR #9 et reproduit l'UI vue dans le prototype Bolt.

Le frontend est construit avec :

- Vite
- React
- TypeScript
- Tailwind CSS

### Démarrage

```bash
cd frontend
npm install
npm run dev
```

### Notes

- Le simulateur desktop Python/Tkinter reste disponible dans `src/`.
- Les branches historiques `agents/visual-pass2` et `agents/web-dashboard` sont conservées pour réutilisation ultérieure.
- Un point de restauration a été créé avant la fusion : tag `before-web-dashboard-merge-2026-08-03`.
