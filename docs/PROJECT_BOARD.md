# EcoBiome Project Board

**Révision :** 15 août 2026.
**Rôle :** tableau d'exécution léger. La roadmap canonique est `../ROADMAP.md`.

## NOW — chaîne scientifique

### Terminé

- [x] PR #10 — intégration des fondations et du Collector CLI.
- [x] Scientific Foundation / persistence SQLite V4 validée.
- [x] Claim et Segment review events append-only.
- [x] Semantic Candidate V2.11 — Phase A intégrée sur `main`.
- [x] Scientific Assertion Projection Contract V1 — validation locale,
  review du commit, push fast-forward et CI post-push validés.
- [x] Canon distant Projection V1 :
  `main@7c17e5d0db8d17d97bf4e6e557d96a7b5349a769`.
- [x] Python CI #4, Frontend CI #24 et Vercel : succès.
- [x] alignement roadmap / vision / README — réalisé par le lot stratégique V2.

### Gate actif

- [ ] fermer le design V5 avant tout DDL, en commençant par la persistence
  append-only de la review humaine des Semantic Candidates V2.11.

## NEXT — Persistence V5

- [ ] auditer le design V5 courant ;
- [ ] résoudre la persistence append-only de la review humaine des candidats
  V2.11 ;
- [ ] figer l'identité Schema V5 ;
- [ ] implémenter `semantic_candidates` ;
- [ ] implémenter provider runs / inputs / events / origins ;
- [ ] protéger les artefacts provider nécessaires dans le CAS ;
- [ ] prouver fresh-database + intégrité + compat Collector.

## THEN — couverture scientifique

- [ ] entity resolution reviewée ;
- [ ] mappings `ENTITY_ARGUMENT` ;
- [ ] étendre les projections relation par relation ;
- [ ] métrique de couverture relation/type ;
- [ ] read models espèces / paramètres / stress / compatibilité ;
- [ ] synthèse corroboration / contradiction.

## VERTICAL SLICE PRODUIT

Objectif : aquarium ou mare de bout en bout.

- [ ] structures, zones et flux ;
- [ ] organismes/populations ;
- [ ] observations et interventions ;
- [ ] au moins une source scientifique ;
- [ ] Claim/Evidence/review/candidat/assertion ;
- [ ] un processus écologique déterministe ;
- [ ] incertitude et données manquantes ;
- [ ] explication « Pourquoi ça marche ? ».

## APRÈS LE VERTICAL SLICE

- [ ] Scientific/Professional/Web/Media collectors spécialisés ;
- [ ] UserDataCollector ;
- [ ] SensorCollector ;
- [ ] TrendAnalyzer ;
- [ ] EventPredictor ;
- [ ] scénarios et BiomeGenerator ;
- [ ] intégration dashboard débutant/intermédiaire/avancé.

## LONG TERME / DEFERRED

- [ ] worker local ;
- [ ] scheduler + retry + DLQ ;
- [ ] cloud provider-neutral ;
- [ ] EcoBiome@home ;
- [ ] apprentissage communautaire gouverné ;
- [ ] automatisation physique avec safety model dédié.

## Dette documentaire identifiée

- le root `SOURCES.md` est remplacé par le lot stratégique V2, encore non commit ;
- `docs/scientific/ECOLOGICAL_MODEL.md` est encore vide ;
- la description GitHub utilise encore l'ancien nom « AquaBiome » ;
- les issues UI historiques ne reflètent plus la priorité scientifique
  actuelle.

Ces points doivent être traités sans réécrire rétroactivement les documents de
référence historiques.
