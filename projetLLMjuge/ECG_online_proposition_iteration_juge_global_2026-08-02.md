# ECG Online — Proposition d’itération autour d’un juge sémantique global

**Version :** 0.1  
**Date :** 2 août 2026  
**Branche de développement :** `main`  
**Branche pré-alpha historique :** `ECG-09/RAG`, à maintenir gelée jusqu’à la mise à jour validée du moteur.

---

## 1. Question de départ

Le pipeline actuel utilise déjà un modèle de langage pour lire l’ensemble de la réponse, mais fragmente ensuite celle-ci en entités résolues séparément. Cette décomposition fonctionne bien pour les mentions explicites et les correspondances lexicales simples. Elle risque toutefois de perdre les informations qui n’existent qu’au niveau du discours global :

- diagnostic exprimé implicitement par une combinaison de signes ;
- contradiction entre deux propositions ;
- négation puis affirmation du même concept ;
- hypothèse discutée puis rejetée ;
- hiérarchisation d’un diagnostic différentiel ;
- incompatibilité entre une mesure et son interprétation ;
- affirmation grave non soutenue ;
- cohérence générale de la réponse.

L’hypothèse de travail est qu’un **jugement sémantique global**, appliqué une seule fois à toute la réponse, pourrait mieux traiter ces phénomènes que la succession actuelle de résolutions locales.

---

## 2. Position proposée

La proposition n’est pas de confier l’ensemble de la correction au modèle de langage.

La cible est une séparation en trois responsabilités :

1. **Le LLM interprète globalement la réponse.**
2. **L’ontologie contraint, normalise et valide les concepts.**
3. **Le code déterministe calcule le score selon le contrat pédagogique du cas.**

Formule cible :

> Une méthode principale de résolution sémantique : le juge LLM global.  
> Une source de vérité conceptuelle : l’ontologie ECG Online.  
> Une méthode de calcul de la note : le scorer déterministe.

Les recherches BM25, embeddings, synonymes et exact matches peuvent être conservés comme **outils de récupération de candidats et de contrôle**, mais ne doivent plus fragmenter le raisonnement avant le jugement global.

---

## 3. Architecture cible

```text
Réponse complète de l’étudiant
        │
        ├── Contrat du cas
        │     ├── validants
        │     ├── descripteurs
        │     ├── exclusions
        │     └── politique de crédit implicite
        │
        ├── Catalogue ontologique compact
        │     ├── concepts candidats
        │     ├── parents/enfants
        │     ├── requires/supports
        │     └── incompatibilités
        │
        ▼
Juge sémantique global LLM
        │
        ▼
Graphe de propositions structuré
        │
        ├── mentions explicites
        ├── conclusions implicites
        ├── polarité et certitude
        ├── preuves textuelles
        ├── contradictions
        ├── mesures
        └── éléments non résolus
        │
        ▼
Validation déterministe
        │
        ├── IDs autorisés
        ├── spans réellement présents
        ├── cohérence numérique
        ├── contraintes ontologiques
        └── détection des sorties invalides
        │
        ▼
Scoring déterministe
        │
        ▼
Feedback pédagogique
```

---

## 4. Sortie minimale du juge global

Le juge ne doit pas directement rendre une note. Il doit produire une représentation structurée, validée par Pydantic ou JSON Schema.

```json
{
  "claims": [
    {
      "claim_id": "c1",
      "concept_id": "PR_COURT",
      "polarity": "present",
      "certainty": "asserted",
      "expression_mode": "explicit",
      "evidence_spans": ["PR à 100 ms"]
    },
    {
      "claim_id": "c2",
      "concept_id": "ONDE_DELTA",
      "polarity": "present",
      "certainty": "asserted",
      "expression_mode": "explicit",
      "evidence_spans": ["présence d'une onde delta"]
    },
    {
      "claim_id": "c3",
      "concept_id": "PREEXCITATION_VENTRICULAIRE",
      "polarity": "present",
      "certainty": "asserted",
      "expression_mode": "implicit_complete",
      "inferred_from": ["c1", "c2"]
    }
  ],
  "measurements": [
    {
      "name": "PR",
      "value": 100,
      "unit": "ms",
      "interpreted_as": "PR_COURT",
      "coherent": true
    }
  ],
  "contradictions": [],
  "unsupported_claims": [],
  "unresolved_mentions": []
}
```

### Champs obligatoires par proposition

- `concept_id`
- `polarity` : `present`, `absent`, `discussed`, `rejected`
- `certainty` : `asserted`, `probable`, `possible`, `uncertain`
- `expression_mode` :
  - `explicit`
  - `paraphrased`
  - `implicit_complete`
  - `implicit_partial`
  - `unsupported`
- `evidence_spans`
- `inferred_from` lorsqu’une conclusion est implicite

### Règle de preuve

