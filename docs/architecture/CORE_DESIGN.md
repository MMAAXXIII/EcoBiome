# EcoBiome Core Design

> Architecture du noyau du moteur de simulation.

---

# Objectif

Le noyau d'EcoBiome est responsable de l'orchestration de la simulation.

Il ne contient aucune connaissance scientifique.

Il exécute uniquement les processus fournis par les modules.

---

# Philosophie

Le moteur ne connaît pas :

- les poissons ;
- les plantes ;
- les bactéries ;
- la chimie.

Le moteur connaît uniquement :

- le temps ;
- les événements ;
- les processus ;
- les données ;
- les dépendances.

---

# Les composants du noyau

```
SimulationContext
        │
        ▼
WorldState
        │
        ▼
SimulationEngine
        │
 ┌──────┼────────┐
 ▼      ▼        ▼
Clock Process EventEngine
        │
        ▼
DriverManager
```

---

# SimulationContext

Contient toutes les informations fixes.

Exemples :

- localisation
- climat
- géométrie
- volume
- objectifs
- contraintes

Le contexte ne change presque jamais pendant la simulation.

---

# WorldState

Représente l'état instantané de l'écosystème.

Il contient :

- eau
- populations
- biomasse
- température
- paramètres chimiques
- équipements
- météo
- historique

Tous les modules lisent et écrivent uniquement dans le WorldState.

---

# SimulationEngine

Le chef d'orchestre.

Responsabilités :

- avancer le temps ;
- appeler les processus ;
- appliquer les événements ;
- mettre à jour le WorldState ;
- calculer les rapports.

---

# Clock

Le temps officiel de la simulation.

Il permet :

- secondes ;
- minutes ;
- heures ;
- jours ;
- saisons ;
- années.

---

# Process

Un processus représente une transformation naturelle.

Exemples :

- photosynthèse ;
- respiration ;
- diffusion ;
- évaporation.

Chaque processus possède :

- des entrées ;
- des sorties ;
- une fréquence ;
- des dépendances.

---

# Event

Les événements représentent les interventions ponctuelles.

Exemples :

- changement d'eau ;
- nourrissage ;
- panne ;
- ajout de plantes.

---

# Driver

Les Drivers représentent les influences extérieures.

Exemples :

- météo ;
- soleil ;
- lune ;
- activité solaire.

---

# Pipeline

SimulationContext

↓

Initialisation

↓

WorldState

↓

Clock

↓

Drivers

↓

Events

↓

Processes

↓

Validation

↓

Rapport

---

# Objectifs

Le noyau doit être :

- rapide ;
- modulaire ;
- reproductible ;
- explicable ;
- extensible.

---

# Ce que le noyau ne doit jamais faire

Le noyau ne doit jamais contenir :

- une équation scientifique ;
- une espèce ;
- une plante ;
- un poisson ;
- une réaction chimique.

Ces éléments appartiennent exclusivement aux modules scientifiques.