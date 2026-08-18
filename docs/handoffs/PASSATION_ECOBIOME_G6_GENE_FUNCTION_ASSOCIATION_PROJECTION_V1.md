# EcoBiome — G6 Gene Function Association Projection V1

## Gate
ECOBIOME_G6_GENE_FUNCTION_ASSOCIATION_PROJECTION_V1_6_RESUME_FIX2

## Canon de départ
- main@9bae2b6bd3e3d87c50e7c3290061f691d404e3de
- tree abaef665342a36ec6c58a6d9482f3be0906145ea
- Scientific Assertion Projection V1.5
- Scientific Foundation Schema V6

## Slice
- relation : primarily_associated_with
- semantic type : gene_function_association
- epistemic class : association_only
- rôles : gene_set, process
- builder réutilisé : spec_binary_entity_relation_v1

## Décisions
- Projection passe à V1.6.
- Un seul mapping relation/type est ajouté.
- gene_set et process restent des ENTITY_ARGUMENT.
- Projection ne décide pas si gene_set désigne un gène, une famille de gènes
  ou un ensemble de gènes : elle consomme uniquement l'identité
  ScientificEntity explicitement revue.
- association_only ne doit jamais être renforcé en causalité.
- Aucun nouveau builder.
- Aucun Schema V7.
- Aucune création automatique de ScientificEntity.
- Aucune acceptation scientifique automatique.
- Aucune persistence automatique de ScientificAssertion.

## Identité Projection V1.6
- SHA-256 canonique : bf1a839602b76b4475651c3c07fb701d77ad96fd5ecd90c3ffff71d555755d54

## Critères d'acceptation
- mapping exact présent une seule fois ;
- deux rôles ENTITY_ARGUMENT ;
- fail-closed si gene_set ou process n'est pas reviewé ;
- contrat et tests historiques convergés vers V1.6 ;
- Ruff, mypy, tests ciblés et suite complète PASS ;
- worktree propre et index vide après commit local ;
- aucun push dans ce gate.

## Historique de reprise
- Gate initial : échec avant validation et avant commit sur une recherche
  ROADMAP contenant un backslash-n littéral.
- Reprise initiale : arrêt fail-closed avant mutation à cause du parsing
  présentation de git status --porcelain.
- FIX1 : Ruff PASS, mypy PASS, 48/49 tests ciblés PASS ; arrêt avant staging
  et avant commit sur l'ancienne assertion de portée à 7 mappings.
- FIX2 : assertion de portée convergée à 8 mappings, 49/49 tests ciblés PASS,
  455 tests projet PASS et 1 skipped, identité Projection V1.6 vérifiée, puis
  création du commit local audité.

## Suite
Le commit local doit être audité avant toute publication distante.

Ne pas pousser, fusionner, créer de PR ou sélectionner automatiquement un
sixième mapping G6 sans autorisation distincte.
