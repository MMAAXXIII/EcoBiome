# EcoBiome

EcoBiome est une plateforme scientifique open source pour **gérer, observer,
comprendre, simuler, concevoir et améliorer des écosystèmes réels**.

Le projet part des écosystèmes aquatiques, mais son architecture cible des
systèmes composables : aquarium, mare, étang, zone humide, serre, potager,
culture hors-sol, aquaponie, paludarium et autres systèmes hybrides reliés par
des flux.

## Promesse produit

EcoBiome doit permettre de répondre à des questions comme :

- **Que se passe-t-il dans mon écosystème ?**
- **Pourquoi cela fonctionne-t-il — ou pourquoi cela dérive-t-il ?**
- **Quelles données manquent pour conclure ?**
- **Que risque-t-il de se passer si les conditions changent ?**
- **Quelle intervention est compatible avec les contraintes biologiques ?**
- **Comment concevoir un biome plus stable, résilient et explicable ?**

Les réponses doivent rester traçables vers les observations, les sources
scientifiques, les hypothèses, les modèles et les simulations qui les
supportent.

## Contrat scientifique

EcoBiome distingue explicitement :

- données de sources scientifiques ;
- observations utilisateur ;
- mesures capteurs ;
- faits ou assertions scientifiques validés ;
- estimations et inférences ;
- résultats de modèles ;
- simulations et recommandations.

Une extraction IA ou un témoignage ne devient jamais automatiquement une
vérité scientifique canonique.

La chaîne scientifique canonique visée est :

```text
Source
→ Evidence
→ Claim
→ review humaine
→ candidat sémantique canonique
→ projection scientifique fail-closed
→ assertion scientifique
→ synthèse / conflit / niveau de preuve
→ raisonnement écologique
```

Les contrats et primitives nécessaires jusqu'à **Scientific Assertion Projection
Contract V1** sont maintenant publiés sur `main`. La persistence durable des
candidats sémantiques, de leur review humaine et des runs provider relève du
prochain jalon V5 ; la synthèse écologique et le raisonnement de bout en bout
restent partiels ou à construire.

## Architecture

Le package Python canonique est `src/ecobiome`.

La cible sépare :

- **Control Plane** — API, interfaces, identité et orchestration ;
- **Data Plane** — acquisition, normalisation, provenance et analyse ;
- **Compute Plane** — calculs et workers spécialisés ;
- **Cloud Plane** — partage et index optionnels ;
- **Worker Plane** — contribution volontaire et limitée.

Le produit reste **local-first**. Le cloud et EcoBiome@home sont des extensions
optionnelles et ne doivent pas devenir des prérequis du cœur scientifique.

## État actuel

Le socle comprend notamment :

- FastAPI et interfaces existantes ;
- frontend React/Vite/TypeScript ;
- Collector CLI et chaîne d'acquisition ;
- provenance Claim/Evidence et reviews append-only ;
- persistence scientifique SQLite V4 + CAS SHA-256 ;
- candidat sémantique canonique V2.11 ;
- Scientific Assertion Projection Contract V1 publié sur `main` ;
- CI Python et frontend vertes après le push Phase B du 15 août 2026.

La priorité immédiate est de **fermer le design V5 avant tout DDL** : décider
où persiste la review humaine append-only des Semantic Candidates V2.11,
puis figer primitives, tables, index, invariants et rétention CAS. Ensuite
viennent l'implémentation V5, l'extension contrôlée des projections
scientifiques, le modèle écologique exécutable et un premier vertical slice
expliquant un écosystème réel de bout en bout.

## Documentation

Lecture recommandée :

1. [`docs/vision/VISION.md`](docs/vision/VISION.md)
2. [`docs/vision/GOVERNING_PRINCIPLES.md`](docs/vision/GOVERNING_PRINCIPLES.md)
3. [`ROADMAP.md`](ROADMAP.md)
4. [`docs/roadmap/ROADMAP.md`](docs/roadmap/ROADMAP.md)
5. [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md)
6. [`docs/architecture/DATA_MODEL.md`](docs/architecture/DATA_MODEL.md)
7. [`docs/SOURCE_REGISTER.md`](docs/SOURCE_REGISTER.md)
