# EcoBiome@home

**Statut :** `PROPOSED`.
**Objet :** calcul volontaire, modulaire et sécurisé.

## Objectif

EcoBiome@home permettrait à un utilisateur de contribuer volontairement des
ressources CPU, GPU et de stockage sans transformer chaque installation en
serveur lourd. Les résultats seraient renvoyés vers un contrôle central ou un
stockage choisi.

## Cycle d'une tâche

```text
soumission
→ segmentation
→ attribution
→ téléchargement minimal
→ exécution locale
→ validation
→ envoi des résultats
→ nettoyage local
```

États cibles :

```text
pending
processing
done
failed
dead-letter
```

## Segmentation

- vidéos en segments audio ;
- analyses en blocs indépendants ;
- NLP en lots ;
- embeddings en batchs ;
- simulations en sous-problèmes.

## Validation

- hash des entrées et sorties ;
- retry avec backoff ;
- DLQ pour les échecs persistants ;
- double calcul possible pour les résultats sensibles ;
- version des modèles et paramètres ;
- journal d'exécution reproductible.

## Worker local

Profil indicatif, non exigence minimale :

- 4 à 16 cœurs CPU ;
- 8 à 32 Go de RAM ;
- GPU optionnel ;
- NVMe pour le calcul ;
- HDD pour les archives.

Le worker doit annoncer ses capacités et accepter des quotas plus faibles.

## Worker cloud

Le cloud peut fournir des capacités spécialisées, mais aucun fournisseur,
orchestrateur ou type de GPU n'est imposé par l'architecture.

## Sécurité et consentement

- activation volontaire ;
- types de tâches autorisés ;
- quotas CPU/GPU/RAM/disque ;
- sandbox adaptée au risque ;
- arrêt et pause immédiats ;
- aucune donnée sensible sans consentement ;
- chiffrement en transit ;
- expiration des artefacts ;
- journal d'accès ;
- refus des tâches incompatibles.

## Mode sûr

Le worker doit pouvoir :

- réduire sa charge quand l'utilisateur utilise la machine ;
- fonctionner uniquement pendant une plage horaire ;
- suspendre sur batterie ou température élevée ;
- limiter l'espace disque ;
- supprimer les intermédiaires ;
- réserver une marge de sécurité.

## Stockage

| Niveau | Usage |
|---|---|
| NVMe | Segments, caches et fichiers intermédiaires. |
| HDD | Archives, datasets, médias originaux et logs historiques. |
| Objet/cloud | Résultats finaux, partage et index. |

## Questions ouvertes

- protocole d'identité et d'attestation des workers ;
- modèle de confiance des résultats ;
- format du manifeste global d'artefacts ;
- politique de rétention ;
- isolation multi-plateforme ;
- gouvernance et coût du service central ;
- traitement des données privées ou réglementées.
