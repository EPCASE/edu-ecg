#!/usr/bin/env python3
"""
patch_ontology_owl.py — Applique au fichier OWL les correctifs issus du
« Rapport de relecture — Optimisation de l'ontologie » (juillet 2026).

Produit un NOUVEAU fichier OWL (n'écrase pas la source) prêt à réimporter
dans WebProtégé, plus un rapport de ce qui a été modifié.

Correctifs appliqués (synonymes + excludes_families), fondés sur les IRIs
réels découverts dans l'ontologie :

  Synonymes (skos:altLabel) ajoutés :
    - Flutter droit typique  : + CTI-dépendant, flutter antihoraire typique
    - Bloc de branche droit complet : + BBD complet + QRS large / rSR' (libellés)
    - SCA ST+ : + IDM ST+, onde de Pardee, courant de lésion sous-épicardique
    - Microvoltage : + bas voltage, faible voltage, petits QRS, QRS très petits
    - Stimulation atriale : + électro-entraîné à l'étage atrial, spike auriculaire
    - Stimulation ventriculaire : + spike ventriculaire, QRS stimulés larges
    - ECG normal : + tracé sp, sans anomalie significative
    - Faisceau accessoire (WPW) : + PR court + onde delta

Usage :
    python patch_ontology_owl.py
"""
import re
import html
import shutil
from pathlib import Path
from datetime import date

SRC = Path("BrYOzRZIu7jQTwmfcGsi35.owl")
OUT = Path(f"BrYOzRZIu7jQTwmfcGsi35_patched_{date.today().isoformat()}.owl")

# IRI -> liste de synonymes à AJOUTER (skos:altLabel)
SYNONYMS_TO_ADD = {
    # Flutter droit typique
    "R8Qu5zTeQYBDtJy6ntEW9Zt": [
        "Flutter CTI-dépendant", "Flutter antihoraire typique",
    ],
    # Bloc de branche droit complet
    "R9vRCWTeo81VmDBWIWkUUV2": [
        "BBD + QRS large", "BBD complet rSR'", "aspect rSR' avec QRS large",
    ],
    # SCA ST+ (Syndrome coronarien phase aiguë avec sus-décalage)
    "R8WlYgdeyMoXnCoJOPfL6ie": [
        "IDM ST+", "infarctus avec sus-décalage", "onde de Pardee",
        "courant de lésion sous-épicardique territorial",
    ],
    # Microvoltage
    "R7QyGgxIXK3MePvmNUhlkYG": [
        "bas voltage", "faible voltage", "petits QRS",
        "QRS de petite amplitude", "QRS très petits", "microvolté",
    ],
    # Stimulation atriale
    "RuLDUWeiujYnS4rjWXWoSd": [
        "électro-entraîné à l'étage atrial", "spike auriculaire",
        "pacemaker atrial", "rythme stimulé atrial",
    ],
    # Stimulation ventriculaire
    "Rsw8UNDCSH098dExZ6ZXdz": [
        "spike ventriculaire", "QRS stimulés larges", "rythme pacé ventriculaire",
    ],
    # ECG normal
    "RB5yWtPR1F86Bu5TIAoqFe5": [
        "tracé sans anomalie significative",
    ],
    # Faisceau accessoire à conduction antérograde (WPW)
    "R0NX2vKfgeRaBNOeCyd8Mu": [
        "PR court + onde delta",
    ],
}

# IRI concept -> liste d'IRIs de FAMILLES à ajouter en excludes_families
# (ici on complète/garantit ECG_NORMAL — déjà à 7, on vérifie sans doublonner)
EXCLUDES_FAMILIES_TO_ADD = {
    # ECG_NORMAL : familles pathologiques déjà présentes ; aucune à rajouter
    # (laissé comme point d'extension documenté).
    "RB5yWtPR1F86Bu5TIAoqFe5": [],
}

PROP_EXCLUDES_FAMILIES = "Rwqzfm396oP2bT07RfnCy8"


