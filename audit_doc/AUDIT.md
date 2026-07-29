# 🔬 AUDIT — Edu-ECG : Pipeline RAG Neurosymbolique

> 🔒 **Figé le 2026-07-30** — document historique (chiffres/diagnostic
> d'origine). Pour la suite du travail, voir `roadmap_scientifique_2026.md`
> (document actif) et `audit_doc/README.md` (index). Les chiffres ici servent
> de base à P0.3 (source de vérité unique des métriques) mais ne doivent plus
> être cités comme état courant sans revérification.

> **Périmètre** : `ECG lecture`, `RAG ontologique`, `ECG collector`, `ECG evaluation`
> **Repo** : [EPCASE/edu-ecg](https://github.com/EPCASE/edu-ecg) — branche `RAGontologiqueV2`
> **Date** : Juillet 2026
> **Objectif** : évaluer pertinence, choix techniques, perspectives IA, et surtout **robustesse des résultats**.

---

## 0. Note de méthode (honnêteté intellectuelle)

Ce document corrige une **surinterprétation** de la première passe d'audit.
Le chiffre « **taux d'hallucination 63,7 %** » (issu de `ECG evaluation/results/table3_metrics_summary.csv`)
**ne doit pas être lu comme « 2 concepts sur 3 sont des inventions »**. Il compare *tous*
les concepts extraits au **golden set de scoring**, qui ne liste que 1 à 3 concepts « qui comptent »
par cas. Les concepts cliniquement **vrais mais non listés** (ex. « QRS fins », « PR normal »
sur un ECG normal) sont donc comptés à tort comme faux positifs.

➡️ **La vraie conclusion n'est pas « le pipeline hallucine beaucoup », mais
« on est aujourd'hui incapable de distinguer une vraie erreur d'une bonne observation non listée ».**
C'est le problème central de robustesse, et sa solution est méthodologique (cf. §4).

**Mise à jour 2026-07-29** : le golden d'extraction proposé au §4 a été **construit et exploité**
(100 réponses réelles annotées, cf. `ECG lecture/ecg-online/GOLDEN_EXTRACTION.md`). Les vrais
chiffres de précision/rappel de l'extraction sont maintenant disponibles — cf. §4bis. Le chiffre
« 63,7 % d'hallucination » ci-dessus est donc officiellement **caduc et remplacé**.

---

## 1. Synthèse exécutive

| Dimension | Note | Commentaire |
|-----------|:----:|-------------|
| Pertinence du besoin | 🟢 9/10 | Vrai vide : évaluation de texte libre ECG, ancrée EDN Item 231 |
| Architecture | 🟢 8/10 | Neurosymbolique rigoureux, séparation symbolique/neuronal, garde-fous réels |
| Choix techniques | 🟡 6/10 | Bonnes briques ; dette (4 workspaces, ~50 scripts jetables), tout-OpenAI |
| **Robustesse des résultats** | � **7/10** | **Golden d'extraction créé et exploité (F1 89.8 %) ; golden de scoring toujours mono-expert/étroit (R1)** |
| Reproductibilité scientifique | 🟡 5/10 | Scoring déterministe ✅, mais chiffres incohérents entre docs & dépendance API |
| Maintenabilité | 🟡 5/10 | Duplication `RAG ontologique` ↔ `ECG lecture/rag_pipeline` |

**Verdict** : colonne vertébrale conceptuelle **solide**, répondant à un vrai besoin.
Le point historiquement bloquant — l'absence de *golden d'extraction* — est **résolu** (§4bis) :
l'extraction (NER + résolution ontologique) affiche désormais une précision de 90.4 % et un rappel
de 89.2 % mesurés sur 100 réponses réelles annotées, avec un accord inter-annotateur de 98.7 % (F1)
validant la fiabilité du golden lui-même. Le golden **de scoring** (R1) reste, lui, à élargir.

---

## 2. Pertinence du projet

- **Besoin réel** : aucune solution n'évalue automatiquement un **texte libre** d'interprétation ECG
  en le comparant à une correction experte structurée, avec feedback ancré dans le cours (SFC, Item 231).
- **Positionnement juste** vs QCM (réducteur), correction manuelle (non scalable), LLM direct (non
  reproductible, non traçable), matching symbolique pur (intolérant aux fautes).
- **Réserve** : la valeur pédagogique dépend de l'hypothèse « le score reflète la qualité clinique ».
  Cette hypothèse **n'est pas encore démontrée** (cf. §3-4).

---

## 3. Le cœur du sujet : la métrique de score

### 3.1 Ce que mesure réellement le score actuel

Le `scoring_v3` calcule, pour chaque concept **attendu** (golden), s'il est retrouvé
(exact / enfant / parent / requires / qualifier / support), puis fait la **moyenne sur les concepts attendus** :

```
score_pct = Σ score(concept_attendu_i) / N_attendus × 100
```

➡️ C'est un **rappel pondéré cliniquement**. Il répond à « les bons concepts sont-ils présents ? »
Il **n'intègre pas** les concepts en trop. Preuve figée par les tests
(`tests/test_scoring_v3.py::TestCasLimites::test_concepts_hors_golden_sont_ignores`).

### 3.2 Ce qui fonctionne déjà bien (crédit partiel ontologique) ✅

Vérifié par exécution (cf. `tests/test_scoring_v3.py`) :

| Situation | Score | Interprétation |
|-----------|:-----:|----------------|
| Concept exact | 100 % | match direct |
| **Enfant** trouvé (plus précis) | 100 % | `BBD complet` crédite `BBD` |
| **Parent direct** (plus vague) | 66,7 % | `BBD` crédite partiellement `BBD complet` |
| 1/4 `requires` satisfait | 25 % | `Rythme sinusal` → `ECG normal` |
| Concept **exclu** présent | 0 % | garde-fou : `FA` annule `ECG normal` |

➡️ **La demande « les attendus du correcteur donnent des points, et les classes qui en dépendent
donnent des points partiels » est DÉJÀ implémentée** et fonctionne. C'est une force.

### 3.3 Ce qui manque (et pourquoi c'est le vrai problème)

Le scoring ne traite pas les **concepts hors-golden**. Deux cas très différents s'y cachent :

1. Concept **vrai mais non listé** par le correcteur (ex. « QRS fins » sur ECG normal) → **inoffensif**.
2. Concept **cliniquement faux** (ex. « TV » sur un ECG normal) → **dangereux**, non pénalisé
   *sauf* s'il tombe dans un `excludes` de l'ontologie.

Aujourd'hui, **on ne peut pas séparer 1 et 2 automatiquement** : d'où l'impossibilité de mesurer une
vraie précision. C'est exactement ce que résout la proposition du §4.

### 3.4 Limite spécifique repérée (négation trop généreuse) ⚠️

`absent("trouble de repolarisation")` se convertit en `ECG_NORMAL`
(via `build_negation_map`). Conséquence : un étudiant écrivant **uniquement**
« pas de trouble de repolarisation » obtient **100 %** sur un cas ECG normal.
Figé par `tests/test_scoring_v3.py::TestNegation::test_absent_trouble_repol_se_convertit`.
➡️ À revoir : une négation isolée ne devrait pas valider un diagnostic composite entier.

---

## 4. 🎯 Recommandation centrale : le « golden d'extraction » (panel annoté)

C'est la meilleure idée pour débloquer la robustesse. Il faut **deux golden sets de natures différentes** :

| | Golden **de scoring** (existant) | Golden **d'extraction** (à créer) |
|---|---|---|
| Contenu | Concepts qui comptent pour la **note** (1-3/cas) | **Tous** les concepts réellement présents dans un texte |
| Sert à | Noter l'étudiant | **Mesurer la lecture du texte par le pipeline** |
| Répond à | « Bon diagnostic ? » | « NER + mapping corrects, sans invention ? » |
| Statut | ✅ `ECG collector/corrections/golden.json` | ❌ **manquant** |

### Protocole proposé (léger, rentable)

1. Sélectionner **~50 réponses étudiantes déjà collectées** (mélange court/long, cas variés).
2. Pour chaque réponse, un expert **surligne/annote chaque concept réellement présent**
   et son statut (present / absent / hypothèse) — indépendamment de la note.
3. Sur un sous-ensemble (~15), **double annotation** → **Kappa de Cohen** (accord inter-annotateur).
4. Rejouer le pipeline et calculer **précision / rappel / F1 réels de l'extraction**
   (concepts pipeline vs concepts annotés), enfin **justes**.

➡️ **C'est le préalable P0.** Sans lui, la refonte de métrique (option B) serait construite sur du sable.

### Refonte de métrique (à faire APRÈS le golden d'extraction)

Deux notes séparées plutôt qu'un chiffre unique :
- **Note d'exactitude** = le scoring V3 actuel (rappel pondéré). Déjà bon.
- **Note de fiabilité** = pénalité des concepts **faux** (contredits par `excludes` **ou** absents du
  golden d'extraction du cas), pondérée par **gravité clinique** (poids 2-5 déjà présents dans l'ontologie).
  Un faux « TV » coûte plus qu'un faux « bradycardie ».

---

## 4bis. ✅ Résultats du golden d'extraction (2026-07-29)

Le protocole du §4 a été **exécuté** (méthodologie complète et reproductible dans
`ECG lecture/ecg-online/GOLDEN_EXTRACTION.md`), avec un échantillon plus large que prévu
initialement (100 réponses réelles au lieu de ~50, sur 47 des 75 cas), pour une marge
statistique meilleure. Script de calcul : `ecg-online/scripts/compute_extraction_metrics.py`.

**Chiffres réels de l'extraction** (100/100 items annotés, `data/extraction_metrics_report.json`) :

| | TP | FP | FN | Précision | Rappel | F1 |
|---|---:|---:|---:|:---:|:---:|:---:|
| **Global** | 547 | 58 | 66 | **90.4 %** | **89.2 %** | **89.8 %** |

**Précision par méthode d'extraction** (ablation par brique, répond à P1.8) :

| Méthode | n | Précision |
|---|---:|:---:|
| `coupe_circuit` (déterministe) | 483 | **96.5 %** |
| `juge_llm` | 84 | 67.9 % |
| `lexical_backstop` | 26 | 69.2 % |
| `fallback_subterm` | 9 | 66.7 % |
| `pattern_inference` | 3 | 0.0 % (échantillon trop petit pour conclure) |

➡️ Le coupe-circuit lexical (méthode dominante, 483/650 résolutions) est très fiable. Les
briques de secours (`juge_llm` et fallbacks) concentrent l'essentiel des faux positifs — 3x moins
fiables que le coupe-circuit — cohérent avec leur rôle sur les cas ambigus, mais identifiées comme
cible prioritaire d'amélioration (R5 ci-dessous, désormais mesuré et non plus supposé).

**Fiabilité du golden lui-même** (18/20 items en double annotation complétés) : accord
inter-annotateur **98.7 % (F1)**, **97.7 % (Jaccard)**, accord parfait sur 16/18 items — le golden
est jugé fiable. Note méthodologique : le Kappa de Cohen classique s'est avéré **inadapté** dans ce
contexte (univers de concepts ouvert → biais connu qui écrase artificiellement le score malgré un
accord quasi-parfait) ; Jaccard/F1 par item est utilisé comme métrique de référence à la place
(documenté dans le rapport JSON).

**Conséquence directe** : le chiffre historique « 63,7 % d'hallucination » (§0) est **invalidé** et
remplacé par une mesure méthodologiquement saine : **~10 % des extractions du pipeline sont de
vrais faux positifs**, très majoritairement concentrés dans les briques non-déterministes.

**Reste à faire** (cf. §4 « refonte de métrique », maintenant déblocable) : recalculer la métrique
pédagogique (note exactitude + note fiabilité pondérée gravité) en s'appuyant sur ces chiffres, et
étendre le golden **de scoring** (R1, toujours en attente, périmètre différent du golden d'extraction).

---

## 5. Robustesse — autres risques

| Réf | Risque | Détail | Priorité |
|-----|--------|--------|:--------:|
| R1 | **Golden de scoring mono-expert & étroit** | 15 cas, 1 expert, souvent 1 concept attendu/cas → validité statistique faible (≠ golden d'extraction, résolu cf. §4bis) | 🔴 P0/P1 |
| R2 | **Chiffres incohérents entre docs** | README ~92 % / RAG-onto 62,4 % / ARCHITECTURE 42 % coupe-circuit / CSV réel 85,1 % & 60,2 % ; **chiffre "63,7% hallucination" désormais caduc, remplacé par P=90.4%/R=89.2% (§4bis)** | 🔴 P0 |
| R3 | **Pas de tests automatisés (avant cet audit)** | Désormais `tests/test_scoring_v3.py` (18 tests) ; reste à couvrir semantic_layer & négation | 🟡 P1 |
| R4 | **Juge LLM non validé indépendamment** | `Ontology mapping accuracy` du CSV = un **compte** (1620), pas un taux | 🟡 P1 |
| R5 | ✅ **Erreurs non tracées par brique** | *Résolu* — cf. §4bis : précision par méthode mesurée (coupe_circuit 96.5% vs juge_llm/fallbacks ~67-69%) | 🟡 P1 |
| R6 | **Dépendance totale OpenAI** | NER + juge + embeddings + feedback. Modèles dépréciables → non-repro à 2 ans | 🟡 P1 |
| R7 | **Négation trop généreuse** | cf. §3.4 (`absent(trouble_repol)` → `ECG_NORMAL` = 100 %) | 🟡 P1 |

---

## 6. Choix techniques — analyse

### Points forts ✅
- **Séparation symbolique/neuronal** : le LLM ne voit jamais l'ontologie complète, ne peut pas
  inventer d'ID (validation post-LLM → forçage `NONE`).
- **Structured Outputs (Pydantic)** : élimine les erreurs de parsing LLM.
- **Recherche hybride Dense + BM25 + RRF** : BM25 rattrape les acronymes, le dense les synonymes/fautes.
- **Coupe-circuit déterministe** (~60 % des résolutions) : rapidité, coût, reproductibilité.
- **Scoring symbolique déterministe** : 100 % reproductible (prouvé par test).

### Points faibles ⚠️
- **NumPy en RAM / `argmax`** : OK pour 658 docs, ne scale pas au-delà de ~10k (→ FAISS/Qdrant si besoin).
- **Flexion FR par heuristique** (`_deflect` retire `-s/-x/-e`) : fragile, faux positifs possibles
  (→ lemmatiseur `spaCy fr_core_news`).
- **4 workspaces désynchronisés** : `RAG ontologique` duplique `ECG lecture/rag_pipeline` (sync manuelle).
- **~50 scripts `_debug_*/_test_*`** à la racine : dette, bruit, pas de valeur pérenne.

---

## 7. Lien avec les développements récents de l'IA

| Levier | Apport pour la **robustesse** | Effort |
|--------|-------------------------------|:------:|
| **LLM-as-Judge encadré** (panel multi-prompts + vote, auto-consistency) | Réduit la variance sur les ~35 % de cas jugés par LLM | Moyen |
| **Exploiter `confiance`** (déjà renvoyée par le juge, 0-100) | Seuil → `NONE`/revue humaine sous un seuil ; réduit les FP | Faible |
| **Embeddings médicaux FR** (BioLORD, CamemBERT-bio, E5 multilingual, **local**) | Meilleur rappel + supprime coût/dépendance OpenAI sur l'embedding | Moyen |
| **Modèles locaux pour le juge** (Mistral/Llama/Qwen via Ollama) | Résultats **gelables/rejouables** pour publication | Moyen |
| **Raisonneur OWL** (HermiT/ELK via `owlready2`) | Valide la cohérence logique de l'ontologie (`excludes` symétriques, pas de cycle) | Faible |
| **Juge multimodal** (vision sur l'image ECG) | Permettrait de pénaliser une affirmation incompatible avec le **tracé réel** | Élevé |

### Sur SNOMED CT (clarification demandée)
SNOMED CT est un **dictionnaire médical mondial** attribuant un code universel à chaque concept
(« fibrillation atriale » = `49436004`). **Il n'améliore ni la robustesse, ni les scores, ni l'extraction.**
Son seul intérêt, **plus tard** : interopérabilité (autre outil/hôpital) et crédibilité publication.
➡️ **Déclassé en « optionnel / bonus »**. Ce n'est pas une priorité pour ton objectif.

---

## 8. Feuille de route priorisée (objectif robustesse)

### 🔴 P0 — Bloquant (avant toute conclusion/publication)
1. ✅ **Créer le golden d'extraction** — *fait* : 100 réponses annotées, 18/20 double-annotation
   complétées, cf. `ECG lecture/ecg-online/GOLDEN_EXTRACTION.md` et §4bis.
2. ✅ **Recalculer P/R/F1 réels** de l'extraction contre ce golden — *fait* : Précision 90.4 %,
   Rappel 89.2 %, F1 89.8 % (`ecg-online/data/extraction_metrics_report.json`) — cf. §4bis.
3. **Unifier les chiffres** : une source de vérité unique, générée automatiquement, versionnée
   (le chiffre "63,7% hallucination" doit être retiré/annoté comme caduc partout où il apparaît
   encore, ex. README, ARCHITECTURE.md).
4. ✅ **Tests de non-régression du scoring** — *fait* : `rag_pipeline/tests/test_scoring_v3.py` (18 tests).

### 🟡 P1 — Important (validité scientifique)
5. **Étendre le golden de scoring** (R1, périmètre différent du golden d'extraction) : 40-50 cas,
   ≥2 experts, plusieurs validants/cas.
6. **Refondre la métrique** : note exactitude + note fiabilité (pénalité FP pondérée gravité) — cf. §4,
   maintenant déblocable grâce aux chiffres du §4bis.
7. **Corriger la négation trop généreuse** (§3.4).
8. ✅ **Ablation par brique** (NER/Search/Juge) — *fait*, cf. §4bis (précision par méthode) ; reste
   la validation humaine d'un échantillon des décisions du juge LLM (non couvert par le golden actuel).
9. **Étendre les tests** à `semantic_layer` et à la conversion des négations.

### 🟢 P2 — Consolidation
10. **Monorepo** : fusionner les 4 dossiers, supprimer la duplication, packager `rag_pipeline`,
    nettoyer les scripts `_*.py`.
11. **Fallback local** : embeddings sentence-transformers + juge Mistral/Llama (reproductibilité).
12. **Panel multi-juges** + exploitation du score de confiance.
13. (Optionnel) Mapping SNOMED + raisonneur OWL.

---

## 9. Livrables de cet audit

| Livrable | Emplacement | Statut |
|----------|-------------|:------:|
| Ce document | `ECG lecture/AUDIT.md` | ✅ |
| Tests de non-régression scoring | `ECG lecture/rag_pipeline/tests/test_scoring_v3.py` | ✅ 18 tests |
| Config pytest | `ECG lecture/rag_pipeline/tests/conftest.py` | ✅ |

**Lancer les tests :**
```powershell
cd "ECG lecture"
.venv\Scripts\python.exe -m pytest rag_pipeline/tests/ -v
```

---

*Audit réalisé le 2026-07-03. Les tests figent le comportement actuel du scoring afin de sécuriser
les évolutions futures (notamment la refonte de la métrique).*
