# Archive Developpement - Edu-ECG
Date: 2026-01-11 18:11
Script: cleanup_simple.ps1

## MODULES EN PRODUCTION (CONSERVES)

### Modules principaux
- frontend/ecg_session_builder.py
- frontend/correction_llm_poc.py

### Backend services
- backend/services/concept_decomposer.py (CRITIQUE)
- backend/services/llm_service.py
- backend/services/llm_semantic_matcher.py

### Extracteurs ontologie (VITAUX)
- backend/owl_to_json_converter.py
- backend/rdf_owl_extractor.py
- backend/pdf_extractor.py
- regenerate_ontology.py
- enrich_ontology_synonyms.py

## CONTENU ARCHIVE

### Prototypes (prototypes/)
13 fichiers archives

### Tests (tests_old/)
14 fichiers archives

### Scripts (scripts/)
10 fichiers archives

### Documentation (docs_old/)
14 fichiers archives

## RECUPERATION

Pour recuperer un fichier:
Copy-Item "dev_archive/[dossier]/[fichier]" "[destination]/"

## TESTS

Test modules:
- .\test_ecg_session_builder.bat
- .\test_correction_llm_poc.bat
