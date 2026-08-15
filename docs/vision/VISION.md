# Vision EcoBiome

**Statut :** vision produit et scientifique de référence.
**Horizon :** plateforme locale-first, explicable, reproductible et
progressivement distribuable.
**Révision stratégique :** 15 août 2026.

## Mission

EcoBiome doit aider à **gérer, observer, comprendre, simuler, concevoir et
améliorer** des écosystèmes réels sans confondre observation, preuve,
inférence et simulation.

Le projet part d'un socle aquatique, mais vise des profils composables :

- aquarium, mare, étang, cours d'eau et zone humide ;
- potager, serre, culture en sol et culture hors-sol ;
- terrarium, paludarium et riparium ;
- aquaponie et systèmes hybrides reliés par des flux.

## North Star produit

Le cas d'usage directeur est :

> Décrire un écosystème réel, importer ses observations et ses sources,
> reconstruire les mécanismes plausibles, puis répondre **« Pourquoi ça
> marche ? »** avec une chaîne explicable, sourcée et accompagnée de son
> incertitude.

La réponse doit pouvoir montrer :

```text
état observé
→ mécanismes pertinents
→ assertions scientifiques utilisées
→ preuves et contradictions
→ hypothèses restantes
→ données manquantes
→ conséquences prévues d'une intervention
```

## Proposition de valeur

EcoBiome couvre quatre niveaux :

```text
Gérer
→ Observer
→ Comprendre
→ Concevoir et améliorer
```

### Gérer

- projets, équipements, populations, tâches et consommables ;
- interventions et historique ;
- sauvegarde, export et restauration.

### Observer

- observations utilisateur ;
- mesures capteurs ;
- médias ;
- état spatio-temporel des zones et populations ;
- météo et autres forçages externes.

### Comprendre

- provenance scientifique ;
- contradictions et corroborations ;
- explications de mécanismes ;
- hypothèses classées ;
- incertitude et données manquantes.

### Concevoir et améliorer

- contraintes absolues ;
- compatibilité biologique ;
- bilans matière/énergie ;
- résilience ;
- scénarios et simulations ;
- comparaison prévu/réel.

## Contrat épistémique

EcoBiome conserve des catégories qui ne doivent jamais être fusionnées
silencieusement :

1. **référence scientifique sourcée** ;
2. **observation utilisateur** ;
3. **mesure instrumentale** ;
4. **assertion scientifique validée** ;
5. **inférence ou estimation** ;
6. **résultat de modèle** ;
7. **simulation ou scénario** ;
8. **recommandation**.

Chaque valeur scientifique conserve, selon le cas, source, date, contexte,
méthode, unité, validité temporelle, niveau de preuve, incertitude et statut
épistémique.

Une extraction IA, un résumé, une corrélation ou un témoignage ne reçoit
aucune promotion automatique vers la vérité scientifique canonique.

## Principe d'explicabilité

Un LLM peut aider à collecter, classer ou présenter. Il ne constitue pas le
moteur de vérité.

Les décisions scientifiques doivent reposer sur des objets déterministes et
auditables :

```text
Source
→ Evidence
→ Claim
→ review
→ Semantic Candidate
→ projection scientifique
→ Scientific Assertion
→ synthèse
→ modèle / raisonnement
→ explication utilisateur
```

Lorsque les données sont insuffisantes, EcoBiome doit :

- répondre avec le niveau d'approximation disponible ;
- indiquer ce qui est supposé ;
- exposer l'incertitude ;
- proposer les mesures ou informations les plus discriminantes.

## Modèle d'écosystème

Le métamodèle cible distingue au minimum :

- système fonctionnel ;
- structure physique ;
- zone environnementale ;
- flux de ressources ;
- taxon, population et individu ;
- occupation spatio-temporelle ;
- observation et événement ;
- intervention ;
- processus écologique ;
- forçage externe ;
- état estimé et état simulé.

La géométrie, la profondeur, le substrat, les flux, les organismes et les
conditions ne sont pas de simples métadonnées : ils conditionnent les
processus.

Les facteurs cibles comprennent notamment :

- chimie de l'eau et cycles biogéochimiques ;
- géologie et substrat ;
- hydrologie et dynamique des fluides ;
- biologie, microbiologie et génétique ;
- température, météo et saisons ;
- lumière et photopériode ;
- influences lunaires ou solaires lorsqu'un modèle et des preuves justifient
  leur usage ;
- interventions humaines ;
- énergie et résilience des équipements.

## Modes de travail

Le produit ne doit pas créer une hiérarchie rigide de « types de biomes ».
Il distingue :

- **profil d'écosystème** : ce qui existe ou est conçu ;
- **mode de travail** : ce que l'utilisateur cherche à faire.

Modes de travail possibles : conception, installation, surveillance,
diagnostic, maintenance, expérimentation, amélioration, restauration,
documentation et comparaison.

## Interfaces

La même connaissance doit pouvoir être présentée à trois profondeurs :

- **débutant** — conclusion, risque, action et explication simple ;
- **intermédiaire** — mécanismes, mesures importantes et incertitude ;
- **avancé** — provenance, hypothèses, paramètres, modèles et preuves.

Ces niveaux changent la présentation, pas la vérité scientifique sous-jacente.

## Architecture et distribution

La cible de long terme sépare :

- **Control Plane** — API, interface, identité, orchestration ;
- **Data Plane** — collecte, transcription, normalisation, provenance ;
- **Compute Plane** — calculs reproductibles et workers spécialisés ;
- **Cloud Plane** — partage, droits et index optionnels ;
- **Worker Plane** — contribution volontaire des machines.

EcoBiome reste utilisable localement. Cloud, GPU distribué et EcoBiome@home
sont **des accélérateurs futurs**, pas des dépendances du MVP scientifique.

## Apprentissage contrôlé

EcoBiome peut apprendre de projets multiples uniquement si les couches restent
séparées :

1. mémoire privée ;
2. connaissance communautaire agrégée et consentie ;
3. référence scientifique validée et sourcée.

Une observation communautaire peut générer une hypothèse ou un signal, jamais
une loi universelle sans validation.

## Automatisation physique

Le contrôle de pompes, chauffages, éclairages, dosages ou autres actionneurs
est différé jusqu'à disposer de :

- limites matérielles ;
- état sûr ;
- consentement explicite ;
- journalisation ;
- reprise manuelle ;
- modèle de risque biologique.

Une recommandation logicielle et une commande physique sont deux frontières
de sécurité distinctes.

## Critère de réussite

EcoBiome réussit lorsque l'utilisateur peut passer d'un écosystème réel à une
explication et à une décision sans perdre la chaîne de preuve :

```text
mon système
→ mes observations
→ ce que la science permet d'affirmer
→ ce que le modèle estime
→ ce qui reste incertain
→ ce que je peux tester ou modifier
```
