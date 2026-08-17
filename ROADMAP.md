# EcoBiome — Roadmap canonique

**Version :** 2.1
**Date de révision :** 17 août 2026
**Statut :** feuille de route de référence ; l'état Git et les tests restent la
source de vérité sur l'implémentation.

## 1. Pourquoi cette révision

La roadmap 1.2 du 4 août 2026 ne reflétait plus le dépôt :

- le socle Git/CI est largement consolidé ;
- SQLite a déjà été retenu pour le cœur scientifique local ;
- la persistence scientifique V4 existe ;
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

## 3. État global au 15 août 2026

Canon distant vérifié après intégration de la PR #13 :
`main@02539f7854f1cebdcf8b74c75c9abefd157df6b6`.

| Jalon | État | Estimation indicative |
|---|---|---:|
| M0 — Socle, CI, hygiène de livraison | `ADVANCED` | 90 % |
| M1 — Chaîne de confiance scientifique | `ADVANCED` | 85 % |
| M2 — Persistence sémantique V5 | `OPEN` | 20 % |
| M3 — Couverture sémantique et entités | `PARTIAL` | 15 % |
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
3. auditer puis figer les primitives, tables, index, invariants et la rétention
   CAS du Schema V5 ;
4. implémenter Schema V5 en fresh-database ;
5. persister les candidats sémantiques, leurs origins et les runs provider ;
6. prouver identité de schéma, intégrité/FK, rétention CAS et compatibilité
   Collector.

### P1 — Étendre sans perdre le fail-closed

1. entity resolution avec review humaine ;
2. mappings de projection relation par relation ;
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
G3  Audit de cohérence roadmap/persistence et gel du design scientifique V6 courant
G4  Schema V5 fresh-database + tests d'identité/intégrité
G5  Persistence provider-neutral semantic_candidates + reviews
G6  Persistence provider-run/origins/CAS
G7  Entity resolution + mappings reviewés
G8  Extension progressive des projections
G9  Vertical slice aquarium/mare « Pourquoi ça marche ? »
G10 Collecteurs user/sensor + synthèse/trends
G11 Simulation et UX intégrée
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
