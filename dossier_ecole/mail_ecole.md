# 📧 Mail pour Farouk — Dossier École ISIMA

> **Statut** : prêt à envoyer — adapter le `[...]` si besoin.

---

**À :** Farouk Toumani  
**Objet :** Dossier Edu-ECG — 4 cas annotés + métriques de confiance

---

Bonjour Farouk,

Comme convenu, voici le dossier technique du pipeline RAG Neurosymbolique d'Edu-ECG.

### Ce qu'il y a dedans

Le dossier `dossier_ecole/` contient :

- **4 cas annotés** (`cas_annotes/*.json`) — trace complète du pipeline avec les
  métriques de confiance réelles : cosine, BM25, RRF, top-k candidats, confiance LLM.
  Scores obtenus : 80%, 100%, 40%, 100%.
- **Architecture pipeline** (`docs/architecture_pipeline.md`) — les 5 briques :
  NER GPT-4o → Hybrid Search (dense+BM25, RRF) → Juge LLM → Scoring hiérarchique → Feedback
- **Limites connues** (`docs/limites_connues.md`) — 9 axes identifiés, dont 8 ouverts,
  classés par criticité et type de projet (TP → stage)
- **Schéma JSON** (`schemas/format_annotation.json`) — pour l'annotation humaine

### Accès au code

- **Repo** : [github.com/EPCASE/edu-ecg](https://github.com/EPCASE/edu-ecg) — branche `RAGontologique`
- **Pipeline** : `rag_pipeline/` (Python, OpenAI embeddings 1536d + GPT-4o-mini, ontologie OWL 292 concepts)
- **Données terrain** : 39 étudiants évalués sur 15 cas ECG, ~4.5 Mo de corrections JSON

Le `README.md` du dossier donne le mode d'emploi de lecture.

Je reste dispo pour en discuter quand tu veux.

Grégoire

---

*PJ : `dossier_ecole/`*
