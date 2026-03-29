# 📋 Dossier d'Évaluation — Partenariat École d'Ingénieurs

## Contexte

Ce dossier est destiné à une école d'informatique dans le cadre d'un partenariat potentiel
sur le projet **Edu-ECG** (EPCASE). L'objectif est de fournir une vision claire et technique
du pipeline RAG Neurosymbolique de correction automatique d'ECG, pour :

1. **Valider la robustesse** du système actuel
2. **Identifier les limites** connues et les axes d'amélioration
3. **Proposer des sujets de développement** pour des étudiants ingénieurs

## Structure du dossier

```
dossier_ecole/
├── README.md                          ← Ce fichier
├── cas_annotes/                       ← 4 cas annotés avec trace pipeline complète
│   ├── cas_01_ecg_normal.json         ← Difficulté : NER rate le diagnostic explicite
│   ├── cas_02_baseline_parfait.json   ← Cas de référence : pipeline performant
│   ├── cas_03_erreur_ner.json         ← Erreur NER : synonyme manquant
│   └── cas_04_hierarchie.json         ← Scoring hiérarchique parent/enfant
├── docs/
│   ├── architecture_pipeline.md       ← Description technique du pipeline
│   ├── difficulte_ecg_normal.md       ← Le problème du diagnostic implicite
│   └── limites_connues.md             ← Inventaire des limites identifiées
└── schemas/
    └── format_annotation.json         ← Schéma JSON pour les annotateurs humains
```

## Les 4 cas annotés

| # | Cas | Étudiant | Score | Intérêt pédagogique |
|---|-----|----------|-------|---------------------|
| 1 | ECG normal (cas n°1) | ECG-2DZE | 80% | L'étudiant écrit *"cet ECG est NORMAL"* mais le NER (GPT-4o) n'extrait pas "ECG normal" — trouvé via hiérarchie (child_gen1). Score 80% au lieu de 100%. **Métriques** : 10 termes, 6 coupe-circuit, 4 juge_llm. |
| 2 | BAV complet (cas n°2) | ECG-84SV | 100% | Cas de référence parfait. "Bloc atrio-ventriculaire complet" → BAV_COMPLET (juge_llm, confiance=100). Top-1 cos=0.752, exact=False. **Métriques** : 3 termes, 2 coupe-circuit, 1 juge_llm. |
| 3 | Hyperkaliémie (cas n°5) | ECG-NDK6 | 40% | "BAV 2 M 2" → NONE (confiance=80, mais top-1 cos=0.697). Synonyme manquant. 1 validant trouvé sur 2. **Métriques** : 4 termes, 1 coupe-circuit, 3 juge_llm. |
| 4 | Flutter typique (cas n°8) | ECG-84SV | 100% | "Flutter commun antihoraire" → FLUTTER_ATRIAL_ANTIHORAIRE (coupe-circuit, cos=0.928, exact=True). Valide le parent via child_gen1. **Métriques** : 6 termes, 4 coupe-circuit, 2 juge_llm. |

## Comment utiliser ce dossier

1. Lire `docs/architecture_pipeline.md` pour comprendre le pipeline
2. Examiner les 4 cas dans `cas_annotes/` — chaque JSON contient la trace complète
3. Consulter `docs/difficulte_ecg_normal.md` pour le problème le plus intéressant
4. Voir `docs/limites_connues.md` pour les axes de travail proposés
5. Le schéma `schemas/format_annotation.json` définit le format d'annotation humaine

---

## 🔍 Limites identifiées du système de notation

Le système de notation repose sur un pipeline en 4 étapes (NER → Matching → Scoring → Feedback).
Les limites identifiées se regroupent en **4 catégories structurantes** :

### 1. Qualité du matching avec l'ontologie

Le pipeline utilise deux méthodes de matching : un **coupe-circuit déterministe** (match exact
sur les surface forms et synonymes) et un **juge LLM** (GPT-4) pour les termes non résolus.

**Problèmes constatés :**
- Le NER (GPT-4o) segmente le texte en entités cliniques unitaires. Quand le diagnostic est
  formulé en langage naturel (*"Je dirai que cet ECG est NORMAL"*), le LLM traite la phrase
  comme du texte narratif et ne reconstitue pas "ECG normal" comme entité extractible.
  Par contraste, les formulations courtes (`"ECG normal."`, `"→ ECG normal"`) sont correctement
  extraites via le coupe-circuit.
- Le juge LLM peut **halluciner un match incorrect** quand les candidats sémantiques sont proches
  (ex: "BAV 2 M 2" mappé sur BAV_2_POUR_1 au lieu de BAV_2_MOBITZ_2).
- Les abréviations ambiguës posent problème (ex: "HAG" = Hypertrophie Atriale Gauche
  ou Hémibloc Antérieur Gauche ?).

> 📄 Voir le cas annoté `cas_01_ecg_normal.json` et `cas_03_erreur_ner.json` pour des exemples.

### 2. Contenu de l'ontologie

L'ontologie OWL (292 concepts, 246 synonymes) ne couvre pas toutes les formulations
utilisées par les étudiants en conditions réelles.

**Problèmes constatés :**
- **Synonymes manquants** : "BAV 2 M 2", "flutter à conduction variable", "RS" (pour Rythme sinusal).
  Quand le coupe-circuit échoue, le juge LLM prend le relais mais peut se tromper.
- **Relations non exploitées** : 59 relations `requiresFinding` dans l'OWL (ex: BAV complet
  → requiert Dissociation AV) sont actuellement mergées avec les relations parent-enfant
  sans traitement différencié.

### 3. Gestion de l'implicite et des concepts compositionnels

