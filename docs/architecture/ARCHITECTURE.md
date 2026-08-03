# EcoBiome Architecture

> Architecture générale du moteur de simulation EcoBiome.

---

# Objectif

L'architecture d'EcoBiome est conçue pour séparer clairement :

- les connaissances scientifiques ;
- les modèles mathématiques ;
- le moteur de simulation ;
- l'interface utilisateur.

Chaque composant possède une responsabilité unique.

---

# Architecture générale

```text
                    Interface Utilisateur
                            │
                            ▼
                    API EcoBiome publique
                            │
                            ▼
                    Simulation Engine
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
    Process Engine      World State      Event Engine
         │                  │                  │
         └──────────────────┼──────────────────┘
                            ▼
                 Scientific Knowledge Base
```

---

# Les grandes couches

## 1. Interface utilisateur

Responsabilités :

- affichage ;
- saisie utilisateur ;
- visualisation ;
- rapports.

Aucun calcul scientifique.

---

## 2. API

Point d'entrée unique.

Permet :

- scripts Python ;
- plugins ;
- interface graphique ;
- tests automatiques.

---

## 3. Simulation Engine

Le chef d'orchestre.

Responsabilités :

- avancer le temps ;
- lancer les processus ;
- appliquer les événements ;
- gérer les dépendances ;
- contrôler la cohérence.

Il ne contient aucune équation scientifique.

---

## 4. Process Engine

Le Process Engine exécute les modèles scientifiques.

Exemples :

- photosynthèse ;
- respiration ;
- nitrification ;
- diffusion ;
- croissance ;
- transfert thermique.

Chaque processus :

- lit le World State ;
- calcule ses effets ;
- propose des modifications.

---

## 5. World State

Le World State représente l'état complet de l'écosystème.

Il constitue l'unique moyen de communication entre les modules.

Aucun module ne dialogue directement avec un autre.

---

## 6. Event Engine

Tous les changements ponctuels sont représentés sous forme d'événements.

Exemples :

- changement d'eau ;
- ajout de poissons ;
- panne ;
- entretien ;
- nourrissage.

Les événements sont datés.

---

## 7. Scientific Knowledge Base

La SKB contient :

- espèces ;
- matériaux ;
- relations scientifiques ;
- références bibliographiques ;
- domaines de validité.

Elle ne réalise aucun calcul.

---

# Pipeline d'une simulation

1. Chargement du projet
2. Construction du Simulation Context
3. Vérification des données
4. Estimation des données manquantes
5. Calcul des incertitudes
6. Construction du World State
7. Boucle de simulation
8. Analyse causale
9. Génération du rapport

---

# Principe fondamental

Le moteur ne connaît aucune espèce.

Il ne connaît que :

- des processus ;
- des paramètres ;
- des modèles.

Les espèces apportent uniquement leurs caractéristiques biologiques.

---

# Modularité

Chaque domaine scientifique est développé indépendamment.

Exemple :

Physics

↓

Chemistry

↓

Biology

↓

Ecology

↓

Genetics

Ces modules ne communiquent jamais directement.

Ils utilisent exclusivement le World State.

---

# Drivers

Les Drivers représentent les influences extérieures.

Ils regroupent :

- Soleil
- Lune
- Activité solaire
- Météo
- Saisons
- Géographie
- Interventions humaines

Les Drivers alimentent le moteur mais ne font pas partie de l'écosystème.

---

# Objectifs de l'architecture

L'architecture doit garantir :

- extensibilité ;
- reproductibilité ;
- traçabilité ;
- modularité ;
- explicabilité ;
- validation scientifique.

---

# Philosophie

EcoBiome est construit autour des processus.

Les organismes ne sont pas le moteur de la simulation.

Les processus le sont.