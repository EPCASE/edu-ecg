# 🔬 Audit technologique — Possibilités et limites (2026)

> Objet : répondre, **avec des chiffres mesurés sur ce projet** (pas des généralités),
> aux 5 questions posées : fine-tuning, passage déterministe, autonomie locale,
> intégration ontologie↔LLM, et validité du choix neurosymbolique.
>
> Sources primaires : `ECG evaluation/goldenset_extraction/RAPPORT_METRIQUES.md`
> (1601 lignes, §1→§26), `LLM_LOCAL_2026.md` (panorama 2026), `_finetune/README.md`,
> `ARCHITECTURE.md` §2.2 (positionnement état de l'art).

---

## 1. Peut-on fine-tuner un modèle ?

**Oui, c'est prêt mais pas encore lancé — et ce n'est pas (encore) nécessaire.**

- Un dataset de fine-tuning est **déjà construit** (`_finetune/` : `dataset_all.jsonl`,
  `folds/`, `test_heldout.jsonl`, `stats.json`) : 342 rapports "professeur" (GPT-4o
  réel), 2119 entités, split objectif (12 codes hold-out = échantillons du pilote
  local pour comparaison directe, 5-fold sur les 60 restants).
- **Ce que le modèle apprendrait** : compétence d'extraction (négation, expansion
  d'abréviations, traduction de mesures, méthode LEGO) — **PAS** la liste de
  concepts de l'ontologie ni le mapping terme→`ontology_id` (ça reste en aval,
  RAG + juge). Conséquence clé : **un changement d'ontologie n'obsolète jamais
  le modèle fine-tuné** — le couplage est volontairement faible.
- **Preuve empirique que ce n'est pas encore urgent** (§21, expérience NER seule) :
  `gemma3:4b` (généraliste) et `medgemma:4b` (spécialisé médical) obtiennent le
  **même score exact** : F1=0.685, κ=0.402. Le fine-tuning médical **n'apporte
  rien** ici — la compétence qui manque est la **discipline de format/extraction**,
  pas la connaissance médicale (déjà couverte par le RAG + l'ontologie).
- **Le vrai gisement de gain** est donc un fine-tuning **d'extraction** (pas
  médical), sur le format LEGO exact attendu — c'est précisément ce que le
  dataset préparé cible.
- **Décision recommandée** : suivre le critère déjà écrit dans `LLM_LOCAL_2026.md`
  §6 — zero-shot + grammaire contrainte **d'abord** ; QLoRA (Unsloth, 24 Go
  suffisent) **seulement si** l'écart résiduel vs étalon GPT-4o le justifie après
  le banc d'essai. Ce critère a déjà été rempli une fois par Qwen2.5 14B (§19,
  voir Q3) **sans aucun fine-tuning** — donc, en l'état, **pas de fine-tuning
  urgent**, juste un plan prêt à activer si un modèle plus petit (4-8B) ne passe
  pas le seuil.

## 2. Faut-il garder le passage déterministe ?

**Oui pour l'essentiel, mais avec un tri chirurgical — pas un "tout ou rien".**

Le "passage déterministe" recouvre en réalité 3 mécanismes distincts, mesurés
séparément (§25) :

| Mécanisme | Rôle | Verdict mesuré |
|---|---|---|
| **Coupe-circuit symbolique** | Bypass LLM sur match exact normalisé | ✅ **Garder** — 74% des résolutions (483/650), gratuit, instantané, précision 96.5% (`AUDIT.md` §4bis). Absorbe le risque : même un LLM local plus faible n'affecte que les 26% restants (§19.3). |
| **N1 — négation lue par le LLM** | Détection de négation généraliste | ✅ **Garder** — mécanisme qui généralise, contrairement à une regex figée. |
| **N3 — axiome déclaratif ontologie** | Négation encodée comme relation dans l'ontologie | ✅ **Garder** — gelé pour mesure, mais déclaratif (dérivé de l'ontologie, pas hardcodé). |
| **N2 — heuristique `convert_absents_to_positive`** | Conversion codée en dur d'un pattern "absent de X" | ❌ **Retirer** — mesuré **net-négatif** : 4 TP vs 12 FP (§25). C'est une "rustine" qui coûte plus qu'elle ne rapporte. |

**Conclusion** : le déterminisme n'est pas le problème — au contraire, c'est ce
qui rend le pipeline **traçable, gratuit sur 74% des cas, et robuste au choix
du LLM**. Le seul geste à faire est de retirer la règle N2 (déjà identifiée et
quantifiée comme nuisible), pas de démanteler le coupe-circuit ni les axiomes
déclaratifs.

## 3. Une solution locale autonome est-elle possible ?

