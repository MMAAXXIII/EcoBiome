# PASSATION ECOBIOME — N9 FEED CATALOG, SEX STRUCTURE & FEED LOAD V1

Date : 2026-08-16
Statut : candidat local à valider avant tout commit/push
Base attendue : N8.1 Progressive UX & Scientific Lexicon V1 validé localement,
branche `agent/n5-canonical-project-event-seam-v1`, HEAD
`c2aa03cfb4a2707620e6da54b26fba12e795afcb`.

## Objectif

N9 transforme le nourrissage en flux scientifique traçable au lieu d'une simple note libre.
Il permet :

1. de constituer une bibliothèque locale d'aliments pour poissons ;
2. d'importer des faits structurés depuis une fiche produit HTTPS autorisée ;
3. de figer la composition de l'aliment utilisée dans chaque événement de nourrissage ;
4. de relier la masse distribuée à la biomasse animale ciblée ;
5. de calculer des bilans d'entrée et des bornes stœchiométriques sans fabriquer de fausses observations ;
6. de renseigner explicitement mâles, femelles et individus non sexés dans chaque population animale.

## Décisions structurantes

### Aliment = objet scientifique réutilisable

Le catalogue partagé local est stocké hors dépôt, sous :

`<ECOBIOME_LOCAL_DATA_DIR>/catalog/feed_products.json`

Un produit peut contenir notamment :

- marque, nom et variante ;
- catégorie et forme physique ;
- rôle nutritionnel ;
- espèces/groupes ciblés et zone de prise alimentaire ;
- liste d'ingrédients ;
- protéines brutes, matières grasses, fibres, humidité, cendres et phosphore ;
- additifs et recommandations de distribution ;
- masse/volume de conditionnement lorsque disponibles ;
- URL source, URL fabricant, date d'observation, prix commercial ponctuel ;
- empreinte SHA-256 de l'identité factuelle normalisée ;
- empreinte du contenu source lorsqu'une page a été importée.

Le prix commercial et l'empreinte brute de la page ne font pas partie de l'identité scientifique du produit : une variation de prix ou de HTML sans variation des faits nutritionnels ne doit pas créer une nouvelle composition scientifique.

### Catalogue ouvert, pas liste fermée

Les aliments pour poissons existent sous de nombreuses formes : flocons, micro-granulés,
granulés, pellets, sticks, comprimés, wafers, chips, poudres, gels, lyophilisés,
congelés, vivants et autres. N9 conserve donc des champs ouverts et structurés plutôt
qu'une taxonomie fermée supposée exhaustive.

N9 V1 autorise l'import réseau seulement depuis des hôtes explicitement approuvés :
`zooplus.fr` et `tetra.net`. La saisie manuelle peut documenter un produit provenant d'une
autre source sans effectuer de requête réseau.

### Provenance et intégrité

Le catalogue est sérialisé en JSON canonique. Chaque produit persistant doit porter un
`product_sha256` cohérent avec son contenu factuel. Le chargement et la sauvegarde refusent
un produit dont l'empreinte ne correspond plus.

Lors d'un nourrissage, une photographie factuelle minimale du produit et son SHA sont
copiés dans l'événement append-only. Une modification ultérieure du catalogue ne doit donc
pas réécrire silencieusement l'historique.

### Sexe des populations

Une population animale conserve :

- effectif total ;
- nombre de mâles connus ;
- nombre de femelles connues ;
- nombre d'individus de sexe indéterminé = total - mâles - femelles.

L'invariant `mâles + femelles <= total` est obligatoire. Les ajouts, retraits et décès
peuvent être attribués à `male`, `female` ou `unknown`.

Ces quantités restent dynamiques et ne sont pas placées dans la topologie N4.

### Compatibilité des tests de régression hérités

Les tests d'une étape antérieure ne doivent pas figer le numéro exact du bridge si leur
objectif fonctionnel est indépendant de cette version. Le test N8 de guidage vérifie donc
que le service local est sain (`status = ok`, identité `ecobiome-local-api`) et conserve
tous ses invariants de complétude/contextualisation, sans imposer `bridge_version = n8`.
La version courante du bridge est vérifiée séparément par le runtime de l'étape active.

