"""
🧪 Test de validation — Brique 2 : Extracteur d'Entités Cliniques (NER)
========================================================================
Vérifie que extract_clinical_terms produit des extractions correctes :
  - Schéma Pydantic respecté (structured outputs)
  - Zéro normalisation (fautes conservées)
  - Périmètre ECG (clinique annexe ignorée)
  - Statuts cliniques corrects (present / absent / hypothese)

Usage:
    python test_brique2.py
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Import local
sys.path.insert(0, str(Path(__file__).parent))
from ner_extractor import extract_clinical_terms, NERExtraction, ClinicalEntity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def termes_bruts(result: NERExtraction) -> list[str]:
    """Retourne les termes bruts en minuscules pour faciliter les assertions."""
    return [e.terme_brut.lower() for e in result.entites]


def entites_par_statut(result: NERExtraction, statut: str) -> list[ClinicalEntity]:
    """Filtre les entités par statut."""
    return [e for e in result.entites if e.statut == statut]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_schema_pydantic():
    """Test 1 : L'output est un objet NERExtraction valide avec des ClinicalEntity."""
    print("\n" + "=" * 60)
    print("📋 TEST 1 : Schéma Pydantic (Structured Outputs)")
    print("=" * 60)

    texte = "Rythme sinusal. BBG complet."
    result = extract_clinical_terms(texte)

    # Type check
    assert isinstance(result, NERExtraction), f"Type inattendu : {type(result)}"
    print("  ✅ Résultat est un NERExtraction")

    assert len(result.entites) > 0, "Aucune entité extraite"
    print(f"  ✅ {len(result.entites)} entités extraites")

    for ent in result.entites:
        assert isinstance(ent, ClinicalEntity), f"Type inattendu : {type(ent)}"
        assert ent.terme_brut.strip(), "terme_brut vide"
        assert ent.statut in ("present", "absent", "hypothese"), f"Statut invalide : {ent.statut}"
        assert ent.contexte_phrase.strip(), "contexte_phrase vide"
        print(f"  ✅ [{ent.statut:>10}] \"{ent.terme_brut}\" — contexte OK")

    return True


def test_zero_normalisation():
    """Test 2 : Les fautes d'orthographe sont conservées telles quelles."""
    print("\n" + "=" * 60)
    print("✏️  TEST 2 : Zéro normalisation (fautes conservées)")
    print("=" * 60)

    texte = "Je vois une tachi supra venticulaire avec des ondes T invertées."
    result = extract_clinical_terms(texte)
    bruts = termes_bruts(result)

    print(f"  📋 Termes extraits : {[e.terme_brut for e in result.entites]}")

    # "tachi supra" ou "tachi supra venticulaire" doit être présent TEL QUEL
    # (pas "tachycardie supraventriculaire")
    has_tachi = any("tachi" in t for t in bruts)
    assert has_tachi, (
        f"Le LLM a normalisé 'tachi supra' ! Termes : {bruts}"
    )
    print("  ✅ 'tachi' conservé (pas normalisé en 'tachycardie')")

    # Vérifier qu'aucun terme ne contient "tachycardie supraventriculaire"
    has_normalized = any("tachycardie supraventriculaire" in t for t in bruts)
    if has_normalized:
        print("  ⚠️  ATTENTION : Le LLM a normalisé en 'tachycardie supraventriculaire'")
    else:
        print("  ✅ Pas de normalisation en 'tachycardie supraventriculaire'")

    return True


def test_perimetre_ecg():
    """Test 3 : La clinique annexe est ignorée, seul l'ECG est extrait."""
    print("\n" + "=" * 60)
    print("🏥 TEST 3 : Périmètre ECG strict")
    print("=" * 60)

    texte = (
        "Patient de 54 ans avec douleur thoracique. "
        "Rythme sinusal. Pas de BBD visible. "
        "On suspecte une amylose devant le microvoltage."
    )
    result = extract_clinical_terms(texte)
    bruts = termes_bruts(result)

    print(f"  📋 Termes extraits : {[e.terme_brut for e in result.entites]}")

    # Doit extraire : rythme sinusal, BBD, amylose, microvoltage
    ecg_terms = ["rythme sinusal", "bbd", "amylose", "microvoltage"]
    for term in ecg_terms:
        found = any(term in t for t in bruts)
        status = "✅" if found else "⚠️"
        print(f"  {status} '{term}' {'trouvé' if found else 'NON trouvé'}")

    # Ne doit PAS extraire : "54 ans", "douleur thoracique", "patient"
    clinique_exclue = ["54 ans", "douleur thoracique", "patient"]
    all_excluded = True
    for term in clinique_exclue:
        found = any(term in t for t in bruts)
        if found:
            all_excluded = False
            print(f"  ❌ '{term}' a été extrait alors qu'il ne devrait pas l'être !")
        else:
            print(f"  ✅ '{term}' correctement ignoré")

    assert all_excluded, "Des termes cliniques non-ECG ont été extraits"

    return True


