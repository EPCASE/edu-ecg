#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rebuild_ontology_from_owl.py — PARTIE B : reconstruire ontology_v2.json depuis
un .owl REANNOTE, SANS perdre la couche d'enrichissement (inférence/cohérence).

Pourquoi ce script existe
=========================
`ontology_v2.json` n'est PAS un simple export du .owl. Il porte une couche
d'enrichissement MANUELLE qui n'existe pas dans l'OWL exporté de WebProtégé :
  • ECG_NORMAL.infer_from_requires   (le déclencheur d'inférence)      [OWL: absent]
  • ECG_NORMAL.excludes_families     (+9 familles ajoutées à la main)
  • negation_of                      (polarité des requires "normaux")  [OWL: absent]
  • requires curados (ECG_NORMAL, PAS_*), VOLTAGE_NORMAL_DU_QRS créé main
  • ~188 concepts à synonymes enrichis
Régénérer NAÏVEMENT depuis le .owl détruirait TOUTE la décision « B ».

Ce que fait ce script
=====================
  1. Convertit le .owl reannoté -> JSON brut (convert_owl_to_v2, déterministe).
  2. Réapplique onto_overlay.json (couche Partie B) selon une politique explicite :
       - hierarchie parents/children  : TOUJOURS le nouveau .owl (but du reannote)
       - infer_from_requires / negation_of / requires(Partie B) : overlay (exact)
       - excludes_families            : UNION(owl, overlay)      (additif)
       - synonymes                    : UNION(owl, overlay)      (additif)
       - concepts_add                 : ajoutés seulement si absents du nouveau .owl
  3. VALIDE le résultat (garde-fous : ECG_NORMAL infère, excludes présents,
     negation_of présents, aucun concept Partie B perdu).
  4. Écrit (avec BACKUP horodaté) les copies runtime, sauf en --dry-run.

Usage
=====
  python rebuild_ontology_from_owl.py --owl <chemin_reannote.owl> --dry-run
  python rebuild_ontology_from_owl.py --owl <chemin_reannote.owl>          # applique
  python rebuild_ontology_from_owl.py --owl <...> --only-main               # 1 seule copie

IMPORTANT : PYTHONHASHSEED est forcé pour la reproductibilité de la conversion.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
import unicodedata
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONVERT = ROOT / "convert_owl_to_v2.py"
OVERLAY = ROOT / "onto_overlay.json"

# Copies runtime à synchroniser (source de vérité unique — RAG ontologique supprimé le 2026-07-29).
RUNTIME_COPIES = [
    ROOT / "data" / "ontology_v2.json",
]
# _standalone est optionnel (présent seulement dans certains layouts)
_STANDALONE = ROOT / "_standalone" / "rag_pipeline" / "data" / "ontology_v2.json"
if _STANDALONE.parent.exists():
    RUNTIME_COPIES.append(_STANDALONE)


def canon(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s).strip())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"_+", "_", re.sub(r"[^A-Z0-9]+", "_", s.upper())).strip("_")


def load_convert():
    spec = importlib.util.spec_from_file_location("c2v", CONVERT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)
    return mod


def as_list(v):
    return v if isinstance(v, list) else ([] if v is None else [v])


# ---------------------------------------------------------------------------
# Fusion overlay
# ---------------------------------------------------------------------------