## Modèle de charge alimentaire N9 V1

N9 sépare strictement deux couches.

### 1. Bilan déterministe de l'entrée

Lorsque les constituants sont disponibles, EcoBiome peut calculer directement, pour la
masse distribuée :

- protéines brutes ;
- lipides ;
- fibres ;
- humidité et matière sèche ;
- cendres ;
- phosphore ;
- quantité estimée d'azote associée aux protéines brutes ;
- part ingérée et part non consommée si l'utilisateur fournit une estimation de consommation ;
- ration de l'événement relativement à la biomasse ciblée.

Convention utilisée pour l'azote protéique :

`N_protéines (mg) ≈ protéines brutes (g) / 6,25 × 1000`

Le facteur 6,25 est une convention d'analyse proximale fondée sur environ 16 % d'azote
moyen dans les protéines. Il n'est pas présenté comme une constante biochimique universelle.

### 2. Bornes stœchiométriques, pas prédictions biologiques

Si une part consommée est renseignée, N9 calcule notamment une borne maximale de TAN-N
si tout l'azote protéique ingéré était converti vers TAN, puis des conséquences théoriques
de nitrification :

- `4,57 mg O2 / mg NHx-N` ;
- `7,14 mg d'alcalinité comme CaCO3 / mg NHx-N` ;
- conversion massique N -> NO3- par le rapport moléculaire `62/14`.

Ces résultats portent explicitement :

`model_kind = stoichiometric_input_and_upper_bounds_not_observed_prediction`

et :

`expected_effect_status = requires_species_feed_digestibility_and_retention_coefficients`

Ils ne créent jamais une observation N5 de TAN, NO3-, O2 ou pH.

## Pourquoi N9 ne prédit pas encore la variation réelle

Les travaux en RAS montrent que l'excrétion ammoniacale et la consommation d'oxygène
varient avec le régime, la stratégie de distribution, l'espèce, le stade, la digestibilité,
la rétention/croissance et les conditions d'élevage. Appliquer un coefficient universel
`1 g aliment -> X mg TAN` donnerait une fausse précision.

La prochaine couche prédictive devra donc utiliser des coefficients versionnés et sourcés,
avec domaine d'application et incertitude, idéalement au couple espèce/stade × aliment/régime.

## Aliment de démonstration intégré

Le catalogue N9 démarre avec `Tetra — TetraMin Flakes` comme exemple reproductible.
Données de référence fabricant utilisées :

- protéines brutes : 46 % ;
- matières grasses brutes : 11 % ;
- cellulose brute : 2 % ;
- humidité : 7 % ;
- forme : flocons ;
- aliment complet pour poissons d'ornement.

La fiche utilisateur Zooplus peut également être importée comme snapshot source distinct.
Les différences éventuelles entre retailer et fabricant ne doivent pas être fusionnées sans
provenance explicite.

## Exemple N9 : 1 g TetraMin dans 250 L

Avec 46 % de protéines :

- protéines brutes apportées = `0,46 g` ;
- azote protéique conventionnel ≈ `73,6 mg N` ;
- si 100 % est déclaré consommé et, de façon volontairement extrême, 100 % de cet azote
  devient immédiatement TAN : borne TAN-N = `0,2944 mg N/L` dans 250 L ;
- O2 théorique correspondant à une nitrification complète de cette borne ≈ `1,345408 mg/L` ;
- alcalinité théorique consommée ≈ `2,102016 mg/L comme CaCO3`.

Ces trois dernières valeurs sont des bornes de bilan, pas des variations attendues.

## Interface

Dans `Vie & nourrissage` :

