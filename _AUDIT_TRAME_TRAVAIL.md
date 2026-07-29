# 🗂️ Trame de tra| 7 | Mettre à jour l'intégralité de la documentation | 🟡 constat fait | inventaire complet fait, mises à jour reportées après décision §8 |
| 8 | Supprimer les doublons (code) | ✅ analysé | duplication confirmée + quantifiée, recommandation écrite, décision utilisateur attendue |

## ✅ Document final produit

`AUDIT_ARCHITECTURE_2026.md` (racine `ECG lecture/`) — audit complet des 8 angles, avec plan d'action
proposé (non exécuté). Cette trame peut être supprimée une fois l'audit validé par l'utilisateur.il — Audit architecture 2026-07-29

> Document de pilotage interne (jetable une fois l'audit final terminé). Sert à ne rien oublier
> et à tracer l'avancement sur un chantier volumineux. Le livrable final est `AUDIT_ARCHITECTURE_2026.md`.
> **Règle absolue** : aucune suppression / modification de fichier existant pendant cette phase de
> reconnaissance. Uniquement lecture, analyse, rédaction. Toute action destructive sera proposée
> et validée avant exécution.

## Les 8 angles demandés par l'utilisateur

| # | Angle | Statut | Notes |
|---|-------|:------:|-------|
| 1 | Mettre à plat l'architecture (vue d'ensemble 4 workspaces) | 🟡 en cours | reconnaissance de surface faite |
| 2 | Généricité des briques vs "patchs" correctifs | ⬜ à faire | nécessite lecture ciblée de `rag_pipeline/*.py` |
| 3 | Anticiper le passage à l'anglais | ⬜ à faire | scan chaînes FR en dur, prompts, UI, ontologie name_en |
| 4 | Solutions alternatives / pistes d'amélioration | 🟡 partiel | déjà esquissé §7 de l'`AUDIT.md` existant, à enrichir |
| 5 | Organiser le repo en local (proposition, pas d'exécution) | 🟡 en cours | cartographie des dossiers/doublons faite |
| 6 | Supprimer les fichiers inutiles (liste proposée, PAS exécutée) | 🟡 en cours | premières cibles identifiées |
| 7 | Mettre à jour l'intégralité de la documentation | ⬜ à faire | inventaire des .md à faire |
| 8 | Supprimer les doublons (code) | 🟡 en cours | duplication `RAG ontologique` ↔ `ecg-online/rag_pipeline` confirmée + quantifiée |

## Décisions déjà validées avec l'utilisateur

- ✅ Un **nouveau document** séparé sera créé (`AUDIT_ARCHITECTURE_2026.md`), sans toucher à `AUDIT.md` existant.
- ✅ L'audit doit **recommander une source de vérité unique** pour `rag_pipeline` (duplication confirmée
  comme risque réel, pas juste cosmétique — cf. divergence `scoring_v3.py`).
- ✅ Autonomie accordée pour la suite de la reconnaissance (angles 2, 3, 5, 6, 7, 8).
- ❌ **INTERDIT** : toute suppression ou modification de fichier sans validation préalable explicite.
  Le résultat de cette phase = un document de recommandations + une liste d'actions proposées,
  pas des actions exécutées.

## Plan d'exécution (ordre prévu)

1. [x] Cartographie 4 workspaces (tailles, doublons, archives) — fait, résumé dans réponse précédente.
2. [x] Quantification duplication `RAG ontologique` vs `ecg-online/rag_pipeline` (hash + diff lignes).
3. [ ] Lecture ciblée des 5 fichiers divergents pour comprendre *lequel* est la version la plus à jour
   fichier par fichier (pas seulement scoring_v3.py déjà fait) → `candidate_report.py` (182 lignes diff,
   à investiguer en priorité), `ner_extractor.py`, `hybrid_search.py`, `neurosymbolic_judge.py`.
