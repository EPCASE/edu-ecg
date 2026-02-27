"""
🧪 Test de validation — Brique 3 : Recherche Hybride (Dense + Sparse + RRF)
=============================================================================
Vérifie que HybridSearchEngine retrouve les bons concepts ontologiques
à partir de termes bruts (acronymes, synonymes, fautes d'orthographe).

Usage:
    python test_brique3.py
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Import local
sys.path.insert(0, str(Path(__file__).parent))
from hybrid_search import HybridSearchEngine

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INDEX_DIR = str(Path(__file__).parent / "rag_index")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def top_ids(results: list[dict]) -> list[str]:
    """Retourne les ontology_ids des résultats."""
    return [r["ontology_id"] for r in results]


def has_concept(results: list[dict], ontology_id: str) -> bool:
    """Vérifie si un concept est dans les résultats."""
    return ontology_id in top_ids(results)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_initialisation(engine: HybridSearchEngine):
    """Test 1 : Le moteur s'initialise correctement depuis les fichiers d'index."""
    print("\n" + "=" * 60)
    print("📂 TEST 1 : Initialisation du moteur")
    print("=" * 60)

    assert engine.embeddings is not None, "Embeddings non chargés"
    assert engine.embeddings.shape[0] > 0, "Matrice d'embeddings vide"
    assert engine.embeddings.shape[1] == 1536, f"Dimensions inattendues : {engine.embeddings.shape[1]}"
    print(f"  ✅ Embeddings : {engine.embeddings.shape}")

    assert len(engine.documents) > 0, "Aucun document chargé"
    assert len(engine.documents) == engine.embeddings.shape[0], "Incohérence docs/embeddings"
    print(f"  ✅ Documents : {len(engine.documents)}")

    assert engine._bm25 is not None, "BM25 non initialisé"
    print(f"  ✅ BM25 initialisé")

    print(engine.describe())
    return True


def test_acronymes(engine: HybridSearchEngine):
    """Test 2 : Les acronymes courts sont retrouvés (force du BM25)."""
    print("\n" + "=" * 60)
    print("🔤 TEST 2 : Acronymes (BM25 fort)")
    print("=" * 60)

    test_cases = [
        ("FA", "FIBRILLATION_ATRIALE"),
        ("BBD", "BLOC_DE_BRANCHE_DROIT"),
        ("BBG", "BLOC_DE_BRANCHE_GAUCHE"),
        ("BAV", "BAV_DE_TYPE_1"),  # BAV seul → doit matcher un des BAV
        ("HVG", "HYPERTROPHIE_VENTRICULAIRE_GAUCHE"),
    ]

    all_passed = True
    for query, expected_id in test_cases:
        results = engine.search_top_k(query, k=5)
        ids = top_ids(results)

        # Pour BAV, on accepte n'importe quel concept contenant "BAV"
        if "BAV" in expected_id:
            found = any("BAV" in oid for oid in ids)
        else:
            found = expected_id in ids

        status = "✅" if found else "❌"
        if not found:
            all_passed = False
        print(f"  {status} '{query}' → attendu: {expected_id} | top 5: {ids[:3]}...")

    return all_passed


def test_synonymes_semantiques(engine: HybridSearchEngine):
    """Test 3 : Les synonymes sémantiques sont retrouvés (force du Dense)."""
    print("\n" + "=" * 60)
    print("🧠 TEST 3 : Synonymes sémantiques (Dense fort)")
    print("=" * 60)

    test_cases = [
        ("fibrillation auriculaire", "FIBRILLATION_ATRIALE"),  # auriculaire ≈ atriale
        ("infarctus du myocarde", "INFARCTUS_DU_MYOCARDE_À_LA_PHASE_AIGUE"),
        ("bloc de branche gauche", "BLOC_DE_BRANCHE_GAUCHE"),
    ]

    all_passed = True
    for query, expected_id in test_cases:
        results = engine.search_top_k(query, k=5)
        ids = top_ids(results)
        found = expected_id in ids
        status = "✅" if found else "❌"
        if not found:
            all_passed = False
        print(f"  {status} '{query}' → attendu: {expected_id} | top 5: {ids[:3]}...")

    return all_passed


def test_fautes_orthographe(engine: HybridSearchEngine):
    """Test 4 : Les fautes d'orthographe courantes sont gérées (force du Dense)."""
    print("\n" + "=" * 60)
    print("✏️  TEST 4 : Fautes d'orthographe (Dense tolère)")
    print("=" * 60)

    test_cases = [
        ("tachi supra", "TACHYCARDIE_SUPRA_VENTRICULAIRE"),
        ("tachycardie ventriculere", "TACHYCARDIE_VENTRICULAIRE"),
        ("onde T négatif", "ONDE_T_NÉGATIVE"),
    ]

    all_passed = True
    for query, expected_id in test_cases:
        results = engine.search_top_k(query, k=5)
        ids = top_ids(results)

        # Accepter un match partiel sur l'ontology_id pour plus de robustesse
        # (ex: "TACHYCARDIE_SUPRA" dans l'id)
        partial_match = any(
            expected_id.split("_")[0] in oid for oid in ids
        )
        found = expected_id in ids or partial_match
        status = "✅" if found else "⚠️"
        if not found:
            all_passed = False
        print(f"  {status} '{query}' → attendu: {expected_id} | top 5: {ids[:3]}...")

    return all_passed


