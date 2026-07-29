# -*- coding: utf-8 -*-
"""make_virtual_students.py — Génère des étudiants VIRTUELS pour tester la fiabilité
de la correction sur les 75 ECG, avec des réponses attendues CONTRÔLÉES.

Profils (chacun répond aux 75 cas) :
  • PIERRE  — « parle comme Pierre » : réponse experte = reponse_attendue verbatim
              (cases_reference.json). Stress-test : DOIT scorer très haut (~100%).
  • FORT    — bon étudiant : cite tous les validants + quelques descripteurs (télégraphique).
  • MOYEN   — étudiant moyen : le diagnostic principal + 1 descripteur ; rate les validants secondaires.
  • FAIBLE  — étudiant faible : lecture vague/partielle ; doit scorer bas.

Chaque réponse est COMPOSÉE à partir des concepts golden du cas lui-même
(golden_config.golden_for_scorer) => l'attendu est connu, donc contrôlable.

Sortie : C:\\Users\\Administrateur\\ECG collector\\corrections\\virtual_students\\<CODE>.json
         (format collector identique aux vrais étudiants) + _summary.md / _summary.json.

Usage :
  python make_virtual_students.py --pilot            # cas 1..3, tous profils (rapide)
  python make_virtual_students.py --cases 1 2 3 8    # cas précis
  python make_virtual_students.py --all              # les 75 cas
  python make_virtual_students.py --all --profiles PIERRE FORT
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\Users\Administrateur\bmad\ECG lecture")
ONLINE = ROOT / "ecg-online"
RAG = ONLINE / "rag_pipeline"  # source de vérité unique (RAG ontologique supprimé le 2026-07-29)
OUT_DIR = Path(r"C:\Users\Administrateur\ECG collector\corrections\virtual_students")

sys.path.insert(0, str(ONLINE))   # app.golden_config
sys.path.insert(0, str(RAG))      # pipeline (copie de production, index reconstruit)

from dotenv import load_dotenv
load_dotenv(ONLINE / ".env")
load_dotenv(ROOT / ".env")
os.chdir(str(RAG))

from candidate_report import generate_candidate_report  # noqa: E402
from app import golden_config as gc                      # noqa: E402

CASES_REF = json.load(open(ONLINE / "data" / "cases_reference.json", encoding="utf-8"))["references"]
REF_BY_NUM = {r["num"]: r for r in CASES_REF}

PIPELINE_VERSION = "RAG Neurosymbolique v1.1 (C1+C2) — VIRTUAL"

PROFILES = ["PIERRE", "FORT", "MOYEN", "FAIBLE"]
PROFILE_CODE = {
    "PIERRE": "ECG-PIERRE",
    "FORT":   "ECG-FORT",
    "MOYEN":  "ECG-MOYEN",
    "FAIBLE": "ECG-FAIBLE",
}
# Bande de score ATTENDUE par profil (min, max) — pour flaguer les anomalies.
EXPECTED_BAND = {
    "PIERRE": (60.0, 100.0),   # expert : doit passer largement
    "FORT":   (60.0, 100.0),
    "MOYEN":  (20.0, 90.0),
    "FAIBLE": (0.0, 55.0),
}


def _is_infra_error(msg: str) -> bool:
    """Vrai si l'erreur vient de l'API (quota/débit/réseau) et non du contenu."""
    m = (msg or "").lower()
    return any(k in m for k in (
        "429", "quota", "rate limit", "rate_limit", "insufficient_quota",
        "billing", "timeout", "timed out", "connection", "503", "502",
        "overloaded", "service unavailable",
    ))


# ──────────────────────────── composition des réponses ────────────────────────────
def _phrase(name: str, statut: str) -> str:
    """Rend un concept en fragment de phrase (négation si statut=absent)."""
    name = (name or "").strip()
    if not name:
        return ""
    if statut == "absent":
        return f"pas de {name.lower()}"
    return name


def author_text(profile: str, num: int, golden: dict) -> str:
    """Compose le texte étudiant pour un profil, à partir du golden du cas."""
    ref = REF_BY_NUM.get(num, {})
    diag = golden.get("diagnostic_principal") or ref.get("titre", "")
    vals = golden.get("validants", [])
    descs = golden.get("descripteurs", [])

    if profile == "PIERRE":
        # Réponse experte verbatim (la « voix » de Pierre).
        txt = (ref.get("reponse_attendue") or "").strip()
        if txt:
            return txt
        # fallback : compose expert si pas de reponse_attendue
        profile = "FORT"

    if profile == "FORT":
        frags = [_phrase(v["concept_name"], v.get("statut", "present")) for v in vals]
        frags += [d["concept_name"] for d in descs[:4]]
        frags = [f for f in frags if f]
        tail = f" {diag}." if diag else ""
        return ", ".join(frags) + "." + tail

    if profile == "MOYEN":
        # diagnostic principal (1er validant présent) + 1 descripteur ; rate le reste.
        present_vals = [v for v in vals if v.get("statut", "present") == "present"]
        frags = []
        if present_vals:
            frags.append(present_vals[0]["concept_name"])
        if descs:
            frags.append(descs[0]["concept_name"])
        tail = f" {diag}." if diag else ""
        return ", ".join(f for f in frags if f) + "." + tail if frags else (diag or "tracé")

    if profile == "FAIBLE":
        # lecture vague : 1 descripteur générique + hésitation, sans le diagnostic.
        vague = "tracé difficile à interpréter"
        d0 = descs[0]["concept_name"] if descs else ""
        return f"{vague}, {d0.lower()} ?".strip(", ") if d0 else vague

    return diag or "tracé"


# ──────────────────────────── sérialisation (format collector) ────────────────────────────
def report_to_dict(report):
    if report is None:
        return None
    return {
        "erreur": getattr(report, "erreur", "") or "",
        "score_final_pct": round(report.score_final_pct, 1),
        "nb_validants_trouves": report.nb_validants_trouves,
        "nb_validants_attendus": report.nb_validants_attendus,
        "nb_descripteurs_trouves": report.nb_descripteurs_trouves,
        "nb_descripteurs_attendus": report.nb_descripteurs_attendus,
        "latence_s": round(report.latence_s, 2),
        "concepts_extraits": [
            {
                "terme_brut": c.terme_brut, "statut": c.statut,
                "ontology_id": c.ontology_id, "concept_name": c.concept_name,
                "method": c.method, "justification": c.justification,
                "top_k_candidats": c.top_k_candidats, "llm_confiance": c.llm_confiance,
            } for c in report.concepts_extraits
        ],
        "validant_details": [
            {
                "golden_name": v.golden_name, "golden_id": v.golden_id,
                "found": v.found, "score_pct": round(v.score_pct, 1),
                "match_type": v.match_type,
                "found_via_name": getattr(v, "found_via_name", ""),
                "explication": getattr(v, "explication", ""),
            } for v in report.validant_details
        ],
        "descripteur_details": [
            {"golden_name": d.golden_name, "golden_id": d.golden_id,
             "found": d.found, "match_type": d.match_type}
            for d in report.descripteur_details
        ],
        "decouvertes": [
            {"concept_name": d.concept_name, "ontology_id": d.ontology_id,
             "categorie": d.categorie}
            for d in report.decouvertes
        ],
    }


def build_golden_contract(num: int):
    """(golden_ids, golden_names, golden_roles, diagnostic) depuis golden_config."""
    g = gc.golden_for_scorer(num)
    ids, names, roles = [], [], []
    for v in g["validants"]:
        ids.append(v["concept_id"]); names.append(v["concept_name"]); roles.append("validant")
    for d in g["descripteurs"]:
        ids.append(d["concept_id"]); names.append(d["concept_name"]); roles.append("descripteur")
    return g, ids, names, roles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", help="cas 1..3 seulement")
    ap.add_argument("--all", action="store_true", help="les 75 cas")
    ap.add_argument("--cases", nargs="*", type=int, default=None, help="numéros de cas précis")
    ap.add_argument("--profiles", nargs="*", default=PROFILES,
                    help=f"profils à générer (défaut : {PROFILES})")
    ap.add_argument("--out", default=str(OUT_DIR))
    args = ap.parse_args()

    if args.pilot:
        case_nums = [1, 2, 3]
    elif args.cases:
        case_nums = args.cases
    elif args.all:
        case_nums = list(range(1, 76))
    else:
        case_nums = [1, 2, 3]
        print("  (aucun scope précisé → pilote cas 1..3)")

    profiles = [p.upper() for p in args.profiles if p.upper() in PROFILES]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 74)
    print("  GÉNÉRATION D'ÉTUDIANTS VIRTUELS (test de fiabilité)")
    print(f"  profils : {profiles}")
    print(f"  cas     : {len(case_nums)}  ({case_nums[0]}..{case_nums[-1]})")
    print(f"  sortie  : {out_dir}")
    print("=" * 74)

    # Pré-charge le contrat golden par cas (une fois).
    golden_by_num = {}
    for num in case_nums:
        g, ids, names, roles = build_golden_contract(num)
        golden_by_num[num] = (g, ids, names, roles)

    summary = []  # lignes {profile, num, score, band, ok, diag, text}
    t_global = time.time()

    for profile in profiles:
        code = PROFILE_CODE[profile]
        out_path = out_dir / f"{code}.json"
        cases_out = {}
        # Reprise : si le fichier existe déjà, on garde les cas déjà calculés.
        if out_path.exists():
            try:
                prev = json.load(open(out_path, encoding="utf-8"))
                cases_out = prev.get("cases", {}) or {}
            except Exception:
                cases_out = {}
        scores = []
        print(f"\n▶ {profile} ({code})", flush=True)

        def _flush(avg_partial):
            payload = {
                "code": code,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pipeline_version": PIPELINE_VERSION,
                "profile": profile,
                "average": avg_partial,
                "nb_answered": len(cases_out),
                "cases": cases_out,
            }
            tmp = out_path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(out_path)

        for num in case_nums:
            g, ids, names, roles = golden_by_num[num]
            text = author_text(profile, num, g)
            # Reprise : cas déjà calculé (rapport valide SANS erreur infra) => réutilisé.
            prev_case = cases_out.get(str(num))
            prev_rep = prev_case.get("report") if prev_case else None
            prev_ok = (isinstance(prev_rep, dict) and "score_final_pct" in prev_rep
                       and not _is_infra_error(prev_rep.get("erreur", "")))
            if prev_ok and isinstance(prev_rep, dict):
                score = prev_rep["score_final_pct"]
                scores.append(score)
                lo, hi = EXPECTED_BAND[profile]
                ok = lo <= score <= hi
                summary.append({
                    "profile": profile, "num": num, "score": score,
                    "band": [lo, hi], "ok": ok,
                    "diag": g["diagnostic_principal"], "text": text[:160],
                })
                print(f"    cas {num:>2} : {score:5.1f}%  ({'OK ' if ok else '!! '})  (repris)",
                      flush=True)
                continue
            t0 = time.time()
            try:
                report = generate_candidate_report(
                    texte_etudiant=text,
                    golden_ids=ids, golden_names=names, golden_roles=roles,
                    diagnostic_principal=g["diagnostic_principal"],
                    with_feedback=False,
                )
                rd = report_to_dict(report)
                score = rd["score_final_pct"] if rd else 0.0
            except Exception as e:
                rd = {"erreur": str(e)[:200]}
                score = 0.0

            # Erreur d'infrastructure (quota/429/réseau) => NE PAS stocker un faux 0.
            # On sauvegarde ce qui est acquis et on ABANDONNE proprement : la reprise
            # relancera ce cas plus tard (quand le quota OpenAI sera rétabli).
            err = (rd or {}).get("erreur", "") if isinstance(rd, dict) else ""
            if err and _is_infra_error(err):
                _flush(round(sum(scores) / len(scores), 1) if scores else 0.0)
                print(f"    cas {num:>2} : ⛔ ARRÊT — erreur infra : {err[:90]}", flush=True)
                print("\n  ⚠️  Quota/ąpi OpenAI épuisé. Cas déjà faits conservés ; "
                      "relancez la MÊME commande pour reprendre.", flush=True)
                _write_summary(out_dir, summary, profiles, case_nums, time.time() - t_global)
                raise SystemExit(2)

            scores.append(score)
            lo, hi = EXPECTED_BAND[profile]
            ok = lo <= score <= hi
            summary.append({
                "profile": profile, "num": num, "score": score,
                "band": [lo, hi], "ok": ok,
                "diag": g["diagnostic_principal"], "text": text[:160],
            })
            cases_out[str(num)] = {"student_text": text, "report": rd}
            _flush(round(sum(scores) / len(scores), 1))  # écriture incrémentale
            flag = "OK " if ok else "!! "
            print(f"    cas {num:>2} : {score:5.1f}%  {flag} ({time.time()-t0:.1f}s)  "
                  f"{g['diagnostic_principal'][:46]}", flush=True)

        avg = round(sum(scores) / len(scores), 1) if scores else 0.0
        _flush(avg)
        print(f"  -> {code}.json  (moyenne {avg}%)", flush=True)

    # Résumé de contrôlabilité
    _write_summary(out_dir, summary, profiles, case_nums, time.time() - t_global)
    print(f"\n✓ Terminé en {time.time()-t_global:.0f}s. Résumé : {out_dir / '_summary.md'}")


def _write_summary(out_dir: Path, summary: list, profiles: list, case_nums: list, dt: float):
    json.dump(summary, open(out_dir / "_summary.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    lines = [f"# Étudiants virtuels — contrôle de fiabilité",
             f"_Généré le {datetime.now():%Y-%m-%d %H:%M} · {len(case_nums)} cas · "
             f"{len(profiles)} profils · {dt:.0f}s_", ""]
    # moyennes par profil
    lines.append("## Moyennes par profil")
    lines.append("| Profil | Moyenne | Attendu | Anomalies |")
    lines.append("|---|---|---|---|")
    for p in profiles:
        rows = [s for s in summary if s["profile"] == p]
        avg = sum(r["score"] for r in rows) / len(rows) if rows else 0
        lo, hi = EXPECTED_BAND[p]
        anomalies = sum(1 for r in rows if not r["ok"])
        lines.append(f"| {p} | {avg:.1f}% | {lo:.0f}–{hi:.0f}% | {anomalies} |")
    lines.append("")
    # anomalies détaillées
    anos = [s for s in summary if not s["ok"]]
    lines.append(f"## Anomalies ({len(anos)})")
    if not anos:
        lines.append("_Aucune — tous les scores tombent dans la bande attendue._")
    else:
        lines.append("| Profil | Cas | Score | Attendu | Diagnostic | Texte |")
        lines.append("|---|---|---|---|---|---|")
        for s in sorted(anos, key=lambda x: (x["profile"], x["num"])):
            lo, hi = s["band"]
            lines.append(f"| {s['profile']} | {s['num']} | {s['score']:.1f}% | "
                         f"{lo:.0f}–{hi:.0f}% | {s['diag'][:40]} | {s['text'][:60]} |")
    (out_dir / "_summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
