# ECG Online — Architecture cible et feuille de route scientifique

**Document de travail pour le développement de la nouvelle architecture**  
**Statut :** version de cadrage  
**Date :** 29 juillet 2026  
**Projet :** ECG Online — correction automatisée de réponses libres en électrocardiographie  
**Objectif principal :** fiabiliser le moteur de correction, poursuivre la constitution du corpus annoté, puis produire une validation scientifique publiable et préparer le déploiement multicentrique.

---

## 1. Vision du projet

ECG Online est une plateforme pédagogique dans laquelle un étudiant :

1. observe un tracé ECG ;
2. rédige une interprétation libre ;
3. reçoit une correction structurée ;
4. visualise les éléments reconnus, manquants ou erronés ;
5. peut progresser dans des parcours pédagogiques ;
6. contribue, par ses réponses, à la constitution d’un corpus de recherche en pédagogie médicale et en traitement automatique du langage clinique.

La finalité du projet n’est pas de produire un « LLM qui note tout seul », mais de développer un système :

- **explicable** ;
- **reproductible** ;
- **versionné** ;
- **évaluable scientifiquement** ;
- **déployable localement ou institutionnellement** ;
- **capable de s’abstenir lorsqu’il n’est pas suffisamment fiable** ;
- **compatible avec une gouvernance multicentrique**.

La cible technologique est une architecture hybride :

> **compréhension neuronale du texte + représentation ontologique explicite + règles de cohérence + scoring déterministe + feedback pédagogique contrôlé.**

---

# 2. Priorités stratégiques

Les priorités doivent rester hiérarchisées.

## Priorité 1 — Fiabiliser l’architecture

Avant d’ajouter de nouvelles fonctionnalités, il faut stabiliser :

- les contrats de données ;
- le pipeline de correction ;
- la séparation entre extraction, résolution, scoring et feedback ;
- les règles de repli et d’abstention ;
- la traçabilité de chaque décision ;
- les tests automatiques ;
- la sécurité ;
- la reproductibilité.

## Priorité 2 — Poursuivre la collecte

Le projet doit continuer à recueillir :

- les réponses libres ;
- les scores ;
- les concepts détectés ;
- les corrections expertes ;
- les votes de validation ou de signalement ;
- les temps de réponse ;
- les modifications de réponse ;
- la confiance de l’étudiant ;
- l’usage des aides ;
- la version du moteur ayant produit la correction.

Cette collecte doit être pensée dès maintenant comme un **futur corpus de recherche**.

## Priorité 3 — Constituer la vérité de terrain

Le corpus doit progressivement permettre :

- une double annotation experte ;
- la mesure de l’accord inter-experts ;
- la validation du moteur d’extraction ;
- la validation du mapping ontologique ;
- la validation du scoring ;
- la détection des erreurs cliniques graves ;
- l’évaluation de la reproductibilité.

## Priorité 4 — Produire l’article technologique

L’article doit décrire et valider :

- l’architecture ;
- l’ontologie ;
- le corpus ;
- les performances du pipeline ;
- les analyses d’ablation ;
- les performances comparées aux humains et aux baselines ;
- la capacité d’abstention ;
- la robustesse aux formulations inhabituelles ou adversariales.

## Priorité 5 — Évaluer l’impact pédagogique

Dans un second temps, le projet doit tester :

- l’apprentissage ;
- la rétention ;
- le transfert vers de nouveaux ECG ;
- la calibration de la confiance ;
- le temps d’apprentissage ;
- l’acceptabilité ;
- l’effet du feedback automatique.

---

# 3. Positionnement scientifique

## 3.1. Ce que fait le système

Le système évalue une **réponse textuelle libre** produite par un étudiant à partir d’un ECG connu.

Il ne réalise pas encore une interprétation primaire du signal ECG.

Le bon positionnement est donc :

> **Automatic short-answer assessment for ECG interpretation using ontology-grounded clinical concept extraction and deterministic scoring.**

## 3.2. Hypothèse scientifique centrale

Une architecture hybride, combinant :

- extraction neuronale ;
- entity linking ;
- ontologie ECG ;
- règles explicites ;
- scoring déterministe ;

devrait être :

- plus reproductible qu’un LLM direct ;
- plus explicable ;
- plus facile à maintenir ;
- plus facile à déployer localement ;
- plus adaptée à la validation scientifique ;
- plus robuste pour un usage pédagogique.

## 3.3. Questions de recherche principales

1. Le système identifie-t-il correctement les concepts exprimés par l’étudiant ?
2. Associe-t-il correctement ces concepts à l’ontologie ?
3. Détecte-t-il correctement la négation, l’incertitude et les contradictions ?
4. Le score automatique est-il concordant avec le score expert ?
5. Le système détecte-t-il les erreurs cliniques graves ?
6. L’architecture hybride est-elle supérieure à un LLM direct ?
7. L’architecture locale est-elle non inférieure à l’architecture cloud ?
8. Le feedback améliore-t-il l’apprentissage et la calibration de la confiance ?

