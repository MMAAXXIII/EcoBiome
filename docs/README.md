# Documentation EcoBiome

Ce répertoire distingue cinq niveaux documentaires :

1. **Vision** — mission, proposition de valeur et principes de gouvernance.
2. **Roadmap** — ordre d'exécution, dépendances et critères de sortie.
3. **Architecture** — frontières techniques, plans distribués et modèle de
   données.
4. **Conception scientifique** — décisions de domaine, hypothèses et questions
   ouvertes.
5. **Références** — textes historiques/inter-IA conservés sans les présenter
   comme du code déjà implémenté.

## Lecture recommandée

1. [`vision/VISION.md`](vision/VISION.md)
2. [`vision/GOVERNING_PRINCIPLES.md`](vision/GOVERNING_PRINCIPLES.md)
3. [`../ROADMAP.md`](../ROADMAP.md)
4. [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md)
5. [`architecture/ARCHITECTURE.md`](architecture/ARCHITECTURE.md)
6. [`architecture/DATA_MODEL.md`](architecture/DATA_MODEL.md)
7. [`scientific/UNIVERSAL_ECOSYSTEM_METAMODEL.md`](scientific/UNIVERSAL_ECOSYSTEM_METAMODEL.md)
8. [`scientific/ECOSYSTEM_MODES_AND_KNOWLEDGE.md`](scientific/ECOSYSTEM_MODES_AND_KNOWLEDGE.md)
9. [`SOURCE_REGISTER.md`](SOURCE_REGISTER.md)

`roadmap/LONG_TERM_ROADMAP.md` et `roadmap/INTER_AI_IDEAS.md` restent des
sources conceptuelles utiles, mais `../ROADMAP.md` et `roadmap/ROADMAP.md`
portent désormais l'ordre d'exécution canonique.

## Statuts utilisés

Le vocabulaire ci-dessous est fermé pour les documents canoniques : tout
nouveau statut doit d'abord être défini ici ou normalisé vers un statut
existant.

| Statut | Sens |
|---|---|
| `IMPLEMENTED` | Présent et validé dans le dépôt courant. |
| `ADVANCED` | Largement réalisé, quelques gates restent ouverts. |
| `PARTIAL` | Sous-ensemble réel déjà implémenté. |
| `PROPOSED` | Cible ou décision proposée, non encore implémentée. |
| `EXPERIMENTAL` | Prototype ou piste nécessitant une validation. |
| `OPEN` | Question non arbitrée. |
| `DEFERRED` | Élément volontairement reporté. |
| `REFERENCE` | Source conservée pour mémoire, sans autorisation implicite. |

Une proposition documentaire n'autorise jamais, à elle seule, une
modification du code, l'ajout d'une dépendance, un déploiement cloud, une
mutation Git distante ou une automatisation agissant sur un écosystème réel.
