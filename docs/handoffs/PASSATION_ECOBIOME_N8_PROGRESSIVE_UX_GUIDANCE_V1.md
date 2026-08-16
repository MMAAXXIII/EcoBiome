# PASSATION ECOBIOME — N8 Progressive UX & Guided Data Entry V1

## Statut visé

Gate local attendu :

`ECOBIOME_N8_PROGRESSIVE_UX_GUIDANCE_V1_LOCAL_IMPLEMENTATION_VALIDATED`

N8 s'appuie sur N7 validé et ne modifie aucun contrat Scientific Foundation, N4 ou N5.

## Objectif

N7 donne à EcoBiome un modèle beaucoup plus riche de stocks, flux, mesures et interventions. N8 empêche cette richesse de devenir une interface de laboratoire illisible.

N8 introduit une divulgation progressive à trois niveaux :

- `beginner` / **Débutant** : données essentielles et saisie courte ;
- `intermediate` / **Intermédiaire** : charge biologique, minéralisation, oxygène, débit réel et maturité du biofiltre ;
- `advanced` / **Avancé** : chimie détaillée, solides, PAR, redox et métrologie avancée.

Le niveau d'affichage est une préférence UI locale. Il ne supprime, ne réécrit et ne dégrade aucune donnée déjà persistée.

## Décisions d'architecture

### 1. Couverture des données ≠ diagnostic

N8 ajoute :

`GET /api/water-bodies/{project_id}/guidance?level=beginner|intermediate|advanced`

La réponse contient :

- `known_required_count` ;
- `required_count` ;
- les éléments `known`, `missing` ou `check` ;
- jusqu'à cinq prochaines informations utiles à renseigner ;
- `is_diagnostic = false` ;
- un message explicite indiquant qu'il ne s'agit pas d'un score de santé.

Aucun seuil de qualité biologique n'est déduit de cette couverture.

### 2. Applicabilité contextuelle

Un élément peut être `check` plutôt que `missing` lorsqu'EcoBiome ne sait pas encore s'il s'applique au milieu.

Exemples :

- faune absente du dossier : « à renseigner si des animaux sont présents » ;
- filtration absente : « à renseigner si une filtration technique est utilisée » ;
- ORP : avancé mais non universel ;
- PAR : exigé en Avancé uniquement lorsqu'une végétation ou un éclairage est déclaré.

Lorsque des animaux sont déclarés, Intermédiaire attend notamment :

- masse moyenne ;
- nourrissage ;
- TAN ;
- oxygène dissous.

Lorsqu'un filtre est déclaré, Intermédiaire attend notamment :

- débit réellement mesuré ;
- maturité biologique.

### 3. Niveau Débutant

Mesures affichées/saisissables directement :

- température ;
- pH ;
- nitrites ;
- nitrates ;
- KH.

Dans les formulaires :

- population animale : nom courant + effectif ;
- nourrissage : aliment + quantité ;
- plante : nom courant ;
- profil d'eau : origine + T° + pH + KH ;
- substrat : matériau + épaisseur ;
- matériel : informations opérationnelles principales.

L'incertitude métrologique est masquée mais conserve la valeur par défaut `0` utilisée par le contrat existant.

### 4. Niveau Intermédiaire

Ajoute notamment :

- GH ;
- TAN ;
- oxygène dissous ;
- conductivité ;
- phosphate ;
- masse moyenne et stade des animaux ;
- protéines de l'aliment ;
- quantité/couverture végétale ;
- chimie plus complète de l'eau source ;
- granulométrie et caractère organique du substrat ;
- débit mesuré ;
- média, volume et maturité biologique du filtre ;
- date de mise en service et opérations plus spécialisées.

### 5. Niveau Avancé

Expose toutes les métriques N7 et notamment :

- TSS ;
- chlorures ;
- calcium ;
- magnésium ;
- salinité ;
- ORP ;
- saturation O2 ;
- PAR surface/fond ;
- algues/périphyton ;
- surface spécifique du média ;
- capacité TAN mesurée ;
- incertitude de mesure ;
- noms scientifiques et détails fins des profils.