---

# 4. Principes de conception

## 4.1. Le LLM ne doit pas être le barème

Le modèle neuronal doit comprendre le texte.

Il ne doit pas décider seul :

- de la note finale ;
- de la réussite ;
- des pénalités ;
- du caractère grave d’une erreur ;
- des relations entre concepts ;
- des conditions de validation d’un parcours.

Ces éléments doivent rester explicites et versionnés.

## 4.2. Le scoring doit rester déterministe

À entrée structurée identique, le score doit être identique.

Le moteur de scoring doit être :

- pur ;
- testable ;
- indépendant du fournisseur de modèle ;
- documenté ;
- versionné ;
- dépourvu d’appels réseau ;
- capable de produire une justification détaillée.

## 4.3. Le système doit pouvoir s’abstenir

Le système ne doit pas basculer silencieusement vers une autre philosophie de correction.

États possibles :

- `SUCCESS` : correction complète et fiable ;
- `LOW_CONFIDENCE` : correction affichée avec avertissement ;
- `ABSTAIN` : correction automatique non rendue ;
- `HUMAN_REVIEW` : revue experte nécessaire ;
- `TECHNICAL_ERROR` : échec technique.

## 4.4. Toute décision doit être traçable

Pour chaque réponse, il faut pouvoir reconstruire :

- le texte reçu ;
- les segments identifiés ;
- les concepts proposés ;
- les concepts retenus ;
- les alternatives ;
- la polarité ;
- la confiance ;
- la méthode ;
- les règles appliquées ;
- la version de l’ontologie ;
- la version du barème ;
- la version du modèle ;
- la version du code ;
- la note finale ;
- la raison d’une éventuelle abstention.

## 4.5. Le corpus doit être indépendant des versions du moteur

La réponse brute ne doit jamais être écrasée.

Les sorties du moteur doivent être stockées comme des prédictions versionnées.

Une même réponse doit pouvoir être rejouée ultérieurement avec :

- une nouvelle ontologie ;
- un nouveau modèle ;
- un nouveau barème ;
- une nouvelle règle de scoring.

---

# 5. Architecture cible

```text
Réponse de l’étudiant
        │
        ▼
[1] API d’entrée
    - authentification
    - contrôle de longueur
    - contrôle de langue
    - identifiant de requête
    - journalisation
        │
        ▼
[2] Prétraitement déterministe
    - normalisation Unicode
    - segmentation
    - expansion d’abréviations non ambiguës
    - détection des valeurs
    - détection des négations simples
    - détection des réponses vides ou hors sujet
        │
        ▼
[3] Extraction des mentions ECG
    - baseline à règles
    - encodeur clinique fine-tuné
    - ou petit LLM local contraint
        │
        ▼
[4] Génération de candidats ontologiques
    - lexique
    - synonymes
    - BM25
    - embeddings locaux
    - relations parent/enfant
        │
        ▼
[5] Entity linking / reranking
    - correspondance exacte
    - cross-encoder
    - petit LLM contraint
    - sortie limitée aux identifiants autorisés
        │
        ▼
[6] Objet de preuve structuré
    - span
    - concept_id
    - statut
    - confiance
    - méthode
    - alternatives
        │
        ▼
[7] Contrôle de cohérence symbolique
    - exclusions
    - contradictions
    - redondances
    - compatibilité diagnostique
    - hiérarchie
    - incohérences de polarité
        │
        ▼
[8] Scoring déterministe
    - validants
    - complémentaires
    - erreurs graves
    - crédit partiel
    - plafond
    - décision de réussite
        │
        ├───────────────┐
        ▼               ▼
[9A] Confiance      [9B] Confiance
     suffisante          insuffisante
        │               │
        ▼               ▼
Feedback contrôlé   Abstention /
et correction       revue humaine
```

---

# 6. Découpage fonctionnel recommandé

## 6.1. `ingestion`

Responsabilités :

- validation du payload ;
- normalisation ;
- sécurité ;
- génération d’identifiants ;
- capture des métadonnées ;
- conservation de la réponse brute.

## 6.2. `preprocessing`

Responsabilités :

- Unicode ;
- casse ;
- ponctuation ;
- apostrophes ;
- unités ;
- espaces ;
- segmentation en propositions ;
- règles simples de négation ;
- reconnaissance des valeurs ECG.

Ce module doit être déterministe et abondamment testé.

## 6.3. `mention_extraction`

Responsabilités :

- identifier les expressions cliniquement pertinentes ;
- retourner leur position dans le texte ;
- ne pas produire directement le score ;
- séparer extraction et normalisation.

Sortie minimale :

```json
{
  "mention_id": "m_001",
  "text": "pas de trouble de repolarisation",
  "start": 18,
  "end": 52,
  "polarity": "absent",
  "certainty": "asserted",
  "extractor": "camembert_ecg_v1",
  "confidence": 0.94
}
```

## 6.4. `ontology_retrieval`

Responsabilités :