def apply_overlay(fresh_full: dict, overlay: dict, log: list) -> dict:
    concepts = fresh_full["concepts"]
    stats = {"infer": 0, "negation": 0, "requires": 0, "has_qualifiers": 0,
             "excludes_union": 0, "syn_union": 0, "concepts_added": 0,
             "part_b_missing_target": 0}

    # 1) concepts créés main : uniquement si absents du nouveau .owl
    for cid, cdef in (overlay.get("concepts_add") or {}).items():
        if cid not in concepts:
            concepts[cid] = json.loads(json.dumps(cdef))  # copie profonde
            stats["concepts_added"] += 1
            log.append(f"  + concept créé (overlay) : {cid}")
        else:
            log.append(f"  = concept déjà dans le .owl (overlay ignoré) : {cid}")

    # 2) concepts Partie B : infer_from_requires / negation_of / requires / has_qualifiers
    for cid, rec in (overlay.get("part_b_concepts") or {}).items():
        c = concepts.get(cid)
        if not c:
            stats["part_b_missing_target"] += 1
            log.append(f"  [!] concept Partie B ABSENT du .owl : {cid} "
                       f"(l'ID a-t-il changé au reannotage ?)")
            continue
        if "infer_from_requires" in rec:
            c["infer_from_requires"] = rec["infer_from_requires"]; stats["infer"] += 1
        if "negation_of" in rec:
            c["negation_of"] = rec["negation_of"]; stats["negation"] += 1
        if "requires" in rec:
            c["requires"] = rec["requires"]; stats["requires"] += 1
        if "has_qualifiers" in rec:
            c["has_qualifiers"] = rec["has_qualifiers"]; stats["has_qualifiers"] += 1

    # 3) excludes_families : UNION(owl, overlay-additions), ordre stable
    for cid, add in (overlay.get("excludes_families_additions") or {}).items():
        c = concepts.get(cid)
        if not c:
            log.append(f"  [!] excludes_families cible absente : {cid}")
            continue
        cur = as_list(c.get("excludes_families"))
        merged = list(cur)
        for fam in add:
            if fam not in merged:
                merged.append(fam)
        if merged != cur:
            c["excludes_families"] = merged
            stats["excludes_union"] += len(merged) - len(cur)

    # 4) synonymes : UNION additive, dédup insensible à la casse
    for cid, add in (overlay.get("synonyms_additions") or {}).items():
        c = concepts.get(cid)
        if not c:
            continue
        cur = as_list(c.get("synonymes"))
        have = {s.strip().lower() for s in cur}
        n0 = len(cur)
        for s in add:
            if s.strip().lower() not in have:
                cur.append(s); have.add(s.strip().lower())
        if len(cur) != n0:
            c["synonymes"] = cur
            stats["syn_union"] += len(cur) - n0

    # 5) curated_overrides (3-WAY merge) : hiérarchie/composition corrigée à la main.
    #    base  = valeur du .owl au moment de la capture de l'overlay
    #    ours  = valeur curados (live)
    #    theirs= valeur du NOUVEAU .owl (conversion courante)
    #    Règle : si le reannotage a CHANGÉ le champ (theirs != base) -> le .owl gagne
    #            (c'est le but du reannotage) ; sinon on restaure 'ours' (edit curados).
    stats["curated_kept_ours"] = 0
    stats["curated_took_theirs"] = 0
    for cid, rec in (overlay.get("curated_overrides") or {}).items():
        c = concepts.get(cid)
        if not c:
            log.append(f"  [!] curated_override cible absente du .owl : {cid}")
            continue
        for field, bo in rec.items():
            base = sorted(as_list(bo.get("base")))
            ours = as_list(bo.get("ours"))
            theirs = sorted(as_list(c.get(field)))
            if theirs != base:
                # le reannotage a modifié ce champ -> on respecte le .owl (theirs)
                stats["curated_took_theirs"] += 1
                log.append(f"  ~ {cid}.{field} : .owl réannoté prime "
                           f"(base={base} -> theirs={theirs}), edit curados NON restauré")
            else:
                # le .owl n'a pas bougé -> on restaure l'édit curados (ours)
                if sorted(theirs) != sorted(ours):
                    c[field] = ours
                    stats["curated_kept_ours"] += 1
                    log.append(f"  ↺ {cid}.{field} : restauration édit curados "
                               f"(ours={ours})")

    fresh_full.setdefault("metadata", {})["overlay_applied"] = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "overlay_stats": stats,
    }
    return stats


# ---------------------------------------------------------------------------
# Validation (garde-fous Partie B)
# ---------------------------------------------------------------------------

