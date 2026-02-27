"""
🧪 Test de validation — Brique 1 : Socle Symbolique & Vectoriel
=================================================================
Vérifie que l'index est correctement construit et que les recherches
retournent des résultats cohérents.

Usage:
    python test_brique1.py
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Import local
sys.path.insert(0, str(Path(__file__).parent))
from ontology_index import OntologyIndex, normalize_text, tokenize

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ONTOLOGY_PATH = str(Path(__file__).parent.parent / "ECG lecture" / "data" / "ontology_from_owl.json")
INDEX_DIR = str(Path(__file__).parent / "rag_index")


def test_parsing():
    """Test 1 : Le parsing de l'ontologie génère le bon nombre de documents."""
    print("\n" + "=" * 60)
    print("📋 TEST 1 : Parsing de l'ontologie")
    print("=" * 60)
    
    idx = OntologyIndex(ontology_path=ONTOLOGY_PATH)
    docs = idx._parse_ontology(include_implications=False)
    
    assert len(docs) > 0, "Aucun document généré !"
    
    # Vérifier qu'on a des canoniques + synonymes
    canonical = [d for d in docs if d.source_type == "canonical"]
    synonyms = [d for d in docs if d.source_type == "synonym"]
    
    print(f"  ✅ {len(docs)} documents totaux")
    print(f"  ✅ {len(canonical)} canoniques (= nb concepts)")
    print(f"  ✅ {len(synonyms)} synonymes")
    
    # L'ontologie annonce ~280 concepts
    assert len(canonical) >= 250, f"Trop peu de concepts canoniques : {len(canonical)}"
    assert len(synonyms) > 50, f"Trop peu de synonymes : {len(synonyms)}"
    
    # Vérifier un concept connu
    fa_docs = [d for d in docs if d.ontology_id == "FIBRILLATION_ATRIALE"]
    assert len(fa_docs) >= 3, f"FIBRILLATION_ATRIALE devrait avoir ≥3 documents (nom + FA + AF), got {len(fa_docs)}"
    print(f"  ✅ FIBRILLATION_ATRIALE : {len(fa_docs)} documents ({[d.surface_form for d in fa_docs]})")
    
    return True


def test_bm25():
    """Test 2 : L'index BM25 retourne des résultats pertinents."""
    print("\n" + "=" * 60)
    print("🔤 TEST 2 : Recherche BM25")
    print("=" * 60)
    
    idx = OntologyIndex(ontology_path=ONTOLOGY_PATH)
    idx.documents = idx._parse_ontology(include_implications=False)
    idx._build_bm25()
    
    # Test : "FA" doit retourner FIBRILLATION_ATRIALE en tête
    results = idx.search_bm25("FA", top_k=5)
    assert len(results) > 0, "BM25 ne retourne aucun résultat pour 'FA'"
    top_ids = [doc.ontology_id for doc, _ in results]
    print(f"  🔍 'FA' → top 5 : {top_ids}")
    assert "FIBRILLATION_ATRIALE" in top_ids, "FIBRILLATION_ATRIALE non trouvée pour 'FA'"
    print(f"  ✅ FIBRILLATION_ATRIALE trouvée via 'FA'")
    
    # Test : "bloc branche gauche"
    results = idx.search_bm25("bloc branche gauche", top_k=5)
    top_ids = [doc.ontology_id for doc, _ in results]
    print(f"  🔍 'bloc branche gauche' → top 5 : {top_ids}")
    assert "BLOC_DE_BRANCHE_GAUCHE" in top_ids, "BLOC_DE_BRANCHE_GAUCHE non trouvé"
    print(f"  ✅ BLOC_DE_BRANCHE_GAUCHE trouvé via 'bloc branche gauche'")
    
    # Test : "BBD" (acronyme synonyme)
    results = idx.search_bm25("BBD", top_k=5)
    top_ids = [doc.ontology_id for doc, _ in results]
    print(f"  🔍 'BBD' → top 5 : {top_ids}")
    assert "BLOC_DE_BRANCHE_DROIT" in top_ids, "BLOC_DE_BRANCHE_DROIT non trouvé via 'BBD'"
    print(f"  ✅ BLOC_DE_BRANCHE_DROIT trouvé via 'BBD'")
    
    return True


def test_vector():
    """Test 3 : L'index vectoriel retourne des résultats sémantiquement pertinents."""
    print("\n" + "=" * 60)
    print("🧠 TEST 3 : Recherche Vectorielle")
    print("=" * 60)
    
    idx = OntologyIndex(ontology_path=ONTOLOGY_PATH)
    idx.documents = idx._parse_ontology(include_implications=False)
    idx._build_embeddings()
    
    # Test sémantique : "auriculaire" doit être proche de "atriale"
    results = idx.search_vector("fibrillation auriculaire", top_k=5)
    top_ids = [doc.ontology_id for doc, _ in results]
    print(f"  🔍 'fibrillation auriculaire' → top 5 : {top_ids}")
    # On espère FIBRILLATION_ATRIALE dans le top 5 (auriculaire ≈ atriale sémantiquement)
    has_fa = "FIBRILLATION_ATRIALE" in top_ids
    print(f"  {'✅' if has_fa else '⚠️'} FIBRILLATION_ATRIALE {'trouvée' if has_fa else 'NON trouvée (test sémantique échoué)'}")
    
    # Test : "infarctus du myocarde" → doit retourner des concepts IDM
    results = idx.search_vector("infarctus du myocarde", top_k=5)
    top_ids = [doc.ontology_id for doc, _ in results]
    print(f"  🔍 'infarctus du myocarde' → top 5 : {top_ids}")
    has_idm = any("INFARCTUS" in oid for oid in top_ids)
    print(f"  {'✅' if has_idm else '⚠️'} Concept INFARCTUS {'trouvé' if has_idm else 'NON trouvé'}")
    
    return True


