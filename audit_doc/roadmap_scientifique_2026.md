# Roadmap scientifique et produit — ECG-online

**Version : 30 juillet 2026**
**Statut : document de référence pou- Validé en test manuel : le juge global détecte correctement la négation-
  puis-affirmation et la contradiction associée sur `NEG_THEN_ASSERT-05`.
- **Comparaison sur corpus synthétique (100 items, gold fuzzy provisoire)** :
  gains concentrés comme attendu sur IMPLICIT/NEG_THEN_ASSERT/LEXICAL_DISTANCE
  (+0.14 F1 chacun), 0.00 sur les deux méthodes pour UNSUPPORTED_CRITICAL
  (signal de sécurité à creuser). Cf. `projetLLMjuge/rapport_comparaison_2026-08-02.json`.
- **✅ Comparaison sur le VRAI golden d'extraction (2026-08-02)** — 100 réponses
  étudiantes réelles, 100 % annotées par un expert humain (`ecg-online/data/
  extraction_golden.json`, cf. `ecg-online/GOLDEN_EXTRACTION.md`). Script :
  `rag_pipeline/scripts/compare_judges_real_gold.py`. Rapport complet :
  `ECG evaluation/rapport_gold_reel_2026-08-02.json`.
  - Pipeline actuel : TP=494 FP=45 FN=48 → **taux de FP=8.3%**, taux
    d'omission=8.9% (P=91.7% R=91.1% F1=91.4%).
  - Juge global (rejoué en direct) : TP=496 FP=44 FN=46 → **taux de
    FP=8.1%**, taux d'omission=8.5% (P=91.9% R=91.5% F1=91.7%).
  - Écart global **marginal** (+0.3 F1) sur ce golden — contrairement au
    corpus synthétique où l'écart était de +3.5 F1. Cohen's kappa=-0.075
    (quasi aucun accord structurel : les deux méthodes se trompent sur des
    concepts différents, pas sur les mêmes).
  - **Analyse de complémentarité par brique (clé pour la décision d'archi)** :
    en comparant les FP du pipeline actuel à leur méthode d'origine (via
    `pipeline_extraction[].method` déjà tracé dans le golden) contre ce que le
    juge global aurait produit sur les mêmes textes :

    | Méthode d'origine du FP pipeline | n FP | Évités par le juge global | Répétés par le juge global |
    |---|---|---|---|
    | `juge_llm` (Brique 4 actuelle) | 15 | **15 (100%)** | 0 |
    | `pattern_inference` | 3 | **3 (100%)** | 0 |
    | `lexical_backstop` | 8 | **8 (100%)** | 0 |
    | `fallback_subterm` | 3 | **3 (100%)** | 0 |
    | `coupe_circuit` (symbolique) | 17 | 15 (88%) | 2 |

    ➡️ **Le juge global élimine quasi totalement les hallucinations des
    méthodes de repli faibles** (juge_llm 67.9% précision, pattern_inference
    0% précision, lexical_backstop 69.2%, fallback_subterm 66.7% — cf. table
    d'ablation §1) alors qu'il n'apporte presque rien sur le coupe-circuit
    symbolique (déjà 96.5% précision, quasi optimal). Sur les FN : 41 concepts
    manqués par le pipeline actuel sont retrouvés par le juge global, et 39
    concepts manqués par le juge global sont retrouvés par le pipeline actuel
    (chevauchement d'erreurs très faible dans les deux sens → forte
    complémentarité, cohérent avec le kappa proche de 0).

**Piste d'architecture retenue pour la suite — juge global en second lecteur
ciblé, pas en remplacement total** :

Le F1 global quasi identique masque une réalité par brique : le coupe-circuit
symbolique (74% du volume, 96.5% précision) n'a **aucun besoin** d'être
remplacé — le juge global n'y apporte rien. En revanche, les ~26% du volume
actuellement traités par les méthodes de repli faibles (juge_llm,
pattern_inference, lexical_backstop, fallback_subterm — précision combinée
~68%) sont exactement le point faible que le juge global corrige quasi
parfaitement (100% des FP évités sur 3 des 4 méthodes, 88% par avance). D'où
la proposition d'un **arbitrage sélectif** :
1. Le coupe-circuit symbolique reste la voie principale, inchangée
   (performance déjà quasi-optimale, rapide, gratuit).
2. **Seuls les termes qui ne matchent PAS le coupe-circuit** (donc qui
   tombent aujourd'hui sur juge_llm/pattern_inference/lexical_backstop/
   fallback_subterm) sont soumis au juge global — qui a déjà tout le contexte
   de la réponse (pas seulement le terme isolé), ce qui explique sa
   supériorité sur ces cas ambigus.
3. Gain attendu : réduction du volume de FP de ~26 points de précision
   perdus aujourd'hui sur ~26% du volume, sans toucher au 74% déjà fiable —
   et sans payer le coût (latence + tokens) d'un appel LLM global sur
   *toutes* les réponses alors que 74% n'en ont pas besoin.
4. Risque à vérifier avant décision finale : le juge global perd le contexte
   d'isolement du coupe-circuit — s'assurer qu'un juge "second lecteur" reçoit
   bien le texte complet (pas juste les termes non résolus) pour garder son
   avantage sur l'implicite/la négation-puis-affirmation.

**Prochaines étapes (après P1.3, pas avant — cf. §2.2 anti-scope-creep) :**
1. ✅ Lancer `compare_judges_extraction.py` sur les 100 items synthétiques,
   analyser par strate — fait.
2. ✅ Tester sur le vrai golden d'extraction (100 réponses réelles annotées)
   — fait, cf. ci-dessus. Résultat : écart marginal en F1 global, mais forte
   complémentarité par brique → oriente vers un hybride ciblé plutôt qu'un
   remplacement total.
3. ✅ **Prototype hybride testé sur les DEUX golds (2026-08-02)** — script
   `rag_pipeline/scripts/compare_hybrid_arbiter.py`. Architecture : coupe-circuit
   inchangé + juge global appelé en second lecteur sur le TEXTE COMPLET avec
   le CATALOGUE COMPLET (⚠️ un catalogue restreint aux seuls concepts non
   résolus par coupe-circuit a été essayé en premier et s'est révélé être un
   contresens : privé du bon concept, le juge hallucine sur le concept
   voisin restant — le filtrage doit se faire en SORTIE, pas en entrée). Les
   claims du juge portant sur un concept déjà validé par coupe-circuit sont
   ignorés (pas de double-compte). Résultat final = coupe_circuit_ids ∪
   (claims du juge global hors coupe_circuit_ids).

   **Sur le gold RÉEL** (`ECG evaluation/rapport_hybride_arbitre_real_fixed_2026-08-02.json`) :

   | | TP | FP | FN | Taux FP | Taux omission | P/R/F1 |
   |---|---|---|---|---|---|---|
   | Pipeline actuel complet | 494 | 45 | 48 | 8.3% | 8.9% | 91.7/91.1/91.4 |
   | **Hybride (coupe-circuit + juge global 2e lecteur)** | 519 | 77 | 23 | 12.9% | **4.2%** | 87.1/**95.8**/91.2 |

   → Gain net de rappel (**-4.7 points d'omission**, de 8.9% à 4.2%), au prix
   d'un taux de FP qui remonte (8.3% → 12.9%). F1 quasi stable (91.4 → 91.2,
   dans le bruit). Le compromis n'est PAS un gain "gratuit" : c'est un
   arbitrage explicite rappel/précision, à calibrer selon le risque
   pédagogique visé (favoriser le rappel a du sens si l'objectif est de ne
   jamais pénaliser un étudiant pour un concept réellement écrit mais non
   détecté ; favoriser la précision a du sens si l'objectif est d'éviter de
   créditer des concepts halluciné). Voir §"decision à prendre" ci-dessous.

   **Sur le gold VIRTUEL** (corpus synthétique, gold fuzzy provisoire,
   `ECG evaluation` rapport combiné) :

   | | TP | FP | FN | Taux FP | Taux omission | P/R/F1 |
   |---|---|---|---|---|---|---|
   | Pipeline actuel complet | 58 | 132 | 118 | 69.5% | 67.0% | 30.5/33.0/31.7 |
   | Hybride | 70 | 191 | 106 | 73.2% | 60.2% | 26.8/39.8/32.0 |

   ⚠️ Chiffres à lire avec prudence : le gold synthétique est un gold
   *provisoire* par projection fuzzy texte-libre (PAS une vraie annotation
   ontologique), donc son taux de FP/omission élevé reflète en grande partie
   du bruit de projection, pas la qualité réelle de l'extraction — cf.
   avertissement dans `compare_judges_extraction.py`. La tendance (F1
   quasi stable, gain de rappel) reste cependant cohérente avec le gold réel.

   **🐛 Cause racine identifiée (2026-08-02)** : `scoring_v3.find_owl_concept()`
   ne retourne PAS `None` quand aucun concept réel n'est trouvé dans
   l'ontologie — il **invente un `ontology_id`** à partir du texte brut
   (`concept_text.upper().replace(" ", "_")`, cf. `scoring_v3.py` L144-149).
   Vérifié empiriquement : **48% des 177 labels `correct_elements` du corpus
   synthétique (85/177) ne matchent AUCUN concept réel de l'ontologie** et
   se retrouvent donc dans le gold comme des IDs fantômes que ni le pipeline
   actuel ni le juge global ne peuvent jamais trouver (ils n'existent pas
   dans le catalogue candidat) → FN artificiels garantis. Exemples observés :
   `BAV` (trop générique, jamais un concept exact), `IRRÉGULARITÉ_COMPLÈTE`
   (avec accents, alors que les vrais IDs sont normalisés sans accents),
   `ABSENCE_D'ONDES_P` (apostrophe typographique ≠ `ABSENCE_D_ONDE_P` réel).
   ➡️ **Le taux de FP/omission catastrophique du corpus synthétique (69.5%/
   67.0%) n'est donc PAS représentatif de la qualité d'extraction** — c'est
   un artefact du gold provisoire lui-même, pas un signal sur le pipeline ni
   sur le juge global. Un correctif de projection locale (rejet des IDs
   fantômes via `get_concept()`) a fait chuter le taux d'omission mesuré à
   36.6%/22.6%, mais le taux de FP reste artificiellement élevé (~70%) pour
   une raison structurelle différente : le corpus ne liste dans
   `correct_elements` que les concepts pertinents au phénomène CIBLÉ par
   chaque item, pas une liste exhaustive de tout ce que le texte décrit —
   ce corpus n'a donc jamais été conçu pour mesurer un taux de FP absolu,
   seulement pour comparer relativement les deux méthodes sur des
   phénomènes rares. **Décision (2026-08-02) : on abandonne ce corpus comme
   source de métriques chiffrées et on se concentre exclusivement sur le
   gold RÉEL** (100 réponses réelles, annotation exhaustive humaine) comme
   unique référence quantitative fiable pour ce chantier. Le corpus
   synthétique reste utile qualitativement (cf. test manuel négation-puis-
   affirmation) mais sort du périmètre de mesure chiffrée tant qu'il n'est
   pas ré-annoté de façon exhaustive par un expert (Phase 1 réelle).

### 📌 Résultat de référence retenu — gold réel (100 réponses, 2026-08-02)

| | TP | FP | FN | **Taux FP** | **Taux omission** | P / R / F1 |
|---|---|---|---|---|---|---|
| Pipeline actuel (coupe-circuit + méthodes de repli) | 494 | 45 | 48 | 8.3% | 8.9% | 91.7/91.1/91.4 |
| **Hybride (coupe-circuit inchangé + juge global 2e lecteur, filtrage en sortie)** | 519 | 77 | 23 | 12.9% | **4.2%** | 87.1/**95.8**/91.2 |

Script : `rag_pipeline/scripts/compare_hybrid_arbiter.py --gold real`.
Rapport : `ECG evaluation/rapport_hybride_arbitre_real_fixed_2026-08-02.json`.

**Lecture** : l'hybride réduit fortement l'omission (-4.7 points, de 8.9% à
4.2% — il retrouve la quasi-totalité des concepts manqués par le pipeline
actuel), au prix d'un taux de FP qui remonte de 8.3% à 12.9%. Le F1 global
est quasi stable (91.4 vs 91.2, dans le bruit de mesure sur 100 items).
**Ce n'est pas un gain gratuit : c'est un arbitrage explicite rappel/
précision**, pas un remplacement strictement supérieur.

### 🧭 Réflexion — quelle direction prendre ?

Trois options se dégagent, non exclusives :

**(a) Ne rien changer.** Le F1 global ne bouge pas significativement (91.4
→ 91.2) et le pipeline actuel est déjà mature, rapide, sans coût LLM
additionnel sur 74% du volume. Argument principal : "si ce n'est pas cassé,
ne pas complexifier l'architecture pour un gain marginal non démontré comme
significatif statistiquement sur seulement 100 items."

**(b) Adopter l'hybride tel quel**, en assumant l'arbitrage recall/precision.
Ça se justifie si le risque pédagogique dominant est **la sous-notation
injuste** (un étudiant a réellement écrit un concept correct, non détecté,
donc non crédité) plutôt que la sur-notation (un concept crédité à tort).
Dans un contexte d'évaluation formative (auto-entraînement, pas d'examen
sommatif), ce choix est défendable : mieux vaut créditer un peu trop que
frustrer l'étudiant par une omission arbitraire du système. Le risque
inverse (FP) devient plus grave si le score sert de note sommative réelle.

