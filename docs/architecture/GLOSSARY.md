# EcoBiome Glossary

> Définitions officielles des principaux concepts utilisés dans EcoBiome.

Ce glossaire constitue la référence terminologique du projet.

---

# Biome

Un biome est un ensemble cohérent de conditions environnementales permettant le développement d'un ou plusieurs écosystèmes.

Exemples :

- aquarium d'eau douce ;
- bassin de jardin ;
- mare naturelle ;
- rivière ;
- lac ;
- système aquaponique.

---

# Ecosystem

Un écosystème est l'ensemble des organismes vivants, des éléments physiques, des éléments chimiques et de leurs interactions.

Dans EcoBiome, un écosystème est représenté par un ensemble d'états et de processus évoluant dans le temps.

---

# World State

Le World State représente l'état complet de l'écosystème à un instant donné.

Il contient notamment :

- géométrie ;
- composition de l'eau ;
- populations ;
- biomasses ;
- substrat ;
- équipements ;
- météo ;
- paramètres astronomiques ;
- paramètres chimiques ;
- paramètres biologiques ;
- historique des événements.

Le World State constitue l'unique moyen de communication entre les modules scientifiques.

---

# Simulation Context

Le Simulation Context regroupe toutes les informations fixes ou lentement variables nécessaires avant le lancement d'une simulation.

Exemples :

- localisation géographique ;
- altitude ;
- climat ;
- type de contenant ;
- installation enterrée ou hors-sol ;
- matériaux ;
- objectifs ;
- contraintes.

---

# Process

Un Process est un mécanisme qui modifie le World State.

Exemples :

- photosynthèse ;
- respiration ;
- nitrification ;
- diffusion ;
- évaporation ;
- transfert thermique ;
- croissance végétale.

Les processus sont indépendants des espèces.

---

# Model

Un modèle est une représentation mathématique ou algorithmique d'un phénomène réel.

Plusieurs modèles peuvent représenter un même processus.

Exemple :

Différents modèles de photosynthèse peuvent être proposés.

---

# Module

Un module est un ensemble cohérent de modèles traitant un même domaine scientifique.

Exemples :

- chimie ;
- physique ;
- biologie ;
- géologie ;
- génétique.

---

# Event

Un Event représente une modification ponctuelle du système.

Exemples :

- changement d'eau ;
- ajout de poissons ;
- ajout d'engrais ;
- panne électrique ;
- canicule.

Chaque événement possède une date et une durée éventuelle.

---

# Driver

Un Driver est un facteur externe influençant l'écosystème.

Exemples :

- météo ;
- saisons ;
- Soleil ;
- Lune ;
- activité solaire.

Les Drivers modifient les conditions d'entrée de la simulation sans appartenir à l'écosystème.

---

# Constraint

Une contrainte est une condition que la simulation doit respecter.

Exemples :

- consommation électrique maximale ;
- coût maximal ;
- température minimale ;
- absence de filtration mécanique.

---

# Objective

Un objectif définit ce que l'utilisateur souhaite optimiser.

Exemples :

- stabilité maximale ;
- biodiversité maximale ;
- consommation minimale ;
- coût minimal.

---

# Scenario

Un scénario est une simulation basée sur un ensemble précis d'hypothèses.

Plusieurs scénarios peuvent être comparés pour un même projet.

---

# Observation

Une observation est une mesure réelle réalisée sur un écosystème.

Les observations servent à :

- calibrer les modèles ;
- valider les simulations ;
- améliorer les prédictions.

---

# Parameter

Un paramètre est une valeur utilisée par un modèle.

Chaque paramètre possède :

- une unité ;
- une origine ;
- une incertitude ;
- une date ;
- un niveau de confiance.

---

# Scientific Knowledge Base

La Scientific Knowledge Base (SKB) est la base de connaissances scientifique d'EcoBiome.

Elle contient notamment :

- espèces ;
- matériaux ;
- réactions chimiques ;
- relations de causalité ;
- références scientifiques ;
- domaines de validité des modèles.

La SKB ne réalise aucun calcul.

---

# Digital Twin

Un Digital Twin est une représentation numérique d'un écosystème réel.

Il évolue en parallèle de celui-ci grâce aux observations et aux interventions enregistrées.

---

# Uncertainty

L'incertitude représente le degré de confiance associé à une donnée ou à un résultat.

Elle doit être propagée dans l'ensemble des calculs.

---

# Calibration

La calibration consiste à ajuster les paramètres des modèles afin de réduire l'écart entre la simulation et les observations.

---

# Validation

La validation consiste à vérifier qu'un modèle reproduit correctement un phénomène réel dans son domaine de validité.

---

# Evidence Level

Le niveau de preuve indique la robustesse scientifique d'un modèle ou d'une donnée.

Exemple :

- observation directe ;
- littérature scientifique ;
- estimation ;
- hypothèse.

---

# Time Step

Le pas de temps correspond à l'intervalle séparant deux états successifs de la simulation.

Il peut être fixe ou adaptatif.

---

# Plugin

Un plugin est un module externe ajoutant des fonctionnalités sans modifier le moteur principal.

---

# Counterfactual Analysis

Une analyse contrefactuelle compare le système réel à un scénario dans lequel un élément, une action ou un mécanisme est modifié ou supprimé.

Elle permet de répondre à des questions comme :

- Que se passerait-il sans la pompe ?
- Le système resterait-il stable sans les plantes ?
- Quelle part de la stabilité vient du substrat ?