**Oui — et le critère de succès (« V1 ») a déjà été atteint une fois, sans fine-tuning.**

- **Pilote exécuté** (§19) : remplacement complet NER+Juge par des modèles locaux.
  - **Qwen2.5 14B** : F1=0.800 vs étalon GPT-4o 0.821 → écart de **-0.020 F1
    seulement**. Cela remplit le critère V1 explicite (« étalon − 2 pts F1 sans
    fine-tuning » → geler, autonomie atteinte).
  - Gemma3 4B et Qwen2.5 7B : scores nettement inférieurs (trop petits pour la
    tâche telle quelle).
- **Décodage contraint sur le juge** (§20.1) : gain gratuit mesuré, **+0.011 F1 /
  +0.025 κ** (0.800→0.811 F1, 0.612→0.637 κ), avec une spécificité qui **dépasse**
  même GPT-4o (0.786 vs 0.738) — la grammaire dérivée de l'ontologie corrige
  certains biais du modèle cloud.
- **Coût/latence** (§19.4) : local ≈7-20s/cas à coût marginal **nul**, vs cloud
  ≈5s/cas mais facturé à l'appel. Compromis : latence contre souveraineté totale
  des données étudiantes + coût zéro à l'échelle.
- **Ce qui reste à faire pour la production** (`LLM_LOCAL_2026.md` §6) : étendre
  le pilote de 12 → 40 → 345 échantillons, tester aussi NuExtract/MedGemma pour
  confirmer/battre Qwen2.5 14B, et passer de Ollama (proto) à vLLM (prod, meilleur
  débit). Le harnais de mesure existe déjà (`metrics_validants.py`).
- **Palier matériel réaliste** : un 7-8B quantifié q4 sur 12-16 Go VRAM est le
  point d'équilibre identifié — le décodage contraint réduisant le besoin de
  "gros" modèle.

**Conclusion** : l'autonomie locale n'est pas hypothétique, elle est **déjà
démontrée** sur un premier modèle candidat. Il reste un travail d'échelle
(élargir le pilote) et d'ingénierie (bascule vLLM), pas une percée scientifique
à attendre.

## 4. Peut-on intégrer une ontologie dans un LLM ?

**Oui — mais pas de la façon dont on l'imagine spontanément (fine-tuning de
connaissance). La méthode qui marche ici est le décodage contraint, déjà
implémenté et mesuré.**

- **Ce qui NE marche PAS** : injecter la connaissance médicale/ontologique par
  fine-tuning. Preuve directe (§21) : MedGemma (fine-tuné médical) et Gemma3
  générique obtiennent un score **strictement identique** en NER isolé — la
  connaissance médicale du modèle n'est pas le facteur limitant, parce que le
  RAG + l'ontologie l'apportent déjà en aval.
- **Ce qui marche** : compiler l'ontologie en une **contrainte de décodage**
  (§18) :
  - `onto_grammar.gbnf` (346 IDs, format GBNF pour llama.cpp/Ollama),
  - `onto_enum.json` (JSON-schema enum, pour vLLM/Outlines/XGrammar/lm-format-enforcer).
  - Résultat : **zéro hallucination d'`ontology_id` par construction**, quel que
    soit le modèle choisi. C'est qualifié à raison de "premier brique concrète
    du pipeline 100% local".
  - Propriété clé : la grammaire est **dérivée** de l'ontologie (régénérable via
    `genere_grammaire_contrainte.py`), donc **déclarative** — elle suit
    automatiquement toute évolution du référentiel ontologique (flywheel), sans
    ré-entraînement.
  - Gain mesuré sur le juge (§20.1) : +0.011 F1 / +0.025 κ, gratuit.
- **Conclusion pratique** : l'intégration ontologie↔LLM la plus efficace ici
  n'est pas "apprendre l'ontologie au modèle" (inutile, testé), c'est "forcer
  la sortie du modèle à respecter l'ontologie" (efficace, mesuré, déjà en
  production partielle). C'est une différence de philosophie importante à
  garder : **contraindre > entraîner**, pour ce type de connaissance structurée
  et évolutive.

## 5. Le neurosymbolique est-il toujours le bon choix ?

**Oui, et les résultats de cette session le renforcent plutôt qu'ils ne le
remettent en question — à condition de bien distinguer où va le "neuro" et où
va le "symbolique".**

Repositionnement (`ARCHITECTURE.md` §2.2) face aux alternatives :

