# EcoBiome Data Model

> Modèle de données de référence du projet EcoBiome.

Ce document définit la manière dont EcoBiome représente, qualifie, relie et conserve les informations nécessaires à l’étude et à la simulation d’un écosystème.

---

## 1. Objectifs

Le modèle de données doit permettre de représenter :

- un milieu existant, conçu ou hypothétique ;
- des données complètes ou incomplètes ;
- des observations réelles ;
- des hypothèses ;
- plusieurs scénarios ;
- plusieurs simulations ;
- l’évolution du système dans le temps ;
- la provenance et l’incertitude de chaque information ;
- les espèces, matériaux et équipements sans les coder directement dans le moteur.

Le modèle doit rester :

- lisible ;
- versionné ;
- extensible ;
- validable ;
- indépendant de l’interface graphique ;
- indépendant du format de stockage définitif.

---

## 2. Hiérarchie générale

```text
Project
└── Study
    ├── Baseline
    ├── KnowledgeState
    ├── Observations
    ├── Interventions
    ├── Hypotheses
    └── Scenarios
        └── SimulationRun
            ├── SimulationContext
            ├── WorldState
            ├── Results
            └── ExplanationReport
```

---

## 3. Project

Un `Project` est un dossier de travail pouvant regrouper une ou plusieurs études liées.

Exemples :

- étude des mares d’un secteur ;
- gestion des milieux aquatiques d’un jardin ;
- comparaison de plusieurs systèmes aquaponiques ;
- projet pédagogique sur les écosystèmes d’eau douce.

### Données minimales

```yaml
project:
  id: "project-uuid"
  name: "Étude des mares du secteur"
  description: ""
  created_at: "2026-08-01T15:00:00Z"
  updated_at: "2026-08-01T15:00:00Z"
  schema_version: "0.1"
  studies: []
```

---

## 4. Study

Une `Study` représente un système écologique particulier.

### Origines possibles

```text
existing
designed
hypothetical
historical
```

- `existing` : milieu réel déjà existant ;
- `designed` : milieu à construire ou à modifier ;
- `hypothetical` : système exploratoire ou fictif ;
- `historical` : reconstitution d’un milieu passé.

### Structure indicative

```yaml
study:
  id: "study-uuid"
  name: "Mare forestière"
  origin: "existing"
  description: ""
  location: {}
  baseline: {}
  knowledge_state: {}
  observations: []
  interventions: []
  hypotheses: []
  scenarios: []
```

---

## 5. Identifiants

Chaque entité persistante possède un identifiant unique stable.

Exemples :

```text
Project
Study
Observation
Intervention
Scenario
SimulationRun
SpeciesRecord
EquipmentRecord
```

Les noms visibles peuvent changer. Les identifiants ne doivent pas changer.

Le format recommandé est un UUID.

---

## 6. Localisation

La localisation peut être précise, approximative ou absente.

```yaml
location:
  latitude_deg: 45.0000
  longitude_deg: -1.0000
  altitude_m: 12.0
  accuracy_m: 1000
  privacy_level: "approximate"
  timezone: "Europe/Paris"
```

### Niveaux de confidentialité

```text
exact
approximate
region_only
private
unknown
```

Une localisation précise ne doit jamais être rendue publique sans consentement explicite.

---

## 7. Baseline

La `Baseline` décrit l’état de référence de l’étude avant l’application d’un scénario.

Elle peut contenir :

```text
Geometry
Installation
Water
Substrate
Organisms
Equipment
Environment
History
```

Exemple :

```yaml
baseline:
  geometry: {}
  installation: {}
  water: {}
  substrate: {}
  organisms: []
  equipment: []
  environment: {}
```

---

## 8. KnowledgeState

Le `KnowledgeState` représente ce que l’utilisateur et le logiciel savent réellement du système.

Il doit être séparé du `WorldState`.

### Différence fondamentale

```text
WorldState :
état simulé de l’écosystème.

KnowledgeState :
état des connaissances disponibles sur cet écosystème.
```

Le `KnowledgeState` contient notamment :