Toute proposition créditée doit être reliée à un segment réellement présent dans la réponse. Une conclusion implicite doit préciser les propositions explicites qui la soutiennent.

---

## 5. Politique de crédit de l’implicite

La compréhension d’un implicite et le crédit pédagogique sont deux décisions différentes.

Chaque concept validant doit recevoir une politique explicite :

### `explicit_required`

Le diagnostic doit être nommé. Une description correcte donne seulement un crédit descriptif.

### `implicit_full_if_complete`

Une combinaison complète et non ambiguë de critères permet le crédit maximal, même sans libellé diagnostique.

### `implicit_partial`

La description des critères donne un crédit progressif, plafonné en l’absence de diagnostic explicite.

### `no_inference`

Le système ne doit pas déduire ce concept à partir d’autres signes pour la notation.

Cette politique doit être stockée dans le contrat golden du cas et non improvisée par le LLM.

---

## 6. Systèmes à comparer

### A — Pipeline actuel

```text
NER global
→ fragmentation en entités
→ recherche hybride
→ exact match ou juge local
→ règles et backstops
→ scoring V3
```

### B — Grader génératif direct

```text
réponse + référence + barème
→ LLM
→ score et feedback
```

Ce système existe déjà comme backend de repli. Il constitue une baseline utile, mais mélange compréhension, adjudication et notation.

### C — Juge global structuré, cible proposée

```text
réponse complète + contrat + ontologie compacte
→ graphe sémantique global
→ validation déterministe
→ scoring déterministe
```

---

## 7. Corpus expérimental

Le benchmark doit associer :

- le corpus historique existant ;
- le nouveau corpus synthétique ciblé de 100 réponses ;
- ultérieurement, des réponses étudiantes réelles sélectionnées pour leur difficulté.

Le corpus synthétique comporte dix strates équilibrées :

1. diagnostic explicitement nommé ;
2. diagnostic seulement décrit ;
3. description partielle ;
4. diagnostic correct avec un élément faux ;
5. diagnostics contradictoires ;
6. négation puis affirmation du même concept ;
7. diagnostic grave non soutenu ;
8. formulation hésitante ou différentielle ;
9. mesure incompatible avec son interprétation ;
10. réponse correcte mais lexicalement éloignée du gold.

### Double annotation recommandée

Deux cardiologues annotent indépendamment :

- ce qui est effectivement exprimé ;
- la polarité ;
- le degré de certitude ;
- les relations argumentatives ;
- les contradictions ;
- la correction clinique par rapport au cas ;
- le niveau de crédit pédagogique.

Les désaccords sont adjudiqués avant de verrouiller le gold.

---

## 8. Critères de jugement

### 8.1. Extraction explicite

- précision, rappel et F1 conceptuels ;
- exactitude de la polarité ;
- exactitude du degré de certitude ;
- fidélité des `evidence_spans`.

### 8.2. Raisonnement global

- détection des diagnostics implicites complets ;
- distinction implicite complet / partiel ;
- détection des contradictions ;
- détection des conflits mesure–interprétation ;
- détection des diagnostics graves non soutenus ;
- conservation correcte des diagnostics différentiels hiérarchisés.

### 8.3. Notation

- erreur absolue moyenne par rapport à la note experte ;
- corrélation et accord avec les cardiologues ;
- sensibilité aux erreurs dangereuses ;
- taux de surcrédit des implicites incomplets ;
- taux de sous-crédit des paraphrases correctes.

### 8.4. Robustesse technique

- stabilité sur plusieurs exécutions ;
- taux de sortie JSON invalide ;
- taux d’abstention ;
- latence ;
- coût ;
- dépendance au modèle et à sa version.

---

## 9. Seuils de décision provisoires

Ces seuils sont des objectifs de développement, pas des résultats acquis.

Le backend global ne devrait remplacer le moteur actuel que s’il remplit simultanément les conditions suivantes :

- absence de baisse cliniquement significative sur les mentions explicites simples ;
- précision élevée sur les diagnostics implicites, afin d’éviter l’invention de raisonnements ;
- détection très sensible des contradictions et erreurs critiques ;
- meilleure concordance avec la notation experte sur le corpus ciblé ;
- stabilité acceptable entre exécutions ;
- traçabilité complète de chaque proposition et de chaque version du système.

Une amélioration moyenne du score ne suffit pas si elle augmente les faux diagnostics graves.

---

## 10. Plan d’implémentation

### Phase 0 — Figer la baseline

- taguer la version actuelle de `main` ;
- enregistrer commit, ontologie, prompts, modèles et seuils ;
- rejouer le corpus historique ;
- conserver toutes les sorties brutes.

### Phase 1 — Verrouiller le corpus ciblé

- relire les 100 réponses synthétiques ;
- réaliser la double annotation ;
- adjudication ;
- fixer un schéma machine-readable versionné.

### Phase 2 — Prototype du juge global

Créer :

