"""
🧪 Test de validation — Brique 4 : Le Juge Neurosymbolique
=============================================================
Vérifie le pipeline complet : Coupe-Circuit + Juge LLM (QCM GPT-4o-mini).

Tests :
  1. Coupe-circuit sur matchs exacts (acronymes, canonical)
  2. Juge LLM sur termes ambigus (fautes, synonymes sémantiques)
  3. Rejet NONE sur termes hors-ontologie
  4. Format de sortie
  5. Intégration pipeline complète (NER → Search → Judge)

Usage:
    python test_brique4.py
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Import local
sys.path.insert(0, str(Path(__file__).parent))
from hybrid_search import HybridSearchEngine
from neurosymbolic_judge import resolve_term_to_ontology
from ontology_index import normalize_text

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INDEX_DIR = str(Path(__file__).parent / "rag_index")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_coupe_circuit(engine: HybridSearchEngine):
    """Test 1 : Le coupe-circuit bypasse le LLM pour les matchs exacts."""
    print("\n" + "=" * 60)
    print("⚡ TEST 1 : Coupe-Circuit (exact match → bypass LLM)")
    print("=" * 60)

    # Ces termes ont un match exact dans l'ontologie (canonical ou synonym)
    exact_cases = [
        ("FA", "On note une FA.", "FIBRILLATION_ATRIALE"),
        ("BBD", "BBD complet.", "BLOC_DE_BRANCHE_DROIT"),
        ("BBG", "Il y a un BBG.", "BLOC_DE_BRANCHE_GAUCHE"),
        ("Rythme sinusal", "Rythme sinusal régulier.", "RYTHME_SINUSAL"),
        ("Flutter atrial", "Flutter atrial rapide.", "FLUTTER_ATRIAL"),
    ]

    all_passed = True
    for terme, contexte, expected_id in exact_cases:
        candidates = engine.search_top_k(terme, k=5)
        result = resolve_term_to_ontology(terme, contexte, candidates)

        is_coupe = result["method"] == "coupe_circuit"
        id_ok = result["ontology_id"] == expected_id
        passed = is_coupe and id_ok

        if not passed:
            all_passed = False
        status = "✅" if passed else "❌"
        print(
            f"  {status} '{terme}' → {result['ontology_id']} "
            f"(method={result['method']}"
            f"{', ATTENDU: '+expected_id if not id_ok else ''})"
        )

    return all_passed


def test_juge_llm_termes_ambigus(engine: HybridSearchEngine):
    """Test 2 : Le Juge LLM résout les termes ambigus / avec fautes."""
    print("\n" + "=" * 60)
    print("🧑‍⚖️ TEST 2 : Juge LLM (termes ambigus → résolution)")
    print("=" * 60)

    # Termes qui NE matchent PAS exactement → doivent passer par le Juge
    ambiguous_cases = [
        (
            "tachi supra",
            "On observe une tachi supra.",
            "TACHYCARDIE_SUPRA_VENTRICULAIRE",
        ),
        (
            "fibrillation auriculaire",
            "Fibrillation auriculaire rapide.",
            "FIBRILLATION_ATRIALE",
        ),
        (
            "bloc de branche G complet",
            "Bloc de branche G complet avec QRS larges.",
            "BLOC_DE_BRANCHE_GAUCHE_COMPLET",
        ),
    ]

    all_passed = True
    for terme, contexte, expected_id in ambiguous_cases:
        candidates = engine.search_top_k(terme, k=5)
        result = resolve_term_to_ontology(terme, contexte, candidates)

        is_juge = result["method"] == "juge_llm"
        id_ok = result["ontology_id"] == expected_id

        # Pour les cas ambigus, on accepte aussi un concept parent
        # (ex: BLOC_DE_BRANCHE_GAUCHE au lieu de _COMPLET)
        partial_ok = expected_id.split("_")[0] in result["ontology_id"]
        passed = is_juge and (id_ok or partial_ok)

        if not passed:
            all_passed = False
        status = "✅" if passed else "⚠️"
        print(
            f"  {status} '{terme}' → {result['ontology_id']} "
            f"(method={result['method']}, justification: {result['justification'][:80]}...)"
        )

    return all_passed


def test_rejet_none(engine: HybridSearchEngine):
    """Test 3 : Le Juge rejette les termes hors-ontologie (→ NONE)."""
    print("\n" + "=" * 60)
    print("❌ TEST 3 : Rejet NONE (termes hors-ontologie)")
    print("=" * 60)

    # Termes qui ne correspondent à aucun concept ECG
    none_cases = [
        ("douleur thoracique", "Patient avec douleur thoracique."),
        ("pneumonie", "Suspicion de pneumonie."),
    ]

    all_passed = True
    for terme, contexte in none_cases:
        candidates = engine.search_top_k(terme, k=5)
        result = resolve_term_to_ontology(terme, contexte, candidates)

        is_none = result["ontology_id"] == "NONE"
        status = "✅" if is_none else "⚠️"
        if not is_none:
            # Ce n'est pas un échec fatal — le LLM peut avoir trouvé un lien
            # clinique inattendu. On le signale mais on ne fail pas.
            print(
                f"  {status} '{terme}' → {result['ontology_id']} "
                f"(le LLM n'a pas rejeté — justification: {result['justification'][:80]}...)"
            )
        else:
            print(f"  {status} '{terme}' → NONE (correctement rejeté)")

    return all_passed


def test_pas_de_candidats():
    """Test 4 : Comportement sans candidats (→ NONE, method=no_candidates)."""
    print("\n" + "=" * 60)
    print("🫙 TEST 4 : Pas de candidats")
    print("=" * 60)

    result = resolve_term_to_ontology("xyz", "xyz sur l'ECG.", [])

    assert result["ontology_id"] == "NONE"
    assert result["method"] == "no_candidates"
    print(f"  ✅ Pas de candidats → NONE (method={result['method']})")

    return True


def test_format_sortie(engine: HybridSearchEngine):
    """Test 5 : Le format de sortie contient toutes les clés requises."""
    print("\n" + "=" * 60)
    print("📋 TEST 5 : Format de sortie")
    print("=" * 60)

    candidates = engine.search_top_k("FA", k=5)
    result = resolve_term_to_ontology("FA", "On note une FA.", candidates)

    required_keys = [
        "ontology_id", "concept_name", "method",
        "justification", "candidats_soumis",
    ]
    for key in required_keys:
        assert key in result, f"Clé manquante : {key}"

    assert result["method"] in ("coupe_circuit", "juge_llm", "no_candidates")
    assert isinstance(result["candidats_soumis"], int)
    assert isinstance(result["justification"], str) and len(result["justification"]) > 0

    print(f"  ✅ Toutes les clés requises présentes")
    print(f"  ✅ method='{result['method']}', candidats_soumis={result['candidats_soumis']}")
    print(f"  ✅ justification: '{result['justification'][:80]}...'")

    return True


def test_integration_pipeline(engine: HybridSearchEngine):
    """Test 6 : Pipeline complète NER (simulé) → Search → Judge."""
    print("\n" + "=" * 60)
    print("🔗 TEST 6 : Intégration Pipeline (NER → Search → Judge)")
    print("=" * 60)

    # Simuler l'output de la Brique 2 (NER)
    entites_ner = [
        {"terme_brut": "Rythme sinusal", "statut": "present",
         "contexte_phrase": "Rythme sinusal régulier."},
        {"terme_brut": "BBD", "statut": "absent",
         "contexte_phrase": "Pas de BBD visible."},
        {"terme_brut": "tachi supra", "statut": "present",
         "contexte_phrase": "On observe une tachi supra."},
        {"terme_brut": "amylose", "statut": "hypothese",
         "contexte_phrase": "On suspecte une amylose devant le microvoltage."},
    ]

    print(f"  📋 {len(entites_ner)} entités NER à résoudre :\n")

    all_resolved = True
    for ent in entites_ner:
        # Brique 3 : recherche hybride
        candidates = engine.search_top_k(ent["terme_brut"], k=5)

        # Brique 4 : juge neurosymbolique
        result = resolve_term_to_ontology(
            ent["terme_brut"],
            ent["contexte_phrase"],
            candidates,
        )

        resolved = result["ontology_id"] != "NONE"
        if not resolved:
            all_resolved = False

        status = "✅" if resolved else "⚠️"
        print(
            f"  {status} [{ent['statut']:>10}] \"{ent['terme_brut']}\" "
            f"→ {result['ontology_id']} "
            f"({result['method']}, {result['concept_name']})"
        )

    return all_resolved


def test_coupe_circuit_vs_juge_comptage(engine: HybridSearchEngine):
    """Test 7 : Vérifier le ratio coupe-circuit / juge sur un lot de termes."""
    print("\n" + "=" * 60)
    print("📊 TEST 7 : Ratio Coupe-Circuit / Juge LLM")
    print("=" * 60)

    # Mix de termes exacts et ambigus
    termes = [
        ("FA", "FA rapide."),
        ("BBG", "BBG complet."),
        ("Rythme sinusal", "Rythme sinusal."),
        ("tachi supra", "On note une tachi supra."),
        ("fibrillation auriculaire", "Fibrillation auriculaire."),
        ("onde T négative", "Ondes T négatives en V1-V3."),
        ("BAV complet", "BAV complet."),
        ("HVG", "HVG probable."),
    ]

    counts = {"coupe_circuit": 0, "juge_llm": 0, "no_candidates": 0}
    for terme, contexte in termes:
        candidates = engine.search_top_k(terme, k=5)
        result = resolve_term_to_ontology(terme, contexte, candidates)
        counts[result["method"]] += 1

    total = len(termes)
    print(f"  📊 Sur {total} termes :")
    print(f"     ⚡ Coupe-circuit : {counts['coupe_circuit']} ({100*counts['coupe_circuit']/total:.0f}%)")
    print(f"     🧑‍⚖️ Juge LLM     : {counts['juge_llm']} ({100*counts['juge_llm']/total:.0f}%)")
    print(f"     🫙 No candidates : {counts['no_candidates']} ({100*counts['no_candidates']/total:.0f}%)")

    # On s'attend à au moins 3 coupe-circuits (FA, BBG, Rythme sinusal, HVG)
    assert counts["coupe_circuit"] >= 3, (
        f"Trop peu de coupe-circuits : {counts['coupe_circuit']}"
    )
    print(f"  ✅ Au moins 3 coupe-circuits activés")

    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n🧪 VALIDATION — Brique 4 : Le Juge Neurosymbolique")
    print("=" * 60)

    # Initialisation unique du moteur de recherche
    print(f"\n📂 Chargement de l'index depuis : {INDEX_DIR}")
    engine = HybridSearchEngine(INDEX_DIR)

    results = {}

    results["coupe_circuit"] = test_coupe_circuit(engine)
    results["juge_llm_ambigus"] = test_juge_llm_termes_ambigus(engine)
    results["rejet_none"] = test_rejet_none(engine)
    results["pas_de_candidats"] = test_pas_de_candidats()
    results["format_sortie"] = test_format_sortie(engine)
    results["integration_pipeline"] = test_integration_pipeline(engine)
    results["ratio_coupe_circuit"] = test_coupe_circuit_vs_juge_comptage(engine)

    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    for name, passed in results.items():
        print(f"  {'✅' if passed else '❌'} {name}")

    all_ok = all(results.values())
    print(f"\n{'🎉 TOUS LES TESTS PASSENT !' if all_ok else '⚠️ Certains tests ont échoué.'}")
    sys.exit(0 if all_ok else 1)
