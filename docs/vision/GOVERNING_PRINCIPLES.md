# Governing Principles

> Les principes fondateurs d'EcoBiome.

Ces principes sont les règles fondamentales du projet.

Ils guident toutes les décisions scientifiques, techniques et architecturales.

---

# 1. La réalité prime toujours sur le modèle

EcoBiome est une représentation du réel.

Le logiciel ne doit jamais prétendre que son modèle est plus fiable qu'une observation correctement réalisée.

Lorsqu'une mesure réelle est disponible, elle prévaut sur une estimation.

---

# 2. Toute prédiction possède une incertitude

Aucun résultat ne doit être présenté comme absolument certain.

Chaque simulation doit préciser :

- son niveau de confiance ;
- les hypothèses utilisées ;
- les principales sources d'incertitude.

---

# 3. Une réponse approximative vaut mieux qu'aucune réponse

Lorsque certaines données sont absentes, EcoBiome doit produire la meilleure estimation possible.

Le logiciel doit cependant :

- identifier les informations manquantes ;
- indiquer leur impact ;
- proposer les mesures prioritaires à réaliser.

---

# 4. Chaque résultat doit être explicable

EcoBiome ne doit jamais être une boîte noire.

Pour chaque recommandation, le logiciel doit pouvoir répondre :

- pourquoi ?
- quelles données ont été utilisées ?
- quels modèles sont intervenus ?
- quelles sont les causes principales ?

---

# 5. La modularité est une priorité

Chaque domaine scientifique est développé comme un module indépendant.

Les modules communiquent uniquement via l'état global du système.

Aucun module ne doit dépendre directement d'un autre.

---

# 6. Les connaissances scientifiques évoluent

Les modèles doivent pouvoir être remplacés sans modifier le moteur.

Les références scientifiques doivent être documentées.

Les hypothèses doivent être explicites.

---

# 7. Les unités internes sont normalisées

Toutes les grandeurs physiques sont manipulées dans le Système International (SI).

Les conversions vers les unités utilisées par les aquariophiles sont réalisées uniquement dans l'interface utilisateur.

---

# 8. Toute intervention humaine est un événement

Les changements d'eau, l'ajout de poissons, les traitements, les tailles de plantes ou les modifications d'éclairage sont représentés comme des événements datés.

Chaque événement doit pouvoir être rejoué dans une simulation.

---

# 9. Les simulations doivent être reproductibles

Une simulation exécutée avec :

- les mêmes paramètres ;
- les mêmes modèles ;
- les mêmes données ;
- la même version du moteur ;

doit produire les mêmes résultats.

---

# 10. Les modèles possèdent un niveau de maturité

Chaque modèle est classé :

- Planned
- Prototype
- Implemented
- Validated
- Stable

L'utilisateur doit toujours connaître le niveau de maturité des modèles utilisés.

---

# 11. Les recommandations doivent être hiérarchisées

EcoBiome ne doit pas seulement dire quoi faire.

Il doit indiquer :

- ce qui est prioritaire ;
- ce qui aura le plus d'impact ;
- ce qui améliorera le plus la précision des simulations.

---

# 12. EcoBiome est un outil scientifique ouvert

Le projet favorise :

- la transparence ;
- la reproductibilité ;
- la collaboration ;
- la validation expérimentale ;
- le partage des connaissances.

Toutes les contributions doivent respecter ces principes.