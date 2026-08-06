# Occupation spatio-temporelle et rôle écologique

**Statut :** `PROPOSED`.

## Chaîne de prudence

EcoBiome distingue :

```text
fait observé
→ relation spatiale
→ interaction observée
→ hypothèse causale
→ rôle écologique évalué
```

La présence près d'une ressource ne prouve ni attraction, ni alimentation, ni
effet bénéfique.

## Niveaux de localisation

- zone ;
- position relative ;
- coordonnées locales ;
- géométrie ;
- coordonnées géographiques protégées.

Le modèle accepte l'incertitude et ne fabrique pas de coordonnées.

## Entités proposées

- `SpatialReferenceFrame` ;
- `SpatialFeature` ;
- `SpatiotemporalOccupancy` ;
- `MovementTrack` ;
- `ResourcePatch` ;
- `InteractionObservation` ;
- `EcologicalRoleAssessment`.

## Niveau de preuve alimentaire

```text
0 — aucune preuve
1 — proximité
2 — contact répété
3 — comportement alimentaire probable
4 — ingestion observée
5 — confirmation expérimentale ou analytique
```

## Rôle écologique

Le rôle est contextuel : le même organisme peut être bénéfique, neutre ou
nuisible selon le système, la période, la culture et le territoire.

## Confidentialité

Les coordonnées exactes, champs de vision et sites sensibles sont privés par
défaut. Le partage peut utiliser une zone généralisée et supprimer les
métadonnées GPS.
