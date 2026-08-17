# EcoBiome — Roadmap canonique

**Version :** 2.6
**Date de révision :** 17 août 2026
**Statut :** feuille de route de référence ; l'état Git et les tests restent la
source de vérité sur l'implémentation.

## 1. Pourquoi cette révision

La roadmap 1.2 du 4 août 2026 ne reflétait plus le dépôt :

- le socle Git/CI est largement consolidé ;
- SQLite a déjà été retenu pour le cœur scientifique local ;
- la persistence scientifique **V6** est le runtime physique canonique (34 tables,
  45 index) ;
- le Collector, Claim/Evidence et les reviews existent ;
- Semantic Candidate V2.11 est intégré ;
- Scientific Assertion Projection Contract V1 est publié sur `main` ;
- ses CI post-push sont vertes ;
- plusieurs concepts initialement décrits comme futures « tables » doivent
  maintenant être des vues ou produits dérivés de la connaissance canonique.

Cette roadmap remplace donc l'ancienne progression linéaire par des jalons
dépendants les uns des autres.

## 2. North Star

Construire un EcoBiome capable de :

1. représenter un écosystème réel ;
2. ingérer observations, capteurs et sources scientifiques sans les confondre ;
3. transformer les sources en connaissances traçables et revues ;
4. expliquer les mécanismes plausibles d'un état observé ;
5. simuler des scénarios avec incertitude ;
6. proposer des mesures ou interventions justifiées ;
7. apprendre de plusieurs projets sous gouvernance explicite.

Cas d'usage directeur : **« Pourquoi ça marche ? »**

## 3. État global au 17 août 2026

Canon distant après premier slice G6 / PR #18 :
`main@7db0079fd76432ea67b543ef9577845ca7682470`.

| Jalon | État | Estimation indicative |
|---|---|---:|
| M0 — Socle, CI, hygiène de livraison | `ADVANCED` | 90 % |
| M1 — Chaîne de confiance scientifique | `ADVANCED` | 85 % |
| M2 — Persistence scientifique et sémantique V6 | `ADVANCED` | 75 % |
| M3 — Couverture sémantique et entités | `PARTIAL` | 25 % |
| M4 — Métamodèle écologique exécutable | `PROPOSED` | 20 % |
| M5 — Collecteurs spécialisés | `PARTIAL` | 35 % |
| M6 — Synthèse, conflits et tendances | `PARTIAL` | 25 % |
| M7 — Moteur de processus et simulation | `PROPOSED` | 10 % |
| M8 — Prédiction / recommandations / biomes | `DEFERRED` | 5 % |
| M9 — Produit et UX scientifique | `PARTIAL` | 35 % |
| M10 — Distribution, EcoBiome@home, v1.0 | `DEFERRED` | 10 % |

Ces estimations par jalon sont **indicatives et non pondérées**. Elles ne sont
pas agrégées en un pourcentage global de projet tant qu'une méthode de
pondération reproductible n'est pas définie.

## 4. Priorités

### P0 — Fermer la chaîne de vérité scientifique

1. **terminé** — publier/revoir Scientific Assertion Projection V1 ;
2. **terminé** — persistence durable append-only et surface opérateur de
   **review humaine des candidats V2.11** ;
3. **terminé** — auditer et figer l'identité physique du **Schema V6** :
   34 tables, 45 index, identité de design, intégrité/FK et fresh-database ;
4. **terminé / supplanté** — l'ancien objectif « Schema V5 fresh-database »
   est déjà couvert par le runtime V6 canonique ; aucune migration V5
   rétroactive ne doit être créée ;
5. **terminé au niveau persistence** — Semantic Candidates, reviews,
   provider runs et candidate origins possèdent déjà leurs structures V6 ;
6. **terminé** — parcours end-to-end Collector → provider-run →
   candidate-origin → CAS prouvé sur V6 par un bridge transactionnel
   append-only, sans Schema V7 et sans acceptation scientifique automatique.

### P1 — Étendre sans perdre le fail-closed

1. **terminé pour G5** — entity resolution humaine sur V6 : workflow
   opérateur, ancrage source/Evidence exact, name usages reviewés et
   historique append-only sont disponibles ;
2. **en cours pour G6** — mappings de projection relation par relation ; slices publiés : `poses_significant_threat_to / industry_impact`, puis `adversely_affects / knowledge_gap` ;
3. aucun « accept all » universel ;
4. read models pour Species, tolérances, paramètres et interactions ;
5. synthèses corroboration/contradiction avec niveau de preuve.

