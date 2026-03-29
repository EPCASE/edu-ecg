# 🏗️ Architecture du Pipeline RAG Neurosymbolique

## Vue d'ensemble

Le pipeline corrige automatiquement les interprétations ECG d'étudiants en médecine
en comparant leurs réponses en texte libre à un **golden set** annoté par un cardiologue expert.

```
┌─────────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Réponse        │───▶│  NER +       │───▶│  Matching    │───▶│  Scoring     │───▶│  Feedback    │
│  étudiant       │    │  Segmentation│    │  Ontologique │    │  Hiérarchique│    │  Pédagogique │
│  (texte libre)  │    │              │    │              │    │              │    │  (LLM)       │
└─────────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                              │                   │                   │
                              ▼                   ▼                   ▼
                       ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
                       │  Ontologie   │    │  Embeddings  │    │  Ontologie   │
                       │  OWL (292    │    │  OpenAI      │    │  (relations  │
                       │  concepts)   │    │  1536 dims   │    │  parent/     │
                       │  + synonymes │    │              │    │  enfant)     │
                       └──────────────┘    └──────────────┘    └──────────────┘
```

## Étape 1 — NER + Segmentation

**Fichier** : `ner_extractor.py`

Le texte libre de l'étudiant est découpé en **segments cliniques** (séparés par virgule,
point-virgule, retour à la ligne). Chaque segment est un candidat à l'extraction.

**Détection de négation** : Les expressions comme "pas de", "sans", "absence de" sont
détectées et le statut du concept est marqué comme `absent` (≠ `present` ou `hypothese`).

```
Entrée : "Rythme sinusal, QRS fins, pas de trouble de la repolarisation"
Sortie : [
  ("Rythme sinusal", statut=present),
  ("QRS fins", statut=present),
  ("trouble de la repolarisation", statut=absent)
]
```

## Étape 2 — Matching Ontologique (2 niveaux)

**Fichiers** : `hybrid_search.py`, `neurosymbolic_judge.py`

### Niveau 1 : Coupe-circuit (déterministe, 0 coût API)

Comparaison exacte du terme normalisé (minuscules, sans accents) avec les
**surface forms** de l'ontologie (noms canoniques + 246 synonymes).

```
"échappement ventriculaire" → normalize → "echappement ventriculaire"
→ Match exact avec surface_form de ECHAPPEMENT_VENTRICULAIRE ✅
```

**Avantage** : Instantané, gratuit, déterministe.
**Limite** : Ne fonctionne que si le terme exact existe dans l'ontologie.

### Niveau 2 : Juge LLM (sémantique, coût API)

Si le coupe-circuit échoue, on fait une **recherche hybride** :
1. **BM25** (lexical) : recherche par mots-clés dans les documents de l'ontologie
2. **Cosine similarity** (sémantique) : comparaison d'embeddings OpenAI (1536 dims)
3. **Fusion RRF** : les résultats sont fusionnés par Reciprocal Rank Fusion

Les top-K candidats sont envoyés à **GPT-4** qui choisit le meilleur match
ou répond `NONE` si aucun candidat ne correspond.

```
"Bloc atrio-ventriculaire complet"
→ Coupe-circuit : ❌ pas de match exact
→ Recherche hybride : candidats = [BAV_COMPLET, BAV_DE_HAUT_GRADE, BAV_2_MOBITZ_2, ...]
→ LLM : "BAV_COMPLET est le bon match" ✅
```

## Étape 3 — Scoring Hiérarchique

**Fichier** : `scoring.py`

Chaque concept attendu (golden set) est comparé aux concepts extraits de l'étudiant.

### Types de match

| Type | Description | Score |
|------|-------------|-------|
| `exact` | L'étudiant a donné exactement le concept attendu | 100% |
| `child_gen1` | L'étudiant a donné un sous-type (enfant direct) | 100% |
| `child_gen2` | Enfant de 2e génération | Dégressif (80%) |
| `parent_gen1` | L'étudiant a donné un concept plus général | 90% |
| `parent_gen2` | Concept encore plus général | 80% |
| `missing` | Concept non trouvé | 0% |

### Garde de poids (Poids Guard)

Pour éviter les matchs absurdes (ex: "Bradycardie" validant "BAV de haut grade"),
une **garde de poids** rejette les matchs enfant quand :
- Le poids du concept extrait < 2 (descripteur simple)
- Le poids du concept attendu ≥ 3 (diagnostic urgent)

```
Bradycardie (poids=1) → enfant de BAV de haut grade (poids=3)
→ Poids guard : rejeté ❌ (un descripteur ne peut pas valider un diagnostic urgent)

Flutter antihoraire (poids=1) → enfant de Flutter typique (poids=2)
→ Poids guard : accepté ✅ (le parent n'est pas un diagnostic urgent)
```

### Exception ECG_NORMAL

Le concept ECG_NORMAL est traité comme un **composant parent** : ses enfants
(rythme sinusal, QRS fins, etc.) ne sont pas des sous-types mais des composants.
Le scoring est donc dégressif (90%, 80%, etc.) au lieu de 100%.

## Étape 4 — Feedback Pédagogique

**Fichier** : `pedagogical_feedback.py`

Un appel LLM génère un commentaire pédagogique structuré en 3 parties :

1. **📖 Référence au cours** — Citation du référentiel SFC (Item 231) avec le rang EDN
2. **🔍 Votre interprétation** — Analyse de ce que l'étudiant a bien/mal identifié
3. **💡 Conseil du correcteur** — Conseils personnalisés incluant le commentaire de l'expert

Le LLM reçoit en contexte :
- Les concepts extraits de la réponse de l'étudiant
- Le golden set avec les concepts attendus
- Le commentaire du correcteur expert
- Des extraits du cours SFC (via RAG sur le Knowledge Base)

## Ontologie OWL

**Fichier source** : `ontologie.owx` (format OWL/XML)
**Export JSON** : `ontology_from_owl.json`

| Métrique | Valeur |
|----------|--------|
| Concepts totaux | 292 |
| Synonymes | 246 |
| Catégories | 4 (DIAGNOSTIC_URGENT, DIAGNOSTIC_MAJEUR, SIGNE_ECG_PATHOLOGIQUE, DESCRIPTEUR_ECG) |
| Relations parent-enfant | ~150 |
| Relations requiresFinding | 59 |

### Poids par catégorie

| Poids | Catégorie | Exemples |
|-------|-----------|----------|
| 3 | DIAGNOSTIC_URGENT | BAV complet, Tachycardie ventriculaire |
| 2 | DIAGNOSTIC_MAJEUR | Flutter typique, Fibrillation atriale |
| 1 | SIGNE_ECG_PATHOLOGIQUE | BBD complet, Bloc fasciculaire |
| 1 | DESCRIPTEUR_ECG | QRS fins, Bradycardie, Rythme sinusal |

## Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Embeddings | OpenAI `text-embedding-3-small` (1536 dims) |
| LLM | GPT-4 (juge + feedback) |
| Recherche lexicale | BM25 (rank_bm25) |
| Ontologie | OWL/XML → JSON |
| Frontend collecte | Streamlit |
| Déploiement | Scalingo |
| Versioning | GitHub (EPCASE/edu-ecg) |
