# Conception du noyau EcoBiome

## Package canonique

Le package applicatif canonique est :

```text
src/ecobiome
```

Les imports ne doivent pas dépendre du répertoire courant. Les copies,
miroirs ou prototypes ne doivent pas masquer le package canonique.

## Responsabilités principales

### Domaine

- projets et études ;
- observations et unités ;
- événements et rejeu ;
- connaissances et provenance ;
- raisonnement, hypothèses et résultats ;
- médias et journal ;
- workspace et manifeste ;
- état du monde spécialisé existant.

### Présentation

- API ;
- frontend web ;
- interface Desktop ;
- sérialiseurs et view models.

### Intégrations

- collecteurs ;
- fichiers et médias ;
- services cloud optionnels ;
- workers spécialisés futurs.

## Chaîne de données

```text
source
→ autorisation
→ extraction
→ normalisation
→ qualité
→ provenance
→ confiance
→ stockage
→ validation
→ usage
```

Aucune étape ne doit effacer silencieusement la source, la licence, le contexte
ou le statut de validation.

## Contrats de stabilité

- écritures atomiques lorsque le format le permet ;
- versions de schéma explicites ;
- refus des versions majeures inconnues ;
- sérialisation déterministe ;
- erreurs ciblées ;
- absence de secret dans le code ou les journaux ;
- timeouts sur les appels réseau ;
- dépendances lourdes isolées.

## Compatibilité

L'introduction du métamodèle universel doit être additive :

- un workspace sans modèle d'écosystème reste valide ;
- les formats aquatiques existants ne sont pas renommés implicitement ;
- les observations, événements et journaux gardent leurs responsabilités ;
- les migrations ont des fixtures et des tests de compatibilité.
