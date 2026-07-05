"""
Tests de NON-RÉGRESSION du Scoring V3 (Brique 5).
==================================================

Objectif : figer le comportement ACTUEL du scoring symbolique déterministe
avant toute évolution (notamment la future refonte de la métrique avec
pénalité des faux positifs).

⚠️ Ces tests décrivent le comportement TEL QU'IL EST aujourd'hui, y compris
   ses limites connues (cf. ARCHITECTURE.md §13, Audit). Un test qui « documente
   une limite » est marqué par un commentaire LIMITE:. Quand la métrique sera
   corrigée, ces tests-là devront être mis à jour intentionnellement.

Aucun appel réseau / LLM : 100% déterministe.
Lancement :
    cd "ECG lecture"
    .venv\\Scripts\\python.exe -m pytest rag_pipeline/tests/test_scoring_v3.py -v
"""

from __future__ import annotations

import math

import pytest

import scoring_v3
from scoring_v3 import score_student_response_v3


def _pct(found, expected, absent=None):
    """Helper : renvoie le score_pct pour un couple (found, expected)."""
    return score_student_response_v3(found, expected, absent_ids=absent).score_pct


def _one(found, expected, absent=None):
    """Helper : renvoie le premier ConceptScore (cas mono-concept)."""
    return score_student_response_v3(found, expected, absent_ids=absent).concept_scores[0]


# ===========================================================================
# 1. Correspondances directes (exact / enfant / parent)
# ===========================================================================

class TestMatchDirect:
    def test_exact_match_donne_100(self):
        cs = _one(["FIBRILLATION_ATRIALE"], ["FIBRILLATION_ATRIALE"])
        assert cs.score == 1.0
        assert cs.match_type == "exact"

    def test_enfant_trouve_credite_le_parent_a_100(self):
        # L'étudiant est PLUS précis que l'attendu → crédit complet.
        # BBD_COMPLET est un enfant de BBD.
        cs = _one(["BLOC_DE_BRANCHE_DROIT_COMPLET"], ["BLOC_DE_BRANCHE_DROIT"])
        assert cs.score == 1.0
        assert cs.match_type == "exact"

    def test_parent_direct_trouve_credite_partiellement_deux_tiers(self):
        # L'étudiant est PLUS vague que l'attendu (parent direct) → 2/3.
        cs = _one(["BLOC_DE_BRANCHE_DROIT"], ["BLOC_DE_BRANCHE_DROIT_COMPLET"])
        assert math.isclose(cs.score, 2.0 / 3.0, rel_tol=1e-3)
        assert cs.match_type == "qualifier"

    def test_aucune_correspondance_donne_0(self):
        cs = _one(["QRS_FINS"], ["FIBRILLATION_ATRIALE"])
        assert cs.score == 0.0
        assert cs.match_type == "missed"


# ===========================================================================
# 2. Relation "requires" (crédit partiel par critères satisfaits)
# ===========================================================================

class TestRequires:
    def test_un_require_sur_quatre_donne_25pct(self):
        # ECG_NORMAL requires = [RYTHME_SINUSAL, PAS_D_ANOMALIE_DE_LE_REPOLARISATION,
        #                        PAS_DE_TROUBLES_DE_LA_CONDUCTION, FREQUENCE_NORMALE]
        cs = _one(["RYTHME_SINUSAL"], ["ECG_NORMAL"])
        assert math.isclose(cs.score, 0.25, rel_tol=1e-3)
        assert cs.match_type == "requires"
        assert cs.requires_total == 4
        assert cs.requires_found == 1

    def test_deux_requires_sur_quatre_donne_50pct(self):
        cs = _one(["RYTHME_SINUSAL", "FREQUENCE_NORMALE"], ["ECG_NORMAL"])
        assert math.isclose(cs.score, 0.5, rel_tol=1e-3)
        assert cs.match_type == "requires"


# ===========================================================================
# 3. Agrégation multi-concepts
# ===========================================================================

class TestAgregation:
    def test_moyenne_avec_exclusion(self):
        # BON COMPORTEMENT (garde-fou clinique) : déclarer FIBRILLATION_ATRIALE
        # exclut ECG_NORMAL (FA ∈ famille ARYTHMIE, exclue par ECG_NORMAL).
        # → FA (exact = 1.0) + ECG_NORMAL (exclu = 0.0) → moyenne 0.5 → 50.0
        r = score_student_response_v3(
            ["FIBRILLATION_ATRIALE", "RYTHME_SINUSAL"],
            ["FIBRILLATION_ATRIALE", "ECG_NORMAL"],
        )
        assert math.isclose(r.score_pct, 50.0, rel_tol=1e-3)
        # ECG_NORMAL doit être marqué "excluded" par la FA
        ecg_normal_cs = next(
            cs for cs in r.concept_scores if cs.concept_id == "ECG_NORMAL"
        )
        assert ecg_normal_cs.match_type == "excluded"
        assert ecg_normal_cs.excluded_by == "FIBRILLATION_ATRIALE"

    def test_moyenne_de_deux_concepts_sans_exclusion(self):
        # QRS_LARGE (exact = 1.0) + ECG_NORMAL (1 require /4 = 0.25), sans exclusion
        # → (1.0 + 0.25) / 2 = 0.625 → 62.5
        pct = _pct(["QRS_LARGE", "RYTHME_SINUSAL"],
                   ["QRS_LARGE", "ECG_NORMAL"])
        assert math.isclose(pct, 62.5, rel_tol=1e-3)

    def test_score_parfait_sur_deux_exacts(self):
        pct = _pct(["FIBRILLATION_ATRIALE", "QRS_LARGE"],
                   ["FIBRILLATION_ATRIALE", "QRS_LARGE"])
        assert pct == 100.0