### 6. Préférence UI

La préférence est stockée dans le navigateur sous :

`ecobiome-experience-level`

Valeurs admises : `beginner`, `intermediate`, `advanced`.

La valeur par défaut est `beginner`.

Cette préférence n'est pas une donnée scientifique et n'est donc ni N4, ni N5, ni N7.

### 7. Historique des mesures

N8 corrige un reliquat d'affichage : les variables N7 marquées `contextual` n'affichent plus une plage universelle « Idéal » dans l'historique.

Elles affichent :

`Selon espèces / contexte`

Les événements N5 eux-mêmes ne changent pas.

## Fichiers N8

Nouveau :

- `tests/test_n8_progressive_guidance.py`
- `docs/handoffs/PASSATION_ECOBIOME_N8_PROGRESSIVE_UX_GUIDANCE_V1.md`

Modifiés :

- `backend/api.py`
- `bolt-dashboard/src/lib/types.ts`
- `bolt-dashboard/src/lib/api.ts`
- `bolt-dashboard/src/lib/hooks.ts`
- `bolt-dashboard/src/views/WaterBodiesView.tsx`
- `bolt-dashboard/src/views/EcosystemInputsPanel.tsx`

## Tests d'acceptation N8

1. le health endpoint expose `bridge_version = n8` ;
2. le guidage Débutant retourne exactement les informations essentielles attendues ;
3. `is_diagnostic` reste toujours `false` ;
4. après saisie des cinq mesures de base + un profil d'eau, la couverture Débutant est complète ;
5. faune et filtration non déclarées restent `check`, pas diagnostic négatif ;
6. lorsqu'une population animale existe, masse/nourrissage/TAN/O2 deviennent contextuellement attendus en Intermédiaire ;
7. lorsqu'un filtre existe, débit mesuré et maturité deviennent attendus ;
8. chimie de base du profil d'eau reconnue ;
9. PAR non obligatoire sans plante/éclairage ;
10. PAR devient requis en Avancé lorsqu'une plante est enregistrée ;
11. le niveau UI est mémorisé localement ;
12. la liste de mesures et les formulaires sont progressivement filtrés ;
13. aucune mesure existante n'est supprimée lorsqu'on change de niveau ;
14. historique : les métriques contextuelles affichent « Selon espèces / contexte » ;
15. N6, N6.1, N6.2 et N7 restent verts ;
16. suite projet complète verte ;
17. Ruff, mypy, TypeScript typecheck, Vite build et `git diff --check` verts ;
18. staging vide avant/après.

## Limites assumées

- N8 ne sait pas encore déduire automatiquement les exigences propres à une espèce depuis la Knowledge Base ; cela appartient au futur moteur de diagnostic espèce-spécifique.
- La couverture n'évalue pas la fraîcheur temporelle des mesures. Une température vieille de six mois compte encore comme « renseignée » ; la notion de péremption/âge des données devra être ajoutée ultérieurement.
- Les actions proposées sont informatives ; elles ne naviguent pas encore automatiquement vers le champ exact.
- Un milieu sans faune ou sans filtre ne peut pas encore être explicitement marqué « non applicable » par l'utilisateur ; N8 utilise donc le statut neutre `check`.
- Le niveau d'affichage est global au navigateur et non spécifique à chaque projet.

## Critères de non-régression

- aucune modification de Scientific Foundation Schema V6 ;
- aucune modification de `src/ecobiome/journal/canonical_project_event_v1.py` ;
- aucun affaiblissement du garde N4 sur les quantités dynamiques ;
- aucune réécriture d'événement N5/N7 existant ;
- aucun nettoyage des fichiers historiques non suivis ;
- staging vide avant/après ;
- aucun commit, push, merge, rebase, stash, reset destructif ou `git clean`.

## Autorisation

**NE PAS COMMITER, PUSHER, MERGER, REBASER, SUPPRIMER DE BRANCHE, MODIFIER LA PR #11 OU PUBLIER N8 SANS AUTORISATION EXPLICITE DE L'UTILISATEUR.**
