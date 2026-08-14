# Flux et budgets énergétiques

**Statut :** `PROPOSED`.

## Catégories

EcoBiome distingue :

1. énergie électrique ;
2. énergie thermique ;
3. énergie lumineuse ;
4. énergie mécanique et hydraulique ;
5. énergie chimique ;
6. énergie biologique et trophique ;
7. énergie incorporée.

## Puissance et énergie

La puissance exprime un rythme instantané. L'énergie est cumulée sur une durée.
Chaque valeur conserve unité, période, provenance, incertitude et statut.

## Entités proposées

- `EnergyCarrier` ;
- `EnergyFlowDefinition` ;
- `EnergyObservation` ;
- `EnergyEstimate` ;
- `EnergyTransformation` ;
- `EnergyStorage` ;
- `EnergyBudget` ;
- `DeviceOperation`.

## Statuts

```text
MEASURED
DECLARED
DERIVED
ESTIMATED
SIMULATED
```

Une estimation métabolique ou un scénario de panne ne doit pas être présenté
comme une mesure.

## Budgets

Un budget relie entrées, stockage, sorties utiles et pertes pour un organisme,
une population, une zone, une structure ou un système.

## Optimisation

Une recommandation énergétique doit annoncer économie attendue, impact
biologique, risque, hypothèses et métrique de contrôle. Elle ne doit jamais
compromettre oxygénation, température, filtration, santé végétale ou bien-être
animal.

## Résilience

Le modèle doit permettre d'étudier autonomie, panne, délestage, équipements
prioritaires, redémarrage, production locale et saisonnalité.