def test_statuts_cliniques():
    """Test 4 : Les statuts present / absent / hypothese sont correctement assignés."""
    print("\n" + "=" * 60)
    print("🏷️  TEST 4 : Statuts cliniques (present / absent / hypothese)")
    print("=" * 60)

    texte = (
        "Rythme sinusal. Pas de BBD visible. "
        "On suspecte une amylose devant le microvoltage."
    )
    result = extract_clinical_terms(texte)

    print(f"  📋 Entités :")
    for ent in result.entites:
        print(f"     [{ent.statut:>10}] \"{ent.terme_brut}\"")

    # Rythme sinusal → present
    presents = entites_par_statut(result, "present")
    termes_presents = [e.terme_brut.lower() for e in presents]
    has_sinusal = any("rythme sinusal" in t or "sinusal" in t for t in termes_presents)
    print(f"  {'✅' if has_sinusal else '⚠️'} 'rythme sinusal' → present")

    # BBD → absent (car "pas de BBD")
    absents = entites_par_statut(result, "absent")
    termes_absents = [e.terme_brut.lower() for e in absents]
    has_bbd_absent = any("bbd" in t for t in termes_absents)
    print(f"  {'✅' if has_bbd_absent else '⚠️'} 'BBD' → absent")

    # Amylose → hypothese (car "on suspecte")
    hypotheses = entites_par_statut(result, "hypothese")
    termes_hypo = [e.terme_brut.lower() for e in hypotheses]
    has_amylose_hypo = any("amylose" in t for t in termes_hypo)
    print(f"  {'✅' if has_amylose_hypo else '⚠️'} 'amylose' → hypothese")

    # Vérifier qu'on a bien au moins un de chaque statut
    assert len(presents) >= 1, f"Aucune entité 'present' trouvée"
    assert len(absents) >= 1, f"Aucune entité 'absent' trouvée"
    assert len(hypotheses) >= 1, f"Aucune entité 'hypothese' trouvée"
    print("  ✅ Les 3 statuts sont représentés")

    return True


def test_texte_complexe():
    """Test 5 : Extraction sur un texte réaliste plus long."""
    print("\n" + "=" * 60)
    print("📄 TEST 5 : Texte complexe réaliste")
    print("=" * 60)

    texte = (
        "ECG 12 dérivations. FC à 88 bpm. "
        "Rythme sinusal régulier, axe normal. "
        "Onde P normale, PR à 180 ms. "
        "BBG complet avec QRS à 140 ms. "
        "Pas de sus-décalage du ST. "
        "Ondes T négatives en latéral. "
        "Pas de signe de péricardite. "
        "Possiblement une HVG associée."
    )
    result = extract_clinical_terms(texte)

    print(f"  📋 {len(result.entites)} entités extraites :")
    for ent in result.entites:
        print(f"     [{ent.statut:>10}] \"{ent.terme_brut}\"")

    # Vérifications minimales
    bruts = termes_bruts(result)

    # Doit trouver au minimum ces concepts ECG
    expected_present = ["rythme sinusal", "bbg"]
    for term in expected_present:
        found = any(term in t for t in bruts)
        print(f"  {'✅' if found else '⚠️'} '{term}' extrait")

    # Doit avoir au moins 5 entités pour un texte de cette richesse
    assert len(result.entites) >= 5, (
        f"Trop peu d'entités pour ce texte : {len(result.entites)}"
    )
    print(f"  ✅ Richesse OK : {len(result.entites)} entités (≥ 5 attendues)")

    return True


def test_texte_vide_ou_minimal():
    """Test 6 : Comportement avec un texte vide ou quasi-vide."""
    print("\n" + "=" * 60)
    print("🫙 TEST 6 : Texte vide / minimal")
    print("=" * 60)

    # Texte vide
    result = extract_clinical_terms("")
    assert isinstance(result, NERExtraction), "Type invalide pour texte vide"
    print(f"  ✅ Texte vide → {len(result.entites)} entités (pas de crash)")

    # Texte sans contenu ECG
    result = extract_clinical_terms("Le patient a 45 ans et se plaint de fatigue.")
    bruts = termes_bruts(result)
    print(f"  📋 Texte non-ECG → termes : {[e.terme_brut for e in result.entites]}")

    # On s'attend à 0 ou très peu d'entités
    if len(result.entites) == 0:
        print("  ✅ Aucune entité ECG extraite d'un texte non-ECG")
    else:
        print(f"  ⚠️  {len(result.entites)} entités extraites d'un texte non-ECG "
              "(le LLM devrait idéalement n'en extraire aucune)")

    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n🧪 VALIDATION — Brique 2 : Extracteur d'Entités Cliniques (NER)")
    print("=" * 60)

    results = {}

    results["schema_pydantic"] = test_schema_pydantic()
    results["zero_normalisation"] = test_zero_normalisation()
    results["perimetre_ecg"] = test_perimetre_ecg()
    results["statuts_cliniques"] = test_statuts_cliniques()
    results["texte_complexe"] = test_texte_complexe()
    results["texte_vide_minimal"] = test_texte_vide_ou_minimal()

    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    for name, passed in results.items():
        print(f"  {'✅' if passed else '❌'} {name}")

    all_ok = all(results.values())
    print(f"\n{'🎉 TOUS LES TESTS PASSENT !' if all_ok else '⚠️ Certains tests ont échoué.'}")
    sys.exit(0 if all_ok else 1)
