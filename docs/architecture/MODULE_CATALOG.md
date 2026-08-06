# Catalogue des modules

Ce catalogue décrit les responsabilités, pas une garantie que chaque capacité
future est déjà implémentée.

## Modules canoniques actuels

| Namespace | Responsabilité |
|---|---|
| `ecobiome.core` | Projets, études, événements, observations et unités. |
| `ecobiome.dashboard` | Modèles et construction des vues de tableau de bord. |
| `ecobiome.integrations` | Ponts entre sous-systèmes. |
| `ecobiome.journal` | Journal scientifique et persistance JSONL. |
| `ecobiome.knowledge` | Variables, relations, chargeurs et registres de connaissance. |
| `ecobiome.knowledge_acquisition` | Sources, transcriptions, claims et traitement. |
| `ecobiome.media` | Actifs, métadonnées, stockage et checksums. |
| `ecobiome.reasoning` | Hypothèses, règles, cohérence, expériences et résultats. |
| `ecobiome.ui.desktop` | Interface Desktop, navigation, thèmes et visualisations. |
| `ecobiome.workspace` | Manifeste, types de projets et sérialisation. |
| `ecobiome.world` | État du monde aquatique, événements et persistance. |

## Composants racine existants

Le dépôt contient aussi des collecteurs, composants API, services cloud
expérimentaux, modules d'analyse et une interface frontend. Leur migration
éventuelle sous le package canonique doit faire l'objet de lots séparés.

## Modules futurs proposés

| Namespace indicatif | Statut | Responsabilité |
|---|---|---|
| `ecobiome.worker` | `PROPOSED` | Exécution de tâches et déclaration de capacité. |
| `ecobiome.worker.safety` | `PROPOSED` | Quotas, pause utilisateur et mode nuit. |
| `ecobiome.storage` | `PROPOSED` | Politiques hot/cold et chemins d'artefacts. |
| `ecobiome.cloud` | `PROPOSED` | Interface fournisseur-agnostique d'objets. |
| `ecobiome.jobs` | `PROPOSED` | États, retry, backoff et DLQ. |
| `ecobiome.ecosystem` | `PROPOSED` | Métamodèle universel versionné. |
| `ecobiome.energy` | `PROPOSED` | Flux, transformations et budgets énergétiques. |

Les noms restent indicatifs jusqu'à une ADR et un audit du dépôt réel.
