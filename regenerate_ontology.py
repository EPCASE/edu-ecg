"""
Script de régénération de l'ontologie JSON depuis le fichier OWL mis à jour

Usage:
    python regenerate_ontology.py

Auteur: BMad Team
Date: 2026-01-11
"""

from pathlib import Path
from backend.rdf_owl_extractor import RDFOWLExtractor  # ✅ UTILISER rdf_owl_extractor (pas owl_to_json_converter!)

def main():
    # Chemins - Utilisation du fichier OWL externe
    owl_path = Path("BrYOzRZIu7jQTwmfcGsi35.owl")  # ✅ Fichier OWL à la racine du projet
    json_output = Path("data/ontology_from_owl.json")
    
    print("🔄 RÉGÉNÉRATION DE L'ONTOLOGIE")
    print("=" * 70)
    print(f"📥 Source OWL: {owl_path}")
    print(f"📤 Sortie JSON: {json_output}")
    print()
    
    # Vérifier que le fichier OWL existe
    if not Path(owl_path).exists():
        print(f"❌ ERREUR: Fichier OWL introuvable: {owl_path}")
        print("\n💡 Assurez-vous que le fichier existe à cet emplacement.")
        return
    
    # Backup de l'ancienne ontologie
    if json_output.exists():
        backup_path = json_output.with_suffix('.json.backup')
        import shutil
        shutil.copy(json_output, backup_path)
        print(f"📦 Backup créé: {backup_path}")
    
    # Conversion ✅ UTILISE RDFOWLExtractor
    try:
        extractor = RDFOWLExtractor(str(owl_path))
        extractor.load()
        extractor.extract_labels()
        extractor.extract_weight_classes()
        extractor.extract_weights()
        extractor.inherit_weights()
        extractor.extract_territoires()
        extractor.extract_concept_territoires()
        extractor.extract_requires_findings()
        extractor.extract_excludes()  # 🆕 Extraction des exclusions depuis annotation "exclut"
        extractor.extract_territory_metadata()  # 🆕 Extraction métadonnées territoire (STEMI, etc.)
        ontology_data = extractor.generate_json(str(json_output))
        
        print("\n" + "=" * 70)
        print("✅ RÉGÉNÉRATION TERMINÉE AVEC SUCCÈS!")
        print()
        print("📊 Statistiques:")
        print(f"   • Concepts: {ontology_data['metadata']['total_concepts']}")
        print(f"   • Territoires: {ontology_data['metadata']['total_territoires']}")
        
        # Compter catégories
        nb_urgent = len(ontology_data.get('concept_categories', {}).get('DIAGNOSTIC_URGENT', {}).get('concepts', []))
        nb_majeur = len(ontology_data.get('concept_categories', {}).get('DIAGNOSTIC_MAJEUR', {}).get('concepts', []))
        nb_signe = len(ontology_data.get('concept_categories', {}).get('SIGNE_ECG_PATHOLOGIQUE', {}).get('concepts', []))
        nb_desc = len(ontology_data.get('concept_categories', {}).get('DESCRIPTEUR_ECG', {}).get('concepts', []))
        
        print(f"   • Diagnostic URGENT: {nb_urgent}")
        print(f"   • Diagnostic MAJEUR: {nb_majeur}")
        print(f"   • Signe ECG: {nb_signe}")
        print(f"   • Descripteur ECG: {nb_desc}")
        print()
        print("🔍 Vérification des synonymes:")
        
        # Compter les concepts avec synonymes (dans concept_mappings, PAS dans concept_categories !)
        concepts_with_synonyms = 0
        total_synonyms = 0
        
        # ✅ CORRECT : Compter dans concept_mappings
        for concept_id, concept_data in ontology_data.get('concept_mappings', {}).items():
            # Format RDFOWLExtractor utilise "synonymes" (français)
            synonyms = concept_data.get('synonymes', [])
            if synonyms:
                concepts_with_synonyms += 1
                total_synonyms += len(synonyms)
        
        print(f"   • Concepts avec synonymes: {concepts_with_synonyms}")
        print(f"   • Total synonymes: {total_synonyms}")
        print()
        print("💡 L'ontologie a été mise à jour. Relancez votre application pour utiliser la nouvelle version.")
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la conversion:")
        print(f"   {type(e).__name__}: {e}")
        print("\n📋 Traceback:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
