# 📋 Index des documents d'audit & runbooks

> Point d'entrée unique pour s'y retrouver parmi les documents `AUDIT*.md` et
> runbooks à la racine du repo. Chacun couvre un **angle distinct**, ce ne sont
> **pas des doublons**.

| Document | Angle | Répond à |
|---|---|---|
| **[`AUDIT.md`](./AUDIT.md)** | Robustesse **scientifique** du pipeline | La correction reflète-t-elle vraiment la qualité clinique ? Précision/rappel de l'extraction, golden set, taux d'erreur réel vs "hallucination" apparente. |
| **[`AUDIT_ARCHITECTURE_2026.md`](./AUDIT_ARCHITECTURE_2026.md)** | Hygiène de **repo & code** | Combien de copies dupliquées du pipeline ? Quels fichiers sont morts ? Comment organiser les 4 workspaces ? |
| **[`AUDIT_TECHNOLOGIQUE_2026.md`](./AUDIT_TECHNOLOGIQUE_2026.md)** | Choix **IA/techno futurs** | Peut-on fine-tuner ? Garder le passage déterministe ? Une solution locale autonome est-elle possible ? Intégrer l'ontologie dans un LLM ? Le neurosymbolique est-il toujours le bon choix ? |
| **[`ONTOLOGIE_DOCTRINE.md`](./ONTOLOGIE_DOCTRINE.md)** | Doctrine de **structuration de l'ontologie** | Comment décider si un concept doit être atomique, composé, rejeté (topographie v1), etc. — utilisé comme system prompt d'audit ontologique. |
| **[`RUNBOOK_REBUILD_ONTOLOGIE.md`](./RUNBOOK_REBUILD_ONTOLOGIE.md)** *(ex-`PART_B_RUNBOOK.md`)* | Procédure opérationnelle | Comment réintégrer un `.owl` réannoté (WebProtégé) sans perdre la couche d'enrichissement manuelle (overlay, merge 3-way). |
| **[`_AUDIT_TRAME_TRAVAIL.md`](./_AUDIT_TRAME_TRAVAIL.md)** | Journal de travail | Trame historique de suivi des sessions d'audit — contenu de référence, conservé à la demande. |

## ⚠️ Note sur le terme « Partie A / Partie B »

`ARCHITECTURE.md` utilise **« Partie A »** pour désigner le **pipeline RAG
neurosymbolique** (les 6 briques, `ecg-online/rag_pipeline/`) et **« Partie B »**
pour l'**app `ecg-online`** de correction en ligne (§12.1).

Le fichier `RUNBOOK_REBUILD_ONTOLOGIE.md` s'appelait auparavant `PART_B_RUNBOOK.md`
mais **n'a aucun rapport** avec cette distinction Partie A/B — il parle du rebuild
de l'ontologie depuis un `.owl` réannoté. Il a été renommé le 2026-07-29 pour lever
l'ambiguïté.

## Ordre de lecture recommandé

1. `AUDIT.md` — comprendre si les résultats sont fiables (base scientifique).
2. `AUDIT_ARCHITECTURE_2026.md` — comprendre l'état du code/repo.
3. `AUDIT_TECHNOLOGIQUE_2026.md` — décider des évolutions futures (fine-tuning, local, etc.).
4. `ONTOLOGIE_DOCTRINE.md` / `RUNBOOK_REBUILD_ONTOLOGIE.md` — au besoin, pour la maintenance de l'ontologie.
