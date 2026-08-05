# Architecture EcoBiome

**Statut :** architecture de référence ; certaines parties sont implémentées,
d'autres restent proposées.

## Vue d'ensemble

```text
Interface / API
      │
      ▼
Control Plane
      │
      ├── Data Plane ── collecte, analyse, médias, provenance
      ├── Compute Plane ── workers CPU/GPU
      ├── Cloud Plane ── stockage partagé, index, droits
      └── Worker Plane ── contribution volontaire et limitée
```

## État actuel

### `IMPLEMENTED`

- package Python canonique sous `src/ecobiome` ;
- API et composants backend existants ;
- interface React/Vite/TypeScript ;
- interface Desktop et modèles de présentation ;
- journal, événements, médias, workspace et raisonnement ;
- collecteurs racine et mécanismes de sécurité déjà validés ;
- tests Python racine et suite canonique ;
- contrôles frontend de typecheck, build et lint.

### `PROPOSED`

- orchestrateur de jobs distribué ;
- worker local et worker cloud ;
- file de tâches persistante avec retry et DLQ ;
- stockage hot/cold géré ;
- manifeste global des artefacts ;
- index cloud et gestion de quotas ;
- validation redondante de calculs ;
- métamodèle universel versionné.

## Plans

### Control Plane

Responsabilités cibles :

- API et dashboard ;
- identité des projets et workers ;
- soumission et suivi des jobs ;
- états, journaux et quotas ;
- sélection d'un worker compatible ;
- autorisations et consentements.

### Data Plane

Responsabilités cibles :

- acquisition de sources ;
- normalisation et qualité ;
- transcription isolée ;
- NLP, extraction et embeddings ;
- médias et artefacts ;
- provenance, licence et confiance.

### Compute Plane

Responsabilités cibles :

- exécution CPU/GPU ;
- tâches segmentées et rejouables ;
- capacité déclarée ;
- reprise, backoff et DLQ ;
- hash et validation des résultats.

### Cloud Plane

Responsabilités cibles :

- objets finaux et index global ;
- droits et quotas ;
- partage volontaire ;
- rétention et suppression ;
- agrégation respectueuse de la confidentialité.

### Worker Plane

Responsabilités cibles :

- récupération de tâches autorisées ;
- téléchargement minimal des entrées ;
- exécution sous quotas ;
- pause pendant l'activité utilisateur ;
- mode nuit ;
- renvoi de résultats et nettoyage local.

## Frontières

- Le noyau ne dépend pas d'un fournisseur cloud.
- La transcription lourde reste un worker isolé.
- Les données durables de projet utilisent des formats déterministes.
- Les connaissances éditoriales peuvent rester en YAML.
- Les historiques append-only utilisent JSONL.
- Les actions physiques exigent des garde-fous spécifiques.

Voir aussi [`ECOBIOME_AT_HOME.md`](ECOBIOME_AT_HOME.md) et
[`DATA_MODEL.md`](DATA_MODEL.md).
