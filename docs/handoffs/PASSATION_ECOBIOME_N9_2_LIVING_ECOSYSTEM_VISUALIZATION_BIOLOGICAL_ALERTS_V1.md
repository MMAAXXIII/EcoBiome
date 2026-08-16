# PASSATION — EcoBiome N9.2 Living Ecosystem Visualization & Biological Alerts V1

## Statut

Candidat local à intégrer et valider. Ne pas considérer N9.2 comme validé tant que le gate local complet n'a pas passé.

## Objectif

Rendre la représentation du milieu aquatique informative d'un seul coup d'œil sans inventer de nouvelles mesures ni transformer une référence biologique en seuil létal.

N9.2 ajoute une couche visuelle réactive au-dessus des données N5/N7/N9 déjà présentes :

- populations déclarées représentées symboliquement dans le bac ;
- nourrissage réel récent représenté temporairement par des particules ;
- disparition progressive de cette représentation après cinq minutes ;
- alertes biologiques visibles directement dans le bac lorsqu'une mesure connue se trouve hors de la plage de référence d'une espèce déclarée ;
- clic sur `!` pour lire l'espèce concernée, la valeur mesurée, la plage de référence et la source.

## Décisions

### 1. Aucune mutation scientifique

`WaterTankViz` et `livingTank.ts` sont en lecture seule.

Ils ne doivent :
- ni appeler `addMeasurement`;
- ni écrire dans le journal;
- ni créer de diagnostic;
- ni convertir une projection ou une animation en mesure scientifique.

### 2. Nourriture : représentation d'un événement réel

L'animation alimentaire provient uniquement d'un `EcologyOperation` dont `operation_type == feeding`.

La masse et la forme proviennent des détails N9 déjà figés dans l'événement.

Durée d'affichage V1 : cinq minutes.

Cette durée est un choix d'interface, pas une durée scientifique de dissolution ou d'ingestion.

### 3. Références biologiques, pas seuils létaux

Le registre V1 contient des références FishBase pour :

- `Mikrogeophagus ramirezi` : température de référence 27–30 °C ;
- `Oryzias latipes` : température de référence 18–24 °C.

Ces plages sont décrites comme des plages écologiques de référence. Elles ne doivent pas être affichées comme limites létales universelles.

Une mesure hors plage produit donc une alerte de niveau `warning`, pas automatiquement `critical`.

### 4. Données manquantes

Si aucune température n'est mesurée, aucune alerte température n'est fabriquée.

Si une population ne correspond à aucun profil sourcé du registre, elle est représentée visuellement mais n'est pas évaluée biologiquement.

L'absence d'alerte ne signifie donc pas automatiquement « tout va bien ».

### 5. Extensibilité

Le registre `SPECIES_REFERENCE_PROFILES` est volontairement séparé du composant graphique afin de pouvoir ajouter ensuite :

- pH ;
- GH/KH ;
- O₂ dissous ;
- salinité ;
- plages selon stade de vie ;
- références multiples avec qualité/provenance ;
- préférences utilisateur ou souche domestique ;
- moteur scientifique backend plus complet.

## Fichiers

Modifiés :

- `bolt-dashboard/src/components/WaterTankViz.tsx`
- `bolt-dashboard/src/views/WaterBodiesView.tsx`

Nouveaux :

- `bolt-dashboard/src/lib/livingTank.ts`
- `tests/test_n9_2_living_ecosystem_visualization.py`
- `docs/handoffs/PASSATION_ECOBIOME_N9_2_LIVING_ECOSYSTEM_VISUALIZATION_BIOLOGICAL_ALERTS_V1.md`

## Critères d'acceptation

1. Baseline N9.1 validée exacte.
2. Staging vide avant et après.
3. Branche et HEAD inchangés.
4. Ruff PASS.
5. mypy PASS.
6. Tests ciblés N6 → N9.2 PASS.
7. pytest complet PASS.
8. TypeScript typecheck PASS.
9. Vite build PASS.
10. `git diff --check` PASS.
11. Aucun Git write distant ou destructif.
12. Le nourrissage récent devient visible puis s'estompe.
13. Une population de Ramirezi + température hors 27–30 °C produit un `!` visible.
14. La source biologique est affichable depuis l'alerte.
15. Aucune mesure n'est créée par la visualisation.

## Limites V1

- seules deux espèces disposent d'une plage biologique sourcée intégrée ;
- seule la température est évaluée par espèce ;
- les poissons dessinés sont symboliques, pas une représentation de l'effectif exact ni de la morphologie ;
- cinq minutes d'animation alimentaire est une durée UX ;
- aucune inférence causale ou prédiction physiologique n'est réalisée ;
- aucune alerte critique n'est déduite d'une simple sortie de plage de référence.

## Suite recommandée

N9.3 / N10 pourra ajouter :
- événements du journal sur les graphiques ;
- registre d'espèces versionné et beaucoup plus large ;
- conflits de plages entre espèces ;
- alertes multi-paramètres ;
- règles combinées (température + O₂ + TAN) ;
- explication « Pourquoi cette alerte ? ».

## Garde-fou

NE PAS implémenter de seuils létaux, diagnostics médicaux/vétérinaires, coefficients physiologiques ou nouvelles espèces sans source explicite et sans autorisation de conception.
