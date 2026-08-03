# Roadmap temporelle — Projet EcoBiome

Date de génération : 2026-08-03
Branch de référence : agents/visual-pass2 (PR #1 : https://github.com/MMAAXXIII/EcoBiome/pull/1)

Résumé rapide

Ce document présente l'état actuel du projet, une feuille de route temporelle (jalons, durées estimées) et les actions restantes pour atteindre un MVP complet (UI web + Bolt DB + API + tests). Il est rédigé en français pour faciliter la communication avec les contributeurs francophones et les outils d'intégration.

État actuel (au 2026-08-03)

- Travail poussé sur la branche agents/visual-pass2 : amélioration du hero desktop (nouvel asset, fallback aquatique enrichi, overlay, démo) — commits et tests validés localement.
- PR créée : #1 (Improve desktop hero...) — contient les modifications visuelles et les captures d'écran de démonstration.
- Tests ciblés et subset de tests UI passés localement (voir logs de CI local).
- Pas (encore) de UI web complète (React/Vite/Next) livrée — dossier front web à créer/planifier.
- Collaboration demandée à bolt.new : brief posté sur la PR demandant de pousser sa proposition/branch.

Travail complété (checkpoints)

- [x] Extraction et remplacement de l'asset hero de référence (src/ecobiome/ui/desktop/assets/hero_reference.png)
- [x] Enrichissement du fallback programmatique (build_aquarium_fallback) avec scintillements, plantes, poissons et bulles
- [x] Mise à jour du demo desktop (examples/desktop_dashboard_demo.py) pour utiliser l'asset de référence par défaut
- [x] Tests unitaires/visuels ciblés révisés et exécutés (visual composition tests) — 6 passed
- [x] Commit + push de la branche agents/visual-pass2 et création de PR #1

Roadmap temporelle (plan sprintisé)

Règle : sprints de 2 semaines (10 jours ouvrés) — ajuster selon disponibilité.

Sprint 0 — Stabilisation & revue (en cours / immédiat)
- Durée estimée : 1 semaine (2026-08-03 → 2026-08-09)
- Objectifs :
  - Documenter l’état actuel (ce fichier), ajouter issues et template PR (fait)
  - Demander à bolt.new de pousser sa proposition et résumer son travail (commentaire ajouté sur PR #1)
  - Décision : fusionner immédiatement agents/visual-pass2 dans main ? (à décider)
- Critères de réussite : réponse de bolt.new ou décision de merge PR #1

Sprint 1 — UI Web Prototype (maquette fonctionnelle)
- Durée estimée : 2 semaines (2026-08-10 → 2026-08-23)
- Livrables :
  - Repo front initial (Vite+React+TypeScript) ou Next.js selon choix
  - Composants : HeroBanner (utilise hero_reference.png), KPICard, RoundedSurfaceCard, ObservationsList
  - Page dashboard statique (mock data) + style tokens (EcoBiome Night)
  - Storybook basique ou pages de démonstration
- Dépendances : BRANCH agents/visual-pass2 assets référencés
- Critères : dashboard visible en local avec mock data; design tokens appliqués

Sprint 2 — Galerie & Media (fonctionnalité d’import)
- Durée estimée : 2 semaines (2026-08-24 → 2026-09-06)
- Livrables :
  - MediaGallery component (grille, lightbox)
  - FileUploader pour importer images (dev mode: sauvegarde locale / preview)
  - Mock endpoints (ou adaptateur local) pour simuler upload
- Critères : upload d’images de démonstration et affichage en galerie

Sprint 3 — Backend Bolt DB & API minimal
- Durée estimée : 2–3 semaines (2026-09-07 → 2026-09-27)
- Livrables :
  - Schéma Bolt DB (projects, media, observations, hypotheses, experiments)
  - Endpoints REST CRUD (projects, media upload, observations, hypotheses)
  - Intégration upload → stockage (Bolt storage ou fallback filesystem)
  - Tests API (supertest ou équivalent)
- Dépendances : choix Bolt storage vs external
- Critères : endpoints CRUD fonctionnels, données persistées et restituées

Sprint 4 — Intégration UI ↔ API, Tests & CI
- Durée estimée : 2–3 semaines (2026-09-28 → 2026-10-18)
- Livrables :
  - UI connectée aux endpoints (listing projets, galerie, create observation)
  - Tests unitaires frontend (React Testing Library) et tests d’intégration API
  - Workflow GitHub Actions : build, test, snapshots
  - Visual snapshot tests basiques sur route dashboard
- Critères : CI vert, tests frontend/backend passés en CI

Sprint 5 — Polissage visuel & accessibilité
- Durée estimée : 2 semaines (2026-10-19 → 2026-11-01)
- Livrables :
  - Ajustements UX (KPI cards, spacing, shadows, tokens)
  - Accessibilité de base (contrastes, focus states)
  - Documentation de déploiement/dev
- Critères : checklist d’accessibilité basique validée; design reviews OK

Sprint 6 — Livraison MVP & documentation
- Durée estimée : 1 semaine (2026-11-02 → 2026-11-08)
- Livrables :
  - Release notes, guide d’installation, checklist de QA
  - Merge des branches pertinentes et création d’un tag release
- Critères : release publique en repo, README mis à jour

Points optionnels / futures phases

- Auth multi‑utilisateur (JWT / OAuth) — après MVP
- Support multi‑tenant ou export/import CSV des données
- Analyse avancée (visualisations temporelles, modèles de qualité)
- Déploiement à l’aide d’un provider (Vercel / Netlify + serverless API) ou déploiement conteneurisé

Dépendances & risques

- Risque principal : attente de la contribution de bolt.new (délai ou divergence de design)
- Décision d’infrastructure : Next.js vs Vite ; Bolt storage vs S3 — ces choix impactent les durées du sprint 1 et 3
- Disponibilité des assets haute fidélité (captures) — déjà en screenshots/ sur agents/visual-pass2

Actions immédiates recommandées (ordre prioritaire)

1. Décider si tu veux merger agents/visual-pass2 dans main maintenant ou attendre la revue de bolt.new
2. Confirmer choix technologique pour le front (Vite SPA recommandé pour prototype rapide) — je peux créer le scaffold initial
3. Assigner bolt.new (ou un dev) à l’issue #2 (https://github.com/MMAAXXIII/EcoBiome/issues/2) pour commencer la mise en œuvre backend
4. Préparer un ticket pour la création du front prototype (lié à l’issue #2)

Fichiers & ressources pertinents

- Branche et PR de référence : https://github.com/MMAAXXIII/EcoBiome/pull/1
- Assets : [src/ecobiome/ui/desktop/assets/hero_reference.png](C:/Users/oboco/Documents/Projets/EcoBiome/src/ecobiome/ui/desktop/assets/hero_reference.png)
- Captures : [screenshots/desktop_hero_demo_ref.png](C:/Users/oboco/Documents/Projets/EcoBiome/screenshots/desktop_hero_demo_ref.png), [screenshots/current_top_fit.png](C:/Users/oboco/Documents/Projets/EcoBiome/screenshots/current_top_fit.png), [screenshots/target_top.png](C:/Users/oboco/Documents/Projets/EcoBiome/screenshots/target_top.png)

Suivi & gouvernance

- Travailler avec GitHub Issues / PRs : associer chaque sprint à une milestone et tracker les issues correspondantes
- Utiliser des labels (priority/epic/frontend/backend/test/needs-review)
- Mises à jour hebdomadaires dans l’issue / PR pour rendre l’avancement transparent

Prochaine étape

Souhaites‑tu que :
- (A) je crée une milestone "Sprint 1 — UI Prototype" et les issues associées automatiquement dans GitHub, OU
- (B) je scaffold le projet front (Vite+React+TS) dans une nouvelle branche `feature/web-prototype` et y push un commit initial, OU
- (C) je merge `agents/visual-pass2` dans `main` pour rendre les fichiers visibles par défaut (et avertir bolt.new) ?

Indique l’option (A / B / C) ou demande une modification du calendrier si tu veux des durées/ordre différents.