- données mesurées ;
- données déclarées ;
- données estimées ;
- données régionales ;
- hypothèses ;
- inconnues ;
- dates et provenance ;
- niveaux d’incertitude.

---

## 9. UncertainValue

Toute valeur scientifique importante doit pouvoir être incertaine.

```yaml
temperature:
  value: 22.4
  unit: "degC"
  uncertainty:
    type: "standard_deviation"
    value: 0.2
  quality: "measured"
  source: "digital_thermometer"
  observed_at: "2026-08-01T14:30:00Z"
  confidence: 0.97
```

### Qualité des données

```text
measured
laboratory
reported
derived
regional
inferred
default
unknown
```

### Distributions possibles

```text
fixed
uniform
normal
lognormal
triangular
empirical
unknown
```

Exemple d’une donnée très incertaine :

```yaml
maximum_depth:
  distribution: "uniform"
  minimum: 0.30
  maximum: 0.80
  unit: "m"
  quality: "inferred"
  confidence: 0.35
```

---

## 10. Unités

Les données internes doivent être exprimées dans les unités du Système international.

Exemples :

| Grandeur | Unité interne |
|---|---|
| longueur | m |
| surface | m² |
| volume | m³ |
| masse | kg |
| durée | s |
| température | K |
| concentration molaire | mol·m⁻³ |
| énergie | J |
| puissance | W |
| débit volumique | m³·s⁻¹ |
| pression | Pa |

Les unités usuelles comme les litres, °C, mg/L, °dGH ou °dKH sont converties aux limites du système, notamment dans l’interface et les importateurs.

Le pH reste une grandeur logarithmique sans unité.

---

## 11. Geometry

La géométrie décrit le volume d’eau et ses surfaces limites.

### Types initiaux

```text
rectangular_prism
vertical_cylinder
profiled_pond
custom
```

Exemple rectangulaire :

```yaml
geometry:
  type: "rectangular_prism"
  length_m: 1.0
  width_m: 0.5
  water_height_m: 0.5
```

Exemple de bassin profilé :

```yaml
geometry:
  type: "profiled_pond"
  depth_zones:
    - minimum_depth_m: 0.00
      maximum_depth_m: 0.20
      area_m2: 2.0
    - minimum_depth_m: 0.20
      maximum_depth_m: 0.80
      area_m2: 1.5
```

Les volumes, surfaces et rapports dérivés doivent être calculés, et non saisis en double, sauf à des fins de vérification.

---

## 12. BoundarySurface

Chaque surface de contact est décrite séparément.

```yaml
boundary_surface:
  id: "surface-uuid"
  role: "side_wall"
  area_m2: 0.50
  boundary_medium: "air"
  material_id: "glass"
  thickness_m: 0.008
  orientation_deg: 180
  burial_depth_m: 0.0
  shaded_fraction: 0.2
```

### Milieux de contact

```text
air
ground
building_interior
water
insulation
unknown
```

---

## 13. Installation

L’installation décrit le contexte physique du contenant.

```yaml
installation:
  placement: "outdoor"
  burial_fraction: 0.80
  cover_type: "open"
  greenhouse: false
  insulated: false
  surrounding_soil_id: "clayey_soil"
```

### Placements possibles

```text
indoor
outdoor
greenhouse
semi_outdoor
underground
```

---

## 14. WaterState

L’état de l’eau doit distinguer les variables mesurées des variables calculées.

```yaml
water:
  volume_m3: {}
  temperature_k: {}
  ph: {}
  alkalinity_eq_m3: {}
  calcium_mol_m3: {}
  magnesium_mol_m3: {}
  sodium_mol_m3: {}
  potassium_mol_m3: {}
  chloride_mol_m3: {}
  sulfate_mol_m3: {}
  dissolved_oxygen_mol_m3: {}
  dissolved_inorganic_carbon_mol_m3: {}
  total_ammonia_n_mol_m3: {}
  nitrite_n_mol_m3: {}
  nitrate_n_mol_m3: {}
  phosphate_p_mol_m3: {}
  conductivity_s_m: {}
  turbidity_ntu: {}
```

Le GH, le KH aquariophile, la salinité et certaines valeurs de toxicité peuvent être calculés à partir des constituants disponibles.

