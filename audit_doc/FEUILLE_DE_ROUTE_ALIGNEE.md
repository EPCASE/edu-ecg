# 🗺️ Feuille de route alignée — Cible vs état réel (2026-07-29)

> 🔒 **Document figé le 2026-07-30.** Palier 1 et Palier 2 (décrits ci-dessous)
> sont **terminés et mergés sur `main`** (`ecg-online`, commit `e6a7180`).
> Pour la suite du travail (ex-"Palier 3"), se référer désormais à
> `roadmap_scientifique_2026.md` (section "Séquence retenue"), plus précis et
> plus complet. Ne plus mettre à jour ce fichier — cf. `audit_doc/README.md`.

> Complète `ECG_Online_Architecture_Cible_Feuille_de_Route.md` (le document de
> cadrage stratégique) en le **confrontant au code réel** du dépôt
> `ecg-online/`, pour obtenir un plan **actionnable immédiatement**, pas
> seulement une vision cible. Sert de pont entre ce document de cadrage et
> `ecg-online/ROADMAP.md` (suivi d'exécution existant, P0/P1/P2).

---

## 1. Où en est-on vraiment ? (audit rapide du code face à la cible)

| Brique cible (§5/§6 du document de cadrage) | État réel constaté | Écart |
|---|---|---|
| **Scoring déterministe, indépendant du réseau** | ✅ Largement acquis — `scoring_v3.py` + `scoring_thresholds.py` (seuils centralisés depuis Phase A), aucun appel réseau dans le scorer | Faible |
| **Fallback silencieux supprimé (§4.3, Décision B)** | ✅ **Fait le 2026-07-30** (branche `palier2-tracabilite-abstention`) : `abstention.classify()` qualifie chaque réponse `/api/grade` (`SUCCESS`/`LOW_CONFIDENCE`/`FALLBACK_GPT`/`TECHNICAL_ERROR`) + bandeau frontend discret | Reste à **merger sur `main`** |
| **`PipelineResult` versionné, `response_id`/`prediction_id`** | ✅ **Fait** : `response_id`/`prediction_id` (UUID) générés à chaque appel, `pipeline_version` + `ontology_version` exposés dans `/api/health` et `/api/grade` | Reste à **merger sur `main`** |
| **Séparation extraction / linking / scoring / feedback en modules dédiés** | 🟡 Partiellement acquis : `ner_extractor.py`, `hybrid_search.py`, `neurosymbolic_judge.py`, `scoring_v3.py`, `pedagogical_feedback.py` sont déjà des fichiers séparés dans `rag_pipeline/` — mais pas encore organisés sous `core/` avec contrats JSON documentés | Moyen |
| **Ontologie versionnée, hors poids du modèle** | ✅ **Fait le 2026-07-30** : `golden_config.ontology_version()` lit `metadata.version` (`"2.0"`) et l'expose dans les réponses HTTP | 🟡 Pas encore de `CHANGELOG` dédié (non bloquant) |
| **Golden de scoring nettoyé et audité** | ✅ **Fait le 2026-07-29** (Phase E, ROADMAP.md) : 0 conflit réel, audité sur 343 réponses réelles | Reste juste à **committer/pousser** |
| **Collecte PostgreSQL, contrats de données stricts** | ❌ Toujours Google Sheets (`collector.py`) | Fort mais non bloquant à court terme |
| **Tests de régression/adversariaux/ablation** | ✅ **Fait le 2026-07-30** : `tests/test_negation_nonregression.py` (8 tests, négation/exclusions, données golden réelles) + `test_scoring_v3.py`, `test_collector_metrics.py`, `test_pathway_routes.py` — adversarial/ablation restent non couverts (Palier 3) | Faible (négation/contradiction) |
| **États d'abstention (`ABSTAIN`, `HUMAN_REVIEW`, etc.)** | ✅ **Fait le 2026-07-30** : `SUCCESS`/`LOW_CONFIDENCE`/`FALLBACK_GPT`/`TECHNICAL_ERROR` implémentés (`ABSTAIN` réservé, `HUMAN_REVIEW` nécessite une file de curation non existante) | Reste à **merger sur `main`** |
| **Message utilisateur "expérimental/indicatif"** | ✅ Déjà présent (`prealpha-badge`, `prealpha-note` dans `index.html`) | Acquis |
| **Accès systématique au corrigé enseignant après réponse** | ✅ Déjà fait (`result.reference`, révélé après correction) | Acquis |
| **Mécanisme de signalement** | ✅ Déjà fait (`report-modal`, `collect_feedback`) | Acquis |

**Constat global** : le projet est **beaucoup plus avancé que ne le suggère un document de cadrage générique** sur les aspects UX/pédagogie/golden (déjà solides), mais **en retard précisément sur les points d'architecture "recherche"** que le document identifie comme bloquants : traçabilité versionnée, abstention explicite, suppression du fallback silencieux. C'est exactement le bon diagnostic du document (§20, P0) — il ne s'agit pas de tout reconstruire, mais de **combler des trous précis**.

---

## 2. Feuille de route actionnable — 3 paliers

### Palier 1 — Cette semaine : fermer les fronts déjà ouverts

1. **Commit + push Phase E** (golden nettoyé, 0 conflit réel) — ROADMAP.md le note comme seule action restante. *(À faire immédiatement, indépendant du reste.)*
2. **Remplacer le fallback silencieux par une abstention tracée** (Décision B) :
   - Dans `server.py::/api/grade`, quand `neuro_grader.grade_neuro()` échoue, ne pas juste basculer sur `grade()` GPT sans trace : ajouter un champ `resolution` explicite dans la réponse :
     ```json
     "resolution": {
       "status": "FALLBACK_GPT",
       "reason": "neuro_pipeline_error: <détail>",
       "primary_backend": "neuro",
       "used_backend": "gpt"
     }
     ```
   - Coût : quelques lignes dans `server.py`, aucun changement de comportement utilisateur — seulement de la traçabilité. **Premier pas concret et peu risqué vers l'abstention (§4.3).**
3. **Ajouter un `pipeline_version` figé dans chaque réponse** (pas encore un `PipelineResult` complet, juste le champ) — `neuro_grader.py`/`candidate_report.py` ont déjà `PIPELINE_VERSION` en dur dans `make_virtual_students.py` (`"RAG Neurosymbolique v1.1 (C1+C2) — VIRTUAL"`) : le généraliser et l'exposer dans **toute** réponse `/api/grade`, pas seulement les étudiants virtuels.

### Palier 2 — 2 à 4 semaines : traçabilité et abstention réelles

**✅ Fait (2026-07-30, branche `palier2-tracabilite-abstention`, non encore mergée sur `main`) :**

| Semaine | Action | État |
|---|---|---|
| 1 | `response_id`/`prediction_id` (UUID) + états `SUCCESS`/`LOW_CONFIDENCE`/`FALLBACK_GPT`/`TECHNICAL_ERROR` (`abstention.py`) | ✅ |
| 1 | `docs/DATA_DICTIONARY.md` (contrat JSON `/api/grade`) | ✅ |
| 2 | Bandeau frontend `resolution` (`app.js::buildResolutionBanner`, `style.css`) — discret, invisible sur `SUCCESS` | ✅ |
| 3 | `ontology_version` exposée (`golden_config.ontology_version()`, `/api/health` + `/api/grade` + colonne collecte) | ✅ |
| 4 | Tests de non-régression négation/exclusions (`tests/test_negation_nonregression.py`, 8 tests, données réelles golden + `annotation_expert`, zéro cas inventé) | ✅ |

Reste à faire avant de merger sur `main` : relecture manuelle du diff complet
de la branche + test end-to-end local (déjà fait pour SUCCESS/LOW_CONFIDENCE
au Palier 1 ; à refaire pour FALLBACK_GPT/TECHNICAL_ERROR visuellement) puis
`git merge palier2-tracabilite-abstention` (ou PR) sur `main`.

Reprend le "Plan des six prochaines semaines" (§21 du document de cadrage), mais **réordonné** pour partir de l'existant réel plutôt que d'une page blanche :

| Semaine | Action | Fichier(s) concernés | Nouveau ou extension ? |
|---|---|---|---|
| 1 | `response_id`/`prediction_id` (UUID) générés à chaque `/api/grade`, renvoyés au client, stockés dans `collector.collect_answer` | `server.py`, `collector.py` | Extension |
| 1 | États explicites `SUCCESS` / `LOW_CONFIDENCE` / `ABSTAIN` / `TECHNICAL_ERROR` (`HUMAN_REVIEW` plus tard, nécessite file de curation) | `neuro_grader.py`, `server.py` | Nouveau (petit) |
| 2 | Isoler un module `core/abstention.py` : règles simples d'abord (aucun concept résolu → `ABSTAIN`; erreur technique → `TECHNICAL_ERROR`; confiance basse → `LOW_CONFIDENCE` avec avertissement affiché) | nouveau fichier | Nouveau |
| 2 | Basculer le "cr-vote" (validation de concepts, déjà existant) pour aussi taguer les cas `LOW_CONFIDENCE`/`ABSTAIN` côté frontend | `app.js`, `style.css` | Extension |
| 3 | Versionner l'ontologie (`ontology_version` explicite dans `ontology_v2.json` + exposé dans la réponse) | `rag_pipeline/data/ontology_v2.json`, `neuro_grader.py` | Extension |
| 3 | Documenter le contrat JSON de sortie (`docs/DATA_DICTIONARY.md` minimal, pas besoin de l'arborescence complète §7 tout de suite) | nouveau doc | Nouveau (léger) |
| 4 | Ajouter des tests de non-régression sur la négation/contradictions (§16.1 du doc cadrage) — cible réaliste : 10-15 cas, pas la couverture complète décrite | `rag_pipeline/tests/` | Extension |

### Palier 3 — Trimestre : aligner avec l'ambition scientifique du document cadrage

Ne pas attaquer avant d'avoir fait le Palier 2 — sinon on retombe dans le risque
identifié §25.1 du document ("construire trop tôt"). Une fois le Palier 2 acquis :

- Étendre le golden de scoring à 2+ experts (P1.5, déjà noté dans `ROADMAP.md`, c'est la suite logique une fois Phase E poussée).
- Étudier la migration PostgreSQL (§12.4) — mais seulement si le volume de collecte le justifie déjà (vérifier le nombre de réponses actuelles avant d'investir ce chantier).
- Baselines comparatives (règles seules / LLM direct / pipeline actuel) pour les analyses d'ablation (§15) — utilisable directement avec `make_virtual_students.py` qui a déjà l'infrastructure de génération de réponses contrôlées.
- Manuel d'annotation (§13) — utile uniquement si l'extension du golden (P1.5) démarre.

---

## 3. Ce qu'il ne faut PAS faire maintenant (anti-scope créep)

Le document de cadrage est ambitieux (arborescence `research/`, `core/`,
`migrations/`, Docker, PostgreSQL, 5 modèles comparés) — appliquer cette
arborescence cible **telle quelle, maintenant**, serait une régression de
productivité : le code actuel fonctionne, est déployé (Scalingo), et a une
dette **ciblée et connue** (`ROADMAP.md` P0-P2). Éviter :

- ❌ Réorganiser tout `rag_pipeline/` en `core/` sous-dossiers avant d'avoir
  besoin de cette granularité (aucun signal actuel qu'on va multiplier les
  extracteurs/rerankers).
- ❌ Migrer vers PostgreSQL avant d'avoir mesuré que Google Sheets est
  réellement un goulot (volume, concurrence d'écriture).
- ❌ Lancer un fine-tuning ou un encodeur clinique dédié (§10) — déjà tranché
  par `AUDIT_TECHNOLOGIQUE_2026.md` : pas urgent, dataset prêt mais gelé tant
  que le gap constaté ne le justifie pas.
- ❌ Écrire l'article scientifique (§18-19) avant d'avoir un corpus gelé et
  un golden à 2+ experts (pas encore le cas, P1.5 non démarré).

---

## 4. Synthèse — 5 actions concrètes pour démarrer aujourd'hui

1. `git add -A && git commit -m "golden Phase E" && git push` (Phase E, déjà prête).
2. Ajouter le champ `resolution` (fallback tracé) dans `/api/grade`.
3. Générer et renvoyer `response_id`/`prediction_id` (UUID) dans chaque réponse.
4. Exposer `pipeline_version`/`ontology_version` dans chaque réponse (valeurs
   en dur pour commencer, pas besoin d'un système de version complet).
5. Créer `docs/DATA_DICTIONARY.md` minimal documentant le contrat JSON actuel
   de `/api/grade` (base pour toute évolution future, coût faible).

Ces 5 actions ne changent **aucun comportement utilisateur visible** et
préparent directement les Paliers 2/3 — cohérent avec la Décision I du
document cadrage ("déployer l'alpha de manière encadrée pendant la
fiabilisation, et non après").
