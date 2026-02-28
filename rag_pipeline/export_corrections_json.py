"""
📦 Export des corrections en JSON pour ECG Collector (Scalingo)
================================================================
Exécute le pipeline sur tous les étudiants du CSV et exporte les résultats
en JSON léger, prêt à être lu par la page Streamlit corrections.

Usage :
    python export_corrections_json.py
    python export_corrections_json.py --students ECG-WY55
    python export_corrections_json.py --output corrections_data.json

Sortie : fichier JSON avec la structure :
{
  "generated_at": "...",
  "students": {
    "ECG-WY55": {
      "average": 97.0,
      "nb_answered": 15,
      "cases": {
        "1": { "score": 100, "diagnostic": "...", "student_text": "...", ... },
        ...
      }
    }
  },
  "golden": { "1": { "diagnostic_principal": "...", "annotations": [...] }, ... }
}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()
PROJECT_ROOT = Path(r"C:\Users\Administrateur\bmad\ECG lecture")
EVAL_ROOT    = Path(r"C:\Users\Administrateur\bmad\ECG evaluation")
RAG_ROOT     = SCRIPT_DIR
COLLECTOR_ROOT = Path(r"C:\Users\Administrateur\ECG collector")

CSV_DEFAULT  = EVAL_ROOT / "ECG_Collector_Data - responses(1).csv"

# ── Setup ─────────────────────────────────────────────────────────────────────
sys.path.insert(0, str(RAG_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
os.chdir(str(RAG_ROOT))

from generate_html_report import load_golden_set, load_student_csv, evaluate_student
from candidate_report import CandidateReport


def report_to_dict(report: Optional[CandidateReport]) -> Optional[dict]:
    """Convertit un CandidateReport en dict sérialisable JSON."""
    if report is None:
        return None

    return {
        "score_final_pct": round(report.score_final_pct, 1),
        "nb_validants_trouves": report.nb_validants_trouves,
        "nb_validants_attendus": report.nb_validants_attendus,
        "nb_descripteurs_trouves": report.nb_descripteurs_trouves,
        "nb_descripteurs_attendus": report.nb_descripteurs_attendus,
        "latence_s": round(report.latence_s, 2),
        "concepts_extraits": [
            {
                "terme_brut": c.terme_brut,
                "statut": c.statut,
                "ontology_id": c.ontology_id,
                "concept_name": c.concept_name,
                "method": c.method,
                "justification": c.justification,
            }
            for c in report.concepts_extraits
        ],
        "validant_details": [
            {
                "golden_name": v.golden_name,
                "golden_id": v.golden_id,
                "found": v.found,
                "score_pct": round(v.score_pct, 1),
                "match_type": v.match_type,
                "found_via_name": v.found_via_name,
                "explication": v.explication,
            }
            for v in report.validant_details
        ],
        "descripteur_details": [
            {
                "golden_name": d.golden_name,
                "golden_id": d.golden_id,
                "found": d.found,
                "match_type": d.match_type,
            }
            for d in report.descripteur_details
        ],
        "decouvertes": [
            {
                "concept_name": d.concept_name,
                "ontology_id": d.ontology_id,
                "categorie": d.categorie,
            }
            for d in report.decouvertes
        ],
        "feedback": {
            "texte": report.feedback_pedagogique.texte,
            "rang_edn_manques": report.feedback_pedagogique.rang_edn_manques,
            "concepts_cours_cites": report.feedback_pedagogique.concepts_cours_cites,
            "has_critical_miss": report.feedback_pedagogique.has_critical_miss,
        } if report.feedback_pedagogique else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Export corrections JSON pour Scalingo")
    parser.add_argument("--csv", type=str, default=str(CSV_DEFAULT))
    parser.add_argument("--students", nargs="*", default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--no-feedback", action="store_true", default=False,
                        help="Désactiver le feedback pédagogique GPT (plus rapide)")
    args = parser.parse_args()

    print("=" * 60)
    print("📦 Export des corrections en JSON")
    print("=" * 60)

    # 1. Charger le golden set
    print("\n📥 Chargement du golden set...")
    golden = load_golden_set()
    print(f"   ✅ {len(golden)} cas chargés")

    # 2. Charger le CSV
    csv_path = Path(args.csv)
    print(f"\n📥 Chargement du CSV : {csv_path.name}")
    students = load_student_csv(csv_path)
    print(f"   ✅ {len(students)} étudiants : {', '.join(students.keys())}")

    if args.students:
        students = {k: v for k, v in students.items() if k in args.students}
        print(f"   📌 Filtré → {len(students)} étudiants")

    # 3. Évaluer
    with_feedback = not args.no_feedback
    print(f"\n🔄 Évaluation de {len(students)} étudiants × 15 cas...")
    print(f"   Feedback pédagogique : {'✅ Activé (GPT + cours SFC)' if with_feedback else '❌ Désactivé'}")
    t_global = time.time()

    export_data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pipeline_version": "RAG Neurosymbolique v1.0",
        "students": {},
        "golden": {},
    }

    # Golden set simplifié
    for cas_num, cas_info in golden.items():
        export_data["golden"][str(cas_num)] = {
            "diagnostic_principal": cas_info["diagnostic_principal"],
            "category": cas_info.get("category", ""),
            "annotations": cas_info.get("annotations", []),
        }

    # Évaluation par étudiant
    for i, (code, responses) in enumerate(students.items(), 1):
        print(f"   [{i}/{len(students)}] 👤 {code}...", end="", flush=True)
        t0 = time.time()

        results = evaluate_student(code, responses, golden, with_feedback=with_feedback)

        cases_data = {}
        scores = []
        for cas_num, texte, report in results:
            report_dict = report_to_dict(report)
            cases_data[str(cas_num)] = {
                "student_text": texte,
                "report": report_dict,
            }
            if report:
                scores.append(report.score_final_pct)

        avg = sum(scores) / len(scores) if scores else 0
        dt = time.time() - t0

        export_data["students"][code] = {
            "average": round(avg, 1),
            "nb_answered": len(scores),
            "cases": cases_data,
        }

        print(f" ✅ {avg:.0f}% ({dt:.1f}s)")

    total_time = time.time() - t_global
    print(f"\n   ⏱️ Total : {total_time:.1f}s")

    # 4. Écrire le JSON
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = COLLECTOR_ROOT / "corrections" / "data.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    size_kb = output_path.stat().st_size / 1024
    print(f"\n✅ JSON écrit : {output_path}")
    print(f"   📏 Taille : {size_kb:.0f} Ko")


if __name__ == "__main__":
    main()