---

## 15. SubstrateProfile

Le substrat est représenté par une succession ordonnée de couches.

```yaml
substrate:
  total_area_m2: 0.50
  layers:
    - id: "layer-1"
      material_id: "fine_gravel"
      thickness_m: 0.03
      grain_size_m:
        median: 0.004
      porosity: 0.40

    - id: "layer-2"
      material_id: "coarse_sand"
      thickness_m: 0.05
      grain_size_m:
        median: 0.001
      porosity: 0.34
```

Chaque couche peut contenir :

- matériau ;
- épaisseur ;
- granulométrie ;
- porosité ;
- perméabilité ;
- matière organique ;
- capacité d’échange cationique ;
- biomasse microbienne ;
- oxygène interstitiel ;
- potentiel redox ;
- humidité ou saturation.

---

## 16. SpeciesRecord

Une espèce est une donnée scientifique, et non une classe Python spécialisée.

```yaml
species:
  id: "oryzias-latipes"
  scientific_name: "Oryzias latipes"
  common_names:
    fr: ["Médaka", "Poisson japonais"]
    en: ["Japanese rice fish"]
  taxonomy: {}
  ecological_roles: []
  environmental_responses: {}
  physiology: {}
  nutrition: {}
  reproduction: {}
  behavior: {}
  genetics: {}
  evidence: []
```

---

## 17. EnvironmentalResponse

Les préférences biologiques doivent être représentées sous forme de courbes ou de zones graduées, et non par une simple plage minimale et maximale.

```yaml
temperature_response:
  variable: "water_temperature"
  unit: "degC"
  thresholds:
    lethal_min: 3
    survival_min: 8
    acceptable_min: 15
    optimum_low: 20
    optimum_high: 25
    acceptable_max: 28
    survival_max: 33
    lethal_max: 38
  evidence_level: "B"
```

Le même principe peut être appliqué au :

- pH ;
- GH ;
- KH ;
- oxygène ;
- courant ;
- lumière ;
- profondeur ;
- salinité ;
- densité de population.

---

## 18. Population

Une population regroupe des organismes d’une même espèce.

```yaml
population:
  id: "population-uuid"
  species_id: "oryzias-latipes"
  count: 20
  biomass_kg: 0.045
  sex_ratio:
    male: 0.33
    female: 0.67
  age_distribution: {}
  genetic_state: {}
  health_state: {}
```

Les valeurs agrégées peuvent être utilisées dans les modes Débutant et Intermédiaire.

Le suivi individuel est optionnel et réservé aux modèles plus détaillés.

---

## 19. IndividualOrganism

Le suivi individuel peut contenir :

```yaml
individual:
  id: "organism-uuid"
  species_id: "oryzias-latipes"
  birth_date: null
  age_s: {}
  sex: "female"
  mass_kg: {}
  length_m: {}
  health: {}
  energy_reserve_j: {}
  genotype: {}
  parents: []
```

Ce niveau ne doit pas être imposé aux simulations simples.

---

## 20. EcologicalRole

Les rôles écologiques sont indépendants de la taxonomie.

Exemples :

```text
primary_producer
biofilm_grazer
detritivore
filter_feeder
predator
prey
decomposer
sediment_mixer
nitrogen_fixer
ammonia_oxidizer
nitrite_oxidizer
```

Une espèce peut remplir plusieurs rôles.

---

## 21. Interaction

Une interaction relie deux entités ou deux rôles écologiques.

```yaml
interaction:
  source_id: "species-a"
  target_id: "species-b"
  type: "predation"
  strength: {}
  conditions: []
  evidence_level: "C"
```

### Types initiaux

```text
competition
predation
mutualism
commensalism
parasitism
facilitation
resource_consumption
habitat_creation
```

---

## 22. EquipmentRecord

Un équipement est décrit par ses caractéristiques physiques et fonctionnelles.

```yaml
equipment:
  id: "equipment-uuid"
  category: "water_pump"
  manufacturer: null
  model: null
  rated_power_w: 7.0
  rated_flow_m3_s: 0.0000833
  measured_flow_m3_s: null
  operating_schedule: {}
  efficiency_curve: {}
  installation: {}
  active: true
```

