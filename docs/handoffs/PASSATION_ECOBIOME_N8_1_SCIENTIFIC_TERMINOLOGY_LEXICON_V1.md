# PASSATION ECOBIOME — N8.1 SCIENTIFIC TERMINOLOGY & LEXICON V1

Date: 2026-08-16
Statut: candidat local à valider avant tout commit/push
Base attendue: N7 validé localement, branche `agent/n5-canonical-project-event-seam-v1`,
HEAD `c2aa03cfb4a2707620e6da54b26fba12e795afcb`.

## Décision

N8.1 remplace le candidat N8 R2 non validé et intègre cumulativement :

1. N8 Progressive UX & Guided Data Entry V1 ;
2. normalisation des libellés physico-chimiques avec symboles/formules et unités ;
3. Lexique scientifique EcoBiome accessible depuis la navigation principale.

Ne pas implémenter une nouvelle logique scientifique ou un nouveau seuil de diagnostic sans autorisation explicite.

## Principes terminologiques

- Le nom pédagogique et la définition scientifique exacte sont distingués.
- `pH` est affiché comme `pH — potentiel hydrogène`, mais le lexique donne la définition IUPAC
  `pH = -log10(aH+)`.
- Les espèces chimiques sont visibles dans les libellés quand elles existent :
  `O₂`, `NH₃`, `NH₄⁺`, `NO₂⁻`, `NO₃⁻`, `PO₄³⁻`, `Cl⁻`, `Ca²⁺`, `Mg²⁺`, `CO₂`.
- Les grandeurs sans formule chimique utilisent un symbole physique ou un acronyme pertinent :
  `T`, `κ`, `ORP/Eh`, `PAR/PPFD`, `MES/TSS`, `Q`.
- Les unités restent visibles au point de saisie et au point d’affichage.

## Lexique scientifique

Nouveau fichier :
`bolt-dashboard/src/lib/scientificGlossary.ts`

Nouvelle vue :
`bolt-dashboard/src/views/ScientificGlossaryView.tsx`

La vue fournit :
- recherche textuelle ;
- catégories ;
- définition ;
- utilité ;
- chimie/symbole ;
- facteurs influents ;
- relations avec les autres paramètres ;
- formules et domaine d’application ;
- points d’attention ;
- sources externes.

## Oxygène dissous

La méthode simplifiée Sandre est documentée :

`Cs(T) = 14.64 - 0.4227T + 0.009937T² - 0.0001575T³ + 0.000001125T⁴`

puis :

`SatO2(%) = O2_mesuré * 100 / Cs(T)`

Domaine explicitement signalé : pression 1013 mbar et salinité nulle.

Le lexique signale aussi que les calculs plus généraux doivent intégrer pression et salinité, conformément
aux méthodes modernes de solubilité de l'oxygène (USGS / Benson & Krause).

## Ammoniac

Le lexique documente l’équilibre NH₃/NH₄⁺ et l’approximation Emerson :

`pKa = 0.09018 + 2729.92 / T(K)`

`fNH3 = 1 / (10^(pKa - pH) + 1)`

Les unités et la base `mg N/L` versus `mg/L de composé` doivent rester explicitement distinguées.

## KH / alcalinité

N8.1 refuse d’assimiler scientifiquement KH et alcalinité dans tous les cas.
Le KH reste le terme aquariophile visible ; le lexique explique le rôle principal de HCO₃⁻/CO₃²⁻
et précise que l’alcalinité peut recevoir d’autres contributions.

## PAR / PPFD

Le lexique présente le domaine classique PAR 400–700 nm et préfère expliciter PPFD pour la grandeur
en `µmol photons·m⁻²·s⁻¹`. Il signale que la littérature récente discute l’apport du far-red >700 nm.

## Fichiers N8.1

Modifiés :
- `backend/api.py`
- `bolt-dashboard/src/App.tsx`
- `bolt-dashboard/src/lib/nav.ts`
- `bolt-dashboard/src/lib/types.ts`
- `bolt-dashboard/src/lib/api.ts`
- `bolt-dashboard/src/lib/hooks.ts`
- `bolt-dashboard/src/views/WaterBodiesView.tsx`
- `bolt-dashboard/src/views/EcosystemInputsPanel.tsx`

Nouveaux :
- `bolt-dashboard/src/lib/scientificGlossary.ts`
- `bolt-dashboard/src/views/ScientificGlossaryView.tsx`
- `tests/test_n8_1_scientific_lexicon.py`
- `docs/handoffs/PASSATION_ECOBIOME_N8_1_SCIENTIFIC_TERMINOLOGY_LEXICON_V1.md`

## Sources structurantes

- IUPAC Gold Book, pH:
  https://goldbook.iupac.org/terms/view/P04524
- Sandre, méthode 1041 saturation O₂:
  https://mdm.sandre.eaufrance.fr/node/414781
- USGS DOTABLES:
  https://www.usgs.gov/tools/dotables
- Benson & Krause (1984):
  https://doi.org/10.4319/lo.1984.29.3.0620
- Truesdale, Downing & Lowden (1955):
  https://doi.org/10.1002/jctb.5010050201
- Emerson et al. (1975):
  https://doi.org/10.1139/f75-274
- USGS alkalinity:
  https://www.usgs.gov/water-science-school/science/alkalinity-and-water
- USGS hardness:
  https://www.usgs.gov/water-science-school/science/hardness-water
- USGS specific conductance:
  https://pubs.usgs.gov/publication/twri09A6.3

## Critères d’acceptation

- compileall PASS ;
- Ruff PASS ;
- mypy PASS ;
- tests N6/N6.1/N6.2/N7/N8/N8.1 PASS ;
- pytest complet PASS ;
- TypeScript typecheck PASS ;
- Vite production build PASS ;
- `git diff --check` PASS ;
- staging vide ;
- branche et HEAD inchangés ;
- aucune opération Git distante ;
- rollback automatique vers N7 si un gate échoue.

## Interdictions

Ne pas commit, stage, push, merge, rebase, reset, clean ou supprimer les fichiers historiques sans
autorisation explicite.