**(c) Affiner le filtrage de sortie du juge global avant de trancher entre
(a) et (b)** — piste concrète non encore testée : ne retenir les claims du
juge global que lorsque `expression_mode` ∈ {implicit_complete,
implicit_partial, paraphrased} (excluant `explicit`). Rationale : c'est
précisément sur l'implicite/la paraphrase que le juge global a un avantage
contextuel documenté (cf. analyse par strate sur le corpus synthétique,
gains concentrés sur IMPLICIT/NEG_THEN_ASSERT/LEXICAL_DISTANCE) ; sur les
formulations explicites, il n'apporte rien et ne fait qu'ajouter du bruit
(FP) sur des reformulations déjà bien couvertes par coupe-circuit et les
méthodes de repli. Cette piste devrait mécaniquement réduire le taux de FP
de l'hybride en ne sacrifiant qu'une petite partie du gain de rappel (celui
qui vient de cas déjà explicites que le pipeline actuel ratait pour d'autres
raisons, ex: bug de résolution plutôt que d'implicite véritable).

**Recommandation initiale** : tester (c) avant de décider entre (a) et (b) —
c'est peu coûteux (aucun nouvel appel LLM, juste un filtre supplémentaire
sur les rapports déjà collectés) et peut faire basculer la décision sans
nouveau run complet.

### ✅ Test de la piste (c) réalisé (2026-08-02) — résultat négatif, piste abandonnée

Script modifié : `extract_global_judge_targeted()` dans
`compare_hybrid_arbiter.py` capture désormais, pour CHAQUE claim du juge
global (avant filtrage), `{claim_id, concept_id, polarity, expression_mode}`
dans `per_item["global_judge_claims_raw"]` — ce qui permet de tester
offline n'importe quelle variante de filtrage de sortie sans nouvel appel
API. Re-run complet sur les 100 items du gold réel :
`ECG evaluation/rapport_hybride_real_with_claims_2026-08-02.json`.

Variante (c) testée : ne garder du juge global que les claims
`polarity == "present"` ET `expression_mode` ∈ {paraphrased,
implicit_complete, implicit_partial} (exclusion des `explicit`), en plus du
filtre déjà existant (hors `coupe_circuit_ids`).

| | TP | FP | FN | Taux FP | Taux omission | P/R/F1 |
|---|---|---|---|---|---|---|
| Pipeline actuel complet | 494 | 45 | 48 | 8.3% | 8.9% | 91.7/91.1/91.4 |
| Hybride complet (sans filtre expression_mode) | 520 | 72 | 22 | 12.2% | 4.1% | 87.8/95.9/91.7 |
| **Variante (c) — filtrage expression_mode (exclut `explicit`)** | **460** | **50** | **82** | 9.8% | **15.1%** | 90.2/84.9/87.5 |