C'est la limite la plus fondamentale. Certains concepts de l'ontologie ne sont pas des signes
ECG unitaires observables sur un tracé, mais des **conclusions diagnostiques** qui se déduisent
de la conjonction de plusieurs paramètres.

**Le cas emblématique : ECG normal**

"ECG normal" n'est pas un signe — c'est la **conclusion** qu'on tire quand *tous* les paramètres
sont normaux ensemble (rythme sinusal + fréquence normale + axe normal + PR normal + QRS fins
+ pas de trouble de repolarisation…). C'est un concept **composé de ~5 paramètres**.

Or le scoring hiérarchique actuel fonctionne ainsi : si le concept attendu (ECG_NORMAL) n'est
pas trouvé directement, le système cherche si un de ses **enfants ontologiques** est présent.
S'il trouve un seul enfant (ex: "Rythme sinusal"), il attribue 90% pour ECG normal.

**C'est excessif** : un ECG peut avoir un rythme sinusal et être profondément pathologique
(infarctus en cours, HVG massive, etc.). Attribuer "ECG normal" à 90% sur la base d'un seul
composant parmi 5 est une sur-attribution. En toute rigueur, il faudrait que l'ensemble
(ou une majorité significative) des composants normaux soient identifiés pour valider
ce diagnostic.

Ce problème est **structurel** : le scoring hiérarchique parent/enfant fonctionne correctement
pour les concepts unitaires (ex: "Flutter antihoraire" → "Flutter droit typique" est légitime,
car c'est une relation de spécialisation). Mais il est inadapté pour les concepts qui sont
des **conjonctions**. D'autres concepts "parapluie" dans l'ontologie pourraient présenter
le même biais.

| Formulation étudiant | Score | Mécanisme | Problème |
|---|---|---|---|
| `"ECG normal."` (isolé) | 100% | Match exact (coupe-circuit) | ✅ Aucun |
| `"→ ECG normal"` | 100% | Match exact (coupe-circuit) | ✅ Aucun |
| `"cet ECG est NORMAL"` (dans une phrase) | 90% | child_gen1 via Rythme sinusal | ⚠️ NER ne reconstitue pas le terme |
| Composants décrits sans conclusion | 80–90% | child_gen1 ou gen2 | ⚠️ 1 seul composant parmi ~5 suffit |
| `"normal"` seul | 0% | Aucun match | ❌ Trop vague |

> 📄 Voir `docs/difficulte_ecg_normal.md` pour l'analyse détaillée et les pistes de solution.

### 4. Métriques de confiance sur le matching — ✅ RÉSOLU (2026-03-29)

Cette limite a été identifiée puis **corrigée dans la même itération**. Lors du matching,
le pipeline calcule en interne des **scores de similarité riches** pour chaque candidat :

- **Score cosinus** (similarité sémantique, embeddings OpenAI `text-embedding-3-small`, 1536 dims)
- **Score BM25** (similarité lexicale, match de mots-clés)
- **Score RRF fusionné** (Reciprocal Rank Fusion des deux précédents)
- **Le top-5 des candidats** classés avec ces scores
- **Le flag `is_exact_match`** (le terme normalisé matche-t-il exactement une surface form ?)

**Avant correction** : le rapport final ne conservait que `ontology_id`, `method` et
`justification` (texte libre). Tous les scores numériques étaient jetés.

**Après correction** (4 fichiers modifiés) :

| Métrique | Calculée en interne | Conservée dans le rapport |
|---|---|---|
| Score cosinus par candidat | ✅ | ✅ `cosine_score` |
| Score BM25 par candidat | ✅ | ✅ `bm25_score` |
| Score RRF fusionné par candidat | ✅ | ✅ `rrf_score` |
| Top-5 candidats complets | ✅ | ✅ `top_k_candidats[]` |
| Flag exact match | ✅ | ✅ `is_exact_match` |
| Score de confiance du LLM (0-100) | ✅ **Nouveau** | ✅ `llm_confiance` |

**Fichiers modifiés :**
- `hybrid_search.py` — `search_top_k()` retourne `cosine_score` et `bm25_score` par candidat
- `neurosymbolic_judge.py` — ajout du champ `confiance: int` au modèle Pydantic, extraction
  du résumé top-k, retour de `top_k_candidats` et `llm_confiance` dans tous les chemins
- `candidate_report.py` — `ExtractedConcept` enrichi de `top_k_candidats: list` et `llm_confiance: int`
- `export_corrections_json.py` — sérialisation des nouvelles métriques dans les JSON

**Exemple réel** (ECG-84SV, cas n°2 — "Bloc atrio-ventriculaire complet") :
```
terme_brut: "Bloc atrio-ventriculaire complet"  →  BAV_COMPLET (juge_llm)
llm_confiance: 100
top_k_candidats:
  #1  BAV complet           rrf=0.0417  cos=0.752  bm25=8.13  exact=False
  #2  Dissociation AV       rrf=0.0397  cos=0.620  bm25=7.02  exact=False
  #3  Bloc AV               rrf=0.0392  cos=0.641  bm25=5.21  exact=False
```

> � Les 4 cas annotés dans `cas_annotes/` incluent désormais les métriques réelles.
> Voir la section `metriques_confiance` de chaque JSON.
>
> ⏳ **Reste à faire** : exploiter ces métriques pour du seuillage automatique,
> de la détection de matchs fragiles, et du dashboard d'auditabilité.

---

## Projet Edu-ECG

- **Repo** : github.com/EPCASE/edu-ecg (branche `RAGontologique`)
- **Stack** : Python, OpenAI API (embeddings + GPT-4), ontologie OWL (292 concepts)
- **Déploiement** : Scalingo (ecg-collector.osc-fr1.scalingo.io)
- **Référentiel médical** : Chapitre 15, Item 231 SFC (CNEC 2e édition)