| Approche | Limite structurelle | Pourquoi le neurosymbolique reste supérieur ici |
|---|---|---|
| LLM direct (ChatGPT "corrige cet ECG") | Hallucinations, non-reproductible, score non traçable | Notre scoring reste **déterministe et symbolique** — un score doit être justifiable en contexte pédagogique/évaluatif |
| RAG classique | Pas de raisonnement ontologique, pas de hiérarchie de concepts | Nos relations requires/excludes/supports/parent-enfant portent une vraie sémantique clinique, pas juste de la similarité vectorielle |
| Ontologie seule (matching symbolique pur) | Pas de tolérance aux fautes/synonymes/langage naturel | Le "neuro" (embeddings + BM25 + LLM juge) gère le flou linguistique que le symbolique seul ne gère pas |

Ce que les expériences de cette session **ajoutent** à cette thèse (pas
seulement la confirment) :

1. **Le partage des rôles se précise et se durcit avec les données** : le
   "neuro" (LLM) est démontré meilleur pour l'extraction/lecture de langage
   naturel (négation généraliste N1) et le "symbolique" (grammaire dérivée de
   l'ontologie, coupe-circuit, axiomes déclaratifs) est démontré meilleur pour
   *contraindre et garantir* la sortie — jamais l'inverse. La tentative de
   coder en dur une règle symbolique "en plus" (N2) s'est révélée **contre-
   productive** (§25) : le symbolique ne doit intervenir que là où il est
   *garanti* correct (contrainte dérivée, pas heuristique ad hoc).
2. **Le fine-tuning ne remplace pas le symbolique** : MedGemma (neuro spécialisé
   médical) = Gemma générique en NER isolé (§21). Cela confirme que la
   connaissance structurée (l'ontologie) doit rester **symbolique et externe**
   au modèle — pas diluée dans des poids de réseau qu'on ne peut ni auditer ni
   mettre à jour facilement.
3. **La tendance 2026 (constrained decoding généralisé — GBNF/XGrammar/Outlines
   désormais supportés nativement par tous les runtimes majeurs : llama.cpp,
   vLLM, TGI, LM Studio)** va exactement dans le sens du pari neurosymbolique
   fait ici : l'industrie convergeant vers "LLM + grammaire/schema" au lieu de
   "LLM fine-tuné sur tout", ce projet est **aligné avec l'état de l'art actuel**,
   pas en retard sur lui.
4. **Limite honnête à surveiller** : à mesure que les LLM généralistes
   s'améliorent (context, raisonnement), la frontière entre "ce que le neuro
   fait bien" et "ce qu'il faut encore forcer symboliquement" peut se déplacer.
   Le design actuel (5 axes découplés dans `LLM_LOCAL_2026.md` : modèle /
   runtime / décodage contraint / spécialisation / matériel) est justement
   pensé pour **absorber ce déplacement sans réécriture** — c'est un point fort
   de robustesse architecturale, pas une garantie figée.

**Conclusion** : le neurosymbolique n'est pas un choix daté qu'il faudrait
remettre en cause au profit d'un "tout LLM" — les mesures de cette session
montrent au contraire que chaque tentative de faire porter au "neuro" (fine-
tuning médical) un rôle qui appartient au "symbolique" (l'ontologie) échoue à
apporter un gain, et que chaque renforcement du "symbolique" bien conçu
(contrainte dérivée de l'ontologie) apporte un gain gratuit et mesurable. C'est
la confirmation empirique, et non plus seulement théorique, du bien-fondé de
l'architecture.

---

## Synthèse — actions concrètes recommandées

| # | Action | Effort | Gain attendu |
|---|---|---|---|
| 1 | Retirer l'heuristique N2 (`convert_absents_to_positive`) | faible | +qualité, -12 FP mesurés |
| 2 | Intégrer le mécanisme de hedging (`HEDGE_MARKERS`/`_hedged()`) en production | faible | +0.011 F1 note, +0.057 F1 complétude (§26) |
| 3 | Étendre le pilote local Qwen2.5 14B de 12 → 345 échantillons | moyen | Valider l'autonomie locale à l'échelle réelle |
| 4 | Basculer Ollama → vLLM pour la prod locale | moyen | Débit/latence en production |
| 5 | Lancer le fine-tuning QLoRA préparé **seulement si** un modèle 4-8B ne franchit pas le seuil étalon-2pts | conditionnel | Combler un écart résiduel, pas une nécessité actuelle |
| 6 | Ne pas fine-tuner la connaissance médicale/ontologique — rester sur le décodage contraint | — | Évite un chantier coûteux et déjà démontré inutile |

*(Document généré le 2026, à partir des mesures existantes dans
`RAPPORT_METRIQUES.md`, `LLM_LOCAL_2026.md`, `_finetune/README.md` et
`ARCHITECTURE.md`. Aucune nouvelle expérimentation n'a été lancée pour produire
cet audit — il s'agit d'une synthèse des données déjà mesurées.)*
