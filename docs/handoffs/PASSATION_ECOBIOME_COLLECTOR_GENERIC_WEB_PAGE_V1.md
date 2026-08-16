# PASSATION — EcoBiome Collector Generic Web Page Adapter V1

## Décision

Ajouter un adaptateur Collector générique pour les pages publiques `http://` et `https://` afin que des sources comme FishFish ou Ammannia puissent être acquises sans adaptateur spécifique par domaine.

## Fichiers

Modifiés :

- `src/ecobiome/knowledge_acquisition/adapters/__init__.py`
- `src/ecobiome/knowledge_acquisition/collector_acquire.py`
- `tests/test_collector_acquisition.py` — remplace l'ancien contrat « HTTP unsupported » par le contrat de routage `web-page` sans réseau.

Nouveaux :

- `src/ecobiome/knowledge_acquisition/adapters/web.py`
- `tests/test_collector_web.py`
- `docs/handoffs/PASSATION_ECOBIOME_COLLECTOR_GENERIC_WEB_PAGE_V1.md`

## Architecture

- `YouTubeAdapter` conserve la priorité 200.
- `LocalFileAdapter` conserve la priorité 100.
- `WebPageAdapter` utilise la priorité 50 et joue le rôle de fallback HTTP/HTTPS.
- `source_type` reste `other` : aucun changement de schéma scientifique/persistence n'est introduit.
- Le HTML brut est conservé comme payload exact ; une représentation texte UTF-8 est dérivée séparément.
- L'extraction privilégie `<main>`, puis `<article>`, puis `<body>` et retire `script/style/noscript/template/svg`.

## Sécurité réseau

Le nouvel adaptateur doit impérativement utiliser les primitives existantes de `knowledge_acquisition.security` :

- validation des schémas HTTP/HTTPS ;
- blocage localhost, adresses privées, link-local, multicast, réservées et non globales ;
- validation de toutes les réponses DNS ;
- connexion à une adresse prévalidée et contrôle de l'IP réellement connectée ;
- revalidation de chaque redirection ;
- interdiction HTTPS → HTTP ;
- limite de 5 redirections ;
- limite de taille ;
- `Accept-Encoding: identity` ;
- Content-Type V1 limité à `text/html` et `text/plain`.

Ne jamais remplacer ce chemin par un simple `requests.get(url)` sans garde SSRF.

## Provenance et confiance

L'acquisition d'une page web n'en valide pas le contenu scientifique. Les passages et claims restent soumis au pipeline Collector existant, avec review/pending et provenance. Une phrase comme « scientifiquement validé » sur une page commerciale n'est pas transformée en preuve vérifiée.

## Canonicalisation

Les fragments sont supprimés et seuls les paramètres de tracking connus (`utm_*`, `gclid`, `gbraid`, `wbraid`, `fbclid`, `msclkid`, `srsltid`) sont retirés de l'identité logique. Les autres paramètres de requête sont conservés.

## Limites V1

- pas de rendu JavaScript/headless browser ;
- pas de PDF dans cet adaptateur ;
- une page nécessitant authentification, cookie/consentement ou challenge anti-bot peut échouer avec un diagnostic HTTP explicite ;
- extraction de contenu générique, sans parseur spécifique au site ;
- pas de crawl récursif des liens.

## Critères d'acceptation

1. FishFish/Ammannia sont routés vers `web-page` au lieu de `UnsupportedSourceError`.
2. YouTube continue d'être routé vers l'adaptateur spécialisé.
3. Redirection vers une cible privée bloquée avant toute seconde requête.
4. HTML brut et texte dérivé persistables par le pipeline existant.
5. Ruff, mypy, tests Collector ciblés et pytest complet passent.
6. staging Git reste vide ; branche/HEAD inchangés.

## Ne pas implémenter sans autorisation

- crawler multi-pages ;
- rendu JavaScript ;
- authentification web ;
- contournement anti-bot ;
- promotion automatique d'un claim web en connaissance vérifiée.
