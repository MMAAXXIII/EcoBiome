# PASSATION — EcoBiome Sprint 58A FINAL v2

## Statut

Sprint 58A terminé et committé localement avec succès le 5 août 2026.

Le socle canonique d’import de transcription est fonctionnel, testé et prêt pour une revue distante. Aucun push, aucune pull request, aucun merge et aucun rebase n’ont été effectués.

## Référence Git

- Branche : `feature/collector-cli-baseline`
- Commit fonctionnel : `79691a6d9f12bbe6294ecdc85b5f0f4c2417d908`
- Parent : `ba1ebc9594f58a11c4685ec55e13ffdc25c0570f`
- Message : `feat(collector): establish transcript import CLI baseline`
- SHA-256 du patch revu : `1f5ad31dc11a24ac0b2c5994b87914a93cd73bbf2cc946872e357b86d0b36dce`

## Validation

- 13 tests canoniques racine réussis.
- Ruff réussi.
- mypy réussi sur 7 fichiers source.
- `python -m ecobiome import-transcript` réussi.
- `ecobiome --help` réussi depuis la commande installée.
- `ecobiome import-transcript` réussi depuis la commande installée.
- `git diff --cached --check` réussi avant commit.
- Arbre de travail propre après le commit fonctionnel.
- Test de sécurité `tests/test_security_hardening.py` conservé et inchangé.
- Aucun push, aucune pull request, aucun merge et aucun rebase.

## Résultat fonctionnel

EcoBiome dispose maintenant d’une première chaîne d’acquisition semi-manuelle :

`transcription locale → source avec provenance → passages déterministes → manifeste JSON → validation scientifique requise`

Commande d’utilisation :

```powershell
uv run --locked ecobiome import-transcript `
    .\transcription.txt `
    --title "Titre de la source" `
    --locator "local:identifiant" `
    --source-type transcript `
    --output .\manifeste.json
```

## Décisions

- `src/ecobiome/knowledge_acquisition/` est la fondation canonique du Collector MVP.
- L’import de transcription reste centré sur la provenance et exige une validation scientifique.
- Le routage `import-transcript` est effectué avant le chargement des modules optionnels.
- Le lancement graphique sans argument reste disponible.
- Les prototypes de collecte contenant des valeurs fictives ou une logique fragile ont été retirés.
- L’ancien analyseur dépendant de `collector_core.logger` a été retiré.
- Les sauvegardes suivies `.bak` et `.bak2` ont été retirées.
- Le test de durcissement de sécurité reste actif.
- La commande console `ecobiome` est déclarée dans `pyproject.toml`.
- Pytest utilise provisoirement `pythonpath = [".", "src"]` pour couvrir le paquet racine `api`.
- SQLite, les preuves textuelles persistantes et le workflow de revue humaine sont reportés au Sprint 58B.

## Modifications du commit fonctionnel

- 16 chemins modifiés.
- 289 insertions.
- 627 suppressions.
- Ajout de `.gitattributes`.
- Mise à jour de `.gitignore`.
- Mise à jour de `pyproject.toml`.
- Mise à jour du routage CLI et de `src/ecobiome/__main__.py`.
- Ajout des tests d’acquisition et de commande.
- Suppression des anciens prototypes et de leurs tests associés.

## Risques et questions ouvertes

- Le paquet actif `api` reste situé à la racine du dépôt ; cette disposition devra être rationalisée.
- Les copies Python sous `frontend/` et `bolt-dashboard/` restent suivies dans Git.
- Le manifeste actuel est un fichier JSON sans identité durable en base de données.
- Les déclarations extraites ne sont pas encore reliées à des plages de preuve exactes.
- Le collecteur ne possède pas encore de détection persistante des doublons.
- La récupération automatique de transcriptions YouTube n’est pas encore intégrée.
- Le rendu accentué dans certains transcripts PowerShell peut être altéré par l’encodage de console, sans affecter les fichiers JSON générés.

## Critères d’acceptation du Sprint 58B

1. Migrations SQLite versionnées.
2. Enregistrements immuables des sources et documents.
3. Conservation du contenu brut et de son SHA-256.
4. Persistance des passages et plages de preuve.
5. Modèle structuré pour les déclarations et paramètres scientifiques.
6. Décisions humaines `accepté`, `corrigé` et `rejeté`.
7. Détection déterministe des doublons.
8. Aucune valeur scientifique fabriquée.
9. Tests complets, Ruff, mypy et test réel d’exécution.
10. Journal automatique et passation versionnée.

## Prochaine opération recommandée

1. Vérifier que le dépôt local est toujours propre.
2. Pousser `feature/collector-cli-baseline` vers `origin`.
3. Créer une pull request en brouillon.
4. Vérifier les contrôles GitHub.
5. Ne pas fusionner avant revue du diff distant.
6. Ne pas commencer le Sprint 58B avant autorisation explicite.

## Instruction à Codex ou à tout autre agent d’implémentation

Ne pas pousser, fusionner, supprimer de branche ou commencer le Sprint 58B sans autorisation explicite.

Ne pas ajouter de transcription audio, de surveillance autonome du Web, de valeurs scientifiques fabriquées ou de scores de confiance arbitraires.
