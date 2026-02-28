# 🏗️ Architecture du Pipeline RAG Neurosymbolique — Évaluation ECG

> **Projet** : edu-ecg / EPCASE  
> **Branche** : `RAGontologique`  
> **Date** : 2026-02-28  
> **Auteur** : Grégoire Massoullié

---

## Table des matières

1. [Vue d'ensemble](#1--vue-densemble)
2. [Chapitre 1 — Socle ontologique (Brique 1)](#chapitre-1--socle-ontologique-brique-1)
3. [Chapitre 2 — Extraction NER (Brique 2)](#chapitre-2--extraction-ner-brique-2)
4. [Chapitre 3 — Recherche hybride (Brique 3)](#chapitre-3--recherche-hybride-brique-3)
5. [Chapitre 4 — Juge neurosymbolique (Brique 4)](#chapitre-4--juge-neurosymbolique-brique-4)
6. [Chapitre 5 — Scoring ensembliste (Brique 5)](#chapitre-5--scoring-ensembliste-brique-5)
7. [Chapitre 6 — Rapport candidat & feedback pédagogique (Brique 6)](#chapitre-6--rapport-candidat--feedback-pédagogique-brique-6)
8. [Résultats du benchmark](#résultats-du-benchmark)
9. [Stack technique](#stack-technique)

---

## 1 — Vue d'ensemble

Le pipeline transforme le **texte libre d'un étudiant** en médecine en une **note structurée avec feedback pédagogique**, en passant par 6 briques enchaînées.

```mermaid
flowchart LR
    subgraph Entrée
        A[📝 Texte libre étudiant]
        B[📋 Golden Set expert]
    end

    subgraph Pipeline RAG Neurosymbolique
        direction TB
        B1["🧱 Brique 1<br/>Socle Ontologique<br/>+ Vectoriel"]
        B2["🧱 Brique 2<br/>Extraction NER<br/>GPT-4o"]
        B3["🧱 Brique 3<br/>Recherche Hybride<br/>Dense + BM25 + RRF"]
        B4["🧱 Brique 4<br/>Juge Neurosymbolique<br/>Coupe-Circuit + GPT-4o-mini"]
        B5["🧱 Brique 5<br/>Scoring Ensembliste<br/>Dégressif par génération"]
        B6["🧱 Brique 6<br/>Rapport Candidat<br/>+ Feedback SFC"]
    end

    subgraph Sortie
        S1[📊 Score %]
        S2[📋 Rapport détaillé]
        S3[🎓 Feedback pédagogique]
    end

    A --> B2
    B1 -.-> B3
    B2 --> B3
    B3 --> B4
    B4 --> B5
    B --> B5
    B5 --> B6
    B6 --> S1
    B6 --> S2
    B6 --> S3
```

### Principe fondamental

L'étudiant écrit une interprétation ECG en texte libre. Le pipeline doit :

1. **Extraire** les concepts cliniques de ce texte (NER)
2. **Relier** chaque concept à l'ontologie ECG officielle (Recherche + Juge)
3. **Comparer** les concepts trouvés au barème expert (Scoring)
4. **Expliquer** la note avec un commentaire pédagogique ancré dans le cours (Feedback)

---

## Chapitre 1 — Socle Ontologique (Brique 1)

> **Fichier** : `ontology_index.py`  
> **Exécution** : one-off (génération d'index)  
> **Dépendance** : `ontology_from_owl.json` (OWL → JSON)

### Rôle

Transformer l'ontologie ECG (fichier OWL) en une **base vectorielle locale** exploitable en temps réel.

### Données produites

| Fichier | Contenu | Taille |
|---------|---------|--------|
| `vecteurs_ontologie.npy` | Matrice d'embeddings N×1536 | ~2.5 Mo |
| `metadata_ontologie.json` | Registre i ↔ document i | ~500 Ko |

### Architecture de l'ontologie

```mermaid
graph TD
    subgraph Catégories pondérées
        DU["🔴 DIAGNOSTIC_URGENT<br/>poids = 4"]
        DM["🟠 DIAGNOSTIC_MAJEUR<br/>poids = 3"]
        DH["🟡 DIAGNOSTIC_HORS_CATEG<br/>poids = 2"]
        DESC["⚪ DESCRIPTEUR_ECG<br/>poids = 1"]
    end

    subgraph Exemples de concepts
        DU --> FA[Fibrillation atriale]
        DU --> TV[Tachycardie ventriculaire]
        DU --> BAV3[BAV complet]
        DM --> BBD[Bloc de branche droit complet]
        DM --> HBAG[Bloc fasciculaire antérieur gauche]
        DESC --> RS[Rythme sinusal]
        DESC --> QRS[QRS fins]
    end

    subgraph Relations
        FA -->|implique| AbsP[Absence d'onde P sinusale]
        FA -->|implique| Irr[Rythme irrégulier]
        BAV3 -->|implique| BAV[BAV]
        BBD -->|implique| QRSl[QRS larges]
    end
```

### Processus d'indexation

Pour chaque concept de l'ontologie :

1. **Normalisation** : unidecode, lowercase, suppression accents et tirets
2. **Documents générés** : nom canonique + chaque synonyme = 1 document
3. **Embedding** : OpenAI `text-embedding-3-small` (1536 dimensions)
4. **Index BM25** : tokenisation + BM25Okapi pour recherche lexicale

> **Résultat** : 411 documents indexés pour ~180 concepts, prêts pour recherche hybride.

---

## Chapitre 2 — Extraction NER (Brique 2)

> **Fichier** : `ner_extractor.py`  
> **Modèle** : GPT-4o (`gpt-4o-2024-08-06`) + Structured Outputs  
> **Latence** : ~1-2s par requête

### Rôle

Extraire du texte libre de l'étudiant une **liste structurée de concepts médicaux bruts**, sans aucune normalisation ni correction.

```mermaid
flowchart LR
    subgraph Entrée
        T["📝 «fibrillation atriale<br/>qrs fins tachycardie»"]
    end

    subgraph "Brique 2 — NER (GPT-4o)"
        direction TB
        P["System Prompt<br/>Périmètre ECG strict"]
        SO["Structured Outputs<br/>Pydantic Schema"]
    end

    subgraph Sortie
        E1["✓ present<br/>«fibrillation atriale»"]
        E2["✓ present<br/>«qrs fins»"]
        E3["✓ present<br/>«tachycardie»"]
    end

    T --> P
    P --> SO
    SO --> E1
    SO --> E2
    SO --> E3

    style P fill:#1e3a5f
    style SO fill:#1e3a5f
```

### Schéma de sortie (Pydantic)

```python
class ClinicalEntity:
    terme_brut: str       # Texte exact (pas de correction !)
    statut: "present" | "absent" | "hypothese"
    contexte_phrase: str   # Phrase d'origine
```

### Règles clés du prompt

| Règle | Description |
|-------|-------------|
| **Extraction pure** | ZÉRO normalisation. "tachi supra" → "tachi supra" |
| **Périmètre ECG** | Morphologie, rythme, diagnostics, étiologies ECG. Pas de clinique anamnestique |
| **Statut clinique** | `present` / `absent` ("pas de BBD") / `hypothese` ("suspi infarctus") |
| **Méthode LEGO** | Séparer diagnostic principal des modificateurs : "ESV polymorphe" → "ESV" + "polymorphe" |
| **Traduction numérique** | FC 150 → "Tachycardie", QRS 140ms → "QRS large", PR 240ms → "PR allongé" |

---

## Chapitre 3 — Recherche Hybride (Brique 3)

> **Fichier** : `hybrid_search.py`  
> **Moteurs** : Dense (OpenAI embeddings) + Sparse (BM25) + RRF  
> **Latence** : ~50ms par requête (dominé par l'API embedding)

### Rôle

Pour chaque terme brut extrait (Brique 2), trouver les **Top-K meilleurs concepts candidats** dans l'ontologie.

```mermaid
flowchart TB
    subgraph Entrée
        Q["🔍 «tachi supra»"]
    end

    subgraph "Brique 3 — Recherche Hybride"
        direction LR

        subgraph Dense
            EMB["Embedding<br/>text-embedding-3-small"]
            COS["Cosinus<br/>vs matrice 411×1536"]
            RD["Ranking Dense<br/>Top-30"]
        end

        subgraph Sparse
            TOK["Tokenisation<br/>normalize + split"]
            BM25["BM25Okapi<br/>scoring lexical"]
            RS["Ranking Sparse<br/>Top-30"]
        end

        RRF["⚡ Reciprocal Rank Fusion<br/>RRF(k=60)<br/>+ boost acronyme ×1.5"]
    end

    subgraph Sortie
        C1["🥇 TACHYCARDIE_SUPRAVENTRICULAIRE<br/>score: 0.89"]
        C2["🥈 TACHYCARDIE_JONCTIONNELLE<br/>score: 0.72"]
        C3["🥉 TACHYCARDIE<br/>score: 0.65"]
    end

    Q --> EMB --> COS --> RD
    Q --> TOK --> BM25 --> RS
    RD --> RRF
    RS --> RRF
    RRF --> C1
    RRF --> C2
    RRF --> C3

    style RRF fill:#4a148c,color:#fff
```

### Fusion RRF (Reciprocal Rank Fusion)

```
Score_RRF(doc) = Σ  1 / (k + rank_i(doc))
                 i∈{dense, sparse}

avec k = 60 (constante standard)
```

- **Boost BM25** : ×1.5 pour les matchs exacts (acronymes courts : "FA", "BBD", "TV")
- **Top-K final** : 5 candidats renvoyés au Juge (Brique 4)

Chaque candidat porte un flag **`is_exact_match`** si le terme normalisé de l'étudiant correspond exactement à une `surface_form` de l'ontologie.

---

## Chapitre 4 — Juge Neurosymbolique (Brique 4)

> **Fichier** : `neurosymbolic_judge.py`  
> **Modèles** : Coupe-circuit (symbolique) + GPT-4o-mini (LLM fallback)  
> **Latence** : 0ms (coupe-circuit) ou ~500ms (juge LLM)

### Rôle

Décider l'**ontology_id final** pour chaque terme brut, à partir des Top-K candidats. Peut répondre `NONE` si aucun candidat ne correspond.

```mermaid
flowchart TB
    subgraph Entrée
        T["terme_brut + contexte"]
        C["Top-K candidats<br/>(Brique 3)"]
    end

    subgraph "Brique 4 — Juge Neurosymbolique"
        D{Candidats<br/>disponibles ?}
        EM{Candidat #1<br/>is_exact_match ?}
        GF{Garde-fou<br/>spécificité ?}
        CC["⚡ Coupe-Circuit<br/>Résolution immédiate<br/>(bypass LLM)"]
        LLM["🧠 Juge LLM<br/>GPT-4o-mini<br/>QCM structuré"]
    end

    subgraph Sortie
        OID["ontology_id<br/>+ justification"]
        NONE["NONE<br/>(aucun match)"]
    end

    T --> D
    C --> D
    D -->|Non| NONE
    D -->|Oui| EM
    EM -->|Oui| GF
    EM -->|Non| LLM
    GF -->|"Pas de concept<br/>plus spécifique"| CC
    GF -->|"Concept plus<br/>spécifique existe"| LLM
    CC --> OID
    LLM --> OID
    LLM --> NONE

    style CC fill:#1b5e20,color:#fff
    style LLM fill:#e65100,color:#fff
```

### Pipeline en détail

| Étape | Méthode | Quand ? | Exemple |
|-------|---------|---------|---------|
| **1. No candidates** | Symbolique | Aucun candidat retourné | Terme hors périmètre → NONE |
| **2. Coupe-circuit** | Symbolique | `is_exact_match = True` ET pas de concept plus spécifique | "fibrillation atriale" → FIBRILLATION_ATRIALE |
| **3. Garde-fou** | Symbolique | Le candidat exact est un descripteur (poids=1) mais un diagnostic (poids>1) plus spécifique existe | "Tachycardie" exact → TACHYCARDIE (p=1), mais TV (p=4) en #2 → passe au Juge |
| **4. Juge LLM** | GPT-4o-mini | Tous les autres cas | QCM : "Quel concept correspond à 'tachi supra' ?" → choix structuré |

### Fallback sous-terme

Si le Juge LLM renvoie `NONE`, un **fallback par sous-terme** tente de découper le terme brut en mots et de relancer la recherche sur chaque mot individuellement.

---

## Chapitre 5 — Scoring Ensembliste (Brique 5)

> **Fichier** : `scoring.py`  
> **Modèle** : Purement symbolique (aucun appel LLM)  
> **Latence** : <1ms

### Rôle

Comparer les `ontology_id` trouvés par le pipeline (Briques 2-4) au **Golden Set expert** (barème du professeur) et calculer un **score pondéré**.

```mermaid
flowchart TB
    subgraph Entrées
        F["IDs trouvés<br/>par le pipeline"]
        G["Golden Set<br/>(IDs + rôles)"]
    end

    subgraph "Brique 5 — Scoring Ensembliste"
        direction TB

        P1["Phase 1 — Match EXACT<br/>ID trouvé = ID golden<br/>→ 100% (ou 80% si hypothèse)"]
        P2["Phase 2 — Match HIÉRARCHIQUE<br/>CHILD : étudiant cite un descendant<br/>PARENT : étudiant cite un ancêtre<br/>→ Score dégressif par génération"]
        P3["Phase 3 — IMPLICATIONS<br/>Si concept matché implique un golden<br/>→ 100% auto-validé"]
        P4["Phase 4 — LOGIQUE ENSEMBLISTE<br/>Séparer validants vs descripteurs<br/>vs découvertes additionnelles"]
        CALC["Calcul final<br/>Moyenne des % validants"]
    end

    subgraph Sortie
        SC["📊 Score final %"]
        DET["Détail par validant<br/>+ match_type + explication"]
    end

    F --> P1
    G --> P1
    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> CALC
    CALC --> SC
    CALC --> DET

    style P1 fill:#1b5e20,color:#fff
    style P2 fill:#e65100,color:#fff
    style P3 fill:#1565c0,color:#fff
    style P4 fill:#4a148c,color:#fff
```

### Barème dégressif par génération

L'étudiant reçoit un **score partiel** si son concept est proche mais pas exact dans l'arbre ontologique :

```mermaid
graph TD
    subgraph "Exemple : Golden = Fibrillation atriale"
        FA["🎯 Fibrillation atriale<br/>(golden validant)"]
        AbsP["Absence onde P sinusale<br/>(enfant gen 1)"]
        Irr["Rythme irrégulier<br/>(enfant gen 1)"]
        Trem["Trémulation ligne de base<br/>(enfant gen 1)"]

        TSV["Tachycardie supraventriculaire<br/>(parent gen 1)"]
    end

    FA -->|"implique<br/>(child gen1)"| AbsP
    FA -->|"implique<br/>(child gen1)"| Irr
    FA -->|"implique<br/>(child gen1)"| Trem
    TSV -->|"implique<br/>(parent gen1)"| FA
```

| Distance | Type | Score | Exemple |
|----------|------|-------|---------|
| 0 | **EXACT** | **100%** | "fibrillation atriale" pour golden FA |
| Gen 1 | CHILD ou PARENT | **90%** | "trémulation" pour golden FA |
| Gen 2 | CHILD ou PARENT | **80%** | Sous-signe d'un signe |
| Gen 3 | CHILD ou PARENT | **70%** | Très indirect |
| Gen 4+ | CHILD ou PARENT | **60%** | Plancher |

### Modificateurs

| Statut | Multiplicateur |
|--------|---------------|
| `present` | ×1.0 |
| `hypothese` | ×0.8 |
| `absent` | ×0.0 (ignoré) |

### Logique ensembliste

```mermaid
graph LR
    subgraph "Concepts de l'étudiant (pipeline)"
        S1[FA ✅]
        S2[Tachycardie]
        S3[QRS fins]
    end

    subgraph "Golden Set (barème prof)"
        G1[FA — validant]
        G2[Repol précoce — descripteur]
    end

    subgraph Résultat
        V["✅ Validants matchés<br/>FA → 100%"]
        D["⬜ Descripteurs<br/>Repol précoce → non trouvé"]
        DEC["🟢 Découvertes<br/>Tachycardie, QRS fins<br/>(vrais, hors barème, 0 pts)"]
    end

    S1 --> V
    S2 --> DEC
    S3 --> DEC
    G1 --> V
    G2 --> D
```

> **Score final = Moyenne des % des VALIDANTS uniquement.**  
> Les descripteurs sont informatifs. Les découvertes montrent la qualité de la lecture mais ne rapportent ni ne retirent de points.

---

## Chapitre 6 — Rapport Candidat & Feedback Pédagogique (Brique 6)

> **Fichiers** : `candidate_report.py` + `pedagogical_feedback.py` + `edn_knowledge_base.py`  
> **Modèle feedback** : GPT-4o-mini  
> **Latence** : ~2-3s (avec feedback) ou ~0s (sans)

### Rôle

Orchestrer les Briques 2→5, puis générer un **rapport structuré** pour le candidat avec un **commentaire pédagogique personnalisé** basé sur le cours SFC (Item 231 EDN).

```mermaid
flowchart TB
    subgraph "Brique 6 — Rapport & Feedback"
        direction TB

        ORCH["🎼 Orchestrateur<br/>candidate_report.py<br/>Enchaîne Briques 2→5"]

        subgraph "Rapport structuré"
            S1["🔍 Section 1<br/>Concepts extraits<br/>(terme → ontology_id)"]
            S2["📊 Section 2<br/>Note & détail<br/>(score par validant)"]
            S3["📝 Section 3<br/>Descripteurs<br/>(non notés)"]
            S4["🟢 Section 4<br/>Découvertes<br/>(hors barème)"]
        end

        subgraph "Feedback pédagogique"
            KB["📚 Knowledge Base<br/>edn_knowledge_base.py<br/>30+ entrées SFC"]
            FB["🎓 Feedback GPT<br/>pedagogical_feedback.py<br/>Citations cours SFC"]
            S5["🎓 Section 5<br/>Commentaire pédagogique"]
        end
    end

    ORCH --> S1
    ORCH --> S2
    ORCH --> S3
    ORCH --> S4
    ORCH --> KB
    KB --> FB
    FB --> S5

    style FB fill:#4a148c,color:#fff
    style KB fill:#1565c0,color:#fff
```

### Knowledge Base SFC (Item 231)

La base `edn_knowledge_base.py` contient **30+ entrées** extraites du cours officiel SFC (Chapitre 15 — Item 231, Référentiel CNEC 2e édition) :

| Champ | Description |
|-------|-------------|
| `ontology_ids` | IDs ontologiques liés (pour mapping automatique) |
| `rang_edn` | "A" (indispensable), "B" (important), "C" (complémentaire) |
| `titre_cours` | Titre du chapitre SFC |
| `points_cles` | Liste des points-clés à retenir |
| `pieges_classiques` | Liste des confusions fréquentes |
| `extrait_cours` | Citation directe du cours |

### Génération du feedback

```mermaid
sequenceDiagram
    participant R as CandidateReport
    participant KB as EDN Knowledge Base
    participant GPT as GPT-4o-mini

    R->>KB: Validants manqués/partiels<br/>(golden_ids)
    KB-->>R: Entrées EDN pertinentes<br/>(rang, points-clés, pièges, extraits)

    R->>GPT: Prompt structuré :<br/>1. Performance étudiant<br/>2. Extraits cours SFC<br/>3. Consignes de ton
    GPT-->>R: Commentaire pédagogique<br/>(150-300 mots)

    Note over R: Le feedback cite le cours SFC<br/>et signale les concepts Rang A manqués
```

### Sorties disponibles

| Format | Usage | Fonction |
|--------|-------|----------|
| **Texte** (terminal) | Debug, CLI | `format_report_text(report)` |
| **HTML** (dark theme) | Streamlit, Notebook | `format_report_html(report)` |
| **Dataclass** | Programmatique | `CandidateReport` (13 champs) |

---

## Résultats du Benchmark

Sur le **Golden Set de 15 cas** avec 10 textes étudiants variés :

| Métrique | Valeur |
|----------|--------|
| **Score moyen** | **90.6%** |
| **Cas parfaits (100%)** | 8/15 |
| **Cas les plus durs** | BAV 2 Mobitz 2 (confusion Mobitz 1/2) |
| **Méthodes de résolution** | ~60% coupe-circuit, ~30% juge LLM, ~10% fallback |
| **Latence moyenne** | ~3-5s par cas (avec NER + recherche + juge) |

### Répartition des méthodes de résolution

```mermaid
pie title Méthodes de résolution (Brique 4)
    "⚡ Coupe-circuit (exact match)" : 60
    "🧠 Juge LLM (GPT-4o-mini)" : 30
    "🔄 Fallback sous-terme" : 8
    "❌ No candidates" : 2
```

---

## Stack Technique

```mermaid
graph TB
    subgraph "Intelligence Artificielle"
        GPT4o["GPT-4o<br/>(NER — Brique 2)"]
        GPT4oMini["GPT-4o-mini<br/>(Juge — Brique 4)<br/>(Feedback — Brique 6)"]
        EMB["text-embedding-3-small<br/>(Recherche — Brique 3)"]
    end

    subgraph "Composants Symboliques"
        OWL["Ontologie OWL<br/>~180 concepts ECG"]
        BM25["BM25Okapi<br/>(recherche lexicale)"]
        RRF["Reciprocal Rank Fusion"]
        IMPL["Règles d'implication<br/>(forward + reverse)"]
    end

    subgraph "Infrastructure"
        PY["Python 3.14"]
        NP["NumPy<br/>(matrice embeddings)"]
        PD["Pydantic<br/>(Structured Outputs)"]
        OAI["openai SDK"]
    end

    subgraph "Frontend"
        ST["Streamlit<br/>(app web)"]
        NB["Jupyter Notebook<br/>(démo / benchmark)"]
    end

    GPT4o --> PD
    GPT4oMini --> PD
    EMB --> NP
    OWL --> IMPL
    BM25 --> RRF
```

### Fichiers du pipeline

| Fichier | Brique | Lignes | Rôle |
|---------|--------|--------|------|
| `ontology_index.py` | 1 | ~616 | Indexation ontologie → vecteurs |
| `ner_extractor.py` | 2 | ~203 | Extraction NER GPT-4o |
| `hybrid_search.py` | 3 | ~399 | Recherche Dense + BM25 + RRF |
| `neurosymbolic_judge.py` | 4 | ~424 | Coupe-circuit + Juge LLM |
| `scoring.py` | 5 | ~529 | Scoring hiérarchique dégressif |
| `candidate_report.py` | 6 | ~720 | Orchestration + rapport |
| `pedagogical_feedback.py` | 6 | ~290 | Feedback GPT + cours SFC |
| `edn_knowledge_base.py` | 6 | ~660 | Base de connaissances Item 231 |

---

## Flux de données complet — Exemple

```mermaid
sequenceDiagram
    participant E as 🧑‍🎓 Étudiant
    participant B2 as Brique 2<br/>NER
    participant B3 as Brique 3<br/>Recherche
    participant B4 as Brique 4<br/>Juge
    participant B5 as Brique 5<br/>Scoring
    participant B6 as Brique 6<br/>Rapport

    E->>B2: "fibrillation atriale qrs fins"

    B2->>B2: GPT-4o Structured Outputs
    B2-->>B3: [{terme:"fibrillation atriale", statut:"present"},<br/>{terme:"qrs fins", statut:"present"}]

    loop Pour chaque terme
        B3->>B3: Embedding → cosinus<br/>BM25 → score lexical<br/>RRF fusion
        B3-->>B4: Top-5 candidats
        B4->>B4: Coupe-circuit :<br/>"fibrillation atriale" = exact match
        B4-->>B5: FIBRILLATION_ATRIALE ✅
    end

    B5->>B5: Golden: [FA(validant), Repol(descripteur)]<br/>Found: [FA, QRS_FINS]<br/>FA = EXACT → 100%<br/>Score = 100/1 = 100%
    B5-->>B6: {score:100%, validants:[FA✅], descripteurs:[Repol⬜]}

    B6->>B6: Lookup EDN Knowledge Base<br/>GPT-4o-mini → commentaire
    B6-->>E: 📋 Rapport + 🎓 Feedback SFC
```

---

> *Ce document est auto-généré et reflète l'état du pipeline au 2026-02-28. Oui... enfin j'ai relu hein...*  
> *Diagrammes au format Mermaid — rendus par GitHub, VS Code, ou tout viewer Markdown compatible.*