# ===========================================================================
# 4. Cas limites / garde-fous
# ===========================================================================

class TestCasLimites:
    def test_golden_vide_donne_0(self):
        r = score_student_response_v3(["FIBRILLATION_ATRIALE"], [])
        assert r.score_pct == 0.0
        assert r.concept_scores == []

    def test_reponse_vide_donne_0(self):
        cs = _one([], ["FIBRILLATION_ATRIALE"])
        assert cs.score == 0.0
        assert cs.match_type == "missed"

    def test_concepts_hors_golden_sont_ignores(self):
        # LIMITE CONNUE (cf. ARCHITECTURE.md §13.4) : les concepts trouvés qui ne
        # sont pas dans le golden n'affectent PAS le score. Un seul concept correct
        # parmi beaucoup de bruit donne quand même 100%.
        # Ce test FIGE cette limite : sa modification future sera intentionnelle.
        pct = _pct(
            ["FIBRILLATION_ATRIALE", "TACHYCARDIE_VENTRICULAIRE",
             "BLOC_DE_BRANCHE_DROIT_COMPLET", "HYPERKALIEMIE"],
            ["FIBRILLATION_ATRIALE"],
        )
        assert pct == 100.0  # ← à faire évoluer quand la métrique intègrera les FP


# ===========================================================================
# 5. Exclusions (garde-fou clinique : un excludes écrase tout)
# ===========================================================================

class TestExcludes:
    def test_fa_exclut_ecg_normal(self):
        # BON COMPORTEMENT : déclarer une arythmie (FA) sur un ECG normal met le
        # concept ECG_NORMAL à 0 via excludes_families (FA ∈ ARYTHMIE).
        cs = _one(["FIBRILLATION_ATRIALE"], ["ECG_NORMAL"])
        assert cs.score == 0.0
        assert cs.match_type == "excluded"
        assert cs.excluded_by == "FIBRILLATION_ATRIALE"

    def test_exclusion_ecrase_meme_des_requires_satisfaits(self):
        # Même si un require d'ECG_NORMAL est présent (RYTHME_SINUSAL),
        # la présence d'un concept exclu (FA) force le score à 0.
        cs = _one(["FIBRILLATION_ATRIALE", "RYTHME_SINUSAL"], ["ECG_NORMAL"])
        assert cs.score == 0.0
        assert cs.match_type == "excluded"


# ===========================================================================
# 6. Négation (conversion absent → concept positif)
# ===========================================================================

class TestNegation:
    def test_negation_map_non_vide(self):
        nm = scoring_v3.build_negation_map()
        assert isinstance(nm, dict)
        assert len(nm) > 0

    def test_absent_trouble_repol_se_convertit(self):
        # LIMITE CONNUE (cf. ARCHITECTURE.md §13.3) : "pas de trouble de repolarisation"
        # se mappe vers ECG_NORMAL. Résultat : un étudiant qui écrit UNIQUEMENT
        # "pas de trouble de repolarisation" obtient 100% sur un cas ECG normal.
        conv = scoring_v3.convert_absents_to_positive(["TROUBLE_DE_REPOLARISATION"])
        assert ("TROUBLE_DE_REPOLARISATION", "ECG_NORMAL") in conv

    def test_absent_booste_le_score_ecg_normal(self):
        # Documente le comportement : les absents convertis rejoignent found_set.
        pct_sans = _pct(["RYTHME_SINUSAL", "FREQUENCE_NORMALE"], ["ECG_NORMAL"])
        pct_avec = _pct(
            ["RYTHME_SINUSAL", "FREQUENCE_NORMALE"], ["ECG_NORMAL"],
            absent=["TROUBLE_DE_REPOLARISATION", "TROUBLES_DE_LA_CONDUCTION"],
        )
        assert pct_avec > pct_sans


# ===========================================================================
# 7. Déterminisme (propriété fondamentale du scoring symbolique)
# ===========================================================================

class TestDeterminisme:
    def test_meme_entree_meme_score_sur_10_runs(self):
        found = ["RYTHME_SINUSAL", "FREQUENCE_NORMALE", "QRS_FINS"]
        expected = ["ECG_NORMAL", "FIBRILLATION_ATRIALE"]
        scores = {_pct(found, expected) for _ in range(10)}
        assert len(scores) == 1  # un seul résultat unique → 100% reproductible