4. [ ] Scan "généricité vs patch" : grep sur `rag_pipeline/*.py` (tous workspaces) pour motifs suspects
   (cas particuliers hardcodés, `if concept_id ==`, listes d'exceptions nominatives, TODO/FIXME/HACK).
5. [ ] Scan "anglicisation" : chaînes FR en dur (prompts système, messages UI, noms de variables),
   vérifier usage réel du champ `name_en` de l'ontologie, lister tout ce qui bloquerait un passage EN.
6. [ ] Inventaire documentation complète (tous `.md` des 4 workspaces) : dater, identifier redondances/
   obsolescence (ex. chiffres caducs dans `ARCHITECTURE.md`, `README.md`).
7. [ ] Vérifier contenu exact des dossiers `_ARCHIVE_*`, `rag_index*`, `_standalone/` pour confirmer
   qu'ils sont bien candidats suppression (pas de code vivant dedans).
8. [ ] Rédiger `AUDIT_ARCHITECTURE_2026.md` complet (8 sections + plan d'action priorisé, sans l'exécuter).
9. [ ] Présenter à l'utilisateur pour validation avant toute action destructive.

## Journal des découvertes (au fil de l'eau)

- 2026-07-29 : `RAG ontologique/_ARCHIVE_2026-07-06` = 867MB, dont 865.6MB = 8 fichiers HTML
  d'export de rapports (avril 2026), aucune valeur code. Candidat suppression évident (à confirmer,
  pas exécuté).
- 2026-07-29 : 5/12 fichiers pipeline divergents entre les 2 copies. `scoring_v3.py` : la copie
  `ecg-online` contient un correctif (bug "requires manquant affiché comme trouvé") **absent** de
  la copie `RAG ontologique`. Preuve concrète que la duplication cause un vrai risque de régression
  silencieuse, pas juste de la dette cosmétique.
- 2026-07-29 : `ECG evaluation/goldenset_extraction/` = 85 scripts `_*.py` jetables (convention du
  projet), tous datés du 06/07/2026 22:10 (probablement générés en lot / session unique).
- 2026-07-29 : `candidate_report.py` (182 lignes diff) : `ecg-online` contient une fonctionnalité
  ENTIÈRE absente de `RAG ontologique` (`_lexical_backstop_ids`, rattrapage déterministe post-NER).
  `ner_extractor.py`/`neurosymbolic_judge.py` : `ecg-online` a `temperature=0, seed=42` (déterminisme),
  absent de `RAG ontologique`. `hybrid_search.py` : `ecg-online` a un fallback de chemin d'index
  vendoré, absent de `RAG ontologique`. **Conclusion sans ambiguïté : `ecg-online/rag_pipeline` est
  strictement en avance sur `RAG ontologique` sur les 5 fichiers divergents — ce n'est pas une
  branche parallèle avec valeur propre, c'est un instantané figé et obsolète.**
- 2026-07-29 : Scan angle "généricité vs patch" (grep sur `app/*.py` + `rag_pipeline/*.py`) : aucun
  ID de concept ou numéro de cas codé en dur trouvé, aucun marqueur TODO/FIXME/HACK. Le code
  s'auto-documente comme générique ("aucun couple codé en dur, tout est lu dans l'ontologie").
  **Bonne nouvelle** : la crainte de "patchs correctifs" ne se vérifie pas dans le cœur du pipeline.
- 2026-07-29 : Scan angle "anglais" : l'ontologie (`ontology_v2.json`) a déjà un champ
  `concept_name_en` rempli pour chaque concept. MAIS ce champ n'est utilisé QUE par des scripts
  d'audit/construction (`_recon_synonymes.py`, `convert_owl_to_v2.py`...), **jamais lu à l'exécution**
  par `app/` ou `rag_pipeline/`. Tous les `SYSTEM_PROMPT` (NER, juge, annotateur, feedback pédagogique)
  sont en français en dur, aucune couche i18n/locale, aucun paramètre `lang=` nulle part.
- 2026-07-29 : Inventaire documentation complet (hors dossiers `.codex`/`_bmad` qui sont des fichiers
  d'outillage, pas des docs projet) : **3 copies de `ARCHITECTURE_PIPELINE.md`** (`_standalone/`,
  `rag_pipeline/`, `RAG ontologique/`) et **2 `ARCHITECTURE.md`** (`ECG lecture/` racine et
  `_standalone/`) — duplication documentaire directement corrélée à la duplication de code.
