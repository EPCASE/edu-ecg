# 📦 Données Edu-ECG — Données pour le pipeline

> Complément au repo GitHub [EPCASE/edu-ecg](https://github.com/EPCASE/edu-ecg) (branche `RAGontologiqueV2`).
> Le code est sur GitHub, **ces données ne le sont pas** (poids des images).

## Contenu du zip

```
edu-ecg-data-share.zip  (67 Mo)
├── goldenset/          ← 15 cas ECG annotés par cardiologue expert
│   └── case_*/
│       ├── ecg_1.png         (image ECG, 1-3 Mo)
│       └── metadata.json     (annotations, expected_concepts, commentaire)
│
├── corrections/        ← 43 étudiants déjà évalués par le pipeline V3
│   ├── ECG-XXXX.json   (réponses + score + trace pipeline complète)
│   ├── golden.json     (golden set agrégé, format Streamlit)
│   └── data.json       (configuration session)
│
└── images_ecg/         ← Les 15 images ECG sources (1.png à 15.png)
```

## Structure d'un cas du goldenset

Chaque sous-dossier `goldenset/case_*/` contient :

```json
{
  "case_id": "case_20260223_220627_22325933",
  "name": "1",
  "category": "Normal",
  "difficulty": "🟢 Débutant",
  "annotations": [
    {
      "concept": "ECG normal",
      "annotation_role": "🎯 Diagnostic validant",
      "coefficient": 1.0
    },
    {
      "concept": "Bloc interatrial",
      "annotation_role": "📝 Description",
      "coefficient": 1.0
    }
  ],
  "expected_concepts": ["ECG normal"],
  "commentaire_correcteur": "C'est ECG est normal, mais il existe..."
}
```

## Structure d'une correction étudiante

Chaque fichier `corrections/ECG-XXXX.json` contient pour chaque cas (1 à 15) :

```json
{
  "cases": {
    "10": {
      "report": {
        "score_final_pct": 100,
        "concepts_extraits": [
          {
            "terme_brut": "BBG",
            "ontology_id": "BLOC_DE_BRANCHE_GAUCHE",
            "method": "coupe_circuit",
            "statut": "present",
            "top_k_candidats": [...]
          }
        ]
      }
    }
  }
}
```

## Comment l'utiliser

1. **Cloner le repo code** : `git clone https://github.com/EPCASE/edu-ecg.git -b RAGontologiqueV2`
2. **Décompresser ce zip** à côté du repo
3. **Placer les dossiers** :
   - `goldenset/` → utilisé par les notebooks `ECG evaluation/*.ipynb`
   - `corrections/` → utilisé pour les benchmarks et les rapports
   - `images_ecg/` → utilisé par l'app de collecte Streamlit

## Pipeline en bref

```
Texte étudiant → NER (GPT-4o) → Recherche Hybride (Dense+BM25)
              → Juge Neurosymbolique → Scoring V3 → Feedback
```

- **Ontologie** : 345 concepts (dans `ECG lecture/data/ontology_v2.json` du repo)
- **Coût** : ~$0.02 / cas étudiant
- **Documentation** : `ARCHITECTURE.md` dans le repo

## Variables d'environnement requises

```bash
OPENAI_API_KEY=sk-...
```

## Contact

Grégoire Massoullié — CHU Clermont-Ferrand