```text
rag_pipeline/global_semantic_judge.py
rag_pipeline/global_semantic_schema.py
rag_pipeline/global_semantic_validation.py
```

Le premier prototype doit :

- recevoir toute la réponse ;
- recevoir uniquement les concepts pertinents au cas et leurs voisins ontologiques ;
- produire des propositions avec preuves ;
- détecter contradictions, incertitudes et mesures ;
- ne produire aucune note.

### Phase 3 — Adaptateur vers le scorer

Créer une conversion :

```text
GlobalSemanticReport
→ found_ids / absent_ids / hypotheses
→ scoring déterministe
```

Les conclusions implicites doivent être transmises avec leur mode d’expression afin que la politique de crédit puisse les traiter différemment.

### Phase 4 — Shadow mode

Ajouter un backend expérimental :

```text
ECG_GRADER_BACKEND=global_llm_shadow
```

Pour chaque réponse :

- le pipeline actuel rend la correction visible ;
- le juge global travaille en parallèle ;
- les deux sorties sont journalisées ;
- aucune décision pédagogique n’est modifiée.

### Phase 5 — Audit comparatif

Produire automatiquement :

- matrice des désaccords ;
- différences de concepts ;
- contradictions détectées par un seul système ;
- écarts de note ;
- erreurs critiques ;
- cas de surinférence ;
- coût et latence.

### Phase 6 — Décision

Trois issues possibles :

1. **remplacement** de la couche de résolution par le juge global ;
2. **hybride sélectif**, le juge global étant activé seulement sur les réponses complexes ;
3. **second lecteur**, utilisé pour détecter contradictions et implicites sans remplacer l’extraction actuelle.

---

## 11. Stratégie de contexte ontologique

Envoyer les 345 concepts complets à chaque requête n’est probablement pas nécessaire.

Proposition :

1. extraction légère de mentions ou récupération lexicale sans décision ;
2. récupération des meilleurs concepts candidats ;
3. ajout de leurs parents, enfants, `requires`, `supports` et `excludes` ;
4. ajout systématique des validants et exclusions du cas ;
5. jugement global sur ce sous-graphe compact.

La récupération ne tranche pas le sens. Elle construit le dossier documentaire soumis au juge.

---

## 12. Garde-fous

- structured output strict ;
- liste fermée d’IDs autorisés ;
- validation des preuves textuelles ;
- refus de créditer un concept sans preuve ou chaîne d’inférence ;
- canal numérique déterministe parallèle ;
- journalisation des contradictions internes ;
- cache versionné par hash du texte, modèle, prompt, ontologie et contrat du cas ;
- abstention explicite lorsqu’aucune résolution n’est suffisamment soutenue ;
- tests de non-régression sur les exact matches simples ;
- seuils de sécurité spécifiques aux diagnostics urgents.

---

## 13. Questions scientifiques et produit encore ouvertes

1. Quel niveau d’implicite doit être crédité pour chaque diagnostic ?
2. Le juge global doit-il recevoir l’interprétation complète de référence ou seulement le contrat ontologique ?
3. Faut-il un seul appel global ou deux lectures indépendantes avec arbitrage ?
4. Le diagnostic différentiel doit-il influencer la note ou seulement le feedback ?
5. Comment pondérer une réponse correcte comportant une affirmation fausse secondaire ?
6. À partir de quel niveau de contradiction faut-il plafonner la note ?
7. Un modèle local peut-il atteindre une performance suffisante sur cette tâche structurée ?
8. Le gain du juge global porte-t-il sur l’extraction, le matching, la cohérence ou surtout le feedback ?
9. L’architecture globale améliore-t-elle réellement la concordance pédagogique, au-delà du F1 conceptuel ?

---

## 14. Premier livrable technique recommandé

Le premier développement sur `main` devrait rester volontairement limité :

- un schéma `GlobalSemanticReport` ;
- un appel LLM unique ;
- dix à vingt concepts candidats maximum par cas, complétés par leurs relations ;
- aucune modification du scorer ;
- aucune modification de l’interface ;
- exécution sur les 100 réponses ciblées ;
- rapport comparatif avec le pipeline actuel.

Cette étape permettra de tester l’hypothèse centrale — la valeur de la compréhension globale — sans engager prématurément une réécriture complète du moteur.

---

## 15. Fichiers de travail associés

- `ECG_online_corpus_cible_100_reponses_2026-08-02.md`
- `ECG_online_corpus_cible_100_reponses_2026-08-02.jsonl`

Sources internes à relire lors de l’implémentation :

- `app/neuro_grader.py`
- `app/grader.py`
- `rag_pipeline/ner_extractor.py`
- `rag_pipeline/neurosymbolic_judge.py`
- `rag_pipeline/candidate_report.py`
- `rag_pipeline/scoring_v3.py`
- `data/cases_golden.json`
- `data/scoring_config.json`
