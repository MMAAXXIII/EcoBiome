# Métamodèle universel d'écosystème

**Statut :** `PROPOSED`.

## Principe

Les entités possèdent une identité stable et des relations explicites. La
notion d'appartenance exclusive ne suffit pas pour les systèmes hybrides.

Relations conceptuelles :

```text
contains
participates_in
occupies
observes
is_connected_to
receives_flow_from
sends_flow_to
influences
replaces
splits_into
merges_from
```

## Concepts

- `EcosystemSystem` — fonction ou processus ;
- `PhysicalStructure` — objet matériel ;
- `EnvironmentZone` — espace observable ;
- `PhysicalContainment` — hiérarchie physique acyclique ;
- `SystemParticipation` — participation fonctionnelle multiple ;
- `ResourceFlow` — route orientée ;
- `Taxon`, `BiologicalPopulation`, `OrganismIndividual` ;
- révisions immuables et validités temporelles.

## Systèmes continus

Un cours d'eau est un réseau orienté de nœuds et tronçons. Une recirculation
est une boucle de flux, pas une propriété magique d'une seule arête.

## Capteurs

Le modèle sépare appareil, montage, site, grandeur et empreinte de mesure.

## Historique

Ne pas réécrire le passé. Une transformation de structure crée de nouvelles
entités ou révisions et des liens de lignée explicites.

## Compatibilité

L'adoption doit rester additive et préserver les modèles aquatiques existants.
Aucun choix de base de données n'est autorisé par ce document.