**Verdict : la variante (c) est PIRE que les deux autres options sur presque
tous les axes.** Elle a même moins de TP (460) que le pipeline actuel seul
(494) — elle perd des concepts que le pipeline actuel trouvait déjà. Son
taux d'omission (15.1%) est le pire des trois configurations testées,
loin derrière le pipeline actuel (8.9%) et l'hybride complet (4.1%). Le gain
sur le taux de FP (9.8% vs 12.2% pour l'hybride complet) ne compense pas
cette perte massive de rappel.

**Explication** : le filtre par `expression_mode` n'est pas un bon proxy
pour distinguer FP de TP. Ce n'est pas parce qu'une mention est jugée
« explicite » par le juge qu'elle est nécessairement redondante avec
coupe-circuit — le juge peut classer « explicit » des reformulations
légèrement différentes de la formulation canonique, que coupe-circuit
(matching plus strict) ne capte pas. Exclure les claims `explicit` prive
donc l'hybride de vrais positifs légitimes en plus des faux positifs visés.
**Piste (c) abandonnée** — pas de variante de repli testée (seuil de
`certainty` ou filtrage par `polarity` seuls n'ont pas été essayés, jugés
hors scope pour ce chantier vu le signal déjà clairement défavorable).

### 📍 Décision formelle prise (2026-08-02) : **option (a) — ne rien changer**

Argumentation :
- Le F1 de l'hybride complet (91.7) n'est pas significativement supérieur à
  celui du pipeline actuel (91.4) sur 100 items — l'écart est dans le bruit
  de mesure, et la variante (c) censée améliorer le compromis s'est révélée
  contre-productive.
- L'hybride complet réduit fortement l'omission (4.1% vs 8.9%) mais au prix
  d'un taux de FP significativement plus élevé (12.2% vs 8.3%) et d'un coût
  additionnel (latence + tokens d'un appel LLM global par réponse). Sans
  piste de filtrage qui améliore ce compromis (la seule testée a échoué),
  le gain net ne justifie pas la complexité et le coût ajoutés.
- Conforme au principe anti-scope-creep (§2.2) : pas de changement
  d'architecture de production tant qu'un gain net et robuste n'est pas
  démontré. Le pipeline actuel (coupe-circuit + méthodes de repli) reste en
  production tel quel.
- Le chantier du juge sémantique global n'est PAS abandonné pour autant :
  il reste une piste de recherche documentée (cf. proposition
  `projetLLMjuge/ECG_online_proposition_iteration_juge_global_2026-08-02.md`),
  à reprendre après P1.3/P1.4 (schéma scoring V2 stabilisé, double
  annotation cardiologue disponible) qui fournira un gold plus riche et
  potentiellement d'autres axes de filtrage (ex: exploiter `certainty`,
  `inferred_from`, ou une calibration par famille de phénomène plutôt que
  par `expression_mode` seul).

4. Double annotation cardiologue du corpus synthétique (Phase 1 réelle) —
   reste utile à terme pour valider finement les strates rares, et devient
   le prérequis nécessaire pour toute reprise future de ce chantier (le
   gold réel actuel, bien que fiable, n'est que 100 items — insuffisant
   pour trancher des écarts fins comme celui observé ici).
5. **Décision formelle prise** : option (a), ne rien changer en production.
   Le chantier est mis en pause (pas fermé) — cf. état des lieux ci-dessous.

### 🤖 Choix du modèle pour ce type de réflexion architecturale — Claude Opus vs Sonnet

Question posée : pour ce genre de travail (diagnostic de bug de mesure,
arbitrage architecture recall/precision, décision de priorisation), y a-t-il
un intérêt à basculer sur un modèle "Opus"-like (raisonnement plus profond,
plus lent, plus cher) plutôt que "Sonnet"-like (rapide, moins cher, déjà
utilisé dans cette session) ?

**Nature du travail réalisé dans ce chantier** : il combine (1) de
l'exécution outillée répétitive (lancer des scripts, lire des logs, corriger
un bug de projection identifié empiriquement) et (2) du raisonnement
d'architecture ponctuel mais peu profond (arbitrage recall/precision assez
standard, pas de preuve mathématique ni de synthèse de littérature complexe
requise). Le point de blocage principal a été atteint par **itération
empirique rapide** (test sur 3 items → observation → hypothèse → correction
→ re-test), pas par un raisonnement long en un seul passage.

**Avantages attendus d'un modèle "Opus"** dans ce contexte précis :
- Meilleure anticipation des pièges AVANT de lancer un run coûteux (le bug
  du catalogue restreint qui force l'hallucination, ou celui du fallback
  fantôme de `find_owl_concept`, auraient pu être anticipés par un
  raisonnement plus approfondi sur le prompt/la fonction AVANT le premier
  test empirique — ça aurait évité 2 runs de 100 items à ~8-10 min chacun).
- Meilleure qualité de synthèse/rédaction sur les arbitrages nuancés
  (formulation des 3 options a/b/c ci-dessus, articulation risque
  pédagogique/technique) — bénéfice réel mais marginal, le résultat actuel
  est déjà exploitable.

**Limites/coûts** :
- Latence et coût significativement plus élevés, alors qu'une bonne partie
  du travail ici est de l'exécution d'outils (scripts, lecture de logs) où
  la vitesse d'itération compte plus que la profondeur de raisonnement par
  requête — un modèle plus lent aurait ralenti le cycle test→observe→corrige
  qui a été le mode de travail dominant.
- Le vrai levier de qualité sur ce chantier n'est pas le modèle utilisé pour
  l'assistance, mais la **qualité du gold de test** (le bug de projection a
  eu bien plus d'impact sur la fiabilité des résultats que n'importe quel
  choix de modèle d'assistance).

**Conclusion pragmatique** : un modèle "Opus"-like serait utile ponctuellement
en amont d'un run coûteux — pour une revue de conception (relire
`extract_global_judge_targeted`/`build_candidate_catalog` et anticiper les
pièges de filtrage catalogue vs sortie) avant de lancer 100 items en
production — mais pas nécessaire pour la boucle d'itération empirique elle-
même, qui bénéficie davantage de rapidité. Recommandation : réserver un
modèle plus coûteux/lent aux moments de **revue de conception avant
exécution** (relecture de prompt système, de logique de filtrage, de
schéma de données) plutôt qu'à l'ensemble du chantier — un usage ciblé, pas
un remplacement systématique.oppements à venir**

