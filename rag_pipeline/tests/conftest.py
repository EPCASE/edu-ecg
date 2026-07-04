"""
Configuration pytest pour les tests du pipeline RAG.

Rôle :
  - Ajoute `rag_pipeline/` au sys.path pour que `import scoring_v3`,
    `import semantic_layer`, etc. fonctionnent sans installation.
  - Charge l'ontologie V2 une seule fois par session de test.

Aucune clé OpenAI n'est requise : ces tests ne touchent QUE la couche
symbolique déterministe (scoring, sémantique). Aucun appel réseau.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# --- Chemins -----------------------------------------------------------------
# tests/ → rag_pipeline/ → (ECG lecture)/
RAG_PIPELINE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = RAG_PIPELINE_DIR.parent
ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology_v2.json"

# Rendre les modules du pipeline importables (import à plat, comme le pipeline)
if str(RAG_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_PIPELINE_DIR))


@pytest.fixture(scope="session", autouse=True)
def _load_ontology():
    """Charge l'ontologie V2 une fois pour toute la session de test."""
    import semantic_layer

    assert ONTOLOGY_PATH.exists(), (
        f"Ontologie introuvable : {ONTOLOGY_PATH}. "
        "Les tests de scoring nécessitent data/ontology_v2.json."
    )
    semantic_layer.load_ontology_v2(ONTOLOGY_PATH)
    yield


@pytest.fixture(scope="session")
def ontology():
    """Expose le dict de concepts pour les tests qui veulent l'inspecter."""
    import semantic_layer

    return semantic_layer._get_ontology_v2()