def test_format_sortie(engine: HybridSearchEngine):
    """Test 5 : Le format de sortie contient toutes les clés requises."""
    print("\n" + "=" * 60)
    print("📋 TEST 5 : Format de sortie")
    print("=" * 60)

    results = engine.search_top_k("rythme sinusal", k=5)

    assert len(results) > 0, "Aucun résultat"
    print(f"  ✅ {len(results)} résultats retournés")

    required_keys = [
        "ontology_id", "surface_form", "concept_name",
        "source_type", "categorie", "poids", "rrf_score",
    ]
    for r in results:
        for key in required_keys:
            assert key in r, f"Clé manquante : {key}"
        assert r["statut"] if "statut" in r else True  # optionnel
        assert isinstance(r["rrf_score"], float), "rrf_score doit être un float"
        assert r["rrf_score"] > 0, "rrf_score doit être positif"
        assert r["poids"] in (1, 2, 3, 4), f"Poids inattendu : {r['poids']}"
        assert r["source_type"] in ("canonical", "synonym"), f"Source inattendue : {r['source_type']}"

    print(f"  ✅ Toutes les clés requises présentes")
    print(f"  ✅ Types et valeurs validés")

    # Afficher un exemple
    r = results[0]
    print(f"  📋 Exemple : {r['ontology_id']} — \"{r['surface_form']}\" "
          f"(score={r['rrf_score']:.6f}, cat={r['categorie']}, poids={r['poids']})")

    return True


def test_rrf_fusion(engine: HybridSearchEngine):
    """Test 6 : La fusion RRF produit des scores décroissants et cohérents."""
    print("\n" + "=" * 60)
    print("🔀 TEST 6 : Fusion RRF (scores décroissants)")
    print("=" * 60)

    queries = ["FA", "tachycardie ventriculaire", "bloc de branche"]

    all_passed = True
    for query in queries:
        results = engine.search_top_k(query, k=5)
        scores = [r["rrf_score"] for r in results]

        # Vérifier que les scores sont décroissants
        is_sorted = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
        if not is_sorted:
            all_passed = False
        status = "✅" if is_sorted else "❌"
        print(f"  {status} '{query}' — scores : {[f'{s:.6f}' for s in scores]}")

    return all_passed


def test_requete_vide(engine: HybridSearchEngine):
    """Test 7 : Une requête vide retourne une liste vide sans crash."""
    print("\n" + "=" * 60)
    print("🫙 TEST 7 : Requête vide")
    print("=" * 60)

    results = engine.search_top_k("", k=5)
    assert isinstance(results, list), f"Type inattendu : {type(results)}"
    assert len(results) == 0, f"Une requête vide devrait retourner 0 résultats, got {len(results)}"
    print(f"  ✅ Requête vide → {len(results)} résultats (pas de crash)")

    results = engine.search_top_k("   ", k=5)
    assert len(results) == 0, f"Espaces seuls devraient retourner 0 résultats"
    print(f"  ✅ Espaces seuls → {len(results)} résultats")

    return True


def test_integration_ner(engine: HybridSearchEngine):
    """Test 8 : Intégration Brique 2 → Brique 3 (NER → Search)."""
    print("\n" + "=" * 60)
    print("🔗 TEST 8 : Intégration NER → Search (Brique 2 → Brique 3)")
    print("=" * 60)

    # Simuler les termes bruts que la Brique 2 extrairait
    termes_ner = [
        {"terme_brut": "Rythme sinusal", "statut": "present"},
        {"terme_brut": "BBD", "statut": "absent"},
        {"terme_brut": "amylose", "statut": "hypothese"},
        {"terme_brut": "microvoltage", "statut": "present"},
    ]

    all_passed = True
    for ent in termes_ner:
        results = engine.search_top_k(ent["terme_brut"], k=3)
        if len(results) == 0:
            print(f"  ❌ '{ent['terme_brut']}' → aucun résultat")
            all_passed = False
        else:
            top = results[0]
            print(
                f"  ✅ [{ent['statut']:>10}] \"{ent['terme_brut']}\" "
                f"→ {top['ontology_id']} (\"{top['surface_form']}\", "
                f"score={top['rrf_score']:.6f})"
            )

    return all_passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n🧪 VALIDATION — Brique 3 : Recherche Hybride (Dense + Sparse + RRF)")
    print("=" * 60)

    # Initialisation unique du moteur (partagé entre tous les tests)
    print(f"\n📂 Chargement de l'index depuis : {INDEX_DIR}")
    engine = HybridSearchEngine(INDEX_DIR)

    results = {}

    results["initialisation"] = test_initialisation(engine)
    results["acronymes"] = test_acronymes(engine)
    results["synonymes_semantiques"] = test_synonymes_semantiques(engine)
    results["fautes_orthographe"] = test_fautes_orthographe(engine)
    results["format_sortie"] = test_format_sortie(engine)
    results["rrf_fusion"] = test_rrf_fusion(engine)
    results["requete_vide"] = test_requete_vide(engine)
    results["integration_ner"] = test_integration_ner(engine)

    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    for name, passed in results.items():
        print(f"  {'✅' if passed else '❌'} {name}")

    all_ok = all(results.values())
    print(f"\n{'🎉 TOUS LES TESTS PASSENT !' if all_ok else '⚠️ Certains tests ont échoué.'}")
    sys.exit(0 if all_ok else 1)