> 📌 **Ce document est LA référence active** (cf. `audit_doc/README.md` pour
> l'index complet). `FEUILLE_DE_ROUTE_ALIGNEE.md` et
> `ECG_Online_Architecture_Cible_Feuille_de_Route.md` sont désormais figés
> (historique). Toute décision de priorité se documente ici.

---

## 0. État d'avancement (à tenir à jour à chaque session)

### ✅ Déjà fait avant ce document (mergé sur `main`, `ecg-online`)

Correspond à ce que ce roadmap appelle **P0.1 (partiel)** et **P5.3** :

- `response_id`/`prediction_id` (UUID) sur chaque `/api/grade`.
- États `SUCCESS`/`LOW_CONFIDENCE`/`FALLBACK_GPT`/`TECHNICAL_ERROR` (`app/abstention.py`)
  — correspond à une partie de P5.3 (`HUMAN_REVIEW`/`ABSTAIN` réels restent à faire, cf. P5).
- `pipeline_version` + `ontology_version` exposés dans `/api/health` et `/api/grade`
  (`app/golden_config.ontology_version()`) — brique de P0.1, incomplet (pas encore
  de tag de release ni de version figée des cas/goldens/dépendances ensemble).
- `docs/DATA_DICTIONARY.md` — contrat JSON `/api/grade` documenté.
- `tests/test_negation_nonregression.py` (8 tests, données golden réelles) —
  premier jalon très partiel de P3.3 (challenge set), pas encore un vrai
  benchmark verrouillé (P3.2) ni un challenge set complet.
- Phase E (`ecg-online/ROADMAP.md`) : golden de scoring actuel (`cases_golden.json`,
  75 cas, mono-expert) nettoyé, 0 conflit réel, audité sur 343 réponses réelles.
- **P1.1 + P1.2 (01/08/2026)** : schéma `scoring_v2` défini et validé
  (`ecg-online/data/scoring_schema_v2.json` + `scripts/validate_scoring_v2.py`),
  pilote réalisé sur 10 cas contrastés (`ecg-online/data/scoring_pilot_v2.json`,
  27 critères, 0 erreur de schéma) — rapport complet dans
  `ecg-online/docs/P1.2_pilote_scoring_v2_rapport.md`. Critère de sortie P1.2
  atteint : aucune situation fréquente n'a nécessité de champ improvisé.
  **Prochaine étape : P1.3 (annotation indépendante multi-expert)**, pas
  encore démarrée (le pilote actuel est en `evidence_source: single_expert`).
- **Liaison curriculum ↔ scoring_v2 (01/08/2026)** : script de dérivation
  automatique `ecg-online/scripts/derive_curriculum_objectives.py`
  (`required_concepts`/`unsafe_errors` du curriculum dérivés des critères
  `role=required`/`role=exclusion` de scoring_v2), testé sur le pilote
  10 cas — voir `ecg-online/docs/curriculum_scoring_v2_liaison.md`. Verdict :
  mécanisme fonctionnel, à utiliser comme pré-remplissage humain (pas comme
  vérité automatique) lors de la Phase 2 du curriculum ; généralisable aux
  75 cas seulement après P1.4.
- **Curriculum Phase 1 — audit de couverture (01/08/2026)** :
  `ecg-online/data/case_curriculum_map.json` (15 parcours, dont les 5
  existants dans `frontend/pathways.json` conservés en compatibilité) +
  validateur `ecg-online/scripts/validate_case_curriculum_map.py`. Vérifie
  automatiquement que les 75 cas apparaissent exactement une fois. Résultat :
  ✅ 75/75 cas affectés, 0 doublon, 0 absence, couverture 100 % sur les 11
  familles cliniques (`data/cases.json`). Ce mapping est un premier jet
  structurel, **pas encore validé cliniquement** (cf. avertissement du
  curriculum) — la Phase 2 (rédaction des objectifs/indices/critères par
  cas) reste à faire.
- **Correctifs de couverture lexicale de l'ontologie + feedback IA
  (2026-08-06)** — deux bugs trouvés et corrigés à partir d'un signalement
  utilisateur sur un cas réel, puis généralisés via un scan systématique
  des 73 sessions étudiantes réelles (345 cas) :
  1. Synonyme manquant "Flutter commun anti-horaire" sur le concept
     `FLUTTER_ATRIAL_ANTIHORAIRE` (ontologie) — écrit littéralement par un
     étudiant mais ni le NER ni le filet lexical de secours ne le
     reconnaissaient faute de correspondance exacte.
  2. Seuil du filet lexical de secours (`_lexical_backstop_ids`) trop
     strict pour les concepts à 2 mots (ex. "Echappement ventriculaire") :
     remplacement du critère `BACKSTOP_MIN_DISTINCTIVE_WORDS` (longueur du
     synonyme) par `BACKSTOP_MAX_WORD_DOCUMENT_FREQUENCY` (spécificité
     lexicale calculée dynamiquement depuis la fréquence documentaire des
     mots dans l'ontologie chargée) — critère générique, sans liste de
     mots figée en dur, donc indépendant de la langue et scalable à
     l'ajout de nouveaux concepts (une première option de liste blanche a
     été explicitement écartée pour cette raison).
  3. Validé sans régression sur le re-scan des 345 cas + régénération
     complète v9 (100 items) + audit qualité gpt-5.6 correspondant (cas
     flutter passé en verdict "excellent", cas échappement ventriculaire
     tous corrigés).
  4. Prompt de rédaction du feedback (`pedagogical_feedback.py`) durci en
     parallèle : validateur clinique post-hoc `ClinicalClaimValidation`
     (second appel LLM à température nulle qui détecte toute affirmation
     non ancrée dans le contexte réel), garde-fou déterministe de
     cohérence ton/score, détection de fuite de jargon technique interne.
  → Détail complet, chiffres et méthodologie : `ecg-online/data/
  audit_feedback_gpt_verdict_2026-08-05_AUDIT.md` (document opérationnel
  dédié au suivi qualité du feedback IA, mis à jour à chaque itération).
  Modèle de génération du feedback : **gpt-4o** (gpt-4o-mini écarté, trop
  d'approximations cliniques) ; gpt-5.6 n'est utilisé que comme juge
  d'audit externe de la qualité rédactionnelle, jamais comme rédacteur.
- **Relecture ontologique complète des 75 cas + outillage IA de relecture
  (2026-08-09)** : session dédiée à la relecture conceptuelle du golden de
  scoring existant, avec un premier outillage IA pour l'assister — à
  rattacher à **P1.3** (l'affirmation "pas encore démarrée" ci-dessus est
  désormais **obsolète**, cf. correction ci-dessous) :
  1. 10 nouveaux concepts ontologiques ajoutés + correction de plusieurs
     redondances structurelles détectées pendant la relecture des 75 cas.
  2. Deux tours de déduplication de synonymes : collisions introduites par
     les nouveaux concepts, puis un second passage sur ~20 collisions
     préexistantes plus anciennes.
  3. Décision de fusion de catégorie D (`VOLTAGE_DU_QRS_NORMAL` /
     `VOLTAGE_NORMAL_DU_QRS`) prise puis **annulée** dans la même session
     après ré-examen (retour au concept OWL d'origine) — `.owl` régénéré
     et archivé (`convert_owl_to_v2.py` / `regenerate_ontology.py`),
     script `scripts/revert_voltage_merge_keep_owl_concept_2026_08_09.py`
     (ecg-online) conservé pour trace.
  4. Double validation de non-régression du revert : `scripts/audit_golden.py`
     → 0 bloquant (21 avertissements résiduels, doublons inoffensifs déjà
     connus) ; script de comparaison numérique avant/après sur les 75 cas
     via `scoring_v3` → **0 régression** (moyenne 90.89 % avant/après ;
     l'écart préexistant du cas 75 à 85.7 % est sans lien avec le revert).
  5. **Bug de dérive découvert et corrigé** : les 3 copies vendorées de
     `ontology_v2.json` (`data/`, `rag_pipeline/data/`,
     `ecg-online/rag_pipeline/data/`) avaient divergé silencieusement sur 5
     concepts (`ARTEFACTE`, `ECG_NORMAL`, `FLUTTER_ATRIAL_ANTIHORAIRE`,
     `PRESENCE_D_ONDE_Q_PATHOLOGIQUE`, `TREMULATION_DE_LA_LIGNE_DE_BASE`),
     antérieur à la session du jour. Resynchronisées manuellement (copie
     canonique = version la plus riche par concept), vérifiées identiques
     (0 diff sur les 358 concepts), re-testées via `audit_golden.py`
     (0 bloquant, inchangé) — commits `8a82d20` (ECG lecture) et `4bc15e0`
     (ecg-online). **Point de vigilance process** : la synchro manuelle des
     3 copies est fragile ; envisager un script de vérification permanent
     (3-way diff par concept) plutôt qu'une vérification ad hoc.
  6. Assainissement du dépôt : ~40 fichiers temporaires supprimés (logs,
     `.bak*`, versions intermédiaires d'`audit_feedback_*.json`, scripts
     `_tmp_*.py`) — commits `3c19b27` (ecg-online) et `44b2cd3` (ECG lecture).
  → **Correction du statut P1.3** : le travail de relecture/annotation
  assistée par IA (fonctions `review_scoring_criteria()` /
  `suggest_scoring_criteria()` dans `app/gpt_annotator.py`,
  `app/scoring_v2_review.py`, UI `frontend/scoring_review.html`) est
  opérationnel et a été exercé sur les 75 cas dans cette session — P1.3
  n'est donc plus "pas encore démarrée" mais **✅ considérée comme suffisante
  et clôturée** (décision d'équipe 2026-08-09) : la **double lecture
  humain + IA** (relecture experte assistée par le second-avis GPT sur
  chaque critère, cf. outillage ci-dessus) est retenue comme méthode
  d'annotation définitive pour ce golden — une annotation multi-expert
  totalement indépendante en plus de la double lecture humain+IA n'est
  **pas jugée nécessaire**. P1.5 (extension du golden) suit la même
  logique et est donc également considéré comme couvert par le processus
  actuel plutôt que bloqué en attente d'un second expert humain isolé.
- **P1.4 — Migration + audit des 75 cas (2026-08-08 à 2026-08-10)** :
  1. Migration bareme V1 → schéma V2 déjà réalisée le 2026-08-08
     (`scripts/bootstrap_pilot_v2_all_cases.py` + `merge_bareme_into_pilot_v2.py`) :
     `data/scoring_pilot_v2.json` et `data/scoring_v2_review.json` couvrent
     les 75 cas (`expert_1` rempli partout, `evidence_source=
     bareme_v1_migre/bareme_v1_valide`).
  2. **Signalement étudiant (feedback Google Sheets, 09/08)** sur cases 25/
     41/49 → correction V1 en production (`cases_golden.json`/
     `scoring_config.json`, script `scripts/fix_golden_redundancy_2026_08_10.py`,
     testée par régression via `golden_for_scorer()` +
     `scripts/_test_scoring_regression_25_41_49.py`).
  3. **Audit de cohérence V2 (2026-08-10)** : 30 incohérences trouvées sur
     les 75 cas migrés — 17 critères `role=alternative` sans
     `alternative_group` (mécanisme OR inopérant) + 13 critères
     `role=exclusion` avec `expected_status=present` (contradiction
     logique). Toutes corrigées avec validation clinique cas par cas
     (script `scripts/fix_alternative_groups_scoring_v2_2026_08_10.py`,
     0 erreur résiduelle après correction). Validateur
     `scripts/validate_scoring_v2.py` corrigé (enum `evidence_source`
     désynchronisé des données réelles).
  4. **Rapport de différences V1/V2** généré
     (`scripts/generate_v1_v2_diff_report.py` →
     `ecg-online/docs/P1.4_diff_v1_v2_report.md`) : 53/75 cas ont au moins
     un écart, mais la majorité des `only_v1` sont des micro-fragments du
     fuzzy-match V1 imparfait (pas de vrais concepts cliniques oubliés).
  5. **Interface d'annotation** : déjà adaptée aux 75 cas (vérifié via
     `app/scoring_v2_review.py::overview()`, qui itère sur
     `scoring_pilot_v2.json` — 75 cas présents).
  → **P1.4 considérée comme couverte** : script de migration ✅, validateur
  JSON ✅, rapport de différences ✅, audit des contradictions ✅, interface
  ✅. Reste optionnel : tests de non-régression dédiés à `scoring_v2_review.json`
  (risque faible car non branché au moteur — cf. avertissement
  `minimum_specificity`/`group_logic` dans `app/scoring_v2_review.py`).

### 🔜 Séquence retenue par l'équipe (30/07/2026)

Ordre validé pour les prochains chantiers, **différent** de l'ordre suggéré en
§4 du document (qui reste une checklist utile pour le détail de chaque étape) :

1. **P1 — Golden conceptuel de scoring V2** (chantier principal de l'été) :
   schéma enrichi (§P1.1), pilote 8-12 cas (§P1.2), annotation multi-expert
   (§P1.3), puis migration des 75 cas (§P1.4).
2. **P3 — Splits et benchmark verrouillé** : une fois le schéma V2 stabilisé
   sur le pilote, verrouiller un test interne (§P3.2) et un challenge set
   (§P3.3) **avant** de migrer massivement — pas après.
3. **P4 — Refonte du scoring** (séparer adéquation/sécurité, calibrer les
   crédits ontologiques, restreindre la négation) — nécessite P1 (et
   idéalement des éléments de P2) pour être calibré contre du réel.

En tâche de fond, en parallèle (peu coûteux, ne pas laisser traîner) :
- **P0.1** : ✅ fait (2026-08-01) — baseline versionnée : script
  `ecg-online/scripts/generate_baseline_report.py`, rapport
  `ecg-online/data/baseline_report.json`, doc `ecg-online/docs/BASELINE_P0.1.md`,
  tag Git `baseline-p0.1-2026-08-01`.
- **P0.2** : trier les fichiers publics/privés avant que leur nombre ne
  grossisse encore.
- **P0.3** : ✅ fait (2026-08-01) — registre unique `audit_doc/METRICS_LEDGER.md` ;
  README racine corrigé (chiffre "~92%" désormais daté/sourcé, distinct du F1
  d'extraction) ; index `audit_doc/README.md` mis à jour.

P2 (golden de décision humaine par réponse), P5-P8 : pas commencés,
volontairement après P1/P3/P4 (cf. §2.2 anti-scope-creep du document).

### 🔬 Chantier parallèle — Juge sémantique global (à porter après P1.3)

Décidé le 2026-08-01/02 : le juge LLM actuel (Brique 4, résolution locale
par concept) a la précision la plus faible de toutes les méthodes
d'extraction (67.9 %, cf. `METRICS_LEDGER.md` §1 — table d'ablation) et ne
traite que ~13 % du volume (le coupe-circuit symbolique absorbant déjà ~74 %
à 96.5 % de précision). Question posée : le juge LLM actuel est-il la bonne
architecture, ou la fragmentation du texte en entités séparées avant
résolution perd-elle des phénomènes de discours global (implicites,
contradictions, négation-puis-affirmation, hiérarchisation de différentiel,
cohérence mesure/interprétation) ?

**Statut (2026-08-02)** :
- Proposition d'architecture documentée : `projetLLMjuge/ECG_online_proposition_iteration_juge_global_2026-08-02.md`
  (juge sémantique global à appel unique, remplaçant NER+recherche+juge local
  par une lecture complète du discours, garde-fous stricts §12).
- Corpus ciblé de 100 réponses synthétiques (10 phénomènes × 10 cas) créé :
  `projetLLMjuge/ECG_online_corpus_cible_100_reponses_2026-08-02.{md,jsonl}`.
  ⚠️ Corpus synthétique, PAS encore doublement annoté par des cardiologues
  (Phase 1 du plan, non faite) — à ne pas citer comme gold validé.
- Prototype Phase 2 implémenté (sans toucher scoring_v3/ner_extractor/
  neurosymbolic_judge existants) : `rag_pipeline/global_semantic_schema.py`
  (schéma `GlobalSemanticReport` : claims/measurements/contradictions/
  unsupported_claims), `rag_pipeline/global_semantic_judge.py` (appel LLM
  unique + catalogue ontologique compact ≤30 concepts).
- Harnais de comparaison (Phase 5 simplifiée) : `rag_pipeline/scripts/
  compare_judges_extraction.py` — compare la capacité d'EXTRACTION des deux
  méthodes (precision/recall/F1 + Cohen's kappa d'accord inter-méthodes),
  PAS la note finale (déterministe, calibrable séparément). Gold utilisé :
  projection fuzzy provisoire des `correct_elements` texte-libre du corpus
  (non-validée cliniquement) — résultats donc INDICATIFS à ce stade.
- Validé en test manuel : le juge global détecte correctement la négation-
  puis-affirmation et la contradiction associée sur `NEG_THEN_ASSERT-05`.

**Prochaines étapes (après P1.3, pas avant — cf. §2.2 anti-scope-creep)** :
1. ✅ Lancer `compare_judges_extraction.py` sur les 100 items, analyser par
   strate — fait, cf. détail ci-dessus (§ résultats hybride/expression_mode).
2. Double annotation cardiologue du corpus (Phase 1 réelle, remplace le gold
   provisoire fuzzy) — PAS FAITE, reste le prérequis pour toute reprise.
3. ✅ Décision prise (2026-08-02) : **option (a) — ne rien changer en
   production**. Le pipeline actuel (coupe-circuit + méthodes de repli)
   reste tel quel. Voir détail complet et justification dans la section
   "🧭 Réflexion — quelle direction prendre ?" ci-dessus.

**🗂️ État des lieux — chantier "juge sémantique global" (statut au 2026-08-02)**

| Item | Statut | Détail |
|---|---|---|
| Schéma `GlobalSemanticReport` (Pydantic) | ✅ Fait | `rag_pipeline/global_semantic_schema.py` — claims/measurements/contradictions/unsupported_claims/unresolved_mentions, `expression_mode`, `min_expression_mode` déjà supporté dans `extract_found_concept_ids()`. |
| Juge global (appel LLM unique) | ✅ Fait | `rag_pipeline/global_semantic_judge.py` — `judge_global()` + `build_candidate_catalog()` (BM25/dense + expansion relations ontologiques, ≤30 concepts). |
| Harnais de comparaison brut (extraction seule) | ✅ Fait | `rag_pipeline/scripts/compare_judges_extraction.py`. |
| Harnais hybride (coupe-circuit + juge 2e lecteur) | ✅ Fait | `rag_pipeline/scripts/compare_hybrid_arbiter.py` — capture désormais aussi les claims bruts avec `expression_mode` par item (`global_judge_claims_raw`), réutilisable offline sans nouveaux appels API. |
| Mesure sur gold réel (100 items) | ✅ Fait | Pipeline actuel : TP=494/FP=45/FN=48 (FP 8.3%, omission 8.9%). Hybride complet : TP=520/FP=72/FN=22 (FP 12.2%, omission 4.1%). |
| Piste de filtrage `expression_mode` (option c) | ✅ Testée, ❌ rejetée | TP=460/FP=50/FN=82 (FP 9.8%, omission **15.1%**) — pire que les deux autres options, piste abandonnée. |
| Décision d'architecture finale | ✅ Prise | **Option (a)** : ne rien changer en production. |
| Double annotation cardiologue (Phase 1 réelle) | ❌ Pas fait | Reste LE prérequis bloquant pour toute reprise crédible de ce chantier — sans lui, le gold synthétique (10 phénomènes ciblés) ne peut pas servir de mesure quantitative absolue (non-exhaustivité documentée). |
| Reprise du chantier | ⏸️ En pause | Pas fermé : à reprendre après P1.3/P1.4 (schéma scoring V2 stabilisé + gold plus riche), avec éventuellement d'autres axes de filtrage à explorer (`certainty`, `inferred_from`, calibration par famille de phénomène plutôt que par `expression_mode` seul). |

**Ce qu'il resterait concrètement à développer si le chantier est repris** :
1. Annotation cardiologue double (au moins 2 experts indépendants) du corpus
   synthétique 100 items — condition sine qua non pour toute nouvelle mesure
   quantitative fiable sur les phénomènes rares (implicite, contradiction,
   négation-puis-affirmation).
2. Explorer des axes de filtrage alternatifs à `expression_mode` seul —
   ex: combiner avec `certainty` (ne garder que les claims à haute
   certitude), ou calibrer un filtre différent par phénomène/famille
   clinique plutôt qu'un filtre global uniforme.
3. Si un filtrage prometteur émerge, refaire une mesure complète sur le gold
   réel (100 items) + le corpus synthétique ré-annoté, avant toute décision
   de mise en production, même partielle (shadow mode recommandé en premier,
   cf. proposition §10 Phase 6).
4. Envisager, indépendamment du filtrage, une réduction de coût/latence du
   juge global (catalogue plus compact, appel restreint aux réponses où le
   pipeline actuel a un signal d'incertitude, plutôt qu'un appel systématique
   sur 100% des réponses) — piste non explorée cette session.



## 1. Positionnement du projet

ECG-online doit désormais être développé comme un système modulaire de correction sélective des interprétations ECG en texte libre.

Le système comprend six tâches distinctes :

1. comprendre ce que l’étudiant a réellement écrit ;
2. normaliser les formulations vers une ontologie ECG ;
3. déterminer leur validité clinique ;
4. calculer une décision pédagogique et un score ;
5. estimer la fiabilité de cette décision ;
6. s’abstenir ou demander une revue humaine lorsque la correction n’est pas suffisamment sûre.

La valeur durable du projet ne repose pas sur GPT-4o, GPT-5.6 ou un autre modèle particulier. Elle repose sur l’association de plusieurs actifs :

* ontologie ECG versionnée ;
* corpus de réponses authentiques ;
* annotations expertes ;
* goldens indépendants ;
* règles pédagogiques explicites ;
* benchmark verrouillé ;
* plateforme utilisée en conditions réelles ;
* validation prospective et multicentrique.

---

# 2. Principes directeurs

## 2.1 Maintenir quatre objets distincts

| Objet                          | Entrée           | Sortie                              | Finalité                          |
| ------------------------------ | ---------------- | ----------------------------------- | --------------------------------- |
| Ontologie                      | domaine ECG      | concepts, synonymes, relations      | représenter les connaissances     |
| Golden d’extraction            | réponse libre    | concepts réellement exprimés        | évaluer la compréhension du texte |
| Golden conceptuel de scoring   | cas ECG          | critères attendus et contradictions | définir le barème                 |
| Golden de décision par réponse | réponse à un cas | jugement global d’experts           | évaluer la correction finale      |

Une bonne extraction ne démontre pas que la note est juste.
Un barème cohérent ne démontre pas que le système corrige comme un enseignant.

## 2.2 Verrouiller l’évaluation avant l’optimisation

Une partie des cas et des réponses doit être retirée du développement avant les prochaines modifications importantes.

Ces données ne devront pas servir à ajuster :

* l’ontologie ;
* les synonymes ;
* les prompts ;
* les seuils ;
* les règles de scoring ;
* les mécanismes de confiance.

## 2.3 Conserver une architecture indépendante des modèles

Les briques suivantes doivent rester remplaçables :

* extracteur NER ;
* modèle d’embeddings ;
* moteur de recherche ;
* reranker ou juge ;
* modèle de feedback.

Les contrats d’entrée et de sortie doivent être stables et versionnés.

## 2.4 Mesurer le risque, pas seulement la performance moyenne

Les métriques centrales doivent inclure :

* fausse validation d’une réponse incorrecte ;
* surnotation ;
* contradiction majeure non détectée ;
* erreur cliniquement dangereuse ;
* proportion de réponses corrigées automatiquement ;
* risque d’erreur parmi les réponses corrigées automatiquement.

---

# 3. Roadmap priorisée

## P0 — Gouvernance et baseline

### P0.1 Figer une baseline scientifique

Créer une release ou un tag comprenant :

* `pipeline_version` ;
* `ontology_version` ;
* version des cas ;
* version du golden d’extraction ;
* version du golden de scoring ;
* versions des modèles ;
* dépendances Python ;
* rapport de métriques correspondant.

### Critère de sortie

Chaque prédiction historique peut être reliée à une configuration complète et identifiable.

> ✅ **Fait le 2026-08-01** — cf. `ecg-online/docs/BASELINE_P0.1.md`,
> `ecg-online/scripts/generate_baseline_report.py`,
> `ecg-online/data/baseline_report.json`, tag `baseline-p0.1-2026-08-01`.

---

### P0.2 Séparer les actifs publics et privés

Classer les fichiers en quatre catégories :

1. publiables ;
2. privés de recherche ;
3. données personnelles ou pédagogiques contrôlées ;
4. contenus soumis aux droits de tiers.

Les éléments à conserver hors du dépôt public comprennent notamment :

* réponses réelles ;
* annotations expertes ;
* jeux de test verrouillés ;
* cas et tracés non explicitement réutilisables ;
* rapports détaillés contenant des données individuelles.

### Critère de sortie

Un inventaire documenté indique pour chaque fichier son statut, son propriétaire et sa licence.

---

### P0.3 Créer une source de vérité unique pour les métriques

Chaque résultat doit préciser :

* tâche évaluée ;
* corpus ;
* split ;
* nombre de réponses ;
* version du pipeline ;
* version de l’ontologie ;
* définition de la métrique ;
* date d’exécution ;
* intervalle de confiance lorsque pertinent.

### Critère de sortie

Le README, les documents d’audit et les futurs manuscrits utilisent les mêmes chiffres.

> ✅ **Fait le 2026-08-01** — cf. `audit_doc/METRICS_LEDGER.md` (registre
> unique de toutes les métriques du projet, avec tâche/corpus/split/n/
> pipeline_version/ontology_version/définition/date pour chacune). README
> racine corrigé (chiffre "~92%" désormais daté/sourcé, distingué du F1
> d'extraction). Anciens chiffres incohérents (README 92%/RAG-onto 62,4%/
> ARCHITECTURE 42%/CSV 85,1%&60,2%) recensés et marqués obsolètes dans le
> registre (§5 "Métriques historiques marquées obsolètes").

---

## P1 — Golden conceptuel de scoring V2

L’extension du golden de scoring demeure la priorité principale.

Elle ne doit cependant pas commencer par l’ajout massif de concepts dans la structure actuelle. Le schéma doit d’abord être enrichi.

### P1.1 Définir le nouveau schéma

Chaque critère devrait pouvoir contenir :

```json
{
  "criterion_id": "case_12_diagnostic_principal",
  "concept_id": "BAV_COMPLET",
  "label": "Bloc auriculo-ventriculaire complet",
  "role": "required",
  "expected_status": "present",
  "importance": "major",
  "error_severity": "dangerous",
  "alternative_group": "diagnostic_principal",
  "group_logic": "ANY",
  "sufficient_alone": true,
  "minimum_specificity": "child_ok",
  "expert_confidence": "high",
  "evidence_source": "expert_consensus",
  "comment": ""
}
```

### Valeurs principales proposées

**Rôle**

* `required`
* `alternative`
* `optional`
* `exclusion`

**Statut attendu**

* `present`
* `absent`
* `hypothesis_acceptable`

**Importance**

* `major`
* `intermediate`
* `minor`

**Gravité d’une erreur**

* `none`
* `minor`
* `major`
* `dangerous`

**Logique de groupe**

* `ANY`
* `ALL`
* `AT_LEAST_N`

### Principe

Les pondérations numériques ne doivent pas encore être figées. Il faut d’abord formaliser correctement la logique clinique.

---

### P1.2 Réaliser un pilote avant les 75 cas

Tester le schéma sur 8 à 12 cas contrastés :

* ECG normal ;
* fibrillation atriale ;
* trouble de conduction ;
* tachycardie à QRS larges ;
* syndrome coronarien ;
* diagnostic étiologique ;
* cas comprenant une exclusion majeure ;
* cas comportant plusieurs réponses diagnostiques recevables.

### Critère de sortie

Aucune situation fréquente ne nécessite de champ improvisé ou de règle codée spécifiquement pour un cas.

---

### P1.3 Annotation indépendante multi-expert

Pour chaque cas :

1. expert 1 annote indépendamment ;
2. expert 2 annote indépendamment ;
3. les désaccords sont enregistrés ;
4. une adjudication est réalisée ;
5. la version consensuelle est produite ;
6. les annotations initiales restent conservées.

Les désaccords constituent eux-mêmes un résultat scientifique.

---

### P1.4 Migrer progressivement les 75 cas

Créer :

* un script de migration ;
* un validateur JSON ;
* un rapport de différences ;
* un audit des contradictions ;
* des tests de non-régression ;
* une interface d’annotation adaptée au nouveau schéma.

### Critère de sortie

Les 75 cas sont couverts sans modification silencieuse du comportement antérieur.

---

## P2 — Golden de décision humaine par réponse

Le golden conceptuel indique ce qui devrait être exigé.
Il ne remplace pas le jugement réel des enseignants devant une réponse complète.

### P2.1 Définir la grille d’évaluation humaine

Chaque réponse reçoit :

* classe globale :

  * exacte ;
  * acceptable ;
  * partielle ;
  * incorrecte ;
* score numérique ;
* présence d’une erreur clinique ;
* gravité maximale ;
* contradiction interne ;
* correction automatique acceptable ou non ;
* justification conceptuelle.

### P2.2 Constituer un corpus stratifié

Stratifier les réponses selon :

* famille ECG ;
* cas ;
* longueur ;
* niveau de performance ;
* négation ;
* hypothèse ;
* fautes orthographiques ;
* réponse télégraphique ou développée ;
* formulation fréquente ou rare.

### Cible initiale réaliste

Un premier corpus robuste pourrait comprendre :

* 400 à 600 réponses doublement annotées ;
* 30 à 40 cas suffisamment représentés ;
* adjudication des désaccords.

Un corpus plus large pourra être constitué ensuite.

### P2.3 Garder une vérité terrain humaine

Un LLM peut :

* proposer des concepts ;
* préremplir l’interface ;
* signaler les désaccords ;
* accélérer la saisie.

Il ne doit pas être l’arbitre final du golden utilisé pour l’évaluer.

---

## P3 — Splits et benchmark verrouillé

> **Statut (2026-08-10)** : décision prise avec l'expert compte tenu de la
> contrainte **« pas de nouveaux ECG disponibles »** — tout le dispositif P3
> doit fonctionner avec le jeu unique des 75 cas existants (golden V1 +
> corrections V2 du 2026-08-10). Voir détail des niveaux ci-dessous.

### P3.1 Organiser quatre niveaux d’évaluation

#### Niveau 1 — Nouvelles réponses sur des cas connus

Évalue la robustesse aux formulations.
✅ **Réalisable dès maintenant** — déjà largement couvert par
`extraction_golden.json` (100 réponses réelles annotées sur les cas
existants).

#### Niveau 2 — Nouveaux ECG dans une famille connue

Évalue la généralisation à un nouveau tracé et à un nouveau barème.
⛔ **Différé** — nécessite l'écriture de nouveaux cas, non disponibles
actuellement. À reprendre dès que de nouveaux ECG/barèmes seront produits.

#### Niveau 3 — Famille diagnostique non vue

Évalue le transfert conceptuel.
⛔ **Différé** — même contrainte que le niveau 2.

#### Niveau 4 — Centre externe

Évalue la généralisation pédagogique et linguistique.
⛔ **Différé** — nécessite des ECG/annotations d'un centre externe, non
disponibles actuellement.

---

### P3.2 Créer un test interne verrouillé

> **Décision (2026-08-10)** : pas de sous-ensemble séparé. **Les 75 cas
> existants (golden V1 + V2 corrigés) constituent la référence unique et
> verrouillée**, plutôt qu'un sous-échantillon dédié « test caché ».
>
> Justification :
> - il n'existe qu'un seul jeu de 75 cas — en sacrifier une partie comme
>   « dev set » réduirait d'autant la couverture des 11 familles cliniques,
>   déjà limitée ;
> - il ne s'agit pas de machine learning statistique optimisé sur les
>   données (où l'overfitting justifie un vrai holdout caché), mais de
>   corrections manuelles guidées par le raisonnement clinique — le risque
>   de sur-ajustement invisible est donc moindre ;
> - les 75 cas ayant déjà été extensivement révisés le 2026-08-10, isoler
>   maintenant un sous-ensemble « jamais touché » serait artificiel et ne
>   donnerait qu'une fausse impression de rigueur.
>
> **Verrouillage = discipline de process, pas de séparation de données** :
> - toute modification future d'un cas golden doit être justifiée par une
>   preuve clinique/pédagogique concrète (signalement étudiant, erreur
>   d'annotation avérée) et documentée via un script dédié + entrée de
>   changelog — jamais par « ça fait monter le score » ;
> - `scripts/generate_v1_v2_diff_report.py` sert de garde-fou de
>   non-régression : à chaque évolution du moteur de scoring, on regénère
>   un diff complet sur les 75 cas et on vérifie l'absence de régression
>   silencieuse.

---

### P3.3 Construire un challenge set

> Réalisable sans nouveaux ECG : il s'agit de construire des **réponses
> étudiantes synthétiques volontairement adversariales** sur les 75 cas
> existants, pas de nouveaux tracés. Ce chantier recoupe directement le
> « trou métrique » documenté dans
> `ecg-online/docs/SCORING_LOGIC_required_optional_alternative_exclusion.md`
> (redondance de crédit sur `alternative_group`, ex. cas 41 flutter) — le
> pattern « concept enfant plus spécifique » / « concept parent trop
> générique » ci-dessous doit explicitement couvrir ce cas de figure.

Inclure volontairement :

* bon diagnostic avec contradiction majeure ;
* mauvais diagnostic utilisant les bons mots-clés ;
* double négation ;
* diagnostic seulement hypothétique ;
* description juste sans diagnostic ;
* diagnostic juste sans justification ;
* concept parent trop générique ;
* concept enfant plus spécifique ;
* abréviation ambiguë ;
* fautes importantes ;
* plusieurs diagnostics concurrents ;
* réponse cherchant à manipuler le barème.

---

## P4 — Refonte du scoring

### P4.1 Séparer adéquation et sécurité

Produire deux dimensions distinctes :

#### Score d’adéquation

Mesure la couverture des critères attendus.

#### Score de sécurité

Mesure :

* concepts faux ;
* contradictions ;
* exclusions violées ;
* erreurs graves.

Le score final peut combiner les deux, mais elles doivent rester visibles séparément.

---

### P4.2 Calibrer les crédits ontologiques

Les valeurs actuelles accordées aux :

* parents ;
* enfants ;
* `requires` ;
* qualifiers ;
* supports ;
* implications ;
* négations ;

doivent être comparées aux jugements humains.

Comparer plusieurs stratégies :

* règles fixes d’experts ;
* calibration statistique ;
* modèle ordinal ;
* pondérations dépendant de la catégorie clinique.

---

### P4.3 Restreindre les conversions de négation

Une phrase comme :

> « pas de trouble de repolarisation »

ne doit pas, à elle seule, valider automatiquement un ECG globalement normal.

La conversion doit dépendre :

* de la portée de la négation ;
* du niveau ontologique ;
* des critères requis ;
* des autres concepts présents ;
* des contradictions éventuelles.

---

## P5 — Confiance et abstention réelle

### P5.1 Enregistrer les signaux de confiance

Pour chaque correction :

* méthode de résolution ;
* score lexical ;
* score dense ;
* écart entre les deux premiers candidats ;
* confiance du juge ;
* concepts non résolus ;
* contradictions ;
* stabilité entre répétitions ;
* désaccord entre modèles ;
* couverture des critères ;
* proximité avec les données annotées.

### P5.2 Calibrer la confiance contre les erreurs réelles

La confiance ne doit pas être définie arbitrairement.

Elle doit prédire :

* probabilité que la correction soit fausse ;
* probabilité de fausse validation ;
* probabilité d’erreur grave.

### P5.3 Implémenter de véritables états

* `SUCCESS` : correction automatique ;
* `LOW_CONFIDENCE` : correction prudente ou signalée ;
* `HUMAN_REVIEW` : file de validation ;
* `ABSTAIN` : aucune note automatique ;
* `TECHNICAL_ERROR` : problème technique distinct.

### P5.4 Produire une courbe couverture–risque

Pour chaque seuil :

* proportion corrigée automatiquement ;
* taux d’erreur ;
* taux de fausse validation ;
* taux d’erreur grave.

Le seuil est choisi sur le jeu de validation, puis évalué une seule fois sur le test verrouillé.

---

## P6 — Baselines et ablations

### Baselines minimales

1. règles lexicales ;
2. LLM direct avec correction de référence ;
3. LLM direct avec rubrique structurée ;
4. extraction + scoring sans juge ;
5. pipeline complet ;
6. encodeur ou reranker spécialisé ;
7. modèle local ou ouvert.

### Ablations

Évaluer séparément la suppression de :

* recherche dense ;
* BM25 ;
* juge LLM ;
* lexical backstop ;
* pattern inference ;
* relations ontologiques ;
* exclusions ;
* feedback génératif.

### Métriques

* extraction ;
* décision finale ;
* fausse validation ;
* erreur grave ;
* latence ;
* coût ;
* reproductibilité.

---

## P7 — Réduction de la dépendance technologique

### P7.1 Évaluer un extracteur spécialisé

Entraîner ou adapter un encodeur sur le golden d’extraction.

Architecture cible possible :

* règles et exact match pour les formes fréquentes ;
* encodeur spécialisé pour les entités habituelles ;
* LLM seulement pour les formulations rares ou ambiguës.

### P7.2 Prévoir un mode local

Remplacer progressivement :

* embeddings OpenAI par embeddings locaux ;
* juge GPT par reranker ou modèle local ;
* NER GPT par modèle spécialisé ;
* feedback génératif par gabarits lorsque possible.

### Critère de sortie

Une indisponibilité d’un fournisseur externe ne rend pas toute la plateforme inutilisable.

---

## P8 — Validation externe et pédagogique

### P8.1 Validation technique externe

Tester sur :

* nouveaux ECG ;
* étudiants d’un autre centre ;
* autre niveau de formation ;
* corpus anglophone ultérieur ;
* autre organisation pédagogique.

### P8.2 Validation prospective

Mesurer :

* temps de correction ;
* acceptabilité ;
* taux d’abstention ;
* recours à l’enseignant ;
* erreurs signalées ;
* coût ;
* progression des étudiants.

### P8.3 Efficacité pédagogique

L’objectif supérieur est de déterminer si le système améliore :

* la qualité des interprétations ultérieures ;
* la structure de la lecture ECG ;
* la détection des erreurs ;
* la rétention ;
* le transfert vers de nouveaux ECG.

---

# 4. Séquence immédiate de développement

Ordre recommandé :

1. créer une baseline versionnée ;
2. séparer les données publiques et privées ;
3. définir le schéma `scoring_v2` ;
4. sélectionner le futur test verrouillé ;
5. tester le schéma sur un pilote ;
6. construire l’interface multi-expert ;
7. migrer progressivement les 75 cas ;
8. constituer le golden de décision par réponse ;
9. comparer le score automatique aux décisions humaines ;
10. calibrer la sécurité et l’abstention ;
11. exécuter les baselines et ablations ;
12. lancer une validation externe.

---

# 5. Backlog concret

## À faire maintenant

* [ ] Créer une release `baseline-2026-07`.
* [ ] Exporter les versions des modèles et dépendances.
* [ ] Créer `scoring_schema_v2.json`.
* [ ] Ajouter un validateur de schéma.
* [ ] Choisir 8 à 12 cas pilotes.
* [ ] Choisir les cas du test verrouillé.
* [ ] Concevoir l’interface d’annotation indépendante.
* [ ] Définir la grille de décision globale par réponse.
* [ ] Documenter les licences et droits de chaque type de contenu.

## À faire après validation du pilote

* [ ] Migrer les 75 cas.
* [ ] Organiser la double annotation.
* [ ] Mesurer les désaccords.
* [ ] Adjuger les critères discutés.
* [ ] Constituer le corpus de réponses notées.
* [ ] Recalibrer les règles de scoring.
* [ ] Développer l’abstention effective.

## À ne pas faire immédiatement

* [ ] Ajouter des centaines de critères dans le schéma actuel.
* [ ] Optimiser les pondérations avant les annotations humaines.
* [ ] Modifier le pipeline à partir du test verrouillé.
* [ ] Utiliser un LLM comme vérité terrain finale.
* [ ] Résumer les performances par un F1 unique.
* [ ] Ouvrir tous les goldens avant d’avoir daté la priorité scientifique.

---

# 6. Stratégie de publication

## Article 1 — Méthodologie et benchmark

Contenu :

* formalisation de la tâche ;
* ontologie ;
* golden d’extraction ;
* golden de scoring ;
* golden de décision ;
* baselines ;
* généralisation ;
* correction sélective ;
* abstention.

## Article 2 — Validation pédagogique prospective

Contenu :

* utilisation réelle ;
* acceptabilité ;
* charge enseignante ;
* progression ;
* sécurité ;
* recours à la supervision humaine.

## Article 3 éventuel — Extension multicentrique ou multilingue

Contenu :

* transfert anglais ;
* adaptation inter-centres ;
* évolution de l’ontologie ;
* robustesse linguistique.

---

# 7. Définition du succès

Le projet sera scientifiquement et technologiquement défendable lorsqu’il démontrera simultanément :

1. une extraction fiable des concepts exprimés ;
2. une décision concordante avec plusieurs experts ;
3. une faible fréquence de fausse validation ;
4. une détection des erreurs graves ;
5. une abstention calibrée ;
6. une généralisation à de nouveaux cas ;
7. une validation dans un autre centre ;
8. une architecture indépendante des fournisseurs ;
9. un bénéfice pédagogique ou organisationnel mesurable.

L’objectif n’est pas de construire un golden unique aussi volumineux que possible.

L’objectif est de construire plusieurs vérités terrain complémentaires, versionnées et indépendantes du développement, capables d’évaluer les générations successives du moteur.
