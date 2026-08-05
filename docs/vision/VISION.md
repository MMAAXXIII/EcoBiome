# Vision EcoBiome

**Statut :** vision de long terme.
**Horizon :** plateforme scientifique locale, distribuée et reproductible.

## Mission

EcoBiome doit aider à **gérer, observer, comprendre, concevoir et améliorer**
des écosystèmes réels. La plateforme part d'un socle aquatique, mais sa cible
est multi-écosystème :

- aquarium, mare, étang, cours d'eau et zone humide ;
- potager, serre, culture en sol et culture hors-sol ;
- terrarium, paludarium et riparium ;
- aquaponie et systèmes hybrides reliés par des flux.

EcoBiome associe un moteur scientifique Python, des interfaces utilisateur,
des collecteurs, des journaux, des médias, des modèles de connaissance et,
à terme, des capacités de calcul distribuées.

## Proposition de valeur

Le produit doit couvrir quatre niveaux sans sacrifier les usages quotidiens :

```text
Gérer
→ Observer
→ Comprendre
→ Concevoir et améliorer
```

Le suivi pratique — mesures, photos, populations, équipements, tâches et
historique — est un socle. La différenciation à long terme vient du
raisonnement explicable, de la provenance, de la topologie versionnée, des
budgets et de l'expérimentation mesurable.

## Vision scientifique

Une conclusion EcoBiome doit pouvoir relier :

```text
observation
→ qualité et incertitude
→ incohérences
→ hypothèses classées
→ preuves
→ expérience discriminante
→ résultat
```

La plateforme doit conserver la source, la date, la licence, le contexte, le
niveau de confiance et le statut épistémique des données. Une observation
privée ou un témoignage ne devient pas silencieusement une vérité universelle.

## Vision d'architecture

La cible distribuée sépare :

- **Control Plane** — API, interface, identité, orchestration et suivi des jobs ;
- **Data Plane** — collecte, transcription, normalisation, analyse et artefacts ;
- **Compute Plane** — workers CPU/GPU locaux ou cloud ;
- **Cloud Plane** — résultats partagés, index et droits ;
- **Worker Plane** — contribution volontaire et limitée des machines.

Le logiciel doit rester utilisable localement. Le cloud et le calcul volontaire
sont des capacités optionnelles, soumises au consentement et à des quotas.

## Supercalculateur logiciel

EcoBiome peut, à terme, segmenter des tâches indépendantes et mutualiser la
puissance disponible :

- lots de collecte et de normalisation ;
- transcription isolée ;
- embeddings et analyses ;
- simulations et sous-problèmes ;
- calcul nocturne ou pendant l'inactivité.

Cette cible ne justifie pas une dépendance lourde dans le package principal.
Les workers spécialisés restent isolés.

## Stockage cible

- **NVMe** : calcul intensif et artefacts temporaires ;
- **HDD** : archives, datasets et stockage froid ;
- **Cloud** : résultats partagés et index global ;
- **Réseau volontaire** : calcul distribué, stockage optionnel et contrôlé.

## Résultat recherché

Un moteur scientifique stable, explicable, reproductible et collaboratif,
capable d'évoluer d'un outil local vers une infrastructure distribuée sans
imposer cette complexité à tous les utilisateurs.
