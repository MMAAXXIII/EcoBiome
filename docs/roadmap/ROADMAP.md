# Roadmap d'exécution EcoBiome

**Statut :** plan d'exécution détaillé dérivé de `../../ROADMAP.md`.
**Date :** 15 août 2026.

Ce document décrit les dépendances, livrables et critères de sortie. Les
pourcentages du fichier racine sont indicatifs, non pondérés et ne définissent
aucun taux global ; les gates ci-dessous sont la référence opérationnelle.

## M0 — Socle de livraison et cohérence documentaire

**État :** `ADVANCED`.

### Déjà acquis

- package canonique `src/ecobiome` ;
- Git et CI Python/frontend ;
- LICENSE ;
- tag `v0.1` ;
- Collector reference ;
- politique d'audit et commits atomiques ;
- frontend intégré ;
- documentation structurée.

### À fermer

- remplacer les placeholders documentaires ;
- maintenir README, roadmap et project board synchronisés ;
- corriger la description GitHub historique « AquaBiome » ;
- décider explicitement public / privé / semi-public ;
- formaliser la politique de versions pré-v1.0.

### Exit criteria

- aucune documentation canonique vide ou placeholder ;
- statut `IMPLEMENTED/PROPOSED` cohérent ;
- CI verte ;
- politique de publication documentée.

---

## M1 — Chaîne de confiance scientifique

**État :** `ADVANCED`.

### Acquis

- provenance Source / Artifact / Representation / Segment ;
- Evidence et Claim ;
- Claim/Segment review events append-only ;
- Scientific Foundation V4 ;
- entités et assertions scientifiques ;
- corroboration / contradiction ;
- CAS SHA-256 ;
- Semantic Candidate V2.11 ;
- Scientific Assertion Projection Contract V1 ;
- Projection V1 publié sur `main` au commit
  `7c17e5d0db8d17d97bf4e6e557d96a7b5349a769` ;
- CI post-push Python #4 et Frontend #24 vertes.

### À fermer

- service d'orchestration candidate → review → projection ;
- parcours de démonstration reproductible.

### Exit criteria

Une source de test traverse toute la chaîne et produit une assertion
scientifique uniquement après review humaine, avec vérification de chaque SHA.

---

## M2 — Persistence sémantique V5

**État :** `OPEN` — design review obligatoire avant tout DDL ; implémentation non commencée.

### Design candidat actuel

V4 + six tables candidates :

- `semantic_provider_runs` ;
- `semantic_provider_run_claim_inputs` ;
- `semantic_provider_run_evidence_inputs` ;
- `semantic_provider_run_events` ;
- `semantic_provider_claim_origins` ;
- `semantic_candidates`.

### Review obligatoire avant DDL

Le pipeline V2.11 exige une review humaine des candidats. Le design V5 courant
doit donc démontrer où cette décision append-only est persistée. Si aucune des
six tables ne satisfait proprement ce contrat, créer une primitive dédiée est
préférable à détourner un événement provider.

**Conséquence :** le nombre « 31 tables » reste un candidat, pas un invariant,
tant que cette question n'est pas close.

### Exit criteria

- identité Schema V5 figée ;
- fresh-database seulement ;
- aucun ajout sous identité V4 ;
- aucune migration V4→V5 implicite ;
- request / raw response / validated output CAS séparés ;
- aucun secret dans le CAS ;
- provider run = occurrence, fingerprint réutilisable ;
- même candidate possible depuis plusieurs origins ;
- review humaine candidate durable et append-only ;
- tests intégrité / FK / schema identity / rétention CAS ;
- compatibilité Collector prouvée.

---

## M3 — Entités et couverture de projection

**Dépend de :** M1 ; persistence durable complète préférable après M2.

### Livrables

- mapping humainement reviewé des rôles `ENTITY_ARGUMENT` ;
- résolution taxonomique et identifiants d'autorité ;
- projection registry versionné ;
- extension relation par relation ;
- tests négatifs fail-closed ;
- gestion de correction/staleness.

### Exit criteria

- aucune relation non mappée n'est promue ;
- chaque mapping d'entité est traçable ;
- correction d'un Claim invalide les candidats obsolètes ;
- couverture mesurée par relation/type, pas par « taux d'acceptation ».

---

## M4 — Métamodèle écologique exécutable

**Dépend de :** M1 ; peut progresser en parallèle de M2/M3.

### Concepts

- `EcosystemSystem` ;
- `PhysicalStructure` ;
- `EnvironmentZone` ;
- `ResourceFlow` ;
- Taxon / Population / Individu ;
- occupation spatio-temporelle ;
- capteur / site / empreinte ;
- événement et intervention ;
- validité temporelle ;
- révisions immuables.

### Vertical slices pilotes

1. aquarium d'eau douce ;
2. mare extérieure ;
3. serre/potager ou aquaponie.

### Exit criteria

Un projet peut représenter sa topologie réelle sans mélanger structure
physique, système fonctionnel et zone environnementale.

---

## M5 — Modèle de connaissance écologique

### Objectif

Transformer la base scientifique générique en connaissance directement
interrogeable par le moteur écologique.

### Livrables

