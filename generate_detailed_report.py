# -*- coding: utf-8 -*-
"""generate_detailed_report.py — Rapport DÉTAILLÉ des étudiants virtuels (75 ECG).

Lit les 4 JSON de profils et produit `_rapport_detaille.md` :
  - Synthèse par profil (moyenne réelle recalculée, médiane, min/max, latence)
  - Distribution des scores (histogramme ASCII)
  - Fiabilité validants/descripteurs
  - Anomalies (hors bande attendue) avec détail des validants ratés
  - Tableau complet des 75 cas pour le profil expert PIERRE
  - Cas les plus faibles (diagnostic de fiabilité pipeline)
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime
from pathlib import Path

VS = Path(r"C:\Users\Administrateur\ECG collector\corrections\virtual_students")
OUT = VS / "_rapport_detaille.md"

PROFILES = ["PIERRE", "FORT", "MOYEN", "FAIBLE"]
LABEL = {
    "PIERRE": "Expert (réponse de référence verbatim)",
    "FORT": "Bon étudiant (tous validants + descripteurs)",
    "MOYEN": "Étudiant moyen (diagnostic + 1 descripteur)",
    "FAIBLE": "Étudiant faible (lecture vague)",
}
BAND = {"PIERRE": (60, 100), "FORT": (60, 100), "MOYEN": (20, 90), "FAIBLE": (0, 55)}


def load(profile: str) -> dict:
    f = VS / f"ECG-{profile}.json"
    if not f.exists():
        return {}
    return json.load(open(f, encoding="utf-8"))


def bar(pct: float, width: int = 20) -> str:
    n = int(round(pct / 100 * width))
    return "█" * n + "·" * (width - n)


def collect(profile: str):
    """Retourne (rows, meta) — rows: liste par cas triée par num."""
    j = load(profile)
    cases = j.get("cases", {})
    rows = []
    for num_s, c in cases.items():
        rep = c.get("report") or {}
        if "score_final_pct" not in rep:
            continue
        rows.append({
            "num": int(num_s),
            "score": rep["score_final_pct"],
            "val_found": rep.get("nb_validants_trouves", 0),
            "val_att": rep.get("nb_validants_attendus", 0),
            "desc_found": rep.get("nb_descripteurs_trouves", 0),
            "desc_att": rep.get("nb_descripteurs_attendus", 0),
            "latence": rep.get("latence_s", 0.0),
            "text": (c.get("student_text") or "")[:70],
            "validant_details": rep.get("validant_details", []),
            "concepts": rep.get("concepts_extraits", []),
        })
    rows.sort(key=lambda r: r["num"])
    return rows


def dist_block(scores: list[float]) -> list[str]:
    buckets = [0] * 5  # 0-20,20-40,40-60,60-80,80-100
    for s in scores:
        idx = min(int(s // 20), 4)
        buckets[idx] += 1
    labels = ["  0–20 ", " 20–40 ", " 40–60 ", " 60–80 ", "80–100 "]
    out = []
    mx = max(buckets) or 1
    for lab, b in zip(labels, buckets):
        out.append(f"    {lab}| {'▓' * int(round(b / mx * 30)):30} {b}")
    return out


def main():
    lines = [
        "# 📊 Rapport détaillé — Étudiants virtuels (75 ECG)",
        f"_Généré le {datetime.now():%Y-%m-%d %H:%M} · pipeline RAG Neurosymbolique "
        "(correctif NER fragments courts appliqué)_",
        "",
        "> **But** : mesurer la fiabilité de la correction automatique sur 4 profils "
        "d'étudiants aux réponses *contrôlées*, dérivées du golden de chaque cas.",
        "",
        "---",
        "",
        "## 1. Synthèse par profil",
        "",
        "| Profil | Rôle | Moyenne | Médiane | Min | Max | Latence moy. | Bande attendue | Anomalies |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    all_rows = {}
    for p in PROFILES:
        rows = collect(p)
        all_rows[p] = rows
        scores = [r["score"] for r in rows]
        if not scores:
            continue
        lo, hi = BAND[p]
        anomalies = [r for r in rows if not (lo <= r["score"] <= hi)]
        lat = statistics.mean(r["latence"] for r in rows) if rows else 0
        lines.append(
            f"| **{p}** | {LABEL[p]} | **{statistics.mean(scores):.1f}%** | "
            f"{statistics.median(scores):.1f}% | {min(scores):.0f}% | {max(scores):.0f}% | "
            f"{lat:.1f}s | {lo}–{hi}% | {len(anomalies)} |"
        )

    # 2. Distributions
    lines += ["", "---", "", "## 2. Distribution des scores", ""]
    for p in PROFILES:
        rows = all_rows[p]
        if not rows:
            continue
        lines.append(f"### {p} — {LABEL[p]}")
        lines.append("```")
        lines += dist_block([r["score"] for r in rows])
        lines.append("```")
        lines.append("")

    # 3. Fiabilité validants / descripteurs
    lines += ["---", "", "## 3. Fiabilité de détection (validants & descripteurs)", "",
              "| Profil | Validants trouvés / attendus | Taux | Descripteurs | Taux |",
              "|---|---|---|---|---|"]
    for p in PROFILES:
        rows = all_rows[p]
        if not rows:
            continue
        vf = sum(r["val_found"] for r in rows)
        va = sum(r["val_att"] for r in rows)
        df = sum(r["desc_found"] for r in rows)
        da = sum(r["desc_att"] for r in rows)
        vt = f"{100*vf/va:.0f}%" if va else "—"
        dt = f"{100*df/da:.0f}%" if da else "—"
        lines.append(f"| {p} | {vf} / {va} | {vt} | {df} / {da} | {dt} |")

    # 4. Anomalies détaillées
    lines += ["", "---", "", "## 4. Anomalies (scores hors bande attendue)", ""]
    any_ano = False
    for p in PROFILES:
        rows = all_rows[p]
        lo, hi = BAND[p]
        anomalies = [r for r in rows if not (lo <= r["score"] <= hi)]
        if not anomalies:
            continue
        any_ano = True
        lines.append(f"### {p} ({len(anomalies)} anomalie·s)")
        lines.append("| Cas | Score | Validants | Texte étudiant | Concepts extraits (NER→onto) |")
        lines.append("|---|---|---|---|---|")
        for r in sorted(anomalies, key=lambda x: x["score"]):
            concepts = ", ".join(
                f"{c.get('terme_brut','?')}→{c.get('concept_name') or c.get('ontology_id') or '∅'}"
                for c in r["concepts"][:4]
            ) or "_(aucun)_"
            lines.append(
                f"| {r['num']} | {r['score']:.0f}% | {r['val_found']}/{r['val_att']} | "
                f"{r['text']} | {concepts[:90]} |"
            )
        lines.append("")
    if not any_ano:
        lines.append("_Aucune anomalie — tous les profils dans leur bande attendue._")
        lines.append("")

    # 5. Cas experts (PIERRE) les plus faibles = signal fiabilité pipeline
    lines += ["---", "", "## 5. Points de vigilance — cas experts (PIERRE) < 70%", "",
              "> Un expert qui répond *verbatim* la référence devrait scorer haut. "
              "Un score bas ici pointe une limite du pipeline (mapping/scoring), pas de l'étudiant.",
              "",
              "| Cas | Score | Val. | Texte de référence | Concepts extraits |",
              "|---|---|---|---|---|"]
    weak = sorted([r for r in all_rows.get("PIERRE", []) if r["score"] < 70],
                  key=lambda x: x["score"])
    for r in weak:
        concepts = ", ".join(
            f"{c.get('terme_brut','?')}→{c.get('concept_name') or '∅'}"
            for c in r["concepts"][:4]
        ) or "_(aucun)_"
        lines.append(
            f"| {r['num']} | {r['score']:.0f}% | {r['val_found']}/{r['val_att']} | "
            f"{r['text']} | {concepts[:80]} |"
        )
    if not weak:
        lines.append("| — | — | — | _Aucun cas expert < 70% 🎉_ | — |")
    lines.append("")

    # 6. Tableau complet PIERRE
    lines += ["---", "", "## 6. Détail complet — profil PIERRE (75 cas)", "",
              "| Cas | Score | Barre | Val. | Desc. | Latence |",
              "|---|---|---|---|---|---|"]
    for r in all_rows.get("PIERRE", []):
        lines.append(
            f"| {r['num']} | {r['score']:.0f}% | `{bar(r['score'])}` | "
            f"{r['val_found']}/{r['val_att']} | {r['desc_found']}/{r['desc_att']} | "
            f"{r['latence']:.1f}s |"
        )
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK — rapport écrit : {OUT}")
    # Résumé console
    for p in PROFILES:
        rows = all_rows[p]
        if rows:
            sc = [r["score"] for r in rows]
            print(f"  {p:7}: moy {statistics.mean(sc):.1f}%  (n={len(sc)})")


if __name__ == "__main__":
    main()