def validate(full: dict, overlay: dict, log: list) -> list:
    """Renvoie une liste d'ERREURS bloquantes (vide = OK)."""
    errors = []
    concepts = full["concepts"]

    # a) tous les concepts Partie B présents avec leur flag
    for cid, rec in (overlay.get("part_b_concepts") or {}).items():
        c = concepts.get(cid)
        if not c:
            errors.append(f"Partie B perdue : concept {cid} absent du résultat")
            continue
        if "infer_from_requires" in rec and "infer_from_requires" not in c:
            errors.append(f"{cid} : infer_from_requires non réappliqué")
        if "negation_of" in rec and not c.get("negation_of"):
            errors.append(f"{cid} : negation_of non réappliqué")

    # b) ECG_NORMAL : excludes_families >= additions overlay
    en = concepts.get("ECG_NORMAL", {})
    ef = set(as_list(en.get("excludes_families")))
    for fam in (overlay.get("excludes_families_additions") or {}).get("ECG_NORMAL", []):
        if fam not in ef:
            errors.append(f"ECG_NORMAL : excludes_families manque {fam}")

    # c) l'inférenceur charge et ECG_NORMAL est bien une cible + infère un cas normal
    try:
        sys.path.insert(0, str(ROOT / "rag_pipeline"))
        from pattern_inference import PatternInferencer  # type: ignore
        inf = PatternInferencer(concepts)
        targets = {t for t, _ in inf.targets}
        if canon("ECG_NORMAL") not in targets:
            errors.append("PatternInferencer : ECG_NORMAL n'est pas une cible d'inférence")
        # cas normal minimal -> doit inférer ECG_NORMAL
        got = inf.infer(["RYTHME_SINUSAL", "QRS_NORMAL", "PAS_D_ANOMALIE_DE_LE_REPOLARISATION"])
        if not any(g["ontology_id"] == "ECG_NORMAL" for g in got):
            errors.append("PatternInferencer : n'infère PAS ECG_NORMAL sur un tracé normal")
        # anomalie atriale -> doit BLOQUER
        blocked = inf.infer(["RYTHME_SINUSAL", "QRS_NORMAL",
                             "PAS_D_ANOMALIE_DE_LE_REPOLARISATION",
                             "HYPERTROPHIE_ATRIALE_GAUCHE"])
        if any(g["ontology_id"] == "ECG_NORMAL" for g in blocked):
            errors.append("PatternInferencer : infère ECG_NORMAL malgré une HAG (excludes KO)")
    except Exception as e:  # pragma: no cover
        errors.append(f"PatternInferencer : erreur de chargement/inférence : {e}")
    finally:
        if str(ROOT / "rag_pipeline") in sys.path:
            sys.path.remove(str(ROOT / "rag_pipeline"))

    log.append(f"  validation : {len(errors)} erreur(s)")
    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Partie B : rebuild ontology_v2.json depuis .owl réannoté.")
    ap.add_argument("--owl", required=True, help="chemin du .owl RÉANNOTÉ")
    ap.add_argument("--dry-run", action="store_true", help="ne rien écrire (valider seulement)")
    ap.add_argument("--only-main", action="store_true",
                    help="n'écrire que la copie source (ECG lecture/data), pas les miroirs")
    ap.add_argument("--overlay", default=str(OVERLAY), help="chemin onto_overlay.json")
    args = ap.parse_args()

    # reproductibilité de la conversion (le convertisseur est déterministe, mais on fige)
    os.environ.setdefault("PYTHONHASHSEED", "0")

    owl = Path(args.owl)
    if not owl.exists():
        print(f"[ERREUR] .owl introuvable : {owl}"); sys.exit(2)
    if not Path(args.overlay).exists():
        print(f"[ERREUR] overlay introuvable : {args.overlay}\n"
              f"          -> lance d'abord :  python _build_overlay.py"); sys.exit(2)

    overlay = json.load(open(args.overlay, encoding="utf-8"))
    mod = load_convert()

    log: list = []
    print("=" * 78)
    print("  PARTIE B — REBUILD ontology_v2.json DEPUIS .owl RÉANNOTÉ")
    print(f"  .owl     : {owl}")
    print(f"  overlay  : {Path(args.overlay).name}")
    print(f"  mode     : {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print("=" * 78)

    print("\n[1/4] Conversion .owl -> JSON (déterministe)…")
    full = mod.build_v2_json(mod.parse_owl(str(owl)))
    print(f"      concepts (brut .owl) : {len(full['concepts'])}")

    print("\n[2/4] Réapplication de la couche d'enrichissement (overlay)…")
    stats = apply_overlay(full, overlay, log)
    for line in log:
        print(line)
    print(f"      infer_from_requires réappliqués : {stats['infer']}")
    print(f"      negation_of réappliqués         : {stats['negation']}")
    print(f"      requires (Partie B) overridés    : {stats['requires']}")
    print(f"      excludes_families ajoutées       : {stats['excludes_union']}")
    print(f"      synonymes ajoutés                : {stats['syn_union']}")
    print(f"      curated 3-way — .owl prime        : {stats.get('curated_took_theirs', 0)}")
    print(f"      curated 3-way — édit restauré     : {stats.get('curated_kept_ours', 0)}")
    print(f"      concepts créés (overlay)         : {stats['concepts_added']}")
    if stats["part_b_missing_target"]:
        print(f"      [!] concepts Partie B absents du .owl : {stats['part_b_missing_target']}")
    print(f"      concepts (final)                 : {len(full['concepts'])}")

    print("\n[3/4] Validation (garde-fous Partie B)…")
    errors = validate(full, overlay, log)
    if errors:
        print("  ── ERREURS BLOQUANTES ──")
        for e in errors:
            print(f"     ✗ {e}")
        print("\n  ABANDON : le rebuild n'est PAS écrit (corrige l'overlay ou le .owl).")
        # écrit quand même un aperçu pour diagnostic
        preview = ROOT / "_rebuild_preview.json"
        preview.write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  Aperçu diagnostic : {preview.name}")
        sys.exit(1)
    print("  ✓ tous les garde-fous passent (inférence, excludes, negation_of, concepts).")

    print("\n[4/4] Écriture des copies runtime…")
    targets = RUNTIME_COPIES[:1] if args.only_main else RUNTIME_COPIES
    payload = json.dumps(full, ensure_ascii=False, indent=2)
    if args.dry_run:
        preview = ROOT / "_rebuild_preview.json"
        preview.write_text(payload, encoding="utf-8")
        print(f"  DRY-RUN : aucune copie runtime modifiée. Aperçu écrit : {preview.name}")
        print(f"  Cibles qui SERAIENT écrites ({len(targets)}) :")
        for p in targets:
            print(f"     - {p}")
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for p in targets:
        if not p.parent.exists():
            print(f"  [skip] dossier absent : {p.parent}")
            continue
        if p.exists():
            bak = p.with_suffix(p.suffix + f".{stamp}.bak")
            shutil.copy2(p, bak)
            print(f"  backup : {bak.name}")
        p.write_text(payload, encoding="utf-8")
        print(f"  écrit  : {p}")
    print("\n  ✓ Rebuild appliqué. Pense à relancer les tests d'inférence / la comparaison golden.")


if __name__ == "__main__":
    main()