- populations : total + mâles + femelles + indéterminés ;
- corrections sexuées des ajouts/retraits/décès ;
- bibliothèque d'aliments ;
- import URL Zooplus/Tetra ;
- saisie manuelle riche ;
- choix de l'aliment au nourrissage ;
- population cible ;
- masse distribuée ;
- part consommée estimée ;
- dernier bilan de charge alimentaire avec avertissement sur les bornes théoriques.

Le lexique scientifique N8.1 est enrichi avec :

- constituants analytiques ;
- protéines brutes ;
- azote protéique estimé ;
- matière sèche ;
- ration relative à la biomasse ;
- digestibilité ;
- rétention azotée ;
- borne stœchiométrique.

## Fichiers N9

Modifiés :

- `backend/api.py`
- `tests/test_n8_progressive_guidance.py` — retire le pin de version N8 devenu obsolète tout en conservant le contrat fonctionnel du guidage ;
- `bolt-dashboard/src/lib/api.ts`
- `bolt-dashboard/src/lib/hooks.ts`
- `bolt-dashboard/src/lib/scientificGlossary.ts`
- `bolt-dashboard/src/lib/types.ts`
- `bolt-dashboard/src/views/EcosystemInputsPanel.tsx`

Nouveaux :

- `backend/feed_catalog_n9.py`
- `tests/test_n9_feed_catalog_sex_feed_load.py`
- `docs/handoffs/PASSATION_ECOBIOME_N9_FEED_CATALOG_SEX_STRUCTURE_FEED_LOAD_V1.md`

## Critères d'acceptation

- compileall PASS ;
- Ruff PASS ;
- mypy PASS ;
- tests N6/N6.1/N6.2/N7/N8/N8.1/N9 PASS ;
- pytest complet PASS ;
- TypeScript typecheck PASS ;
- Vite production build PASS ;
- `git diff --check` PASS ;
- staging vide ;
- branche et HEAD inchangés ;
- aucun Git write distant ;
- un nourrissage ne crée aucune mesure physico-chimique artificielle ;
- une ancienne population N7 sans champs de sexe reste lisible comme entièrement non sexée ;
- un ancien nourrissage libre reste accepté sans produit de catalogue ;
- rollback automatique vers N8.1 au premier échec.

## Sources structurantes

- Tetra, TetraMin Flakes :
  https://www.tetra.net/fr-fr/produits/tetramin-flakes
- Zooplus, Tetra TetraMin :
  https://www.zooplus.fr/shop/poissons/type_nourriture_poissons/nourriture_flocons_poissons/flocons_tetra/15277
- FAO, Principles of feed and fertilizer analysis :
  https://www.fao.org/4/ab468e/AB468E01.htm
- Aquaculture International (2022), diet/feeding strategy, oxygen consumption and ammonia excretion in RAS :
  https://doi.org/10.1007/s10499-021-00821-3
- US EPA, nitrification stoichiometry reference :
  https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P100GE8B.TXT

## Risques / limites connues

- Une fiche retailer peut diverger d'une fiche fabricant ou évoluer ; provenance obligatoire.
- L'import HTML dépend de la structure du site et peut nécessiter des adaptateurs spécifiques.
- Le catalogue V1 n'est pas une base mondiale préchargée ; il est extensible par import et saisie.
- Les aliments vivants/frais/congelés ont souvent une composition très variable ; une fiche générique
  ne doit pas être traitée comme analyse de lot.
- La masse moyenne de la population et la part réellement consommée peuvent être incertaines.
- Les valeurs stœchiométriques N9 ne remplacent jamais une mesure de l'eau.

## NE PAS IMPLEMENTER SANS AUTORISATION

- coefficients prédictifs espèce/stade × aliment ;
- prédiction de TAN/NO2-/NO3-/O2/pH présentée comme valeur attendue sans modèle validé ;
- apprentissage automatique à partir de données utilisateur ;
- scraping massif ou crawler de boutiques ;
- import réseau de domaines non approuvés ;
- modification rétroactive des événements de nourrissage ;
- écriture de valeurs prédites dans le journal des observations comme si elles avaient été mesurées ;
- commit, stage, push, merge, rebase ou suppression de branche.