- produire les candidats possibles ;
- utiliser les noms, synonymes et variantes ;
- combiner sparse et dense retrieval ;
- ne jamais créer d’identifiant absent de l’ontologie.

## 6.5. `entity_linking`

Responsabilités :

- choisir un concept parmi les candidats ;
- produire un score de confiance calibrable ;
- conserver les alternatives ;
- permettre l’abstention.

Sortie minimale :

```json
{
  "mention_id": "m_001",
  "concept_id": "TROUBLE_REPOLARISATION",
  "confidence": 0.91,
  "method": "cross_encoder",
  "alternatives": [
    {
      "concept_id": "ANOMALIE_ONDE_T",
      "score": 0.18
    }
  ]
}
```

## 6.6. `symbolic_validator`

Responsabilités :

- vérifier les relations ;
- identifier les contradictions ;
- identifier les concepts incompatibles ;
- détecter les diagnostics multiples non hiérarchisés ;
- distinguer diagnostic principal et alternatives ;
- vérifier la cohérence entre polarité et barème.

## 6.7. `scoring_engine`

Responsabilités :

- calculer les sous-scores ;
- calculer la note finale ;
- expliquer chaque point gagné ou perdu ;
- produire une décision ;
- rester indépendant du feedback textuel.

Entrées :

- concepts de l’étudiant ;
- barème du cas ;
- ontologie ;
- règles de scoring.

Sorties :

```json
{
  "score_total": 78,
  "score_diagnostic": 85,
  "score_description": 60,
  "critical_error": false,
  "decision": "ACCEPTABLE",
  "evidence": [],
  "missing": [],
  "incorrect": [],
  "rule_version": "scoring_v4.0.0"
}
```

## 6.8. `feedback_engine`

Responsabilités :

- transformer les preuves en retour pédagogique ;
- ne pas modifier le score ;
- ne pas inventer de concept ;
- s’appuyer uniquement sur les sorties structurées ;
- utiliser un template déterministe ou un LLM local/cloud ;
- pouvoir être désactivé dans les benchmarks.

## 6.9. `evaluation`

Responsabilités :

- replay du corpus ;
- comparaisons de modèles ;
- calcul des métriques ;
- analyses d’ablation ;
- rapports de régression ;
- génération des tables et figures de l’article.

---

# 7. Arborescence cible du dépôt

