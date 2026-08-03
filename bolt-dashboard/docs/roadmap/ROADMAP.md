# EcoBiome Roadmap

> Feuille de route officielle du projet EcoBiome.

Cette roadmap décrit les grandes étapes du développement.

Elle pourra évoluer au fil du projet, mais son objectif est de fournir une vision claire des priorités.

---

# Philosophie

Le développement d'EcoBiome repose sur trois principes :

- construire des fondations solides avant d'ajouter des fonctionnalités ;
- privilégier la qualité scientifique à la quantité de code ;
- maintenir un moteur modulaire et extensible.

---

# Phase 0 — Fondation du projet

Objectif :

Créer une base documentaire et architecturale robuste.

## Livrables

- [x] Vision
- [x] Governing Principles
- [x] Glossary
- [x] Architecture
- [ ] Module Catalog
- [ ] Architecture Decision Records (ADR)
- [ ] Contributing Guide

---

# Phase 1 — Noyau du moteur

Objectif :

Construire le cœur d'EcoBiome.

Modules :

- Simulation Engine
- WorldState
- SimulationContext
- Event Engine
- Driver System
- Time Engine
- Unit System
- Logging
- Configuration

Résultat attendu :

Le moteur peut exécuter une simulation vide.

---

# Phase 2 — Premier modèle scientifique

Objectif :

Construire un premier modèle fonctionnel.

Modules :

- Géométrie
- Eau
- Température
- Oxygène dissous
- pH
- KH
- GH
- Conductivité
- Cycle simplifié de l'azote

Résultat attendu :

Simulation simple d'un aquarium.

---

# Phase 3 — Biologie

Modules :

- Plantes
- Poissons
- Crevettes
- Bactéries
- Croissance
- Respiration
- Reproduction

Résultat attendu :

Premier écosystème vivant.

---

# Phase 4 — Écologie

Modules :

- Réseau trophique
- Compétition
- Biodiversité
- Capacité de charge
- Stabilité

Résultat attendu :

Écosystème autonome simplifié.

---

# Phase 5 — Milieu extérieur

Modules :

- Climat
- Météo
- Soleil
- Lune
- Activité solaire
- Saisons
- Température du sol

Résultat attendu :

Simulation réaliste d'un bassin extérieur.

---

# Phase 6 — Géologie

Modules :

- Sol
- Substrat multicouche
- Porosité
- Diffusion
- Compaction
- Minéraux

Résultat attendu :

Simulation du fonctionnement du substrat.

---

# Phase 7 — Génétique

Modules :

- Population
- Diversité génétique
- Consanguinité
- Sélection
- Reproduction

Résultat attendu :

Simulation de l'évolution génétique.

---

# Phase 8 — Interface graphique

Objectif :

Créer une interface simple et intuitive.

Fonctionnalités :

- Assistant de création
- Vue 2D
- Coupe du substrat
- Tableau de bord
- Graphiques
- Chronologie
- Recommandations

---

# Phase 9 — Optimisation

Objectif :

Aider à concevoir automatiquement un écosystème.

Modules :

- Contraintes
- Objectifs
- Optimisation
- Comparaison de scénarios

---

# Phase 10 — Jumeau numérique

Objectif :

Synchroniser EcoBiome avec un écosystème réel.

Fonctionnalités :

- Import de mesures
- Capteurs
- Calibration
- Validation
- Historique

---

# Vision long terme

À terme, EcoBiome devra être capable de représenter :

- aquariums ;
- bassins ;
- mares ;
- aquaponie ;
- rivières ;
- lacs ;
- milieux saumâtres.

L'architecture devra également permettre d'étendre le moteur vers d'autres biomes.

---

# Principe fondamental

Chaque nouvelle fonctionnalité devra respecter :

- la modularité ;
- la traçabilité scientifique ;
- l'explicabilité ;
- la reproductibilité ;
- la validation expérimentale.