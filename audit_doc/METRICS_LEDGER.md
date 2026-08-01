# 📊 Registre des métriques — source de vérité unique

> **P0.3** (`audit_doc/roadmap_scientifique_2026.md` §P0.3 / `ecg-online/ROADMAP.md` P0.3) :
> chaque métrique citée dans le projet (README, audits, futurs manuscrits) doit
> pointer vers **cette table**, ou vers le rapport généré
> `ecg-online/data/baseline_report.json` (cf. P0.1), plutôt que d'être
> recopiée à la main dans plusieurs documents.
>
> **Règle** : toute nouvelle métrique ajoutée ici DOIT préciser : tâche évaluée,
> corpus, split, n, version du pipeline, version de l'ontologie, définition
> exacte, date d'exécution, intervalle de confiance si pertinent (cf. critère
> de sortie P0.3).

---

## 1. Extraction (NER + résolution ontologique)

| Champ | Valeur |
|---|---|
| **Tâche** | Extraction de concepts ECG depuis un texte libre d'étudiant, comparée au golden d'extraction humain |
| **Corpus / split** | 100 réponses réelles annotées (18/20 double-annotées) |
| **n (confusion globale)** | TP=547, FP=58, FN=66 |
| **Précision** | **90.4 %** |
| **Rappel** | **89.2 %** |
| **F1** | **89.8 %** |
| **Version du pipeline** | `neuro-v1.1` |
| **Version de l'ontologie** | `2.0` (345 concepts) |
| **Définition** | Précision/rappel/F1 micro sur l'ensemble des concepts extraits vs golden, cf. `scripts/compute_extraction_metrics.py` |
| **Date d'exécution** | 2026-07-29 |
| **Source canonique** | `ecg-online/data/extraction_metrics_report.json` (champ `confusion`) |
| **Régénérable via** | `python scripts/generate_baseline_report.py` (champ `extraction_metrics`) |
| **Doc de référence détaillée** | `ecg-online/GOLDEN_EXTRACTION.md` |

### Précision par méthode d'extraction (ablation)

| Méthode | TP | FP | Précision |
|---|---:|---:|---:|
| coupe_circuit | 466 | 17 | 96.5 % |
| juge_llm | 57 | 27 | 67.9 % |
| pattern_inference | 0 | 3 | 0.0 % |
| fallback_subterm | 6 | 3 | 66.7 % |
| lexical_backstop | 18 | 8 | 69.2 % |

### Accord inter-annotateur (fiabilité du golden lui-même)

| Métrique | Valeur |
|---|---|
| Jaccard moyen | 97.7 % |
| F1 moyen | 98.7 % |
| Items double-annotés | 18 |
| Accord parfait | 16/18 |
| **Note** | Le Kappa de Cohen classique (-0.02) est **peu informatif ici** (univers de concepts restreint par item, cf. `kappa_caveat` dans le rapport JSON) — préférer Jaccard/F1. |

---

## 2. Robustesse du coupe-circuit symbolique

| Champ | Valeur |
|---|---|
| **Tâche** | Part des résolutions de concepts faites sans appel LLM (match exact normalisé) |
| **Résultat** | ~74 % des résolutions (483/650), précision 96.5 % |
| **Statut historique** | ⚠️ Corrige l'ancienne estimation "~42 %" citée dans certaines versions antérieures d'`ARCHITECTURE.md` (corrigé le 2026-07-29, 5 occurrences) |
| **Source canonique** | `audit_doc/AUDIT.md` §4bis |
| **Date de mesure** | 2026-07-29 |

---

## 3. Golden de scoring / audit ontologique

| Champ | Valeur |
|---|---|
| **Tâche** | Audit de cohérence du mapping `cases_golden.json` / `scoring_config.json` vs ontologie |
| **Résultat** | 0 bloquant, 21 avertissements (doublons de concepts inoffensifs) |
| **Corpus** | 75 cas |
| **Script** | `ecg-online/scripts/audit_golden.py` |
| **Statut golden de scoring** | ⚠️ Toujours mono-expert / étroit (souvent 1 concept attendu par cas) — validité statistique faible, cf. `AUDIT.md` risque R1. Distinct du golden d'extraction (§1), qui lui est résolu. |

---

## 4. Suite de tests de non-régression

| Champ | Valeur |
|---|---|
| **Tests** | 18/18 passants |
| **Fichiers** | `ecg-online/tests/test_collector_metrics.py`, `test_negation_nonregression.py`, `test_pathway_routes.py` |
| **Commande** | `python -m unittest discover -s tests` |

---

## 5. Métriques historiques marquées obsolètes / à ne plus citer

| Chiffre | Statut | Remplacé par |
|---|---|---|
| "Taux d'hallucination 63,7 %" | 🔴 **Caduc** — surinterprétation méthodologique (comparait tous les concepts extraits au golden de scoring, trop étroit) | P=90.4 % / R=89.2 % (§1 ci-dessus) |
| "42 % coupe-circuit" | 🔴 **Obsolète** — mesure imprécise | ~74 % (§2 ci-dessus) |
| "Score moyen ~92 % (README racine)" | ⚠️ **Métrique différente, non datée** — score pédagogique moyen étudiant (15 cas × 7 étudiants), pas un F1 d'extraction. À ne pas confondre avec §1. Source exacte non retrouvée / à recalculer si besoin. | — (cf. note ajoutée dans le README racine) |
| "RAG-onto 62,4 %" / "CSV réel 85,1 % & 60,2 %" | 🔴 **Obsolètes** — chiffres d'un ancien CSV (`ECG evaluation/results/table3_metrics_summary.csv`), périmètre différent, non recalculés depuis | P=90.4 % / R=89.2 % (§1 ci-dessus) pour ce qui concerne l'extraction |

---

## Comment ajouter une nouvelle métrique

1. Si elle est produite par `scripts/generate_baseline_report.py`, il suffit de régénérer
   `data/baseline_report.json` — pas besoin de dupliquer les chiffres ici à la main.
2. Sinon, ajouter une section ci-dessus avec **tous** les champs de la règle en tête de
   ce document (tâche, corpus, split, n, pipeline_version, ontology_version, définition,
   date, IC si pertinent).
3. Ne jamais citer un chiffre de métrique dans un README/audit sans lien vers ce fichier
   ou vers `baseline_report.json`.
