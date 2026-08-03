# 🧬 EcoBiome - Journal des Rationnels Scientifiques

## 1. Objectif du document
Ce fichier assure la traçabilité des décisions architecturales et scientifiques de **EcoBiome**. Il lie le code source aux réalités biologiques (biochimie, écologie) pour garantir l'intégrité du simulateur. Chaque section "Acte" correspond à une phase de développement majeure ou à un apport spécifique d'IA.

---

## 📅 Acte 01 : Initialisation & Fondations Biologiques
**Date :** 2026-08-04 (Session actuelle)
**Acteur Principal :** Ingénieur IA (Qwen 3.6) & Développeur MMAAXXIII

### Contexte de la décision
Démarrage du développement du moteur de simulation (`core`). Avant d'écrire le code, il est crucial de valider les lois physiques et biologiques régissant un aquarium clos. Sans ces fondations, le dashboard web sera inutilisable car alimenté par des données aléatoires.

### Logique Scientifique Intégrée (Rationale)
1.  **Modélisation Closed-Loop (Boucle Fermée) :**
    *   *Choix :* Le système ne fonctionne pas en "continuel" (eau changée constamment), mais en "batch" cyclique (cycle de l'azote).
    *   *Résilience :* Cela oblige les bactéries nitrifiantes à être les acteurs principaux du jeu, simulant la réalité d'un bac mûr ou en cycle.

2.  **Stoichiométrie des Cycles :**
    *   *Choix :* Priorité au Cycle de l'Azote (N) et de l'Oxygène (O).
    *   *Règle biologique :* L'ammoniac (NH3/NH4+) est le poison principal. Il doit être converti en Nitrites (NO2), puis Nitrates (NO3), consommés par les plantes ou évacués par changement d'eau.

### Planification Technique (Next Steps)
*   [ ] **Créer `src/biome_core/water_model.py`** : Définition des classes de données (`WaterChemistry`) avec validation stricte (ex: pH ne peut pas être < 0 ni > 14).
*   [ ] **Créer `src/biome_core/organisms.py`** : Implémentation de la classe abstraite `Organism` et des enfants `Bacteria` (Nitrosomonas/Nitrobacter) et `Plant`.

---
