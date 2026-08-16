# PASSATION — EcoBiome N7 Biological Load & Ecosystem Inputs V1

Date de conception : 2026-08-15 (Europe/Paris)

## Gates

- Design : `ECOBIOME_N7_BIOLOGICAL_LOAD_ECOSYSTEM_INPUTS_V1_DESIGN_FROZEN`
- Validation locale cible : `ECOBIOME_N7_BIOLOGICAL_LOAD_ECOSYSTEM_INPUTS_V1_LOCAL_IMPLEMENTATION_VALIDATED`

## Objet

N7 fait évoluer l'application locale d'un suivi de paramètres d'eau vers une description exploitable des **stocks, flux et interventions** qui produisent l'état observé du milieu.

N7 ne remplace ni N4 ni N5 :

- N4 reste l'autorité pour la topologie/configuration durable (`EcosystemProfileV1`).
- N5 reste l'autorité canonique pour les observations d'eau et le changement d'eau N4/N5.
- Scientific Foundation reste Schema V6 ; N7 n'ajoute aucune Schema V7.
- N7 ajoute une persistance applicative locale explicitement séparée pour les états biologiques évolutifs et les opérations qui ne disposent pas encore d'un seam canonique N5 gelé.

## Constat scientifique ayant motivé N7

La qualité d'un système aquatique fermé ne peut pas être expliquée à partir d'une liste de concentrations instantanées seulement. Le moteur doit progressivement représenter :

1. la charge biologique animale ;
2. l'apport alimentaire ;
3. la capacité et la maturité de la biofiltration ;
4. les apports/retraits d'eau et leur composition ;
5. la matière organique/les solides ;
6. les plantes, algues et périphyton ;
7. l'hydraulique réelle ;
8. l'éclairage réellement reçu ;
9. le substrat ;
10. les perturbations et opérations humaines.

Référence de formule incluse dans N7 : l'estimation de la fraction d'ammoniac non ionisé à partir du TAN, du pH et de la température utilise l'équilibre eau-ammoniac d'Emerson et al. (1975), uniquement comme approximation eau douce / salinité nulle :

`pKa = 0.09018 + 2729.92 / (T_C + 273.2)`

`fraction_NH3 = 1 / (1 + 10 ** (pKa - pH))`

N7 ne transforme pas cette estimation en diagnostic universel de toxicité : le risque reste espèce/contextuel.

## Décisions d'architecture

### 1. Ne pas mettre les quantités biologiques dynamiques dans la topologie N4

Le garde N4 interdit déjà `biomass`, `abundance`, température, pH, volume d'eau et autres quantités dynamiques dans `properties_json` de la topologie. N7 respecte cet invariant.

- L'identité statique d'une population animale/végétale peut être projetée dans `BiologicalPopulationV1`.
- Les effectifs, masses moyennes, biomasses et couvertures évolutives restent dans l'état écologique local N7.

### 2. Persistance N7 locale séparée

Pour chaque projet :

```text
<project>/ecology/state.json
<project>/ecology/events.jsonl
```

`state.json` : vue courante des stocks/configurations dynamiques N7.

`events.jsonl` : journal append-only des opérations N7. Chaque événement contient `previous_event_sha256` et `event_sha256`. La chaîne est validée intégralement à la lecture.

Cette chaîne SHA est une garantie d'intégrité applicative locale. Elle ne doit pas être présentée comme une assertion Scientific Foundation ni comme un événement canonique N5.

### 3. Les observations d'eau restent N5

Les nouvelles mesures N7 passent toujours par le seam d'observation N5 :

- GH ;
- KH ;
- conductivité ;
- chlorures ;
- TSS ;
- calcium ;
- magnésium ;
- salinité ;
- ORP ;
- TAN ;
- saturation O2 instrumentale ;
- profondeur d'eau ;
- PAR surface/fond ;
- couverture algale ;
- couverture de périphyton.