- taxons et organismes ;
- variables environnementales ;
- processus ;
- tolérances et réponses biologiques contextualisées ;
- interactions ;
- cycles de vie ;
- contexte géographique et temporel ;
- read models `Species`, `OptimalParameters`, `StressSignals`,
  `BiomeCompatibility`.

### Règle

Les read models ne deviennent pas une deuxième source de vérité. Ils sont
recalculables depuis les assertions et synthèses canoniques.

---

## M6 — Acquisition spécialisée

### Base déjà disponible

Collector CLI, acquisition, segmentation, Claim/Evidence, providers et
provenance.

### Extensions

- `ScientificCollector` ;
- `ProfessionalCollector` ;
- `WebCollector` ;
- `MediaCollector` ;
- `UserDataCollector` ;
- `SensorCollector`.

### Règles

Chaque collecteur rejoint le même provenance envelope. Les observations
utilisateur et capteurs restent distinctes de la littérature scientifique.

---

## M7 — Synthèse, conflits et tendances

### Livrables

- politiques SourceReliability / EvidenceAssessment ;
- agrégation multi-source ;
- corroboration et contradiction ;
- `knowledge_syntheses` exploitables ;
- TrendAnalyzer pour séries d'observations ;
- détection d'anomalies ;
- distinction conflit de sources / variation contextuelle / évolution réelle.

### Exit criteria

Une conclusion affiche :
- preuve favorable ;
- preuve contradictoire ;
- indépendance des sources ;
- contexte ;
- incertitude ;
- statut de synthèse.

---

## M8 — Moteur de processus et simulation

### Couches séparées

```text
topologie du projet
+ état observé
+ interventions
+ connaissance scientifique
+ forçages externes
+ modèles de processus
→ état estimé / trajectoires / explications
```

### Modules cibles

- chimie et cycles biogéochimiques ;
- hydrologie / circulation / temps de résidence ;
- géométrie et profondeur ;
- substrat / géologie ;
- plantes, bactéries, microfaune, animaux ;
- température, météo, saisons ;
- lumière / photopériode ;
- génétique lorsque pertinente ;
- énergie et résilience ;
- lune / activité solaire uniquement lorsque des modèles validés justifient
  leur inclusion.

### Exit criteria

Un premier processus déterministe est calibré, testé, versionné et capable
d'expliquer sa contribution à un cas aquarium/mare.

---

## M9 — Raisonnement, prédiction et conception

### Livrables

- hypothèses classées ;
- expérience discriminante suggérée ;
- EventPredictor ;
- scénarios ;
- BiomeGenerator ;
- comparaison prévu/réel ;
- recommandations sous contraintes.

### Règle

Aucune recommandation ne masque :
- les assertions utilisées ;
- les hypothèses ;
- le domaine de validité ;
- l'incertitude.

---

## M10 — UX, distribution et v1.0

### UX scientifique

Trois niveaux de présentation :

- débutant ;
- intermédiaire ;
- avancé.

Fonctions :
- vue système/zones/flux ;
- timeline ;
- provenance drill-down ;
- incertitude ;
- données manquantes ;
- comparaison scénarios ;
- « Pourquoi ça marche ? ».

### Distribution — après vertical slice

- worker local ;
- scheduler/retry/DLQ ;
- quotas ;
- cloud provider-neutral ;
- EcoBiome@home ;
- apprentissage communautaire gouverné.

### v1.0

La v1.0 exige :
- sauvegarde/export ;
- politique de migration ;
- sécurité/privacy ;
- API stable ;
- docs utilisateurs ;
- packaging ;
- tests de bout en bout ;
- comportement sûr hors ligne.

---

# Séquence des prochains lots

## Lot N0 — Publication de Projection V1 — TERMINÉ

- review read-only du commit : terminée ;
- push fast-forward distinctement autorisé et exécuté : terminé ;
- CI post-push : Python #4 et Frontend #24 vertes ;
- canon distant :
  `main@7c17e5d0db8d17d97bf4e6e557d96a7b5349a769`.

## Lot N1 — V5 design closure — ACTIF

- auditer les six tables candidates ;
- résoudre d'abord la persistence durable et append-only de la review humaine
  des Semantic Candidates V2.11 ;
- décider si une primitive dédiée de review-event est requise ;
- seulement ensuite geler primitives, DDL, index, invariants et CAS retention.

## Lot N2 — V5 implementation

- fresh DB ;
- repositories/contracts ;
- tests d'identité et intégrité ;
- compat Collector.

## Lot N3 — Entity mapping + projection coverage

- premier mapping entité reviewé ;
- 3 à 5 relations supplémentaires à forte valeur ;
- métrique de couverture.

## Lot N4 — Vertical slice aquarium/mare

- topologie minimale ;
- observations ;
- une petite base d'assertions ;
- un processus déterministe ;
- explication sourcée ;
- incertitude et données manquantes.

## Lot N5 — User/Sensor acquisition

- ingestion séparée ;
- timeline ;
- qualité et calibration ;
- comparaison science ↔ réel.

## Lot N6 — Synthèse et simulation

- contradictions ;
- synthèses ;
- tendances ;
- scénarios ;
- UI intégrée.

Les workers distribués et EcoBiome@home restent après N4/N6 sauf besoin
démontré par les charges réelles.