def find_class_block(owl: str, iri: str):
    m = re.search(
        rf'(<owl:Class rdf:about="http://webprotege\.stanford\.edu/{re.escape(iri)}">)(.*?)(</owl:Class>)',
        owl, re.DOTALL)
    return m


def existing_altlabels(body: str):
    return {html.unescape(s).strip().lower()
            for s in re.findall(r'<skos:altLabel[^>]*>([^<]+)', body)}


def existing_excludes_families(body: str):
    return set(re.findall(
        rf'{PROP_EXCLUDES_FAMILIES}"/>\s*<owl:someValuesFrom rdf:resource="http://webprotege\.stanford\.edu/([^"]+)"',
        body))


def add_altlabels(body: str, syns, report):
    have = existing_altlabels(body)
    new_lines = []
    for s in syns:
        if s.strip().lower() in have:
            report.append(f"    (déjà présent) altLabel « {s} »")
            continue
        esc = html.escape(s)
        new_lines.append(f"        <skos:altLabel>{esc}</skos:altLabel>")
        report.append(f"    + altLabel « {s} »")
    if not new_lines:
        return body
    # insère après la dernière balise rdfs:label ou au début du body
    insert_at = 0
    for m in re.finditer(r'</rdfs:label>', body):
        insert_at = m.end()
    if insert_at == 0:
        return body[:0] + "\n" + "\n".join(new_lines) + body
    return body[:insert_at] + "\n" + "\n".join(new_lines) + body[insert_at:]


def add_excludes_families(body: str, fam_iris, report):
    have = existing_excludes_families(body)
    blocks = []
    for fam in fam_iris:
        if fam in have:
            report.append(f"    (déjà présent) excludes_families -> {fam}")
            continue
        blocks.append(
            "        <rdfs:subClassOf>\n"
            "            <owl:Restriction>\n"
            f'                <owl:onProperty rdf:resource="http://webprotege.stanford.edu/{PROP_EXCLUDES_FAMILIES}"/>\n'
            f'                <owl:someValuesFrom rdf:resource="http://webprotege.stanford.edu/{fam}"/>\n'
            "            </owl:Restriction>\n"
            "        </rdfs:subClassOf>")
        report.append(f"    + excludes_families -> {fam}")
    if not blocks:
        return body
    # insère juste après la balise d'ouverture (début du body)
    return "\n" + "\n".join(blocks) + body


def main():
    owl = SRC.read_text(encoding="utf-8")
    report = []
    n_changes = 0

    # Fusionne toutes les cibles
    all_iris = set(SYNONYMS_TO_ADD) | set(EXCLUDES_FAMILIES_TO_ADD)
    for iri in all_iris:
        m = find_class_block(owl, iri)
        if not m:
            report.append(f"[!] IRI introuvable : {iri}")
            continue
        open_tag, body, close_tag = m.group(1), m.group(2), m.group(3)
        label = re.search(r'<rdfs:label[^>]*>([^<]+)', body)
        report.append(f"\n### {html.unescape(label.group(1)) if label else iri}  [{iri}]")
        new_body = body
        before = new_body
        if iri in SYNONYMS_TO_ADD:
            new_body = add_altlabels(new_body, SYNONYMS_TO_ADD[iri], report)
        if EXCLUDES_FAMILIES_TO_ADD.get(iri):
            new_body = add_excludes_families(new_body, EXCLUDES_FAMILIES_TO_ADD[iri], report)
        if new_body != before:
            n_changes += 1
        owl = owl[:m.start()] + open_tag + new_body + close_tag + owl[m.end():]

    OUT.write_text(owl, encoding="utf-8")
    print("=" * 70)
    print(f"OWL patché -> {OUT}")
    print(f"Concepts modifiés : {n_changes}")
    print("=" * 70)
    print("\n".join(report))

    # Sauvegarde du rapport
    Path("_patch_owl_report.txt").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
