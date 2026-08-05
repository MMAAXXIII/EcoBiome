# Principes directeurs EcoBiome

## 1. Analyser avant d'agir

Une opération risquée commence par un audit en lecture seule. La remédiation,
le commit, le push, le déploiement et l'automatisation sont des autorisations
distinctes.

## 2. Travailler par lots atomiques

Chaque lot doit avoir :

- un périmètre explicite ;
- une sauvegarde ;
- des invariants vérifiables ;
- des validations adaptées ;
- un journal ;
- une possibilité de retour documentée.

## 3. Préserver la source de vérité

Le code, les tests et l'historique Git décrivent l'existant. Les documents de
vision décrivent une cible et doivent annoncer leur statut.

## 4. Respecter la prudence scientifique

EcoBiome distingue :

- fait observé ;
- relation spatiale ou temporelle ;
- interaction observée ;
- hypothèse causale ;
- estimation ;
- simulation ;
- évaluation contextuelle.

La proximité, la corrélation ou une trajectoire ne prouvent pas une causalité.

## 5. Conserver provenance et incertitude

Une donnée utile conserve au minimum :

- source et date ;
- contexte et méthode ;
- unité ;
- confiance ou incertitude ;
- statut mesuré, déclaré, dérivé, estimé ou simulé.

## 6. Rester local-first et consent-driven

Le stockage local est disponible sans cloud obligatoire. La contribution
communautaire, l'analyse par un service tiers, l'entraînement d'un modèle et
le partage de données demandent des consentements séparés.

## 7. Protéger les utilisateurs et les écosystèmes

Les workers ne doivent pas saturer CPU, GPU, RAM, NVMe ou HDD. Une commande
agissant sur un chauffage, une pompe, un dosage ou un autre actionneur doit
avoir des limites, un état sûr, une journalisation et une reprise manuelle.

## 8. Isoler les dépendances lourdes

Les moteurs de transcription, d'embeddings ou de calcul GPU vivent dans des
workers ou extras spécialisés. Ils ne sont pas imposés au noyau.

## 9. Garantir la reproductibilité

Les imports, formats, tests, versions et migrations doivent être déterministes.
Les données locales, caches et secrets restent hors Git.

## 10. Ne pas choisir une technologie trop tôt

Le métamodèle et les contrats précèdent le choix d'une base, d'une file de
tâches, d'un orchestrateur ou d'un fournisseur cloud.
