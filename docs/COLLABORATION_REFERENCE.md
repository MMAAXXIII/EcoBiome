# Références collaboratives du projet EcoBiome

## Prototype Bolt

- Prototype web Bolt : https://bolt.new/p/69547705
- Preview temporaire observée : https://graphical-user-inter-ka4h.bolt.host/

Ce prototype Bolt a servi de référence pour l'interface web et le design du tableau de bord. Il est utile de conserver ces liens pour :

- retrouver rapidement la direction visuelle et fonctionnelle du travail web
- partager la référence avec d'autres contributeurs
- comparer ensuite l'implémentation locale à ce qui a été conçu par Bolt

## Branches de travail

- Branche actuelle de prototype front : `agents/web-dashboard`
- Branche de base / visual pass : `agents/visual-pass2`

## Organisation collaborative recommandée

1. Garder les composants web et le prototype front sur la branche `agents/web-dashboard`.
2. Utiliser des issues GitHub dédiées pour chaque grand domaine :
   - UI / design web
   - données et schéma Bolt Database
   - intégration desktop / web
   - validation visuelle et tests
3. Réserver la branche `main` aux versions stables fusionnées après revue.
4. Documenter chaque décision d'architecture dans `docs/` afin que des contributeurs différents puissent reprendre rapidement.

## Prochaines étapes suggérées

- Créer une issue GitHub pour centraliser le travail sur le prototype web (`agents/web-dashboard`).
- Ajouter une issue séparée pour la synchronisation des données entre le desktop Python/Tkinter et l'interface web.
- Garder ce document à jour chaque fois qu'un nouveau prototype externe ou une nouvelle maquette est ajoutée.