### Catégories initiales

```text
water_pump
air_pump
filter
lamp
heater
cooler
aerator
sensor
solar_panel
battery
```

---

## 23. ProductRecord

Les produits ajoutés au système doivent être décrits par leur composition lorsque celle-ci est connue.

```yaml
product:
  id: "product-uuid"
  name: "Bacterial starter"
  category: "microbial_additive"
  composition: []
  declared_effects: []
  evidence_level: "C"
  composition_known: false
```

Un nom commercial ne doit jamais être considéré comme une composition chimique ou biologique suffisante.

---

## 24. Observation

Une observation peut être qualitative ou quantitative.

```yaml
observation:
  id: "observation-uuid"
  study_id: "study-uuid"
  observed_at: "2026-08-01T10:00:00Z"
  observer: "user"
  type: "species_presence"
  target: "dragonfly_larvae"
  value: true
  method: "visual"
  confidence: 0.75
  attachments: []
```

Exemples :

- présence d’une espèce ;
- eau trouble ;
- ponte observée ;
- mortalité ;
- odeur ;
- comportement inhabituel ;
- mesure instrumentale.

---

## 25. Measurement

Une mesure est une observation quantitative structurée.

```yaml
measurement:
  id: "measurement-uuid"
  variable: "ph"
  value: 7.3
  unit: "dimensionless"
  measured_at: "2026-08-01T10:00:00Z"
  method: "electronic_probe"
  instrument_id: "sensor-uuid"
  uncertainty: 0.1
  calibration_status: "calibrated"
  quality: "measured"
```

---

## 26. Intervention

Une intervention modifie volontairement ou accidentellement le système.

```yaml
intervention:
  id: "intervention-uuid"
  type: "water_change"
  scheduled_at: "2026-08-02T18:00:00Z"
  duration_s: 1800
  parameters:
    replaced_fraction: 0.30
    replacement_water_id: "tap-water-profile"
  status: "completed"
```

### Types initiaux

```text
water_change
feeding
additive
organism_addition
organism_removal
equipment_addition
equipment_removal
maintenance
lighting_change
failure
repair
harvest
plant_pruning
```

---

## 27. Hypothesis

Une hypothèse représente une proposition incertaine utilisée pour compléter les connaissances disponibles.

```yaml
hypothesis:
  id: "hypothesis-uuid"
  statement: "Le fond de la mare est majoritairement argileux."
  target_variable: "substrate_material"
  proposed_value: "clay"
  probability: 0.55
  rationale: "Contexte géologique régional"
  status: "active"
  testable_by:
    - "sediment_sample"
```

Une hypothèse doit rester distincte d’une mesure.

---

## 28. Scenario

Un scénario décrit une configuration à simuler à partir d’une étude et d’un ensemble d’hypothèses.

```yaml
scenario:
  id: "scenario-uuid"
  name: "Sans pompe"
  baseline_study_id: "study-uuid"
  active_hypotheses: []
  modifications:
    - type: "equipment_state"
      equipment_id: "pump-uuid"
      active: false
  simulation_settings: {}
```

Les scénarios doivent être comparables entre eux.

---

## 29. SimulationContext

Le `SimulationContext` contient les conditions immuables ou externes nécessaires à une exécution.

```yaml
simulation_context:
  location: {}
  start_time: "2026-08-01T00:00:00Z"
  end_time: "2027-08-01T00:00:00Z"
  time_step_s: 3600
  random_seed: 123456
  selected_models: {}
  model_versions: {}
  enabled_modules: []
```

---

## 30. WorldState

Le `WorldState` représente l’état simulé du système à un instant précis.

Il ne doit pas contenir directement l’intégralité de l’historique.

```yaml
world_state:
  timestamp: "2026-08-01T12:00:00Z"
  water: {}
  substrate: {}
  populations: []
  equipment_states: []
  environmental_drivers: {}
  conserved_quantities: {}
```

L’historique est conservé séparément sous forme de sorties ou de séries temporelles.

---

## 31. SimulationRun

Une exécution de simulation doit être entièrement reproductible.

