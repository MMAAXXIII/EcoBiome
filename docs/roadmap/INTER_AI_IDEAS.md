# Idées inter-IA

Ce document transforme les suggestions inter-IA en backlog explicite. Une idée
n'est pas une décision d'implémentation.

## Fondations déjà réalisées

- package canonique ;
- retrait du package racine masquant ;
- résolution d'import stable ;
- audit pré-push ;
- tests Python et frontend ;
- politique de données locales ;
- push contrôlé sans force.

## Candidats prioritaires

### Worker local minimal

- déclaration de capacité ;
- exécution d'une tâche déterministe ;
- timeout ;
- journal ;
- hash des résultats ;
- arrêt propre.

### Scheduler minimal

- états `pending`, `processing`, `done`, `failed` et `dead-letter` ;
- lease limitée ;
- retry et backoff ;
- idempotence ;
- absence de fournisseur imposé.

### Politique de stockage

- chemins hot/cold configurables ;
- quotas ;
- nettoyage ;
- manifeste des artefacts ;
- checksums ;
- rétention.

### Mode sûr

- pause pendant l'usage actif ;
- mode nuit ;
- limites CPU, GPU, RAM et disque ;
- surveillance de température et batterie ;
- consentements par catégorie de tâche.

### Interface cloud

Contrat fournisseur-agnostique :

```text
upload
download
list
delete
```

Les fournisseurs cités dans les sources restent des exemples, pas des choix.

## Idées à différer

- orchestration Kubernetes, Nomad ou Ray ;
- double calcul systématique ;
- stockage distribué pair-à-pair ;
- entraînement communautaire ;
- automatisation physique en boucle fermée.

Ces éléments exigent d'abord des modèles de menace, coûts, consentements,
protocoles de reprise et critères de sécurité biologique.