GH/KH sont saisis en degrés allemands mais persistés en `mg/L` équivalent CaCO3 selon le contrat N6.1, puis reprojetés pour l'affichage.

### 4. NH3 non ionisé : dérivé, non persisté comme mesure

Si TAN + pH + température sont disponibles, N7 calcule une estimation `NH3-N mg/L` dans `derived_indicators`.

- ce calcul n'est pas une observation ;
- il n'est pas écrit dans le journal N5 ;
- la méthode et les entrées sont exposées ;
- si une salinité mesurée > 0.5 g/L est disponible, l'approximation zéro salinité n'est pas appliquée.

### 5. Profils d'eau réutilisables

Un profil d'eau peut contenir : origine, température, pH, KH, GH, conductivité, nitrate, nitrite, ammoniac/ammonium déclaré, phosphate, chlorure, calcium, magnésium, salinité et notes.

Le profil peut être référencé par :

- un complément après évaporation ;
- un changement d'eau.

Limite importante : N7 **ne propage pas encore automatiquement la chimie du profil d'eau dans la composition N4 `replacement_composition`**. Le changement d'eau reste canonique N4/N5, le profil est une information locale associée. Cette propagation nécessite un futur contrat de mélange/chimie explicitement gelé.

### 6. Complément après évaporation distinct du changement d'eau

Le complément :

- ajoute un volume sans retrait ;
- crée l'observation N5 de volume résultant ;
- ajoute une opération N7 `top_up` ;
- la projection du journal masque la duplication technique de l'observation de volume afin que l'utilisateur voie une seule intervention lisible.

### 7. Biofiltration

Les équipements de filtration peuvent enregistrer :

- débit nominal ;
- débit mesuré ;
- média ;
- volume de média ;
- surface spécifique ;
- date de mise en service ;
- inoculation ;
- maturité biologique (`unknown`, `new`, `cycling`, `mature`, `disturbed`) ;
- capacité TAN mesurée facultative en mg N/j ;
- dernier entretien.

Aucune capacité TAN n'est inventée à partir du nom commercial d'un média.

### 8. Éclairage

Les équipements d'éclairage peuvent enregistrer puissance/photopériode/spectre/température de couleur et PAR surface/fond. PAR peut aussi être enregistré comme observation N5 pour permettre un historique de mesure.

### 9. Journal humain

Le journal N6.2 fusionne :

- les événements canoniques N5 ;
- les opérations N7 validées par leur chaîne SHA.

Les opérations N7 sont projetées en français lisible : nourrissage, mortalité, ajout/retrait de population, plantes, complément d'eau, matériel, profils d'eau, substrat, entretien filtre, panne électrique, fertilisation, bactéries, modification CO2, traitement, siphonnage, taille, médicament, etc.

La provenance technique reste disponible sans devenir le langage principal de l'utilisateur.

## Interface N7

Dans un milieu : onglet `Écosystème & flux`.

Sous-sections :

1. `Vie & nourrissage`
   - populations animales ;
   - effectifs et masse moyenne ;
   - biomasse connue ;
   - décès/retraits/ajouts ;
   - nourrissages ;
   - plantes et couverture.

2. `Eau & substrat`
   - profils d'eau ;
   - compléments après évaporation ;
   - couches de substrat.

3. `Interventions`
   - entretien filtre ;
   - panne électrique ;
   - ajout générique ;
   - fertilisation ;
   - ajout de bactéries ;
   - modification CO2 ;
   - traitement de l'eau ;
   - siphonnage ;
   - taille de plantes ;
   - entretien du substrat ;
   - médicament ;
   - autre.

## Règle d'interprétation des métriques

Les plages universelles « idéales » ne doivent pas être présentées comme scientifiquement valides pour les variables dépendantes des espèces et du contexte.

N7 marque les paramètres contextuels comme `unknown` pour le statut automatique et affiche : `Interprétation selon espèces et contexte`.

Le futur moteur devra relier espèces/stades de vie + données scientifiques validées avant de produire des seuils de diagnostic.

