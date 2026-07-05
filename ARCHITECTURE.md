# 🏗️ DOCUMENTATION — Edu-ECG : Pipeline RAG Neurosymbolique + App de correction ECG

> **Projet** : Edu-ECG
> **Repo** : [EPCASE/edu-ecg](https://github.com/EPCASE/edu-ecg) — Branche `feat/align-canonical-and-onto-fixes`
> **Date** : Juillet 2026
> **Version** : V3 (Scoring V3, NER V2, Feedback V2) + App en ligne `ecg-online` (GPT-4o)
>
> 📌 **Document unique et centralisé.** Il fusionne l'ancienne `ARCHITECTURE.md`,
> l'`AUDIT.md`, la `REANNOTATION_WEBPROTEGE.md` et le *Rapport de relecture —
> Optimisation de l'ontologie*. C'est la référence à jour du projet.

---

## Table des matières

**Partie A — Architecture du pipeline**
1. [Objectif du projet](#1-objectif-du-projet)
2. [Positionnement scientifique et pédagogique](#2-positionnement-scientifique-et-pédagogique)
3. [Analyse de l'ontologie ECG](#3-analyse-de-lontologie-ecg)
4. [Architecture technique — Les 6 briques](#4-architecture-technique--les-6-briques)
5. [Flux de données complet](#5-flux-de-données-complet)
6. [Stratégie d'interaction Ontologie ↔ LLMs](#6-stratégie-dinteraction-ontologie--llms)
7. [Stack technique](#7-stack-technique)
8. [Structure du projet](#8-structure-du-projet)
9. [Forces](#9-forces)
10. [Faiblesses et axes d'amélioration](#10-faiblesses-et-axes-damélioration)
11. [Métriques actuelles](#11-métriques-actuelles)

**Partie B — Application en ligne `ecg-online`**
12. [App autonome de correction ouverte (GPT-4o)](#12-app-autonome-de-correction-ouverte-gpt-4o)

**Partie C — Audit de robustesse**
13. [Audit — robustesse des résultats](#13-audit--robustesse-des-résultats)

**Partie D — Ontologie : réannotation & OWL**
14. [Réannotation WebProtégé & patch OWL](#14-réannotation-webprotégé--patch-owl)
15. [Rapport de relecture — synthèse et décisions](#15-rapport-de-relecture--synthèse-et-décisions)

---

## 1. Objectif du projet

### 1.1 Problème adressé

En médecine, l'**interprétation d'un ECG (électrocardiogramme)** est une compétence fondamentale évaluée aux Épreuves Dématérialisées Nationales (EDN, ex-ECN). Aujourd'hui, l'évaluation de cette compétence repose sur des QCM simplifiés ou des corrections manuelles chronophages par des cardiologues. Aucune solution ne permet :

- d'**évaluer automatiquement un texte libre** d'interprétation ECG rédigé par un étudiant,
- de **comparer ce texte à une correction experte** structurée,
- de **produire un feedback pédagogique individualisé** ancré dans le cours officiel.

### 1.2 Solution proposée

**Edu-ECG** est un pipeline de **Retrieval-Augmented Generation (RAG) neurosymbolique** qui transforme automatiquement le **texte libre d'un étudiant** en une **note structurée sur 100% avec un feedback pédagogique personnalisé**, en 6 briques séquentielles.

Le terme **neurosymbolique** traduit la combinaison de :
- **Raisonnement symbolique** : ontologie OWL hiérarchique avec 345 concepts, relations sémantiques (requires, excludes, supports, has_qualifiers) et règles d'inférence déterministes.
- **Inférence neuronale** : GPT-4o pour l'extraction NER, GPT-4o-mini pour le jugement de correspondance et le feedback pédagogique, text-embedding-3-small pour la recherche vectorielle.

### 1.3 Cas d'usage concret

```
Entrée :  "rythme sinusal, 70 bpm, BBD complet, pas de trouble de repolarisation"
            (texte libre de l'étudiant)

Sortie :  Score : 78/100
          ✅ Rythme sinusal — trouvé (exact)
          ✅ BBD complet — trouvé (exact)
          ⚠️ Bloc de branche droit — déduit (enfant trouvé = 1.0)
          ❌ Hypertrophie ventriculaire droite — manqué
          📝 Feedback pédagogique (150-300 mots, ancré cours SFC)
```

---

## 2. Positionnement scientifique et pédagogique

### 2.1 Contexte académique

Le projet s'inscrit dans le cadre d'un **mémoire de Master 2** en cardiologie, supervisé par un cardiologue expert. Il combine des enjeux de :

- **Pédagogie médicale** : évaluation formative des étudiants en médecine sur l'interprétation ECG.
- **Intelligence artificielle médicale** : application de RAG et LLMs au domaine cardiologique structuré.
- **Ingénierie ontologique** : modélisation formelle des concepts ECG dans un formalisme OWL.

### 2.2 Positionnement par rapport à l'état de l'art

| Approche | Exemples | Limites | Notre différence |
|----------|----------|---------|-----------------|
| **QCM automatisé** | Moodle, SIDES | Évalue la reconnaissance, pas la production textuelle | Nous évaluons du **texte libre** |
| **Correction NLP brute** | Regex / bag-of-words | Pas de compréhension sémantique, fragile aux synonymes | Notre pipeline tolère fautes, synonymes, abréviations |
| **LLM direct** (GPT évalue un texte) | ChatGPT en mode "corrige cet ECG" | Hallucinations, non-reproductibilité, pas de traçabilité du score | Notre scoring est **déterministe** et symbolique |
| **RAG classique** (retrieval + generation) | LangChain + base documentaire | Pas de raisonnement ontologique, pas de hiérarchie de concepts | Notre RAG est **neurosymbolique** avec ontologie OWL |
| **Ontologie ECG seule** (matching symbolique pur) | SNOMED CT + règles | Pas de tolérance aux fautes, pas de gestion du langage naturel | Nos embeddings + BM25 gèrent le fuzzy matching |

### 2.3 Innovations clés

1. **Coupe-circuit symbolique** : ~42% des résolutions se font **sans appel LLM** (matching exact normalisé → déterministe, gratuit, instantané).
2. **Scoring V3 ontologique** : le score exploite les **relations sémantiques** (requires, supports, excludes, parent/enfant) plutôt qu'un simple match binaire.
3. **Séparation NER / Jugement** : le NER extrait brutalement (aucune normalisation), la normalisation est déléguée à la recherche hybride + au juge — ce qui découple l'extraction de l'ontologie.
4. **Feedback ancré dans le cours** : le feedback cite les extraits du cours SFC (Item 231 EDN), classés par rang de priorité (A/B/C).
5. **Gestion explicite de la négation** : double filet (prompt NER + regex post-processing) pour capturer "pas de trouble de repolarisation" → `absent(TROUBLE_DE_REPOLARISATION)`.

### 2.4 Référentiel pédagogique

Le feedback s'appuie sur la **Knowledge Base EDN** intégrée au pipeline :

| Métrique | Valeur |
|----------|--------|
| Entrées EDN | **33** sections du cours SFC Item 231 |
| Rangs couverts | **23 rang A**, 9 rang B, 1 rang C |
| Concepts ontologiques mappés | **85** concept_ids liés à une entrée de cours |
| Source | Chapitre 15, SFC — Référentiel CNEC 2e édition |

---

## 3. Analyse de l'ontologie ECG

### 3.1 Vue d'ensemble

L'ontologie ECG est modélisée en **OWL (Web Ontology Language)** via WebProtégé, puis convertie en JSON V2 pour le pipeline.

| Métrique | Valeur |
|----------|--------|
| **Concepts** | **345** |
| **Synonymes** | **318** surface forms alternatives |
| **Documents indexés** (RAG) | **658** (345 canoniques + 313 synonymes) |
| **Profondeur max** | **8 niveaux** (arbre hiérarchique) |
| **4 racines** | `CONCEPTS_ECG`, `DESCRIPTION_ECG`, `PATHOLOGIE`, `TOPOGRAPHIE` |
| **Concepts cachés** | 55 (hide=1, non visibles dans les rapports) |

### 3.2 Typologie des concepts

| Type | Nb | Rôle |
|------|----|------|
| **finding** | 146 | Signe ECG observé (ex: QRS large, tachycardie) |
| **qualifier** | 106 | Modificateur d'un concept (ex: complet, incomplet, rapide) |
| **pattern** | 53 | Diagnostic composite = requires + qualifiers (ex: ECG normal, BBD complet) |
| **topography** | 40 | Localisation anatomique (ex: antéro-septal, latéral) |

### 3.3 Catégories cliniques (pondération)

```
                    ┌─────────────────────────────┐
                    │   DIAGNOSTIC_URGENT (15)     │  poids 5
                    │   BAV complet, TV, Asystolie │
                    ├─────────────────────────────┤
                    │   DIAGNOSTIC_MAJEUR (88)     │  poids 4
                    │   BBD complet, FA, Flutter   │
                    ├─────────────────────────────┤
                    │   DIAGNOSTIC_MOYEN (49)      │  poids 3
                    │   BBD, ESV, artefacte        │
                    ├─────────────────────────────┤
                    │   DESCRIPTION_ECG (130)      │  poids 2
                    │   QRS large, tachycardie     │
                    ├─────────────────────────────┤
                    │   QUALIFICATEUR (23)         │  poids 2
                    │   complet, incomplet, lent   │
                    ├─────────────────────────────┤
                    │   TOPOGRAPHIE (40)           │  poids 2
                    │   antérieur, latéral, apex   │
                    └─────────────────────────────┘
```

### 3.4 Relations sémantiques

| Relation | Nb d'occurrences | Sémantique | Exemple |
|----------|-----------------|------------|---------|
| **parents** | 345 (100%) | Hiérarchie is-a | `BBD_COMPLET → BLOC_DE_BRANCHE_DROIT` |
| **has_qualifiers** | 94 | Ce pattern est qualifié par… | `ECG_NORMAL.has_qualifiers = [RYTHME_SINUSAL, QRS_FINS, …]` |
| **requires** | 68 | Ce pattern nécessite ces findings | `BBD_COMPLET.requires = [QRS_LARGE, ASPECT_DE_RETARD_DROIT]` |
| **excludes** | 49 | Incompatible avec… | `ABSENCE_D_ISCHEMIE.excludes = [ISCHEMIE_SOUS_ENDOCARDIQUE]` |
| **supports** | 47 | Élément supportant (mais pas obligatoire) | `FA.supports = [ABSENCE_D_ONDE_P, TREMULATION]` |
| **synonymes** | 318 | Formes de surface alternatives | `FIBRILLATION_ATRIALE.synonymes = ["FA", "ACFA", "Fibrillation auriculaire"]` |

### 3.5 Distribution par profondeur dans l'arbre

```
Depth 0  ████                                   4 concepts  (racines)
Depth 1  ████████████████████                   36 concepts
Depth 2  ████████████████████████████████████   99 concepts  ← pic
Depth 3  ████████████████████████████████       92 concepts
Depth 4  ██████████████████                     52 concepts
Depth 5  █████████████                          38 concepts
Depth 6  █████                                  14 concepts
Depth 7  ███                                     8 concepts
Depth 8  █                                       2 concepts
```

### 3.6 Comparaison avec les standards existants

#### SNOMED CT (Systematized Nomenclature of Medicine)

| Critère | SNOMED CT | Ontologie Edu-ECG |
|---------|-----------|-------------------|
| **Couverture** | ~350 000 concepts (toute la médecine) | **345 concepts** (ECG uniquement) |
| **Granularité ECG** | ~500 concepts ECG, très hétérogènes | 345 concepts ECG structurés hiérarchiquement |
| **Relations** | is-a, part-of, finding-site, etc. (génériques) | **requires, supports, excludes, has_qualifiers** (spécifiques ECG) |
| **Scoring** | Non prévu (terminologie, pas évaluation) | **Natif** : poids 2-5 par catégorie clinique |
| **Synonymes français** | Variable (traduction INSERM) | **318 synonymes** curatés manuellement pour le français médical |
| **Langue** | Anglais natif, traductions variables | **Français natif** + labels anglais |

**Verdict** : SNOMED CT est un standard de terminologie, pas un outil d'évaluation. Notre ontologie est **spécialisée, pondérée, et orientée scoring** — ce que SNOMED ne fait pas.

#### HL7 aECG / SCP-ECG

Ces standards (HL7 annotated ECG, Standard Communication Protocol for ECG) sont des **formats d'échange de signaux ECG**, pas des ontologies de concepts. Ils ne couvrent pas l'interprétation textuelle.

#### Ontologie ECG de PhysioNet

PhysioNet propose des annotations ECG basiques (MIT-BIH, PTB-XL) mais sans hiérarchie sémantique ni pondération clinique. Leur périmètre est le **signal**, pas le **texte**.

**Conclusion** : À notre connaissance, il n'existe pas d'**ontologie ECG francophone orientée évaluation pédagogique** avec relations sémantiques (requires/excludes/supports) et scoring intégré. L'ontologie Edu-ECG comble ce vide.

---

## 4. Architecture technique — Les 6 briques

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  BRIQUE 0    │    │  BRIQUE 2    │    │  BRIQUE 3    │    │  BRIQUE 4    │    │  BRIQUE 5    │    │  BRIQUE 6    │
│  Ontologie   │    │  NER         │    │  Recherche   │    │  Juge        │    │  Scoring     │    │  Rapport +   │
│  Index       │───▶│  Extraction  │───▶│  Hybride     │───▶│  Neuro-      │───▶│  V3          │───▶│  Feedback    │
│              │    │              │    │              │    │  symbolique  │    │              │    │              │
│ OWL→Vecteurs │    │ GPT-4o       │    │ Dense+BM25   │    │ Coupe-circuit│    │ Ontologique  │    │ GPT-4o-mini  │
│ + BM25       │    │ Structured   │    │ + RRF        │    │ + GPT-4o-mini│    │ Hiérarchique │    │ + Cours SFC  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### 🧱 Brique 0 — Socle Ontologique & Index Vectoriel

**Fichier** : `ontology_index.py` (619 lignes)  
**Exécution** : one-shot (régénéré quand l'ontologie OWL change)  
**Entrée** : `ontology_v2.json` (345 concepts)  
**Sortie** :
- `vecteurs_ontologie.npy` — matrice **658 × 1536** (float32, ~4 Mo)
- `metadata_ontologie.json` — registre index ↔ document
- `bm25_corpus.json` — corpus tokenisé pour BM25

**Processus** :
1. Charger `ontology_v2.json` (345 concepts, 318 synonymes)
2. Générer 658 documents (1 canonique + N synonymes par concept)
3. Normaliser chaque surface_form (lowercase, strip accents, ponctuation → espaces)
4. Encoder les 658 documents via `text-embedding-3-small` (1536 dims)
5. Construire l'index BM25 sur les tokens normalisés
6. Sauvegarder en local

**Coût** : ~$0.01 (658 embeddings × ~10 tokens chacun)

---

### 🧱 Brique 2 — Extraction NER (V2)

**Fichier** : `ner_extractor.py` (255 lignes)  
**Modèle** : `gpt-4o-2024-08-06` avec **Structured Outputs** (schéma Pydantic garanti)  
**Entrée** : Texte libre de l'étudiant  
**Sortie** : Liste de `ClinicalEntity(terme_brut, statut, contexte_phrase)`

**7 règles du prompt système** :

| # | Règle | Objectif |
|---|-------|----------|
| 1 | **Extraction pure** | Zéro normalisation — fautes incluses |
| 2 | **Périmètre ECG large** | Morphologie + rythme + diagnostics + diagnostics étiologiques + stimulation |
| 3 | **Gestion de la négation** | "pas de X" → `terme_brut="X", statut="absent"` |
| 4 | **Méthode LEGO** | Adjectifs et modificateurs → entités séparées |
| 5 | **Valeurs numériques** | FC=70 → `"Fréquence cardiaque à 70 bpm"` |
| 6 | **Expansion des abréviations** *(V2)* | RS→Rythme sinusal, BBD→Bloc de branche droit, BAV 1→Bloc atrioventriculaire de type 1 |
| 7 | **Reformulation morphologique** *(V2)* | "onde R rabotée"→"Rabotage de l'onde R" |

**Filet de sécurité post-NER** : regex Python `_fix_negation()` dans `candidate_report.py` pour détecter les négations ratées par le LLM.

**Coût** : ~$0.003/cas (texte étudiant ~100 tokens)

---

### 🧱 Brique 3 — Recherche Hybride

**Fichier** : `hybrid_search.py` (454 lignes)  
**Modèle** : `text-embedding-3-small` (pour vectoriser la requête)  
**Entrée** : Un terme NER brut (ex: `"tachi supra"`)  
**Sortie** : Top-K candidats avec `ontology_id`, `score`, `is_exact_match`

**Deux moteurs combinés** :

```
                    Terme brut
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
      ┌──────────┐          ┌──────────┐
      │  Dense   │          │  BM25    │
      │ Cosinus  │          │ Sparse   │
      │ 1536-dim │          │ Tokens   │
      └────┬─────┘          └────┬─────┘
           │    Top-K dense      │    Top-K sparse
           └─────────┬───────────┘
                     ▼
              ┌──────────────┐
              │  RRF Fusion  │
              │  + boost BM25│
              │  acronymes   │
              └──────┬───────┘
                     ▼
              Top-K candidats
              + is_exact_match
```

**Flexion** : un helper `_deflect()` gère les variantes singulier/pluriel et masculin/féminin pour le test d'exact match (ex: "qrs larges" ↔ "qrs large").

**Coût** : ~$0.001/terme (1 embedding de requête)

---

### 🧱 Brique 4 — Juge Neurosymbolique

**Fichier** : `neurosymbolic_judge.py` (472 lignes)  
**Modèle** : `gpt-4o-mini` (fallback si coupe-circuit échoue)  
**Entrée** : Terme brut + contexte + Top-K candidats  
**Sortie** : `ontology_id` final ou `"NONE"`

**Pipeline en 2 étapes** :

```
         Terme brut + Top-K candidats
                     │
                     ▼
         ┌───────────────────────┐
         │  Étape 1 : Coupe-    │
         │  Circuit (exact match)│
         │  ~42% des cas        │──── ontology_id (déterministe)
         │  0 token LLM         │
         └───────────┬───────────┘
                     │ (pas de match exact)
                     ▼
         ┌───────────────────────┐
         │  Garde-fou spécificité│
         │  Si match exact       │
         │  = descripteur (p=1)  │──── annule le coupe-circuit
         │  ET concept plus      │     si concept spécifique
         │  spécifique dans Top-K│     dans les candidats
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Étape 2 : Juge LLM  │
         │  QCM (GPT-4o-mini)   │
         │  ~58% des cas        │──── ontology_id ou "NONE"
         │  Structured Outputs   │
         └───────────────────────┘
```

**5 règles du juge** :
1. Analyser terme + contexte
2. Choisir UNIQUEMENT parmi les options fournies
3. Correspondance exacte d'abord
4. Spécificité maximale (quand le terme est qualifié)
5. Diagnostic > Descripteur (quand le terme désigne une pathologie)

**Garde-fous** :
- `Structured Outputs` (Pydantic) → format garanti
- Validation post-LLM → si l'ID renvoyé n'est pas dans les candidats → forçage `NONE`

**Coût** : ~$0.001/terme (prompt court, GPT-4o-mini)

---

### 🧱 Brique 4.5 — Couche d'Expansion Sémantique

**Fichier** : `semantic_layer.py` (506 lignes)  
**Modèle** : Aucun (purement symbolique)  
**Entrée** : Liste de `found_ids` (sortie Briques 2→4)  
**Sortie** : `SemanticResult` enrichi (patterns détectés, qualifiers regroupés, négations converties)

**Rôle clé** : Convertir les négations (`absent(TROUBLE_DE_REPOLARISATION)` → `PAS_D_ANOMALIE_DE_LE_REPOLARISATION`) via le mapping `excludes` de l'ontologie. Regroupe les findings par pattern et prépare les données pour le scoring.

---

### 🧱 Brique 5 — Scoring V3 Ontologique

**Fichier** : `scoring_v3.py` (665 lignes)  
**Modèle** : Aucun (purement symbolique)  
**Entrée** : `found_ids` (étudiant) vs `golden_ids` (expert)  
**Sortie** : `ScoringResultV3` avec score global et score détaillé par concept

**Algorithme de scoring** :

```
Pour chaque concept attendu (golden) :

  1.  Trouvé exact (ou synonyme) dans found_ids         → 1.0
  1b. Un enfant (descendant) trouvé dans found_ids       → 1.0
  1c. Un parent trouvé dans found_ids :
      - parent direct (distance 1)                       → 2/3
      - parent éloigné (distance ≥ 2)                    → 1/3
  2.  Non trouvé, mais a requires → nb_req_trouvés / nb_req   (0..1)
      - Vérification récursive (profondeur max 2)
  3.  Non trouvé, pas de requires, has_qualifiers trouvés → 2/3
  4.  Non trouvé, pas de requires, supports trouvés       → 1/3
  5.  Un excludes trouvé                                  → 0 (écrase tout)
  6.  Rien                                                → 0

  Score final = MAX(scores possibles) pour chaque concept
  Score global = moyenne des scores / N concepts golden × 100
```

**Conversion des négations** : les concepts `absent` sont convertis en concepts positifs via le mapping `excludes` de l'ontologie.

---

### 🧱 Brique 6 — Rapport + Feedback Pédagogique

**Fichiers** :  
- `candidate_report.py` (845 lignes) — orchestrateur du pipeline complet  
- `pedagogical_feedback.py` (440 lignes) — génération du feedback GPT  
- `edn_knowledge_base.py` (919 lignes) — base de connaissances cours SFC  
- `generate_html_report.py` (776 lignes) — export HTML standalone

**Feedback V2** (2 sections) :

```
┌─────────────────────────────────────────────┐
│ 📚 Section 1 : Référence au cours           │
│   - Concepts validants trouvés/manqués       │
│   - Descripteurs trouvés/manqués             │
│   - Citations du cours SFC (Item 231)        │
│   - Concepts erronés expliqués               │
├─────────────────────────────────────────────┤
│ 💬 Section 2 : Votre interprétation         │
│   - Félicitations courtes (si score > 80%)   │
│   - Explication du score                     │
│   - Commentaire du correcteur intégré        │
│   - Conseil personnalisé                     │
└─────────────────────────────────────────────┘
```

**Modèle** : `gpt-4o-mini` (prompt ~500 tokens de contexte)  
**Coût** : ~$0.002/cas

---

## 5. Flux de données complet

```
                          ┌─────────────────────┐
                          │    ONTOLOGIE OWL     │
                          │   (WebProtégé)       │
                          └──────────┬───────────┘
                                     │
                          ┌──────────▼───────────┐
                          │  rdf_owl_extractor.py │
                          │  convert_owl_to_v2.py │
                          └──────────┬───────────┘
                                     │
                          ┌──────────▼───────────┐
                          │  ontology_v2.json    │
                          │  345 concepts        │
                          └──────┬───────┬───────┘
                                 │       │
                    ┌────────────▼┐     ┌▼────────────┐
                    │ Brique 0    │     │ semantic_    │
                    │ ontology_   │     │ layer.py     │
                    │ index.py    │     │ scoring_v3   │
                    └──────┬──────┘     └──────────────┘
                           │
                 ┌─────────▼──────────┐
                 │  rag_index/        │
                 │  658 docs × 1536   │
                 └─────────┬──────────┘
                           │
   ┌───────────┐  ┌────────▼────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
   │ Texte     │  │ Brique 2: NER   │  │ Brique 3:   │  │ Brique 4:   │  │ Brique 5:    │
   │ étudiant  │─▶│ ner_extractor   │─▶│ hybrid_     │─▶│ neuro_      │─▶│ scoring_v3   │
   │           │  │ GPT-4o          │  │ search      │  │ symbolic_   │  │              │
   └───────────┘  └─────────────────┘  │ Dense+BM25  │  │ judge       │  │ + semantic_  │
                                       └─────────────┘  │ Coupe-circ. │  │   layer      │
                                                        │ + GPT-4o-   │  └──────┬───────┘
   ┌───────────┐                                        │   mini      │         │
   │ Golden    │                                        └─────────────┘         │
   │ Set       │──────────────────────────────────────────────────────────▶─────┘
   │ (expert)  │                                                          │
   └───────────┘                                                   ┌──────▼───────┐
                                                                   │ Brique 6:    │
   ┌───────────┐                                                   │ candidate_   │
   │ Cours SFC │──────────────────────────────────────────────────▶│ report       │
   │ Item 231  │                                                   │ + feedback   │
   │ (EDN KB)  │                                                   │ + HTML       │
   └───────────┘                                                   └──────────────┘
```

---

## 6. Stratégie d'interaction Ontologie ↔ LLMs

### 6.1 Principe fondamental : séparation des responsabilités

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ONTOLOGIE (symbolique)                               │
│  • Source de vérité : 345 concepts, poids, catégories, synonymes       │
│  • Index vectoriel : 658 documents (embeddings 1536-dim)               │
│  • Relations sémantiques : requires, excludes, supports, qualifiers    │
│  • Scoring déterministe : résultat 100% reproductible                  │
│  • Normalisation de texte : matching exact sans ambiguïté              │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                         Candidats Top-K
                         + métadonnées
                         (poids, catégorie,
                          is_exact_match)
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│                        LLMs (neuronal)                                  │
│  • Brique 2 (GPT-4o) : extraction NER brute — AUCUNE ontologie         │
│  • Brique 4 (GPT-4o-mini) : QCM contraint — ontologie comme garde      │
│  • Brique 6 (GPT-4o-mini) : feedback pédagogique — cours comme contexte│
│                                                                          │
│  Le LLM ne voit JAMAIS l'ontologie complète.                            │
│  Il voit uniquement les Top-K candidats pré-filtrés.                    │
│  Il ne peut PAS inventer un ID — validation post-LLM stricte.           │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Les 3 interactions clés

| Interaction | Qui → Qui | Mécanisme | Objectif |
|---|---|---|---|
| **NER → Search** | LLM → Ontologie | Terme brut → embedding → cosinus + BM25 | Trouver des candidats (tolérant aux fautes) |
| **Search → Juge** | Ontologie → LLM | Top-K candidats (avec poids/catégorie) → QCM | Décision clinique contextuelle |
| **Coupe-circuit** | Ontologie seule | Matching exact normalisé → bypass LLM | Rapidité + déterminisme (42% des cas) |

### 6.3 Garde-fous contre les erreurs LLM

| Garde-fou | Couche | Mécanisme |
|---|---|---|
| **Structured Outputs** | Briques 2 & 4 | Schéma Pydantic garanti par l'API OpenAI — impossible de dévier |
| **Validation post-LLM** | Brique 4 | L'ID renvoyé doit être dans les candidats soumis — sinon forçage `NONE` |
| **Coupe-circuit spécificité** | Brique 4 | Annule le bypass si concept plus spécifique existe dans le Top-K |
| **Filet négation** | Brique 2 + post | Regex Python double-vérifie les négations ratées par GPT-4o |
| **Scoring symbolique** | Brique 5 | Poids/catégories/relations gérés par l'ontologie, pas par le LLM |
| **Forçage NONE** | Brique 4 | Si ID invalide → NONE plutôt qu'un faux positif |

---

## 7. Stack technique

### 7.1 Langages et frameworks

| Composant | Technologie |
|-----------|-------------|
| **Langage** | Python 3.12+ |
| **LLMs** | OpenAI GPT-4o (NER) + GPT-4o-mini (Juge + Feedback) |
| **Embeddings** | OpenAI text-embedding-3-small (1536 dims) |
| **Ontologie source** | OWL (WebProtégé) → RDF/XML |
| **Ontologie runtime** | JSON V2 (345 concepts) |
| **Recherche vectorielle** | NumPy (cosinus sur matrice dense, in-RAM) |
| **Recherche sparse** | BM25Okapi (rank_bm25) |
| **Validation structurée** | Pydantic v2 |
| **Collecte étudiants** | Streamlit (ECG Collector) |
| **Analyse & évaluation** | Jupyter Notebooks (ECG Evaluation) |
| **Déploiement collecte** | Scalingo (PaaS) |
| **Rapports** | HTML standalone (base64 images) |

### 7.2 Coûts API (estimation par cas étudiant)

| Brique | Modèle | Coût estimé |
|--------|--------|-------------|
| Brique 0 (index) | text-embedding-3-small | ~$0.01 total (one-shot) |
| Brique 2 (NER) | gpt-4o | ~$0.003/cas |
| Brique 3 (search) | text-embedding-3-small | ~$0.001/terme × ~8 termes = $0.008 |
| Brique 4 (juge) | gpt-4o-mini | ~$0.001/terme × ~5 termes = $0.005 |
| Brique 6 (feedback) | gpt-4o-mini | ~$0.002/cas |
| **Total** | | **~$0.02/cas** soit **~$0.30/étudiant** (15 cas) |

Pour 43 étudiants × 15 cas = 645 évaluations → **~$13 total**.

---

## 8. Structure du projet

```
ECG lecture/                          # Repo git principal (edu-ecg)
├── ARCHITECTURE.md                   # ← CE FICHIER (documentation centralisée A→D)
├── README.md                         # Documentation d'usage du pipeline
├── BrYOzRZIu7jQTwmfcGsi35.owl        # Ontologie OWL source (WebProtégé)
├── BrYOzRZIu7jQTwmfcGsi35V1.owl      # Version antérieure de l'OWL
├── BrYOzRZIu7jQTwmfcGsi35_patched_*.owl  # OWL patché (à réimporter) — cf. §14
├── patch_ontology_owl.py             # Génère l'OWL patché (synonymes + excludes)
├── convert_owl_to_v2.py              # Convertisseur OWL → JSON V2
├── regenerate_ontology.py            # Script de régénération ontologie
├── requirements.txt                  # Dépendances Python (pipeline)
│
├── ecg-online/                       # ★ APP AUTONOME EN LIGNE (Partie B) ★
│   ├── app/                          #   grader.py, server.py, cases_repo.py
│   ├── frontend/                     #   index.html, style.css, app.js
│   ├── data/                         #   cases.json (75 cas) + ecg_images/ (108 PNG)
│   ├── scripts/                      #   extraction docx/pdf → cases.json
│   ├── run.py, Procfile, runtime.txt #   local + Scalingo
│   ├── README.md, ROADMAP.md         #   doc & plan de route
│   └── requirements.txt              #   dépendances app (Flask, openai, gunicorn)
│
├── backend/
│   └── rdf_owl_extractor.py          # Parseur RDF/XML de l'OWL (V1)
│
├── data/
│   ├── ontology_from_owl.json        # Ontologie V1 (289 concepts, historique)
│   └── ontology_v2.json              # Ontologie V2 (345 concepts) ← RUNTIME
│
├── rag_pipeline/                     # ★ CŒUR DU PIPELINE RAG (Partie A) ★
│   ├── ontology_index.py             # Brique 0 — Index vectoriel + BM25
│   ├── ner_extractor.py              # Brique 2 — NER GPT-4o
│   ├── hybrid_search.py              # Brique 3 — Recherche hybride
│   ├── neurosymbolic_judge.py        # Brique 4 — Juge neurosymbolique
│   ├── semantic_layer.py             # Brique 4.5 — Expansion sémantique
│   ├── scoring_v3.py                 # Brique 5 — Scoring V3 ontologique
│   ├── candidate_report.py           # Brique 6 — Orchestrateur + rapport
│   ├── pedagogical_feedback.py       # Brique 6 — Feedback GPT
│   ├── edn_knowledge_base.py         # Brique 6 — Knowledge base EDN/SFC
│   ├── tests/test_scoring_v3.py      # 18 tests de non-régression (cf. §13)
│   └── rag_index/                    # Index pré-calculés (npy + metadata + BM25)
│
├── frontend/
│   └── pages/correction_llm.py       # Page Streamlit corrections
│
└── dossier_ecole/                    # Dossier académique (rapports, schémas)

ECG collector/                        # Application de collecte Streamlit
├── app.py                            # Interface de saisie (50 participants × 15 cas)
├── corrections/students/             # réponses étudiants (ECG-*.json) + golden.json
└── images/                           # images ECG

ECG evaluation/                       # Notebooks d'analyse et de benchmark
├── 01_Evaluation_Pipeline.ipynb …    # pipeline, sandbox, publication, rapports
├── goldenset/                        # 15 cas ECG annotés par expert
└── results/                          # Résultats benchmark (CSV)
```

---

## 9. Forces

### ✅ F1 — Architecture neurosymbolique rigoureuse

La **séparation symbolique/neuronal** est le cœur de la robustesse. Le LLM ne voit jamais l'ontologie complète, ne peut pas inventer d'IDs, et le scoring est 100% déterministe. Le coupe-circuit (42% des cas) garantit la reproductibilité.

### ✅ F2 — Ontologie ECG spécialisée et unique

345 concepts hiérarchiques avec **5 types de relations sémantiques**, 318 synonymes français, pondération clinique à 4 niveaux. À notre connaissance, **il n'existe pas d'équivalent francophone** orienté évaluation pédagogique.

### ✅ F3 — Scoring V3 hiérarchique

Le scoring dépasse le simple match binaire : il exploite la **hiérarchie parent/enfant** (un enfant trouvé vaut 1.0, un parent vaut 2/3 ou 1/3), les **requires récursifs**, et les **excludes** pour pénaliser les erreurs. Cela rend l'évaluation cliniquement pertinente.

### ✅ F4 — Tolérance aux fautes d'orthographe et abréviations

La combinaison **embeddings sémantiques + BM25 lexical + RRF** absorbe les fautes (`"tachi supra"` → `TACHYCARDIE_SUPRA_VENTRICULAIRE`) et les abréviations (`"BBD"`, `"FA"`, `"BAV"`). Le NER V2 étend explicitement les acronymes courants.

### ✅ F5 — Feedback pédagogique ancré dans le cours

Le feedback n'est pas un commentaire générique : il cite les **extraits du cours SFC Item 231**, classés par rang EDN (A/B/C), et intègre le **commentaire du correcteur** expert. Le format en 2 sections (Référence au cours + Votre interprétation) est structuré pour l'apprentissage.

### ✅ F6 — Coût maîtrisé

~$0.02/cas et ~$13 pour l'ensemble du dataset (43 étudiants × 15 cas). Aucune GPU locale requise — tout tourne via API OpenAI.

### ✅ F7 — Gestion explicite de la négation

Double filet (prompt NER + regex post-processing) pour transformer "pas de trouble de repolarisation" en `absent(TROUBLE_DE_REPOLARISATION)`, puis mapping ontologique vers le concept positif correspondant.

### ✅ F8 — Rapports HTML autonomes

Les rapports sont des **fichiers HTML standalone** (images en base64) ouvrables dans n'importe quel navigateur, imprimables en PDF via Ctrl+P. Pas de dépendance serveur.

---

## 10. Faiblesses et axes d'amélioration

### ⚠️ W1 — Dépendance à l'API OpenAI

L'ensemble du pipeline repose sur OpenAI (GPT-4o, GPT-4o-mini, text-embedding-3-small). Pas de **fallback local**. Si l'API est indisponible ou si les prix augmentent, le pipeline est bloqué.

**Piste** : Évaluer des modèles locaux (Mistral, Llama 3) pour le NER et le juge. L'embedding pourrait être remplacé par un modèle sentence-transformers local.

### ⚠️ W2 — Pas de recherche vectorielle scalable

L'index vectoriel est une **matrice NumPy en RAM** (658 × 1536). La recherche est un simple `argmax(cosinus)`. Cela suffit pour 658 documents mais ne passera pas à l'échelle si l'ontologie dépasse ~10 000 concepts.

**Piste** : Intégrer FAISS, Qdrant, ou ChromaDB si l'ontologie grandit significativement.

### ⚠️ W3 — Ontologie non standardisée

L'ontologie est **custom** : elle n'est pas alignée avec SNOMED CT, ni avec un standard international. Cela limite l'interopérabilité et la réutilisation par d'autres projets.

**Piste** : Ajouter des mappings `owl:sameAs` vers les codes SNOMED CT pour les concepts principaux. Publier l'ontologie sur un dépôt ouvert (BioPortal, OLS).

### ⚠️ W4 — Golden set limité (15 cas)

15 cas ECG annotés par un seul expert → **risque de biais de l'annotateur** et couverture incomplète de la diversité ECG (pas de cas pédiatrique, pas de stimulateur cardiaque complexe, etc.).

**Piste** : Étendre à 50+ cas avec annotations multi-experts et calcul d'accord inter-annotateurs (Kappa de Cohen).

### ⚠️ W5 — Pas de tests unitaires automatisés

Le scoring V3 et le NER n'ont pas de suite de tests unitaires exécutables en CI. Les tests sont manuels via notebooks.

**Piste** : Écrire des tests pytest couvrant les cas limites (négation, hiérarchie, synonymes, concepts multi-niveaux). Intégrer en GitHub Actions.

### ⚠️ W6 — Couplage entre workspaces

Le code vit dans 4 dossiers distincts (`ECG lecture`, `RAG ontologique`, `ECG collector`, `ECG evaluation`). `RAG ontologique` est une copie de travail de `ECG lecture/rag_pipeline/` qu'il faut synchroniser manuellement.

**Piste** : Utiliser un monorepo avec des symlinks ou un script de sync automatique. Ou restructurer en un seul workspace Python avec des packages installables.

### ⚠️ W7 — Pas de versionnement de l'ontologie

L'ontologie `ontology_v2.json` est versionnée dans git, mais il n'y a pas de **mécanisme de migration** ni de changelog structuré pour les changements de concepts.

**Piste** : Adopter un format de diff ontologique (ajout/suppression/modification de concepts) et un numéro de version sémantique pour le JSON.

### ⚠️ W8 — Évaluation sur un seul site / une seule promotion

43 étudiants d'une seule faculté. Pas de validation croisée multi-centres.

**Piste** : Déployer auprès d'autres facultés et comparer les distributions de scores pour valider la généralisabilité.

### ⚠️ W9 — Pas d'interface de correction en temps réel

Le pipeline fonctionne en **batch** (notebooks ou scripts CLI). Pas d'API REST ni d'interface web permettant à un étudiant de soumettre un texte et obtenir un feedback en temps réel.

**Piste** : Exposer le pipeline via FastAPI et intégrer dans une interface Streamlit ou web.

### ⚠️ W10 — Coverage de la knowledge base EDN limitée

33 entrées EDN couvrent 85 concept_ids sur 345 (24.6%). Les concepts non couverts ne bénéficient pas de feedback ancré dans le cours.

**Piste** : Étendre la knowledge base à l'ensemble du référentiel CNEC (pas seulement l'Item 231) et couvrir les concepts de stimulation cardiaque, canalopathies, etc.

---

## 11. Métriques actuelles

### 11.1 Dataset

| Métrique | Valeur |
|----------|--------|
| Étudiants | 43 |
| Cas ECG | 15 (golden set annoté par cardiologue expert) |
| Total évaluations | ~645 (43 × 15) |
| Concepts par cas (médiane) | ~6 validants + ~4 descripteurs |

### 11.2 Performance du pipeline

| Métrique | Valeur |
|----------|--------|
| Coupe-circuit (bypass LLM) | ~42% des résolutions |
| Latence par cas (15 questions) | 5-8 secondes |
| Latence rapport complet (1 étudiant × 15 cas, avec feedback) | ~200-400 secondes |
| Coût API par étudiant | ~$0.30 |

### 11.3 Ontologie

| Métrique | Valeur |
|----------|--------|
| Concepts | 345 |
| Synonymes | 318 |
| Documents indexés | 658 |
| Embedding model | text-embedding-3-small (1536 dims) |
| Taille index | ~4 Mo (vecteurs) + ~1 Mo (metadata + BM25) |

---

*Document généré le 2026-04-22 — Version V3 du pipeline (Scoring V3, NER V2, Feedback V2)*

---

# Partie B — Application en ligne `ecg-online`

## 12. App autonome de correction ouverte (GPT-4o)

> **Nouveau (juillet 2026).** Dépôt applicatif **autonome** et déployable sur
> Scalingo, situé dans `ECG lecture/ecg-online/`. Il transforme le projet de
> *pipeline d'évaluation batch* en *plateforme d'entraînement en ligne* : un
> étudiant lit un ECG, rédige une interprétation **en texte libre**, et GPT-4o la
> corrige (score + commentaire). Voir `ecg-online/README.md` et `ecg-online/ROADMAP.md`.

### 12.1 Positionnement vs pipeline neurosymbolique

| | Pipeline neurosymbolique (Partie A) | App `ecg-online` (Partie B) |
|---|---|---|
| But | Évaluer un corpus, mesurer, publier | Entraîner l'étudiant en ligne, feedback immédiat |
| Correction | NER→RAG→Juge→Scoring V3 (déterministe) | GPT-4o direct, ancré sur l'interprétation de référence |
| Banque | 15 cas golden annotés | **75 cas** extraits de l'ouvrage (tracés + interprétations) |
| Dépendances | 4 workspaces + index RAG | **Autonome** (Flask + OpenAI, 1 clé) |
| Reproductibilité | 100 % (scoring symbolique) | dépend de GPT (temperature 0) |
| Déploiement | notebooks / CLI | Scalingo (`Procfile`, gunicorn) |

➡️ Les deux sont **complémentaires** : l'app délivre la valeur pédagogique
immédiate ; le pipeline reste la référence de mesure et la future source d'un
**scoring hybride** (cf. §13-15 et `ecg-online/ROADMAP.md` Phase 2).

### 12.2 Banque de 75 cas

Extraite de l'ouvrage ECG de référence (Word + PDF) via `ecg-online/scripts/`
(`extract_cases.py`, `compile_ecg_pdf.py`, `build_cases_json.py`). Sortie :
`ecg-online/data/cases.json` — **75 cas, 75/75 avec tracé et interprétation**.

Répartition des familles :
`rythme 25 · conduction 21 · ischémie 12 · hypertrophie 4 · péricarde 3 ·
normal 2 · génétique 2 · embolie 2 · métabolique 2 · technique 1 · infiltratif 1`

Contrat de données (par cas) : `num, titre, famille, patient, contexte,
qcm{question,options,reponses}, interpretation_ref, second_trace, commentaires,
referentiel, images[]`.

### 12.3 Architecture applicative

```
Frontend (HTML/CSS/JS)  ──► Flask API (app/server.py) ──► grader GPT-4o (app/grader.py)
  sélecteur de cas            /api/cases, /api/case/<n>       function calling « rendre_correction »
  visualiseur de tracé        /api/grade  (score+comment)     ancré sur interpretation_ref
  zone de réponse libre       /images/<f> (tracés PNG)        barème progressif + équivalences
  résultat animé              cases_repo.py (expurge la réf)  cliniques (cf. §15)
```

- **`app/grader.py`** — cœur IA. Renvoie un JSON structuré : `score`,
  `score_diagnostic`, `score_descriptif`, `correspondance` (exacte/acceptable/
  partielle/incorrecte), `type_erreur` (aucune/étudiant/incomplet/formulation),
  `elements_trouves/manques/errones`, `commentaire`. Le prompt intègre les règles
  du rapport de relecture (§15) : crédit partiel, équivalences cliniques, règle
  « ECG normal », valorisation des négations.
- **`app/cases_repo.py`** — accès banque + **expurgation** : l'interprétation de
  référence n'est jamais renvoyée avant que l'étudiant ait soumis sa réponse.
- **`app/server.py`** — API REST + service du front + des images.

### 12.4 Comportement validé (tests end-to-end)

| Scénario | Score obtenu | Correspondance | Type |
|----------|:-----------:|----------------|------|
| « ECG normal » explicite sur cas normal | 100 | exacte | aucune |
| SCA décrit (sus-ST + miroir + Pardee) sans nommer | 70 | partielle | incomplet |
| « ECG normal » affirmé sur un STEMI | **30** (plafonné) | incorrecte | étudiant |

### 12.5 Lancer / déployer

```powershell
cd "ECG lecture\ecg-online"
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # renseigner OPENAI_API_KEY
python run.py                 # http://localhost:5000
```

Scalingo : `git push scalingo main` (détecte `requirements.txt` + `runtime.txt`,
lance le `web:` du `Procfile`). Aucune base de données (banque = JSON versionné).

---

# Partie C — Audit de robustesse

## 13. Audit — robustesse des résultats

> Repris de l'ancien `AUDIT.md` (juillet 2026). Périmètre : `ECG lecture`,
> `RAG ontologique`, `ECG collector`, `ECG evaluation`.

### 13.0 Note de méthode (honnêteté intellectuelle)

Le chiffre « **taux d'hallucination 63,7 %** » **ne doit pas être lu comme « 2
concepts sur 3 sont des inventions »**. Il compare *tous* les concepts extraits au
golden **de scoring**, qui ne liste que 1 à 3 concepts « qui comptent » par cas.
Les concepts cliniquement **vrais mais non listés** (« QRS fins », « PR normal »)
sont comptés à tort comme faux positifs.

➡️ La vraie conclusion : **« on est aujourd'hui incapable de distinguer une vraie
erreur d'une bonne observation non listée »**. C'est le problème central de
robustesse ; sa solution est méthodologique (golden d'extraction, §13.4).

### 13.1 Synthèse exécutive

| Dimension | Note | Commentaire |
|-----------|:----:|-------------|
| Pertinence du besoin | 🟢 9/10 | Vrai vide : évaluation de texte libre ECG, ancrée EDN Item 231 |
| Architecture | 🟢 8/10 | Neurosymbolique rigoureux, garde-fous réels |
| Choix techniques | 🟡 6/10 | Bonnes briques ; dette (4 workspaces, ~50 scripts jetables), tout-OpenAI |
| **Robustesse des résultats** | 🟠 **4/10** | **Métrique = rappel déguisé ; pas de golden d'extraction ; golden mono-expert** |
| Reproductibilité | 🟡 5/10 | Scoring déterministe ✅, mais chiffres incohérents entre docs & dépendance API |
| Maintenabilité | 🟡 5/10 | Duplication `RAG ontologique` ↔ `ECG lecture/rag_pipeline` |

**Verdict** : colonne vertébrale conceptuelle **solide**. Le point bloquant n'est
**pas** l'architecture, mais la **chaîne de mesure** : tant qu'un *golden
d'extraction* n'existe pas, aucun chiffre de précision/rappel n'est fiable.

### 13.2 Le cœur du sujet : la métrique de score

Le `scoring_v3` calcule `score_pct = Σ score(concept_attendu_i) / N_attendus × 100`.
➡️ C'est un **rappel pondéré cliniquement**. Il **n'intègre pas** les concepts en trop.

**Ce qui fonctionne déjà (crédit partiel ontologique)** ✅ :

| Situation | Score | Interprétation |
|-----------|:-----:|----------------|
| Concept exact | 100 % | match direct |
| **Enfant** trouvé (plus précis) | 100 % | `BBD complet` crédite `BBD` |
| **Parent direct** (plus vague) | 66,7 % | `BBD` crédite partiellement `BBD complet` |
| 1/4 `requires` satisfait | 25 % | `Rythme sinusal` → `ECG normal` |
| Concept **exclu** présent | 0 % | garde-fou : `FA` annule `ECG normal` |

**Ce qui manque** : le scoring ne traite pas les **concepts hors-golden**. Deux cas
s'y cachent — vrai-mais-non-listé (inoffensif) vs cliniquement-faux (dangereux) —
et **on ne peut pas les séparer automatiquement** aujourd'hui.

### 13.3 Limite : négation trop généreuse ⚠️

`absent("trouble de repolarisation")` se convertit en `ECG_NORMAL`. Un étudiant
écrivant **uniquement** « pas de trouble de repolarisation » obtient **100 %** sur
un cas ECG normal. ➡️ Une négation isolée ne devrait pas valider un diagnostic
composite entier.

### 13.4 🎯 Recommandation centrale : le « golden d'extraction »

Il faut **deux golden sets** de natures différentes :

| | Golden **de scoring** (existant) | Golden **d'extraction** (à créer) |
|---|---|---|
| Contenu | Concepts qui comptent pour la **note** (1-3/cas) | **Tous** les concepts réellement présents |
| Sert à | Noter l'étudiant | **Mesurer la lecture du texte par le pipeline** |
| Statut | ✅ `ECG collector/corrections/golden.json` | ❌ **manquant** |

**Protocole** : annoter ~50 réponses (tous concepts présents + statut), double
annotation sur ~15 (Kappa de Cohen), rejouer le pipeline → **P/R/F1 réels**.
➡️ **Préalable P0** avant toute refonte de métrique.

### 13.5 Risques de robustesse

| Réf | Risque | Priorité |
|-----|--------|:--------:|
| R1 | **Golden mono-expert & étroit** (15 cas, 1 expert) | 🔴 P0/P1 |
| R2 | **Chiffres incohérents entre docs** (92 % / 62,4 % / 42 % / 85,1 %) | 🔴 P0 |
| R3 | Tests : désormais `tests/test_scoring_v3.py` (18 tests) ; reste négation/semantic | 🟡 P1 |
| R4 | Juge LLM non validé indépendamment | 🟡 P1 |
| R5 | Erreurs non tracées par brique (pas d'ablation) | 🟡 P1 |
| R6 | Dépendance totale OpenAI | 🟡 P1 |
| R7 | Négation trop généreuse (§13.3) | 🟡 P1 |

### 13.6 Feuille de route priorisée (robustesse)

**🔴 P0** — golden d'extraction (~50 annotés + Kappa) ; recalcul P/R/F1 réels ;
unifier les chiffres (une source de vérité versionnée) ; ✅ tests scoring (fait).
**🟡 P1** — étendre le golden de scoring (≥2 experts) ; refondre la métrique (note
exactitude + note fiabilité pondérée gravité) ; corriger la négation ; ablation par
brique ; couvrir semantic_layer & négation en tests.
**🟢 P2** — monorepo & nettoyage ; fallback local (sentence-transformers + Mistral) ;
panel multi-juges + score de confiance ; (option) SNOMED + raisonneur OWL.

---

# Partie D — Ontologie : réannotation & OWL

## 14. Réannotation WebProtégé & patch OWL

> Fusion de `REANNOTATION_WEBPROTEGE.md` + patch OWL de juillet 2026.

### 14.1 Fichiers OWL

| Fichier | Rôle |
|---------|------|
| `BrYOzRZIu7jQTwmfcGsi35.owl` | Ontologie OWL source (WebProtégé, 401 classes, 345 concepts) |
| `BrYOzRZIu7jQTwmfcGsi35V1.owl` | Version antérieure |
| `BrYOzRZIu7jQTwmfcGsi35_patched_AAAA-MM-JJ.owl` | **OWL patché** (généré par `patch_ontology_owl.py`) — à réimporter dans WebProtégé |
| `patch_ontology_owl.py` | Applique les correctifs (synonymes + excludes_families) et produit l'OWL patché + `_patch_owl_report.txt` |
| `convert_owl_to_v2.py` | Convertisseur OWL → `data/ontology_v2.json` (runtime) |

### 14.2 Patch OWL de juillet 2026 (synonymes ajoutés)

Généré automatiquement par `patch_ontology_owl.py` (IRIs réels, XML validé) :

| Concept (IRI) | Synonymes `skos:altLabel` ajoutés |
|---------------|-----------------------------------|
| Flutter droit typique `R8Qu5zTeQYBDtJy6ntEW9Zt` | CTI-dépendant, flutter antihoraire typique |
| BBD complet `R9vRCWTeo81VmDBWIWkUUV2` | BBD + QRS large, BBD complet rSR', aspect rSR' + QRS large |
| SCA ST+ `R8WlYgdeyMoXnCoJOPfL6ie` | IDM ST+, infarctus avec sus-décalage, onde de Pardee, courant de lésion sous-épicardique territorial |
| Microvoltage `R7QyGgxIXK3MePvmNUhlkYG` | bas voltage, faible voltage, petits QRS, QRS de petite amplitude, QRS très petits, microvolté |
| Stimulation atriale `RuLDUWeiujYnS4rjWXWoSd` | électro-entraîné à l'étage atrial, spike auriculaire, pacemaker atrial, rythme stimulé atrial |
| Stimulation ventriculaire `Rsw8UNDCSH098dExZ6ZXdz` | spike ventriculaire, QRS stimulés larges, rythme pacé ventriculaire |
| ECG normal `RB5yWtPR1F86Bu5TIAoqFe5` | tracé sans anomalie significative |
| Faisceau accessoire/WPW `R0NX2vKfgeRaBNOeCyd8Mu` | PR court + onde delta |

➡️ **8 concepts modifiés**, 685 `skos:altLabel` au total, XML bien formé.
**Reproduire** : `python patch_ontology_owl.py` (n'écrase pas la source).

### 14.3 Réannotations antérieures (V3.1) — déjà appliquées / à vérifier

- **ECG_NORMAL.excludes_families** : 7 familles (dont TROUBLES_DE_CONDUCTION,
  STIMULATION, EVENEMENTS_ECTOPIQUES, INTERFERENCE_EXTRA_CARDIAQUE). ✅ vérifié
  présent dans l'OWL courant.
- **TROUBLE_DE_REPOLARISATION** : + synonyme « Trouble de la repolarisation ».
- **AXE_NORMAL_DU_QRS** : + « axe gauche physiologique », « axe physiologique »,
  « Axe du cœur normal », « Axe cardiaque normal ».
- **BLOC_INTERATRIAL** : `has_qualifier_families: [ONDE_P_ANORMALE]`.
- Propriété `has_qualifier_families` (IRI `R8vQ8mX6hV4s7wN4eSTlvaF`) supportée par
  le convertisseur et `scoring_v3.py`.

### 14.4 Procédure de mise à jour de l'ontologie

```powershell
cd "ECG lecture"
# 1. (option) régénérer un OWL patché depuis les correctifs
python patch_ontology_owl.py
# 2. importer l'OWL patché dans WebProtégé, ré-exporter l'OWL « propre »
# 3. régénérer le JSON runtime
python convert_owl_to_v2.py           # -> data/ontology_v2.json
# 4. reconstruire l'index RAG (rag_pipeline/ontology_index.py)
```

### 14.5 Checklist WebProtégé

- [ ] Importer `BrYOzRZIu7jQTwmfcGsi35_patched_*.owl` (8 concepts enrichis, §14.2)
- [ ] Vérifier ECG_NORMAL : 7 `excludes_families`
- [ ] Vérifier les synonymes V3.1 (§14.3)
- [ ] Vérifier la property `has_qualifier_families`
- [ ] Ré-exporter l'OWL + régénérer `ontology_v2.json` + index RAG

---

## 15. Rapport de relecture — synthèse et décisions

> Synthèse du *Rapport de relecture — Optimisation de l'ontologie et de l'algorithme
> de correction ECG* (arbitrage humain des FN/FP sur 43 étudiants × 15 cas).

### 15.1 Diagnostic

Le nouveau pipeline GPT **détecte bien mieux** diagnostics et concepts. Mais la
relecture humaine montre que **les FN/FP bruts surestiment les erreurs** : la
plupart ne sont **pas** des erreurs cliniques de l'étudiant ni de GPT, mais des
problèmes **d'ontologie, de règles d'inférence ou de scoring** (logique trop
binaire, négations mal valorisées, granularité, mapping des synonymes).

### 15.2 Cas reclassés après arbitrage (extraits)

| Cas | Problème réel | Nature |
|-----|---------------|--------|
| 4H0K/DFLC/WY55 cas 12 | mapping « infarctus ST+ » → `SCA ST+` incomplet | ontologie/agrégation |
| 87P4 cas 1 | « normal » seul doit valider ECG normal | scoring trop rude |
| IDXQ cas 8 | « flutter commun isthmique » = flutter droit typique | granularité |
| ITB8 cas 7 | BBD + QRS 140 ms → BBD complet | inférence |
| K05S cas 4 | « QRS très fins et petits » = microvoltage | synonymes |
| U8SA cas 14 | ESV décrite non nommée → crédit **partiel** | scoring progressif |
| VQFO cas 6 | « électro-entraîné » atrial mal détecté | synonymes/inférence |

### 15.3 Décisions appliquées (juillet 2026)

**Dans l'app `ecg-online` (grader GPT, §12.3)** — implémenté :
- ✅ **Crédit partiel progressif** (barème ESV type).
- ✅ **Équivalences cliniques** : flutter, BBD/BBG complet, WPW, SCA ST+,
  microvoltage, stimulation atriale/ventriculaire.
- ✅ **Valorisation des négations** pertinentes.
- ✅ **Règle « ECG normal »** (explicite OU ≥4 critères ; bloquée si patho explicite).
- ✅ **Deux scores séparés** : `score_diagnostic` + `score_descriptif`.
- ✅ **Typage de l'écart** : aucune / étudiant / incomplet / formulation +
  niveau de `correspondance` (exacte/acceptable/partielle/incorrecte).

**Dans l'ontologie OWL (§14.2)** — implémenté :
- ✅ Synonymes flutter, BBD complet, SCA ST+, microvoltage, stimulation, WPW.

**À porter dans le scoring symbolique `scoring_v3.py` (Partie A)** — backlog :
- [ ] Relations parent-enfant « X + qualifiant → forme complète » (BBD/BBG complet).
- [ ] Crédit partiel paramétrable (indice isolé < description < nommé).
- [ ] Négation isolée ne validant pas un diagnostic composite entier (§13.3).
- [ ] Règle d'inférence « ECG normal » symétrique de celle du grader.

### 15.4 Priorités d'amélioration (rappel)

1. mieux **valoriser les réponses négatives** ;
2. **scoring partiel** ;
3. **formaliser les relations parent-enfant** ;
4. **enrichir les synonymes** descriptifs ;
5. **règles d'inférence** BBD complet, SCA ST+, flutter droit typique, microvoltage, stimulation ;
6. **distinguer erreurs étudiant vs erreurs algorithme**.

➡️ Après arbitrage, **le pipeline est meilleur que ne le suggèrent les FN/FP bruts**.
Le problème n'est plus le modèle GPT, mais la **couche de décision** (ontologie,
règles, agrégation, notation).

---

*Document centralisé — dernière mise à jour : 2026-07-05. Fusionne Architecture V3,
Audit, Réannotation WebProtégé, patch OWL et Rapport de relecture. App `ecg-online`
autonome (GPT-4o) ajoutée en Partie B.*