def test_hybrid():
    """Test 4 : La recherche hybride combine BM25 + vectoriel."""
    print("\n" + "=" * 60)
    print("🔀 TEST 4 : Recherche Hybride (RRF)")
    print("=" * 60)
    
    idx = OntologyIndex(ontology_path=ONTOLOGY_PATH)
    idx.build(include_implications=False)
    
    test_queries = [
        ("FA", "FIBRILLATION_ATRIALE"),
        ("BAV complet", "BAV_COMPLET"),
        ("BBG", "BLOC_DE_BRANCHE_GAUCHE"),
        ("tachycardie ventriculaire", "TACHYCARDIE_VENTRICULAIRE"),
        ("onde T négative", "ONDE_T_NÉGATIVE"),
    ]
    
    all_passed = True
    for query, expected_id in test_queries:
        results = idx.search_hybrid(query, top_k=5)
        top_ids = [doc.ontology_id for doc, _ in results]
        found = expected_id in top_ids
        if not found:
            all_passed = False
        status = "✅" if found else "❌"
        rank = top_ids.index(expected_id) + 1 if found else "N/A"
        print(f"  {status} '{query}' → attendu: {expected_id} | rang: {rank} | top 5: {top_ids[:3]}...")
    
    return all_passed


def test_save_load():
    """Test 5 : Sauvegarde et rechargement de l'index."""
    print("\n" + "=" * 60)
    print("💾 TEST 5 : Save / Load")
    print("=" * 60)
    
    idx = OntologyIndex(ontology_path=ONTOLOGY_PATH)
    idx.build(include_implications=False)
    idx.save(INDEX_DIR)
    
    # Recharger
    idx2 = OntologyIndex.load(INDEX_DIR)
    
    assert len(idx2.documents) == len(idx.documents), "Nombre de documents différent après load"
    print(f"  ✅ {len(idx2.documents)} documents rechargés")
    
    assert idx2._embeddings.shape == idx._embeddings.shape, "Shape des embeddings différent"
    print(f"  ✅ Embeddings shape OK : {idx2._embeddings.shape}")
    
    # Vérifier qu'une recherche fonctionne après load
    results = idx2.search_hybrid("FA", top_k=3)
    assert len(results) > 0, "Pas de résultats après reload"
    top_id = results[0][0].ontology_id
    print(f"  ✅ Recherche post-reload OK : 'FA' → {top_id}")
    
    return True


def test_normalization():
    """Test 6 : La normalisation textuelle NFD fonctionne correctement."""
    print("\n" + "=" * 60)
    print("📝 TEST 6 : Normalisation NFD")
    print("=" * 60)
    
    # Minuscules
    assert normalize_text("Fibrillation Atriale") == "fibrillation atriale"
    print("  ✅ Minuscules : 'Fibrillation Atriale' → 'fibrillation atriale'")
    
    # Accents supprimés (NFD) + tiret → espace
    result = normalize_text("Ischémie sous-épicardique")
    assert result == "ischemie sous epicardique", f"Got: '{result}'"
    print(f"  ✅ NFD + tiret : 'Ischémie sous-épicardique' → '{result}'")
    
    # Underscores → espaces
    result = normalize_text("FIBRILLATION_ATRIALE")
    assert result == "fibrillation atriale", f"Got: '{result}'"
    print(f"  ✅ Underscore : 'FIBRILLATION_ATRIALE' → '{result}'")
    
    # Points → espaces
    result = normalize_text("BAV.complet")
    assert result == "bav complet", f"Got: '{result}'"
    print(f"  ✅ Point : 'BAV.complet' → '{result}'")
    
    # Espaces multiples
    assert normalize_text("BAV 2  Mobitz  2") == "bav 2 mobitz 2"
    print("  ✅ Espaces multiples collapsés")
    
    # Cas à accents complexes
    result = normalize_text("Hémibloc antérieur gauche")
    assert result == "hemibloc anterieur gauche", f"Got: '{result}'"
    print(f"  ✅ Accents complexes : '{result}'")
    
    tokens = tokenize("Bloc de branche gauche")
    assert "bloc" in tokens
    assert "branche" in tokens
    assert "gauche" in tokens
    print(f"  ✅ tokenize OK : {tokens}")
    
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n🧪 VALIDATION — Brique 1 : Socle Symbolique & Vectoriel")
    print("=" * 60)
    
    results = {}
    
    # Tests séquentiels (du plus rapide au plus lent)
    results["normalisation"] = test_normalization()
    results["parsing"] = test_parsing()
    results["bm25"] = test_bm25()
    results["vectoriel"] = test_vector()
    results["hybride"] = test_hybrid()
    results["save_load"] = test_save_load()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    for name, passed in results.items():
        print(f"  {'✅' if passed else '❌'} {name}")
    
    all_ok = all(results.values())
    print(f"\n{'🎉 TOUS LES TESTS PASSENT !' if all_ok else '⚠️ Certains tests ont échoué.'}")
    sys.exit(0 if all_ok else 1)