## Fichiers N7

Nouveaux :

- `backend/__init__.py` — marqueur de package explicite pour une résolution mypy/import non ambiguë ;
- `backend/ecology_n7.py`
- `bolt-dashboard/src/views/EcosystemInputsPanel.tsx`
- `tests/test_n7_biological_load_ecosystem_inputs.py`
- `docs/handoffs/PASSATION_ECOBIOME_N7_BIOLOGICAL_LOAD_ECOSYSTEM_INPUTS_V1.md`

Modifiés :

- `backend/api.py`
- `bolt-dashboard/src/components/MetricCard.tsx`
- `bolt-dashboard/src/components/Sparkline.tsx`
- `bolt-dashboard/src/lib/api.ts`
- `bolt-dashboard/src/lib/hooks.ts`
- `bolt-dashboard/src/lib/types.ts`
- `bolt-dashboard/src/views/WaterBodiesView.tsx`

## Tests d'acceptation N7

Au minimum :

1. ajout d'une population animale ;
2. identité statique présente dans N4 mais absence de biomasse/effectif dynamique dans ses propriétés ;
3. modification d'effectif et mortalité historisées ;
4. nourrissage historisé ;
5. chaîne SHA des opérations valide ;
6. profil d'eau durable ;
7. complément après évaporation distinct ;
8. couches de substrat durables ;
9. mesures étendues passent par N5 ;
10. GH/KH conversion aller/retour ;
11. TAN + pH + température produisent une estimation NH3 documentée ;
12. changement d'eau peut référencer un profil d'eau sans fausse propagation chimique ;
13. biofiltre stocke débit mesuré, média, maturité et capacité TAN facultative ;
14. éclairage stocke PAR ;
15. journal humain expose nourrissage/mortalité/complément/interventions ;
16. tests N6/N6.1/N6.2 restent verts ;
17. suite projet complète verte ;
18. mypy, Ruff, frontend typecheck/build, `git diff --check` verts.

## Risques / limites assumées

- La persistance `state.json` + profil N4 + journal N7 n'est pas encore une transaction multi-fichiers atomique. Chaque fichier est écrit prudemment, mais une panne exactement entre deux écritures peut demander une réparation future.
- Les valeurs saisies dans l'état N7 sont conservées sous forme de chaînes décimales normalisées lorsque c'est applicable ; la projection API redevient numérique pour l'UI.
- Les opérations N7 n'ont pas encore un event schema N5 générique ; ne pas les faire passer artificiellement pour des événements canoniques Scientific Foundation.
- La composition d'une eau de remplacement n'est pas encore mélangée automatiquement avec l'état chimique courant.
- Pas encore de modèle espèce-spécifique de besoins/limites ; les métriques contextuelles ne produisent donc pas de diagnostic universel.
- Pas encore de calcul de saturation O2 à partir de mg/L, altitude/pression et salinité ; N7 permet de saisir la saturation si un appareil la fournit.
- Pas encore de bilan massique complet nourriture -> azote -> solides -> biofiltre ; N7 fournit les données nécessaires au futur moteur.

## Critères de non-régression

- aucune modification de Scientific Foundation Schema V6 ;
- aucune modification de `src/ecobiome/journal/canonical_project_event_v1.py` ;
- aucun affaiblissement du garde N4 sur les propriétés dynamiques ;
- aucun nettoyage des fichiers historiques non suivis ;
- staging vide avant/après ;
- aucun commit, push, merge, rebase, stash, reset, checkout destructif ou `git clean`.

## Autorisation

**NE PAS COMMITER, PUSHER, MERGER, REBASER, SUPPRIMER DE BRANCHE, MODIFIER LA PR #11 OU PUBLIER N7 SANS AUTORISATION EXPLICITE DE L'UTILISATEUR.**

Ce handoff fige le design et les critères d'acceptation ; il n'autorise aucune écriture Git distante.
