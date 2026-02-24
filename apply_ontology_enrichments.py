"""
Script d'application des enrichissements manuels sur l'ontologie JSON.

Ce script lit `data/ontology_enrichments.json` et applique les corrections
(synonymes, implications) sur `data/ontology_from_owl.json`.

Il est conçu pour être appelé automatiquement après chaque régénération
de l'ontologie depuis WebProtégé OWL.

Usage autonome:
    python apply_ontology_enrichments.py

Usage programmatique:
    from apply_ontology_enrichments import apply_enrichments
    stats = apply_enrichments()

Auteur: BMad Team
Date: 2026-01-11
"""

import json
from pathlib import Path


def apply_enrichments(
    ontology_path: str = "data/ontology_from_owl.json",
    enrichments_path: str = "data/ontology_enrichments.json",
    dry_run: bool = False
) -> dict:
    """
    Applique les enrichissements manuels sur l'ontologie JSON.
    
    Args:
        ontology_path: Chemin vers le fichier ontologie JSON
        enrichments_path: Chemin vers le fichier d'enrichissements
        dry_run: Si True, affiche les changements sans modifier le fichier
    
    Returns:
        dict avec statistiques: {applied, skipped, errors, details}
    """
    ontology_path = Path(ontology_path)
    enrichments_path = Path(enrichments_path)
    
    # Charger l'ontologie
    if not ontology_path.exists():
        raise FileNotFoundError(f"Ontologie introuvable: {ontology_path}")
    
    with open(ontology_path, 'r', encoding='utf-8') as f:
        ontology = json.load(f)
    
    # Charger les enrichissements
    if not enrichments_path.exists():
        print(f"ℹ️  Pas de fichier d'enrichissements: {enrichments_path}")
        return {"applied": 0, "skipped": 0, "errors": 0, "details": []}
    
    with open(enrichments_path, 'r', encoding='utf-8') as f:
        enrichments_data = json.load(f)
    
    enrichments = enrichments_data.get("enrichments", [])
    if not enrichments:
        print("ℹ️  Aucun enrichissement à appliquer.")
        return {"applied": 0, "skipped": 0, "errors": 0, "details": []}
    
    concept_mappings = ontology.get("concept_mappings", {})
    
    stats = {"applied": 0, "skipped": 0, "errors": 0, "details": []}
    
    print(f"\n🔧 APPLICATION DES ENRICHISSEMENTS MANUELS")
    print(f"   Source: {enrichments_path}")
    print(f"   Cible:  {ontology_path}")
    print(f"   Enrichissements: {len(enrichments)}")
    print("=" * 60)
    
    for enrichment in enrichments:
        concept_id = enrichment.get("concept_id", "???")
        reason = enrichment.get("reason", "")
        
        print(f"\n📋 {concept_id}")
        if reason:
            print(f"   Raison: {reason[:80]}...")
        
        # Trouver le concept dans l'ontologie
        if concept_id not in concept_mappings:
            # Essayer avec des variantes d'encodage (accents, apostrophes)
            found = False
            for key in concept_mappings:
                if key.replace("'", "_").replace("'", "_") == concept_id.replace("'", "_").replace("'", "_"):
                    concept_id = key
                    found = True
                    break
            if not found:
                print(f"   ⚠️  CONCEPT NON TROUVÉ dans l'ontologie — IGNORÉ")
                stats["skipped"] += 1
                stats["details"].append({"concept_id": concept_id, "status": "not_found"})
                continue
        
        concept = concept_mappings[concept_id]
        changes_made = []
        
        # 1. add_synonymes
        if "add_synonymes" in enrichment:
            current = concept.get("synonymes", [])
            added = []
            for syn in enrichment["add_synonymes"]:
                if syn not in current:
                    current.append(syn)
                    added.append(syn)
            concept["synonymes"] = current
            if added:
                changes_made.append(f"+{len(added)} synonymes: {added}")
                print(f"   ✅ Ajouté {len(added)} synonymes: {added}")
            else:
                print(f"   ⏭️  Synonymes déjà présents")
        
        # 2. override_synonymes (remplace complètement)
        if "override_synonymes" in enrichment:
            old_count = len(concept.get("synonymes", []))
            concept["synonymes"] = enrichment["override_synonymes"]
            changes_made.append(f"synonymes remplacés ({old_count} → {len(enrichment['override_synonymes'])})")
            print(f"   ✅ Synonymes remplacés: {old_count} → {len(enrichment['override_synonymes'])}")
        
        # 3. remove_implications
        if "remove_implications" in enrichment:
            current = concept.get("implications", [])
            removed = []
            for impl in enrichment["remove_implications"]:
                if impl in current:
                    current.remove(impl)
                    removed.append(impl)
            concept["implications"] = current
            if removed:
                changes_made.append(f"-{len(removed)} implications: {removed}")
                print(f"   ✅ Retiré {len(removed)} implications: {removed}")
            else:
                print(f"   ⏭️  Implications à retirer non trouvées")
        
        # 4. add_implications
        if "add_implications" in enrichment:
            current = concept.get("implications", [])
            added = []
            for impl in enrichment["add_implications"]:
                if impl not in current:
                    current.append(impl)
                    added.append(impl)
            concept["implications"] = current
            if added:
                changes_made.append(f"+{len(added)} implications: {added}")
                print(f"   ✅ Ajouté {len(added)} implications: {added}")
            else:
                print(f"   ⏭️  Implications déjà présentes")
        
        # 5. override_implications (remplace complètement)
        if "override_implications" in enrichment:
            old_count = len(concept.get("implications", []))
            concept["implications"] = enrichment["override_implications"]
            changes_made.append(f"implications remplacées ({old_count} → {len(enrichment['override_implications'])})")
            print(f"   ✅ Implications remplacées: {old_count} → {len(enrichment['override_implications'])}")
        
        if changes_made:
            stats["applied"] += 1
            stats["details"].append({"concept_id": concept_id, "status": "applied", "changes": changes_made})
        else:
            stats["skipped"] += 1
            stats["details"].append({"concept_id": concept_id, "status": "no_changes"})
    
    # Sauvegarder si pas dry_run
    if not dry_run and stats["applied"] > 0:
        with open(ontology_path, 'w', encoding='utf-8') as f:
            json.dump(ontology, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Ontologie sauvegardée: {ontology_path}")
    elif dry_run:
        print(f"\n🔍 DRY RUN — aucune modification effectuée")
    
    print(f"\n📊 RÉSUMÉ: {stats['applied']} appliqués, {stats['skipped']} ignorés, {stats['errors']} erreurs")
    
    return stats


def validate_enrichments(
    ontology_path: str = "data/ontology_from_owl.json",
    enrichments_path: str = "data/ontology_enrichments.json"
) -> bool:
    """
    Vérifie que tous les enrichissements sont bien présents dans l'ontologie.
    Utile pour vérifier après régénération.
    
    Returns:
        True si tout est correct, False sinon
    """
    ontology_path = Path(ontology_path)
    enrichments_path = Path(enrichments_path)
    
    with open(ontology_path, 'r', encoding='utf-8') as f:
        ontology = json.load(f)
    with open(enrichments_path, 'r', encoding='utf-8') as f:
        enrichments_data = json.load(f)
    
    concept_mappings = ontology.get("concept_mappings", {})
    all_ok = True
    
    print(f"\n🔍 VALIDATION DES ENRICHISSEMENTS")
    print("=" * 60)
    
    for enrichment in enrichments_data.get("enrichments", []):
        concept_id = enrichment["concept_id"]
        
        if concept_id not in concept_mappings:
            print(f"❌ {concept_id}: CONCEPT MANQUANT")
            all_ok = False
            continue
        
        concept = concept_mappings[concept_id]
        
        # Vérifier synonymes ajoutés
        for syn in enrichment.get("add_synonymes", []) + enrichment.get("override_synonymes", []):
            if syn not in concept.get("synonymes", []):
                print(f"❌ {concept_id}: synonyme manquant '{syn}'")
                all_ok = False
        
        # Vérifier implications ajoutées
        for impl in enrichment.get("add_implications", []) + enrichment.get("override_implications", []):
            if impl not in concept.get("implications", []):
                print(f"❌ {concept_id}: implication manquante '{impl}'")
                all_ok = False
        
        # Vérifier implications retirées
        for impl in enrichment.get("remove_implications", []):
            if impl in concept.get("implications", []):
                print(f"❌ {concept_id}: implication '{impl}' devrait être retirée")
                all_ok = False
        
        if all_ok:
            print(f"✅ {concept_id}: OK")
    
    print()
    if all_ok:
        print("🎉 TOUS LES ENRICHISSEMENTS SONT CORRECTEMENT APPLIQUÉS")
    else:
        print("⚠️  CERTAINS ENRICHISSEMENTS SONT MANQUANTS — relancez apply_ontology_enrichments.py")
    
    return all_ok


if __name__ == "__main__":
    import sys
    
    if "--validate" in sys.argv:
        ok = validate_enrichments()
        sys.exit(0 if ok else 1)
    elif "--dry-run" in sys.argv:
        apply_enrichments(dry_run=True)
    else:
        apply_enrichments()