### P2 — Construire le vertical slice écologique

Premier objectif produit de bout en bout :

```text
profil aquarium ou mare
→ zones / structures / flux
→ observations et interventions
→ connaissances scientifiques
→ un petit ensemble de processus déterministes
→ état / risque / incertitude
→ « Pourquoi ça marche ? »
```

Le vertical slice doit fonctionner avant l'infrastructure distribuée.

### P3 — Étendre les sources et les usages

- ScientificCollector ;
- ProfessionalCollector ;
- Web/MediaCollector ;
- UserDataCollector ;
- SensorCollector ;
- météo et forçages externes versionnés.

### P4 — Simulation, prédiction et conception

- TrendAnalyzer ;
- EventPredictor ;
- moteur de scénarios ;
- BiomeGenerator contraint par preuves ;
- comparaison prévu/réel ;
- recommandations explicables.

### P5 — Distribution et apprentissage gouverné

- worker local ;
- scheduler ;
- quotas et mode sûr ;
- cloud optionnel ;
- EcoBiome@home ;
- agrégation communautaire consentie.

## 5. Décisions structurantes

### Le cœur canonique n'est pas une collection de tables métier plates

Les anciens concepts `Species`, `OptimalParameters`, `StressSignals`,
`BiomeCompatibility`, `Trends` et `Conflicts` restent utiles, mais doivent
principalement devenir des **read models, synthèses ou vues** construites à
partir :

- des entités scientifiques ;
- des assertions scientifiques ;
- de leurs preuves et reviews ;
- du contexte écologique ;
- des observations du projet.

Ils ne doivent pas dupliquer la vérité canonique.

### SQLite est la base locale canonique actuelle

Le choix « SQLite ou Supabase » n'est plus une question ouverte pour le cœur
scientifique local. Une couche cloud future doit rester une frontière de
service optionnelle.

### IA ≠ vérité

Les providers IA peuvent proposer ou extraire. La promotion scientifique reste
déterministe, auditée et revue.

### Distribué après le vertical slice

EcoBiome@home, GPU mutualisé et orchestration cloud restent dans la vision,
mais ne doivent pas retarder le premier produit scientifique explicable.

## 6. Prochains gates

Ordre recommandé :

```text
G0  TERMINÉ — review du commit Projection V1
G1  TERMINÉ — publication fast-forward + CI post-push de Projection V1
G2  TERMINÉ — review humaine append-only des Semantic Candidates V2.11 + CLI opérateur
G3  TERMINÉ — audit de cohérence + réconciliation roadmap / Scientific Foundation V6
G4  TERMINÉ — provider-run/origins/CAS + compatibilité Collector sur V6
G5  TERMINÉ — entity-resolution opérateur + mappings reviewés sur V6
G6  EN COURS — deux slices relation/type : `poses_significant_threat_to / industry_impact`, `adversely_affects / knowledge_gap`
G7  Vertical slice aquarium/mare « Pourquoi ça marche ? »
G8  Collecteurs user/sensor + synthèse/trends
G9  Simulation et UX scientifique intégrée
```

Chaque gate garde les règles EcoBiome : audit, périmètre exact, validation,
journal, passation et autorisation distincte pour les mutations sensibles.

## 7. Définition de la première vraie démonstration EcoBiome

Le projet aura franchi un cap produit majeur lorsqu'une démonstration pourra :

1. créer un aquarium ou une mare avec géométrie, zones et organismes ;
2. importer quelques observations utilisateur ;
3. rattacher des mesures instrumentales ;
4. importer au moins une source scientifique ;
5. produire Claim/Evidence/review/candidat/assertion ;
6. synthétiser ce qui est supporté ou contesté ;
7. exécuter un processus écologique déterministe ;
8. expliquer un état observé avec provenance ;
9. afficher l'incertitude et les données manquantes ;
10. comparer une intervention simulée à l'état actuel.

C'est la priorité produit avant le « supercalculateur logiciel ».

## 8. Documents liés

- `docs/vision/VISION.md`
- `docs/vision/GOVERNING_PRINCIPLES.md`
- `docs/roadmap/ROADMAP.md`
- `docs/roadmap/LONG_TERM_ROADMAP.md`
- `docs/roadmap/INTER_AI_IDEAS.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/scientific/UNIVERSAL_ECOSYSTEM_METAMODEL.md`
- `docs/scientific/ECOSYSTEM_MODES_AND_KNOWLEDGE.md`
- `docs/SOURCE_REGISTER.md`