```text
ecg-online/
├── app/
│   ├── api/
│   ├── services/
│   ├── auth/
│   └── schemas/
├── core/
│   ├── preprocessing/
│   ├── mention_extraction/
│   ├── ontology_retrieval/
│   ├── entity_linking/
│   ├── symbolic_validation/
│   ├── scoring/
│   ├── abstention/
│   └── feedback/
├── ontology/
│   ├── ontology.json
│   ├── ontology.schema.json
│   ├── migrations/
│   ├── mappings/
│   └── tests/
├── data/
│   ├── cases/
│   ├── scoring/
│   ├── fixtures/
│   └── examples/
├── research/
│   ├── annotation_guidelines/
│   ├── gold_standard/
│   ├── benchmarks/
│   ├── ablations/
│   ├── statistics/
│   └── manuscript/
├── frontend/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   ├── adversarial/
│   └── end_to_end/
├── scripts/
├── migrations/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_DICTIONARY.md
│   ├── ONTOLOGY_GOVERNANCE.md
│   ├── ANNOTATION_MANUAL.md
│   ├── SCIENTIFIC_VALIDATION.md
│   └── DEPLOYMENT.md
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

# 8. Contrats de données

## 8.1. Réponse brute

```json
{
  "response_id": "uuid",
  "student_pseudonym": "uuid",
  "institution_id": "clermont",
  "case_id": "case_023",
  "answer_raw": "Rythme sinusal avec PR allongé...",
  "submitted_at": "2026-07-29T19:20:00Z",
  "language": "fr",
  "session_id": "uuid",
  "attempt_number": 1,
  "metadata": {}
}
```

## 8.2. Prédiction du moteur

```json
{
  "prediction_id": "uuid",
  "response_id": "uuid",
  "pipeline_version": "2.0.0",
  "ontology_version": "1.4.0",
  "scoring_version": "4.0.0",
  "model_versions": {
    "extractor": "camembert-ecg-v1",
    "embedding": "local-embedding-v1",
    "reranker": "ecg-linker-v1",
    "feedback": "local-instruct-v1"
  },
  "mentions": [],
  "concepts": [],
  "contradictions": [],
  "score": {},
  "abstention": {},
  "latency_ms": 820
}
```

## 8.3. Annotation experte

```json
{
  "annotation_id": "uuid",
  "response_id": "uuid",
  "annotator_id": "expert_01",
  "annotation_version": "1.0",
  "mentions": [],
  "global_score": 80,
  "diagnostic_score": 90,
  "description_score": 65,
  "critical_error": false,
  "decision": "ACCEPTABLE",
  "comment": ""
}
```

## 8.4. Adjudication

```json
{
  "response_id": "uuid",
  "expert_1": "annotation_uuid_1",
  "expert_2": "annotation_uuid_2",
  "adjudicator": "expert_03",
  "final_annotation": "annotation_uuid_final",
  "disagreement_types": [
    "ENTITY_LINKING",
    "SCORE_DIFFERENCE"
  ]
}
```

---

# 9. Gestion de l’ontologie

## 9.1. L’ontologie reste externe aux modèles

Elle doit être :

- lisible ;
- modifiable ;
- versionnée ;
- testée ;
- documentée ;
- indépendante des poids d’un modèle.

## 9.2. Chaque concept doit comporter

- `concept_id` stable ;
- nom canonique français ;
- éventuel nom anglais ;
- synonymes ;
- type ;
- catégorie ;
- parents ;
- enfants ;
- relations `requires` ;
- qualificatifs ;
- supports ;
- exclusions ;
- familles incompatibles ;
- niveau pédagogique ;
- exemples positifs ;
- exemples négatifs ;
- statut actif ou déprécié ;
- version d’introduction ;
- justification clinique.

## 9.3. Tests automatiques de cohérence

À chaque modification :

- identifiants uniques ;
- aucune référence vers un identifiant absent ;
- absence de cycle hiérarchique non intentionnel ;
- relations parent/enfant symétriques ;
- exclusion non contradictoire ;
- absence de conflit `present/absent` ;
- concepts dépréciés correctement remplacés ;
- compatibilité avec les goldens ;
- couverture des cas ;
- absence de duplication de synonymes ambigus non documentés.

## 9.4. Gouvernance

Toute modification significative doit être :

1. proposée ;
2. documentée ;
3. relue par au moins un expert ECG ;
4. testée sur le corpus ;
5. associée à une migration ;
6. publiée avec un numéro de version.

---

# 10. Stratégie de modèles

## 10.1. Baselines obligatoires

Le projet doit conserver plusieurs moteurs comparables :

### Baseline A — Règles et dictionnaire

- déterministe ;
- rapide ;
- local ;
- explicable ;
- point de comparaison minimal.

### Baseline B — LLM direct

- correction globale ;
- prompt identique ;
- température nulle ;
- sortie structurée ;
- uniquement comme comparateur.

### Baseline C — Pipeline hybride actuel

- NER LLM ;
- recherche hybride ;
- juge ;
- scoring ontologique.

### Modèle D — Encodeur clinique

- CamemBERT-bio ou modèle équivalent ;
- fine-tuning pour l’extraction ;
- classification de polarité ;
- entity linking séparé.

### Modèle E — Petit LLM local

- sortie contrainte ;
- LoRA éventuelle ;
- utilisé uniquement pour les segments ambigus.

## 10.2. Fine-tuning recommandé

Le fine-tuning doit viser :

- extraction de mentions ;
- polarité ;
- incertitude ;
- type de mention ;
- entity linking ;
- contradictions.

Il ne doit pas viser directement :

- la note finale ;
- le verdict final ;
- tout le raisonnement de correction ;
- la mémorisation de l’ontologie.

## 10.3. Stratégie locale

Cible :

- embeddings locaux ;
- NER local ;
- reranker local ;
- feedback local optionnel ;
- API compatible OpenAI interne ;
- aucune dépendance obligatoire à un service cloud.

Le cloud peut rester :

- une baseline ;
- une solution de secours administrativement contrôlée ;
- un outil d’annotation ;
- un comparateur scientifique.

---

# 11. Confiance et abstention

## 11.1. Facteurs de confiance

La confiance globale doit intégrer :

- couverture de la réponse ;
- confiance de l’extracteur ;
- marge entre les deux meilleurs concepts ;
- taux de concepts non résolus ;
- présence de contradictions ;
- couverture des validants ;
- présence d’une erreur grave ;
- longueur anormale ;
- détection d’une injection ;
- accord entre plusieurs méthodes.

## 11.2. Exemple de règles initiales

Le système s’abstient si :

- aucun concept n’est résolu ;
- plus de 40 % des mentions restent non résolues ;
- un validant central a deux candidats proches ;
- une contradiction diagnostique majeure reste non résolue ;
- le texte contient plusieurs diagnostics incompatibles sans hiérarchie ;
- le moteur détecte une possible injection ;
- le modèle ou l’ontologie n’est pas disponible ;
- un contrôle de cohérence échoue.

Ces seuils doivent être calibrés et non considérés comme définitifs.

## 11.3. Métriques d’abstention

Il faut rapporter :

- taux d’abstention ;
- exactitude sur les cas non abstenus ;
- couverture ;
- risque sélectif ;
- erreurs graves non détectées ;
- performance en fonction du seuil.

---

# 12. Collecte des données

## 12.1. Objectifs

La collecte doit servir simultanément :

- au suivi pédagogique ;
- à l’amélioration technique ;
- à la constitution du corpus ;
- à la préparation des études ;
- à la détection des erreurs du système.

## 12.2. Données minimales à conserver

- réponse brute ;
- cas ;
- date ;
- session ;
- pseudonyme ;
- faculté ;
- niveau d’étude ;
- première réponse ;
- réponse finale ;
- confiance ;
- temps actif ;
- temps hors application ;
- aides consultées ;
- modèle ;
- concepts extraits ;
- score ;
- backend ;
- erreurs techniques ;
- signalement étudiant ;
- revue experte éventuelle.

## 12.3. Données à ne pas collecter sans nécessité

- identité civile ;
- adresse électronique en clair ;
- numéro étudiant en clair ;
- données médicales personnelles ;
- informations sans intérêt scientifique ou pédagogique.

## 12.4. Migration depuis Google Sheets

Google Sheets peut rester une solution transitoire.

La cible doit être PostgreSQL avec :

- migrations ;
- contraintes ;
- index ;
- séparation des institutions ;
- journal append-only ;
- exports versionnés ;
- sauvegarde ;
- politique de rétention ;
- contrôle d’accès ;
- possibilité de suppression ou d’opposition.

## 12.5. Constitution progressive du corpus

### Étape A

- nettoyer les réponses existantes ;
- dédupliquer ;
- identifier les réponses inexploitables ;
- documenter les variables ;
- figer une première version.

### Étape B

- double annotation de toutes les réponses disponibles ;
- adjudication des désaccords principaux ;
- calcul de l’accord inter-experts.

### Étape C

- apprentissage actif ;
- suréchantillonnage des formulations difficiles ;
- collecte ciblée des concepts rares ;
- enrichissement des négations, ambiguïtés et contradictions.

### Étape D

- validation externe ;
- faculté différente ;
- nouveaux cas ;
- niveau d’étude différent ;
- formulations non vues.

---

# 13. Manuel d’annotation

Le manuel doit préciser :

- ce qui constitue une mention ;
- les limites du segment ;
- la gestion des abréviations ;
- les valeurs numériques ;
- la négation ;
- l’hypothèse ;
- les alternatives ;
- les diagnostics multiples ;
- la redondance ;
- les erreurs cliniques ;
- les concepts hors ontologie ;
- la manière de noter une réponse partielle ;
- les règles d’adjudication.

## 13.1. Exemple

Réponse :

> « FA rapide avec QRS fins, pas de signe de pré-excitation. »

Annotations :

| Segment | Concept | Statut |
|---|---|---|
| FA | FIBRILLATION_ATRIALE | présent |
| rapide | TACHYCARDIE | présent |
| QRS fins | QRS_FINS | présent |
| pas de signe de pré-excitation | PREEXCITATION | absent |

## 13.2. Cas difficiles à documenter

- « probablement une TV » ;
- « TV ou TSV avec aberration » ;
- « pas franchement de BBG » ;
- « BBD ? » ;
- « rythme sinusal mais peut-être FA » ;
- « QRS larges compatibles avec une stimulation » ;
- réponses comportant plusieurs diagnostics contradictoires ;
- bonne conclusion avec description incorrecte ;
- mauvaise conclusion avec description correcte.

---

# 14. Plan d’évaluation technique

## 14.1. Extraction

Métriques :

- précision ;
- rappel ;
- F1 ;
- micro-F1 ;
- macro-F1 ;
- F1 par famille ;
- F1 par polarité ;
- F1 sur les concepts rares ;
- exact match des segments ;
- overlap match.

## 14.2. Entity linking

Métriques :

- exactitude top-1 ;
- recall top-3 ;
- MRR ;
- taux de `NONE` correct ;
- calibration ;
- erreurs parent/enfant ;
- erreurs entre concepts incompatibles.

## 14.3. Négation et incertitude

Métriques :

- F1 `present` ;
- F1 `absent` ;
- F1 `hypothèse` ;
- matrice de confusion ;
- taux d’erreurs graves de polarité.

## 14.4. Scoring

Métriques :

- ICC ;
- kappa pondéré ;
- corrélation ;
- erreur absolue moyenne ;
- erreur quadratique moyenne ;
- proportion à ±5 points ;
- proportion à ±10 points ;
- Bland–Altman ;
- sensibilité aux erreurs critiques ;
- spécificité ;
- taux de surévaluation des réponses fausses.

## 14.5. Reproductibilité

Pour une même réponse :

- répétition de 10 à 20 exécutions ;
- variance de la note ;
- variance des concepts ;
- taux de changement de verdict ;
- taux de changement de backend ;
- stabilité du feedback.

## 14.6. Robustesse

Tester :

- fautes d’orthographe ;
- abréviations ;
- style télégraphique ;
- phrases longues ;
- diagnostics multiples ;
- contradiction ;
- négation complexe ;
- hedging ;
- copier-coller ;
- réponse hors sujet ;
- injection ;
- répétition de mots-clés ;
- Unicode inhabituel ;
- absence de ponctuation ;
- mélange français/anglais.

---

# 15. Analyses d’ablation

Comparer sur le même corpus :

1. règles seules ;
2. LLM direct ;
3. BM25 seul ;
4. embeddings seuls ;
5. BM25 + embeddings ;
6. NER LLM sans ontologie ;
7. NER LLM + ontologie ;
8. encodeur + ontologie ;
9. système complet sans juge ;
10. système complet sans rattrapage lexical ;
11. système complet sans règles de négation ;
12. système complet sans relations ontologiques ;
13. système cloud ;
14. système local ;
15. système complet avec abstention ;
16. système complet sans abstention.

Objectif :

> identifier la contribution réelle de chaque brique et éviter d’attribuer abusivement la performance au seul caractère « neurosymbolique ».

---

# 16. Tests logiciels

## 16.1. Tests unitaires

- normalisation ;
- négation ;
- valeurs numériques ;
- synonymes ;
- relations ontologiques ;
- scoring exact ;
- scoring parent/enfant ;
- exclusions ;
- contradictions ;
- plafonds ;
- abstention.

## 16.2. Tests de régression

Corpus minimal figé avec :

- réponse ;
- concepts attendus ;
- note attendue ;
- erreurs attendues ;
- décision attendue.

Aucune modification du moteur ne doit pouvoir être fusionnée si elle modifie ces résultats sans justification.

## 16.3. Tests adversariaux

- injection ;
- réponse très longue ;
- spam de concepts ;
- contradictions volontaires ;
- réponse en boucle ;
- données invalides ;
- appels simultanés ;
- indisponibilité du modèle ;
- indisponibilité de la base ;
- timeout.

## 16.4. Intégration continue

La CI doit exécuter :

- lint ;
- type checking ;
- tests unitaires ;
- tests d’intégration ;
- validation du schéma ontologique ;
- audit des goldens ;
- tests de régression ;
- contrôle de secrets ;
- contrôle des dépendances.

---

# 17. Sécurité et déploiement

## 17.1. Avant diffusion multicentrique

- authentification ;
- rôles ;
- rate limiting ;
- CORS contrôlé ;
- protection CSRF ;
- secrets hors URL ;
- journal d’audit ;
- chiffrement ;
- sauvegardes ;
- monitoring ;
- politique de rétention ;
- information des utilisateurs ;
- gouvernance des accès.

## 17.2. Modes de déploiement

### Mode recherche centralisé

- serveur universitaire ;
- base centrale ;
- plusieurs facultés ;
- séparation logique ;
- version identique du moteur.

### Mode local autonome

- Docker ;
- modèle local ;
- base locale ;
- export du corpus pseudonymisé ;
- aucune dépendance externe obligatoire.

### Mode hybride

- scoring local ;
- feedback cloud optionnel ;
- aucun envoi d’identité ;
- fallback administrativement contrôlé ;
- journalisation du fournisseur utilisé.

---

# 18. Plan de publication

## Article 1 — Validation technologique

### Question

Un système hybride fondé sur une ontologie peut-il corriger de manière fiable des réponses libres en interprétation ECG ?

### Contenu

- architecture ;
- ontologie ;
- corpus ;
- annotation ;
- accord inter-experts ;
- performances ;
- ablations ;
- comparaison LLM direct ;
- comparaison cloud/local ;
- reproductibilité ;
- abstention ;
- analyse des erreurs.

### Cibles potentielles

- JMIR Medical Education ;
- Medical Education Online ;
- BMC Medical Education ;
- Journal of the American Medical Informatics Association ;
- JAMIA Open ;
- Artificial Intelligence in Medicine ;
- International Journal of Medical Informatics.

Le choix dépendra du niveau de validation technique et pédagogique atteint.

## Article 2 — Étude pédagogique

### Question

Le feedback automatique structuré améliore-t-il l’apprentissage de la lecture ECG ?

### Critères

- pré-test ;
- post-test ;
- rétention ;
- transfert ;
- confiance ;
- temps ;
- acceptabilité ;
- charge cognitive.

## Article 3 — Corpus et ontologie

Possible si le corpus et l’ontologie deviennent suffisamment importants :

- description du corpus ;
- schéma d’annotation ;
- ontologie ECG pédagogique ;
- benchmark public ou semi-ouvert ;
- tâches de NER, linking et scoring.

---

# 19. Critères de préparation de l’article technologique

L’article ne doit pas être soumis avant d’avoir :

- un corpus gelé ;
- un protocole écrit avant analyse ;
- au moins deux experts ;
- une adjudication ;
- des métriques cohérentes ;
- un jeu de test indépendant ;
- une analyse d’ablation ;
- une baseline LLM direct ;
- une baseline déterministe ;
- une analyse de reproductibilité ;
- une analyse d’erreurs ;
- une analyse d’abstention ;
- des chiffres traçables vers une version de code.

---

# 20. Feuille de route opérationnelle

## P0 — Bloquant

### Architecture

- [ ] supprimer le fallback silencieux ;
- [ ] introduire l’abstention ;
- [ ] séparer extraction, linking, scoring et feedback ;
- [ ] définir les contrats JSON ;
- [ ] versionner modèle, ontologie et scoring ;
- [ ] créer un identifiant par réponse et prédiction ;
- [ ] rendre le scoring totalement indépendant des appels réseau ;
- [ ] garantir le replay d’une réponse.

### Qualité des données

- [ ] corriger tous les conflits du golden ;
- [ ] auditer tous les cas sans validant ;
- [ ] auditer les mappings absents ;
- [ ] auditer les doublons ;
- [ ] figer une première version de l’ontologie ;
- [ ] créer un schéma de validation.

### Tests

- [ ] tests unitaires du scoring ;
- [ ] tests unitaires de négation ;
- [ ] corpus de régression ;
- [ ] CI obligatoire ;
- [ ] audit automatisé de l’ontologie ;
- [ ] audit automatisé des goldens.

### Collecte

- [ ] conserver toutes les réponses brutes ;
- [ ] conserver les versions du pipeline ;
- [ ] stocker les concepts détectés ;
- [ ] stocker les erreurs et abstentions ;
- [ ] documenter le dictionnaire de données ;
- [ ] préparer la migration PostgreSQL.

## P1 — Validation scientifique

- [ ] rédiger le manuel d’annotation ;
- [ ] sélectionner les experts ;
- [ ] annoter les réponses existantes ;
- [ ] calculer l’accord inter-experts ;
- [ ] créer le gold standard ;
- [ ] recalculer precision, recall et F1 ;
- [ ] évaluer l’entity linking ;
- [ ] évaluer la négation ;
- [ ] évaluer le scoring ;
- [ ] mesurer la reproductibilité ;
- [ ] créer le benchmark adversarial ;
- [ ] comparer au LLM direct ;
- [ ] comparer aux règles seules ;
- [ ] exécuter les ablations.

## P2 — Architecture locale

- [ ] embedding local ;
- [ ] encodeur clinique ;
- [ ] reranker local ;
- [ ] petit LLM local ;
- [ ] serveur compatible OpenAI ;
- [ ] benchmarks de latence ;
- [ ] benchmarks CPU/GPU ;
- [ ] comparaison cloud/local ;
- [ ] paquet Docker.

## P3 — Déploiement multicentrique

- [ ] authentification institutionnelle ;
- [ ] base multi-tenant ;
- [ ] gestion des facultés ;
- [ ] gouvernance de l’ontologie ;
- [ ] gestion des versions ;
- [ ] tableau de bord enseignant ;
- [ ] monitoring ;
- [ ] documentation de déploiement ;
- [ ] conformité RGPD ;
- [ ] pilote dans une deuxième faculté.

## P4 — Étude pédagogique

- [ ] protocole ;
- [ ] enregistrement ;
- [ ] critères de jugement ;
- [ ] randomisation ;
- [ ] calcul d’effectif ;
- [ ] collecte prospective ;
- [ ] analyse ;
- [ ] publication.

---

# 21. Plan des six prochaines semaines

## Semaine 1 — Stabilisation

- corriger les conflits golden restants ;
- créer les tests absents ;
- geler `ontology_v1.0.0` ;
- geler `scoring_v4.0.0` ;
- définir le schéma de prédiction.

## Semaine 2 — Découplage

- isoler `scoring_engine` ;
- isoler `feedback_engine` ;
- introduire `PipelineResult` ;
- supprimer le fallback silencieux ;
- créer les états d’abstention.

## Semaine 3 — Traçabilité

- versionner chaque sortie ;
- ajouter `response_id` et `prediction_id` ;
- journaliser les méthodes de résolution ;
- permettre le replay ;
- exporter un rapport par réponse.

## Semaine 4 — Collecte

- auditer les colonnes actuelles ;
- définir le modèle PostgreSQL ;
- écrire les migrations ;
- importer un échantillon historique ;
- vérifier la pseudonymisation.

## Semaine 5 — Annotation

- finaliser le manuel ;
- créer l’interface d’annotation ;
- sélectionner 30 à 50 réponses pilotes ;
- double annotation ;
- analyser les désaccords ;
- corriger le guide.

## Semaine 6 — Benchmark initial

- baseline règles ;
- baseline LLM direct ;
- pipeline actuel ;
- corpus pilote ;
- premier rapport de performance ;
- première matrice d’erreurs ;
- décision sur le modèle d’extraction suivant.

---

# 22. Premier sprint technique

## Sprint 1 — Objectif

Créer une architecture reproductible dans laquelle :

- la réponse brute est conservée ;
- le pipeline produit un objet structuré ;
- le score est calculé sans appel externe ;
- le backend ne change jamais silencieusement ;
- le système peut s’abstenir ;
- toute sortie est rejouable.

## Issues proposées

### Architecture

- [ ] `feat: define PipelineResult schema`
- [ ] `refactor: isolate deterministic scoring engine`
- [ ] `refactor: isolate feedback generation`
- [ ] `feat: add abstention state machine`
- [ ] `fix: remove silent GPT fallback`
- [ ] `feat: add pipeline and ontology version metadata`

### Tests

- [ ] `test: add scoring regression fixtures`
- [ ] `test: add negation edge cases`
- [ ] `test: add exclusion and contradiction cases`
- [ ] `ci: run ontology audit on every pull request`

### Collecte

- [ ] `feat: persist raw response independently from prediction`
- [ ] `feat: persist extracted concepts and confidence`
- [ ] `feat: persist technical errors and abstentions`
- [ ] `docs: add research data dictionary`

---

# 23. Definition of Done

Une brique n’est terminée que si :

- le contrat d’entrée est documenté ;
- le contrat de sortie est documenté ;
- les erreurs sont explicites ;
- les tests unitaires existent ;
- les cas limites sont couverts ;
- la version est enregistrée ;
- les sorties sont rejouables ;
- la documentation est à jour ;
- aucune donnée brute n’est écrasée ;
- la modification est analysée sur le corpus de régression.

Une release n’est publiable que si :

- tous les tests passent ;
- l’audit ontologique passe ;
- l’audit des goldens passe ;
- le benchmark de régression est disponible ;
- les changements de performance sont documentés ;
- les migrations sont testées ;
- le changelog est complet.

---

# 24. Indicateurs de progression

## Technique

- couverture des tests ;
- nombre de conflits ontologiques ;
- nombre de cas sans mapping ;
- taux d’abstention ;
- variance des scores ;
- latence ;
- coût par correction ;
- taux d’erreurs techniques.

## Scientifique

- nombre de réponses collectées ;
- nombre de réponses doublement annotées ;
- accord inter-experts ;
- F1 extraction ;
- exactitude linking ;
- ICC scoring ;
- sensibilité aux erreurs graves ;
- performance externe.

## Pédagogique

- progression ;
- rétention ;
- calibration de confiance ;
- temps ;
- taux de complétion ;
- acceptabilité ;
- recours aux aides.

---

# 25. Risques principaux

## Risque 1 — Construire trop tôt un modèle fine-tuné

Réponse :

- stabiliser d’abord les labels ;
- stabiliser l’ontologie ;
- constituer le gold standard ;
- comparer à des baselines simples.

## Risque 2 — Confondre performance du score et performance pédagogique

Réponse :

- séparer validation technologique et étude d’apprentissage.

## Risque 3 — Dépendre d’un fournisseur externe

Réponse :

- abstraction d’API ;
- composants locaux ;
- replay ;
- versions figées.

## Risque 4 — Collecter beaucoup de données inutilisables

Réponse :

- contrats de données ;
- dictionnaire ;
- pseudonymisation ;
- versions ;
- contrôle qualité ;
- annotations ciblées.

## Risque 5 — Suradapter le système aux 75 cas

Réponse :

- split par cas ;
- nouveaux ECG ;
- validation externe ;
- nouveaux enseignants ;
- nouveaux centres.

## Risque 6 — Produire une note très précise mais faussement objective

Réponse :

- sous-scores ;
- intervalle ou classe ;
- confiance ;
- abstention ;
- transparence ;
- concordance experte.

---

# 26. Décisions architecturales proposées

## Décision A

**Conserver le scoring déterministe.**

## Décision B

**Remplacer le fallback automatique par une abstention explicite.**

## Décision C

**Stocker séparément réponse, prédiction automatique et annotation experte.**

## Décision D

**Maintenir l’ontologie hors des poids du modèle.**

## Décision E

**Comparer un encodeur clinique, un petit LLM local, des règles et un LLM cloud.**

## Décision F

**Prioriser la validation de l’extraction avant le fine-tuning de bout en bout.**

## Décision G

**Poursuivre immédiatement la collecte, mais avec une architecture de données adaptée à la recherche.**

## Décision H

**Produire d’abord un article de validation technologique, puis un article pédagogique.**

---

# 27. Prochaine action immédiate

La prochaine étape du projet est de lancer un sprint de fiabilisation avec quatre livrables :

1. **un objet de sortie structuré et versionné** ;
2. **un scoring indépendant et entièrement testé** ;
3. **une abstention explicite en cas d’échec ou d’incertitude** ;
4. **une collecte séparant réponse brute, prédiction et annotation experte**.

Ces quatre éléments permettent ensuite de poursuivre la collecte sans perdre de données, de rejouer toutes les réponses avec les futures architectures et de préparer une validation scientifique solide.

---

# 28. Résumé exécutif

La trajectoire recommandée est la suivante :

```text
Fiabiliser l’architecture
        ↓
Poursuivre une collecte versionnée
        ↓
Construire le gold standard expert
        ↓
Comparer plusieurs architectures
        ↓
Valider extraction, linking et scoring
        ↓
Produire l’article technologique
        ↓
Déployer dans plusieurs facultés
        ↓
Tester l’impact pédagogique
```

Le projet doit désormais être conduit comme :

- un logiciel de recherche ;
- une infrastructure pédagogique ;
- un futur corpus clinique textuel ;
- un programme de validation scientifique.

La priorité n’est pas d’ajouter rapidement un nouveau modèle.

La priorité est de rendre chaque réponse, chaque concept, chaque score et chaque erreur :

> **traçable, rejouable, testable et publiable.**
