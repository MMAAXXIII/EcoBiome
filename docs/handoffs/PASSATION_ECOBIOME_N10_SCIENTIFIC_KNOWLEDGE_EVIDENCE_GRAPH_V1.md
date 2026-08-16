# EcoBiome — Passation N10 Scientific Knowledge Extraction, Entity Profiles, Ecosystem Observables & Evidence Graph V1

## Statut de cette implémentation

Implémentation locale N10 V1, sans staging, commit, push, merge, rebase ni mutation Git distante.

## Décisions appliquées

- N10 est une couche logique/read-model au-dessus des primitives Collector/persistence existantes ; aucune table SQLite parallèle n’est créée.
- `Source` et `Passage` restent fournis par le Collector existant.
- un `Claim` N10 démarre `pending` et exige au moins une `Evidence` primaire exacte ;
- la revue de Claim est append-only et les transitions vers `rejected`/`superseded`, puis `reopen`, sont explicites ;
- `confidence` est une dimension facultative et ne vaut jamais acceptation ;
- une dimension absente dans `ApplicabilityScope` signifie **inconnue**, jamais « universelle » ;
- `Morphotype` reste distinct de `LivingEntity`/taxon ;
- `EcosystemObservable` accepte les phénomènes non vivants, notamment le mulm ;
- `EcosystemObservation` représente une occurrence observée dans un écosystème et reste distinct de la définition réutilisable de l’observable ;
- les relations conservent séparément les Claims `supports` et `contradicts` ; aucune contradiction n’est effacée ;
- `SourceDependency=unknown` ne compte jamais comme corroboration indépendante ;
- les profils sont calculés depuis les relations et Claims acceptés ; aucun texte de fiche opaque n’est stocké ;
- une image ne peut être attachée que si `usage_permission=allowed` ET `verification_status=verified` ;
- l’agrégateur bio-indicateur ne déduit aucune causalité : il rend concordance, non-concordance, données manquantes et avertissement explicite ;
- absence de données de facteur => `not_evaluated`, jamais faux « tout va bien » ;
- les valeurs numériques N10 ne deviennent jamais implicitement des seuils opérationnels.

## Bridge Collector

`collector_bridge.py` reconstruit l’Evidence exacte depuis `SourceEvidenceRow` + `SegmentsRow.text_inline`, vérifie le span et le SHA-256, puis transforme un Claim Collector déjà `atomic` en Claim N10 sans inventer de sémantique.

Le bridge refuse :

- Claim non atomique ;
- identité Claim/Evidence incohérente ;
- Evidence hors span ;
- hash Evidence incorrect ;
- Segment sans texte exact ;
- rôle Claim/Evidence non supporté.

## Cas de référence obligatoires

### Algues

- morphotype vert filamenteux distinct de toute identification taxonomique certaine ;
- relation `grows_on` construite depuis Claims acceptés ;
- support et contradiction restent simultanément visibles ;
- profil calculé depuis le graphe ;
- image non vérifiée refusée.

### Mulm

- modélisé comme `EcosystemObservable`, pas comme être vivant ;
- observation semi-quantitative `ordinal_abundance` ;
- localisation et trajectoire séparées ;
- données O2 manquantes restent explicitement manquantes ;
- aucune conclusion bénéfique/nuisible ou causale n’est créée automatiquement.

## Hors périmètre volontaire

- aucune migration/schema SQLite ;
- aucune modification du Collector existant ;
- aucune modification de Semantic Candidate / Projection V1 ;
- aucune modification N9.2 / alertes ;
- aucune UI/frontend ;
- aucun provider IA/réseau ;
- aucune ingestion automatique d’anciennes conversations comme preuve scientifique.

Les anciennes conversations pourront ultérieurement produire des hypothèses à vérifier, jamais une preuve scientifique automatique.

## Critères de validation du script

- préchecks branche/HEAD/staging ;
- cibles N10 exclusivement nouvelles ;
- `uv lock --check` hors réseau ;
- parse AST N10 ;
- prévalidation AST + Ruff du payload embarqué avant toute écriture dans le dépôt ;
- Ruff N10 ;
- mypy N10 ;
- pytest N10 ciblé ;
- pytest complet projet ;
- staging vide après validation ;
- HEAD/branche inchangés ;
- état Git hors cibles N10 inchangé ;
- rollback automatique exact si une validation échoue ;
- ZIP PASS/FAIL copié dans `C:\Users\oboco\Downloads`.

## Prochaine frontière sensible

Cette implémentation ne constitue pas une autorisation de staging/commit/push. Toute mutation Git sensible reste une étape séparée nécessitant autorisation explicite.
