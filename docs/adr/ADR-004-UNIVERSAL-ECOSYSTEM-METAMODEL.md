# ADR-004 — Topologie écologique immuable et chronologies séparées

**Statut :** `PROPOSED`.
**Date de consolidation :** 5 août 2026.
**Implémentation autorisée par ce document :** non.

## Contexte

EcoBiome doit représenter des aquariums, mares, serres, sols, cours d'eau et
systèmes hybrides sans transformer les modèles existants en dictionnaires
génériques ni casser les formats actuels.

## Décision proposée

### Identité

- `project_id` identifie le projet ;
- `model_id` identifie une lignée ;
- `revision_id` identifie une révision immuable ;
- `revision_number` ordonne les révisions ;
- les prédécesseurs sont explicites.

### Topologie

Une révision contient :

- systèmes ;
- structures ;
- zones ;
- contenances ;
- participations ;
- flux.

Elle ne contient pas de mesures instantanées.

### Contenance et participation

- la contenance active est acyclique ;
- une structure ou zone a au plus un parent physique direct ;
- une entité peut participer à plusieurs systèmes ;
- la participation n'implique ni contenance ni flux.

### Flux

Les endpoints sont des zones, ports de structures ou frontières externes. Une
recirculation est une boucle de flux. Les mesures dynamiques restent hors de la
définition structurelle.

### Formats

```text
Données durables d'application -> JSON
Connaissances éditoriales       -> YAML
Historique append-only          -> JSONL
```

### Temporalité

Révision, validité temporelle et événement répondent à trois questions
différentes et ne se reconstruisent pas silencieusement entre elles.

### Statut épistémique

`MEASURED`, `DECLARED`, `DERIVED`, `ESTIMATED` et `SIMULATED` restent distincts
de la confiance, de l'incertitude et de la provenance.

## Compatibilité

La première tranche doit être additive. Un workspace sans
`ecosystem/model.json` reste valide. Des fixtures exactes des formats existants
précèdent toute migration.

## Hors périmètre

- choix d'une base de données ;
- checkpoint de reprise ;
- automatisation physique ;
- infrastructure distribuée ;
- moteur de simulation complet.

## Conséquences

La conception gagne en explicabilité, versionnement et extensibilité, au prix
d'invariants et de migrations plus rigoureux.
