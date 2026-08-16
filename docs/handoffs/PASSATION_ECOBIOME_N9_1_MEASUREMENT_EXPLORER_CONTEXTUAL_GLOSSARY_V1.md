# PASSATION — EcoBiome N9.1 Measurement Explorer & Contextual Glossary V1

## Statut

Candidat local à valider après N9 R3. Ne pas commit, pousser, fusionner ou publier sans autorisation explicite.

## Objectif

Rendre chaque mesure physico-chimique directement explorable depuis un milieu aquatique :

1. bouton circulaire `+` ouvrant directement une saisie préremplie pour le paramètre ;
2. bouton circulaire `?` ouvrant directement la fiche scientifique correspondante du lexique ;
3. bouton d’évolution ouvrant une vue détaillée du paramètre ;
4. courbe historique filtrable par période ;
5. superposition d’une deuxième variable pour comparer la chronologie des variations.

## Décisions

- N9.1 est une couche frontend : aucune écriture scientifique, aucun événement N5/N7/N9 et aucun contrat backend n’est modifié.
- Le bouton `+` réutilise strictement le flux `addMeasurement` existant : il ne crée aucun nouveau type d'événement ni chemin de persistence.
- Le paramètre cliqué est préselectionné, son unité est dérivée du registre `METRICS` et le focus est placé sur la valeur.
- Un raccourci direct peut afficher le paramètre préselectionné même s'il est hors du niveau Débutant/Intermédiaire courant ; cela n'élargit pas le niveau global de l'interface.
- Le bouton `+` est disponible sur les cartes avec ou sans donnée, dans l'historique et dans la vue détaillée.
- Le bridge backend reste `n9`.
- Périodes V1 : 7 jours, 1 mois (30 j), 3 mois (90 j), 1 an (365 j), tout l’historique.
- Une seule variable de comparaison est autorisée en V1 afin de préserver la lisibilité.
- Lorsque les unités sont identiques, les deux séries partagent l’échelle Y.
- Lorsque les unités diffèrent, la série principale utilise l’axe gauche et la comparaison l’axe droit. L’interface avertit que la superposition compare surtout la chronologie et non l’amplitude numérique directe.
- Une concordance visuelle ne doit jamais être présentée comme une causalité.
- Le graphique utilise uniquement les mesures réellement enregistrées ; aucune projection N9 de nourrissage ne devient une mesure.
- Aucun package graphique supplémentaire n’est introduit : rendu SVG local et déterministe.

## Navigation lexique

`Metric -> getGlossaryEntryForMetric -> App -> ScientificGlossaryView(initialEntryId)`.

La vue lexique :

- réinitialise recherche/catégorie pour rendre la fiche visible ;
- ouvre la fiche ciblée ;
- défile jusqu’à l’entrée correspondante.

Les métriques qui n’avaient pas de cible directe sont couvertes :

- fer -> nouvelle fiche `iron` ;
- couverture algale -> nouvelle fiche `algae_coverage` ;
- PAR fond -> alias vers la fiche commune `par` / PPFD.

## Vue détaillée

La vue affiche pour la période sélectionnée :

- dernière valeur ;
- minimum ;
- maximum ;
- moyenne ;
- nombre de mesures ;
- série principale ;
- série de comparaison optionnelle.

Les points SVG comportent un titre avec date/heure, valeur et unité.

## Fichiers existants modifiés

- `bolt-dashboard/src/App.tsx`
- `bolt-dashboard/src/components/MetricCard.tsx`
- `bolt-dashboard/src/lib/scientificGlossary.ts`
- `bolt-dashboard/src/views/ScientificGlossaryView.tsx`
- `bolt-dashboard/src/views/WaterBodiesView.tsx`

## Nouveaux fichiers

- `bolt-dashboard/src/views/MeasurementExplorerView.tsx`
- `tests/test_n9_1_measurement_explorer_contextual_glossary.py`
- `docs/handoffs/PASSATION_ECOBIOME_N9_1_MEASUREMENT_EXPLORER_CONTEXTUAL_GLOSSARY_V1.md`

## Risques / limites V1

- Les courbes servent à l’exploration visuelle ; aucun coefficient de corrélation ni test de causalité n’est calculé.
- Les périodes sont relatives à l’horloge locale du navigateur.
- Aucun rééchantillonnage/interpolation n’est effectué entre deux mesures.
- Deux séries de fréquences d’échantillonnage différentes restent affichées sur leurs horodatages réels.
- Les axes indépendants peuvent accentuer visuellement une co-variation ; l’avertissement UX est obligatoire.

## Critères d’acceptation

- `+` depuis une carte, une ligne d’historique ou la vue détaillée ouvre la saisie avec le bon paramètre préselectionné.
- La valeur reçoit le focus et l’unité affichée provient du registre métrique existant.
- `?` depuis une carte ou une ligne d’historique ouvre la bonne fiche du lexique.
- Le bouton évolution ouvre la vue détaillée du bon paramètre.
- Les cinq périodes fonctionnent sans modifier les données.
- Une seconde métrique disposant de données peut être superposée.
- Unités identiques -> échelle partagée ; unités différentes -> axes gauche/droite explicitement étiquetés.
- Le graphique ne fabrique aucune mesure ; une mesure n’est persistée qu’après soumission explicite du formulaire existant.
- Tests N6 -> N9.1, pytest complet, TypeScript, Vite et `git diff --check` passent.
- Staging vide, branche et HEAD inchangés.

## Instruction Codex

Ne pas implémenter de corrélation statistique, interpolation, prédiction causale, troisième axe, modification backend ou persistance supplémentaire sans autorisation explicite.