```yaml
simulation_run:
  id: "run-uuid"
  scenario_id: "scenario-uuid"
  engine_version: "0.1.0"
  schema_version: "0.1"
  random_seed: 123456
  started_at: "2026-08-01T15:00:00Z"
  completed_at: null
  status: "running"
  context: {}
  initial_state: {}
  result_reference: null
```

---

## 32. Results

Les résultats peuvent contenir :

- séries temporelles ;
- bilans de masse ;
- indicateurs de risque ;
- indicateurs biologiques ;
- intervalles d’incertitude ;
- détection de seuils ;
- comparaison avec des observations ;
- événements critiques.

```yaml
results:
  time_series: {}
  mass_balance: {}
  risks: []
  biological_indices: {}
  uncertainty_summary: {}
  warnings: []
```

---

## 33. ExplanationReport

Le rapport explicatif relie les résultats aux processus responsables.

```yaml
explanation_report:
  conclusion: "Le système reste stable principalement grâce au biofiltre."
  confidence: 0.74
  primary_causes: []
  limiting_factors: []
  counterfactuals: []
  missing_information: []
  recommended_measurements: []
```

Chaque explication doit indiquer :

- les données utilisées ;
- les hypothèses ;
- les modèles ;
- les contributions causales ;
- les incertitudes.

---

## 34. Provenance scientifique

Toute donnée de référence doit pouvoir citer sa provenance.

```yaml
evidence:
  id: "evidence-uuid"
  type: "scientific_publication"
  citation: ""
  publication_year: 2024
  doi: null
  url: null
  accessed_at: null
  evidence_level: "B"
  notes: ""
```

### Niveaux de preuve initiaux

```text
A — mécanisme démontré et quantifié
B — résultat robuste et reproductible
C — preuve limitée ou dépendante du contexte
D — hypothèse exploratoire
E — non démontré ou contradictoire
```

---

## 35. Versionnement des schémas

Chaque fichier persistant doit déclarer une version de schéma.

```yaml
schema_version: "0.1"
```

Toute modification incompatible nécessite :

- une nouvelle version ;
- une procédure de migration ;
- des tests de compatibilité ;
- une documentation.

---

## 36. Formats de stockage

La décision définitive sera documentée dans une ADR dédiée.

Orientation actuelle :

- YAML ou JSON pour les fiches lisibles et versionnées ;
- SQLite pour les projets, historiques et volumes importants ;
- CSV ou Parquet pour les séries temporelles exportées ;
- archive ouverte pour les futurs fichiers `.ecobiome`.

Le modèle conceptuel ne doit pas dépendre d’un format de stockage particulier.

---

## 37. Validation

Chaque objet chargé doit être validé avant utilisation.

Les contrôles doivent notamment vérifier :

- présence des champs obligatoires ;
- types de données ;
- unités ;
- bornes physiques ;
- cohérence des identifiants ;
- absence de valeurs impossibles ;
- compatibilité de version ;
- conservation des quantités lorsque nécessaire.

Une donnée invalide ne doit jamais être corrigée silencieusement.

---

## 38. Données manquantes

Les données manquantes doivent être représentées explicitement.

Elles ne doivent pas être remplacées silencieusement par zéro.

Le moteur peut proposer une estimation, mais celle-ci doit être enregistrée comme :

```text
inferred
regional
default
hypothesis
```

avec une incertitude et une provenance.

---

## 39. Extensibilité

Le modèle doit permettre l’ajout futur :

- d’autres biomes ;
- de nouveaux types d’organismes ;
- de nouvelles géométries ;
- de nouveaux équipements ;
- de nouvelles variables chimiques ;
- de nouveaux modèles scientifiques ;
- de plugins ;
- de nouveaux formats d’import et d’export.

Les champs inconnus doivent être gérés de manière contrôlée selon la politique de compatibilité choisie.

---

## 40. Principe fondamental

> EcoBiome doit distinguer ce qui existe, ce qui est observé, ce qui est supposé, ce qui est simulé et ce qui est recommandé.

Cette séparation est obligatoire pour garantir la transparence, l’explicabilité et la validité scientifique du projet.