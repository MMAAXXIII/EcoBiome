# Modèle de données cible

**Statut :** `PROPOSED`.
**Source principale :** dossiers de conception 002, 002A, 002B et ADR 002G.

## Identité et révisions

Une lignée de modèle possède un `model_id` stable. Chaque révision publiée
possède un `revision_id` unique, un numéro ordonné et des prédécesseurs
explicites. Une révision publiée est complète et immuable.

## Trois concepts distincts

### Système

Ensemble fonctionnel ou processus : boucle aquaponique, système climatique,
réseau d'irrigation ou système de filtration.

### Structure physique

Objet matériel : serre, aquarium, bac, filtre, tuyau ou réservoir.

### Zone environnementale

Espace où les conditions sont observées : eau, air, zone racinaire, berge,
substrat profond ou canopée.

La contenance physique et la participation fonctionnelle sont deux relations
différentes. Une zone a au plus un parent physique direct actif, mais peut
participer à plusieurs systèmes.

## Flux

Un `ResourceFlow` décrit une route orientée entre des endpoints :

```text
ZoneEndpoint
StructurePortEndpoint
ExternalBoundaryEndpoint
```

Une recirculation est une boucle composée de plusieurs flux. Les valeurs
instantanées — débit, température, concentration, puissance ou rendement —
restent dans des observations ou estimations, pas dans la route structurelle.

## Organismes

Le modèle distingue :

- `Taxon` ;
- `BiologicalPopulation` ;
- `OrganismIndividual` ;
- occupation spatio-temporelle ;
- trajectoire ;
- interaction observée ;
- rôle écologique contextuel.

Le statut invasif ou bénéfique dépend d'un territoire, d'une période et d'un
contexte ; il n'est pas une propriété absolue du taxon.

## Capteurs

Le dispositif, son montage, le site d'observation et l'empreinte de mesure sont
séparés :

```text
SensorDevice
ObservationSite
MeasurementFootprint
SensorAssignment
```

## Énergie

L'énergie reste une extension spécialisée :

```text
EnergyFlowDefinition
EnergyTransformation
EnergyObservation
EnergyEstimate
EnergyStorage
EnergyBudget
```

Chaque valeur porte une unité et un statut épistémique.

## Révision, validité et événement

| Dimension | Question |
|---|---|
| Révision | Quelle topologie était représentée ? |
| Validité temporelle | Pendant quelle période était-elle vraie ou supposée vraie ? |
| Événement | Que s'est-il passé, quand et sous quelle causalité ? |

Aucune surface ne reconstruit silencieusement les deux autres.

## Formats

```text
Données durables manipulées par l'application -> JSON
Connaissances et configurations éditoriales    -> YAML
Historique append-only                         -> JSONL
```

## Statut épistémique

Valeurs initiales :

```text
MEASURED
DECLARED
DERIVED
ESTIMATED
SIMULATED
```

Ce statut reste distinct de la confiance, de l'incertitude, de la méthode et
du niveau de preuve.
