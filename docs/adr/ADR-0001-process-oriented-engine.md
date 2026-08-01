# ADR-0001 — Process-Oriented Simulation Engine

**Statut :** Accepté

**Date :** 2026-08-01

---

# Contexte

EcoBiome est conçu pour simuler des écosystèmes complexes dans lesquels les phénomènes physiques, chimiques, biologiques et environnementaux interagissent en permanence.

Une première approche consistait à organiser le moteur autour des organismes :

- Fish
- Plant
- Bacteria
- Shrimp

Chaque objet aurait contenu sa propre logique.

Cependant, cette architecture entraîne une duplication importante des connaissances scientifiques et rend difficile l'ajout de nouvelles espèces.

---

# Décision

EcoBiome adopte une architecture orientée **processus**.

Les processus représentent les phénomènes naturels qui modifient l'état de l'écosystème.

Exemples :

- PhotosynthesisProcess
- RespirationProcess
- HeatTransferProcess
- NitrificationProcess
- DiffusionProcess
- EvaporationProcess
- ReproductionProcess
- GrowthProcess

Les espèces ne contiennent pas la logique scientifique.

Elles fournissent uniquement leurs caractéristiques biologiques :

- besoins thermiques ;
- consommation d'oxygène ;
- vitesse de croissance ;
- préférences écologiques ;
- paramètres de reproduction.

---

# Motivation

Cette architecture présente plusieurs avantages.

## Réutilisation

Un même processus peut être utilisé par des centaines d'espèces différentes.

Par exemple :

Le processus de photosynthèse est identique pour de nombreuses plantes.

---

## Modularité

Chaque processus peut évoluer indépendamment.

Un nouveau modèle de nitrification pourra remplacer l'ancien sans modifier le reste du moteur.

---

## Maintenance

Les phénomènes naturels sont regroupés par domaine scientifique.

Le code est plus facile à maintenir.

---

## Validation scientifique

Chaque processus peut être :

- documenté ;
- testé ;
- validé expérimentalement ;
- relié à des publications scientifiques.

---

## Explicabilité

Chaque résultat peut être relié aux processus qui l'ont produit.

EcoBiome pourra expliquer les causes d'une évolution observée.

---

# Conséquences

Le moteur devra contenir :

- un gestionnaire de processus ;
- un WorldState partagé ;
- un moteur temporel ;
- un système d'événements.

Les organismes deviendront essentiellement des ensembles de paramètres biologiques.

---

# Alternatives étudiées

## Architecture orientée objets biologiques

Chaque organisme contient sa propre logique.

### Avantages

- intuitive ;
- simple au début.

### Inconvénients

- duplication importante ;
- faible extensibilité ;
- maintenance difficile ;
- validation scientifique plus complexe.

Cette solution n'a pas été retenue.

---

# Impact

Cette décision influence l'ensemble du projet.

Tous les futurs modules devront être développés sous forme de processus indépendants utilisant exclusivement le WorldState pour communiquer.

---

# Révision

Cette ADR pourra être réévaluée si une architecture plus adaptée est démontrée.

Toute évolution devra cependant préserver :

- la modularité ;
- la traçabilité scientifique ;
- l'explicabilité ;
- la reproductibilité.