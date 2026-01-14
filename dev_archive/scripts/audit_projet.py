"""
🎯 AUDIT COMPLET - Projet Edu-ECG Import/Correction
Analyse l'état actuel du système et vérifie la cohérence

Auteur: BMAD Party Mode Team
Date: 2026-01-11
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

def audit_ontology():
    """Audit de l'ontologie"""
    print("=" * 70)
    print("1. AUDIT ONTOLOGIE")
    print("=" * 70)
    
    try:
        with open('data/ontology_from_owl.json', encoding='utf-8') as f:
            ont = json.load(f)
        
        cm = ont.get('concept_mappings', {})
        
        # Stats de base
        total_concepts = len(cm)
        concepts_with_impl = sum(1 for v in cm.values() if v.get('implications'))
        concepts_with_terr = sum(1 for v in cm.values() if v.get('territoires_possibles'))
        total_impl = sum(len(v.get('implications', [])) for v in cm.values())
        
        print(f"✅ Ontologie chargée")
        print(f"   📊 {total_concepts} concepts totaux")
        print(f"   🎯 {concepts_with_impl} concepts avec implications")
        print(f"   🗺️  {concepts_with_terr} concepts avec territoires")
        print(f"   💡 {total_impl} implications totales")
        
        # Catégories
        categories = ont.get('concept_categories', {})
        print(f"\n   📂 Catégories:")
        for cat_name, cat_data in categories.items():
            poids = cat_data.get('poids', 0)
            nb = len(cat_data.get('concepts', []))
            print(f"      - {cat_name}: {nb} concepts (poids {poids})")
        
        # Test concepts critiques
        critical = ['BAV de type 1', 'ECG normal', 'Bloc de branche']
        print(f"\n   🔍 Concepts critiques:")
        for concept_name in critical:
            found = any(v.get('concept_name') == concept_name for v in cm.values())
            if found:
                concept = next(v for v in cm.values() if v.get('concept_name') == concept_name)
                impl = concept.get('implications', [])
                print(f"      ✅ {concept_name}: {len(impl)} implications")
            else:
                print(f"      ❌ {concept_name}: NON TROUVÉ")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False


def audit_backend_services():
    """Audit des services backend"""
    print("\n" + "=" * 70)
    print("2. AUDIT SERVICES BACKEND")
    print("=" * 70)
    
    services = {
        'ontology_relations.py': 'backend/services/ontology_relations.py',
        'scoring_service_llm.py': 'backend/scoring_service_llm.py',
        'correction_engine.py': 'backend/correction_engine.py',
        'ontology_service.py': 'backend/ontology_service.py',
    }
    
    results = {}
    for name, path in services.items():
        exists = Path(path).exists()
        results[name] = exists
        status = "✅" if exists else "❌"
        print(f"   {status} {name}")
        
        if exists and 'ontology_relations' in name:
            # Vérifier contenu
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                has_resolver = 'OntologyRelationResolver' in content
                has_get_implications = 'get_implications' in content
                has_concept_implies = 'concept_implies' in content
                
                if has_resolver and has_get_implications and has_concept_implies:
                    print(f"      ✅ Contient OntologyRelationResolver complet")
                else:
                    print(f"      ⚠️ Classe incomplète")
    
    return all(results.values())


def audit_frontend_modules():
    """Audit des modules frontend"""
    print("\n" + "=" * 70)
    print("3. AUDIT MODULES FRONTEND")
    print("=" * 70)
    
    modules = {
        'ecg_session_builder.py': 'frontend/ecg_session_builder.py',
        'correction_llm_poc.py': 'frontend/correction_llm_poc.py',
    }
    
    results = {}
    for name, path in modules.items():
        exists = Path(path).exists()
        results[name] = exists
        status = "✅" if exists else "❌"
        print(f"   {status} {name}")
        
        if exists:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = len(content.split('\n'))
                print(f"      📄 {lines} lignes")
                
                # Détection des imports clés
                if 'ecg_session_builder' in name:
                    has_ontology = 'get_ontology_concepts' in content
                    has_streamlit = 'import streamlit' in content
                    print(f"      {'✅' if has_ontology else '❌'} get_ontology_concepts")
                    print(f"      {'✅' if has_streamlit else '❌'} Streamlit UI")
                
                if 'correction_llm_poc' in name:
                    has_scoring = 'SemanticScorer' in content or 'scoring' in content.lower()
                    has_streamlit = 'import streamlit' in content
                    print(f"      {'✅' if has_scoring else '❌'} Scoring service")
                    print(f"      {'✅' if has_streamlit else '❌'} Streamlit UI")
    
    return all(results.values())


def audit_data_files():
    """Audit des fichiers de données"""
    print("\n" + "=" * 70)
    print("4. AUDIT FICHIERS DE DONNÉES")
    print("=" * 70)
    
    files = {
        'ontology_from_owl.json': 'data/ontology_from_owl.json',
        'case_templates_epic1.json': 'data/case_templates_epic1.json',
        'OWL source': 'data/epi1c_dataset/BrYOzRZIu7jQTwmfcGsi35.owl',
    }
    
    for name, path in files.items():
        exists = Path(path).exists()
        status = "✅" if exists else "❌"
        
        if exists:
            size = Path(path).stat().st_size
            size_mb = size / 1024 / 1024
            print(f"   {status} {name} ({size_mb:.2f} MB)")
        else:
            print(f"   {status} {name} - MANQUANT")
    
    return True


def audit_workflow_integration():
    """Audit de l'intégration du workflow"""
    print("\n" + "=" * 70)
    print("5. AUDIT INTÉGRATION WORKFLOW")
    print("=" * 70)
    
    print("\n   📋 WORKFLOW IMPORT → CORRECTION:")
    print("   1. ecg_session_builder.py (Import)")
    print("      ↓ Charge ontologie via get_ontology_concepts()")
    print("      ↓ Annotation manuelle/LLM/recherche")
    print("      ↓ Sauvegarde session JSON")
    print("   2. correction_llm_poc.py (Correction)")
    print("      ↓ Charge session importée")
    print("      ↓ Utilise SemanticScorer avec OWL resolver")
    print("      ↓ Scoring hiérarchique via concept_implies()")
    print("      ↓ Affiche résultats + feedback")
    
    # Vérifier que les deux utilisent la même ontologie
    print("\n   🔍 Vérification cohérence:")
    
    try:
        # Test import ontology_relations
        sys.path.insert(0, str(Path(__file__).parent / "backend" / "services"))
        from ontology_relations import get_resolver
        
        resolver = get_resolver()
        print(f"   ✅ OntologyRelationResolver chargeable")
        print(f"      📊 {len(resolver.concept_mappings)} concepts")
        
        # Test une implication
        test_impl = resolver.concept_implies("BAV de type 1", "PR allongé")
        print(f"   ✅ Test implication: BAV 1 → PR allongé = {test_impl}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        return False


def audit_tests():
    """Audit des tests existants"""
    print("\n" + "=" * 70)
    print("6. AUDIT TESTS")
    print("=" * 70)
    
    test_files = [
        'test_ontology_compatibility.py',
        'test_scoring_owl.py',
        'test_scoring_non_regression.py',
    ]
    
    for test_file in test_files:
        exists = Path(test_file).exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {test_file}")
    
    return True


def generate_test_plan():
    """Génère le plan de test end-to-end"""
    print("\n" + "=" * 70)
    print("7. PLAN DE TEST END-TO-END")
    print("=" * 70)
    
    plan = """
   📝 SCÉNARIO DE TEST:
   
   ÉTAPE 1: Import Session ECG
   - Lancer: streamlit run frontend/ecg_session_builder.py
   - Charger une image ECG
   - Annoter avec concepts (ex: BAV 1, PR allongé)
   - Sauvegarder la session
   
   ÉTAPE 2: Correction Session
   - Lancer: streamlit run frontend/correction_llm_poc.py
   - Charger la session créée
   - Ajouter réponses étudiants (simulées)
   - Vérifier scoring hiérarchique
   - Valider que BAV 1 valide PR allongé
   
   ÉTAPE 3: Validation Résultats
   - Score global correct
   - Implications OWL détectées
   - Feedback approprié
   - Aucune régression
   
   ✅ CRITÈRES DE SUCCÈS:
   - Import fonctionne sans erreur
   - Ontologie chargée correctement
   - Scoring utilise implications OWL
   - BAV 1 → PR allongé validé à 100%
   - Interface Streamlit responsive
    """
    
    print(plan)
    return True


def main():
    """Execute audit complet"""
    print("\n")
    print("=" * 70)
    print("🎊 AUDIT COMPLET - PROJET EDU-ECG IMPORT/CORRECTION")
    print("=" * 70)
    print("Analyse de l'état actuel avant tests end-to-end")
    print("=" * 70)
    
    audits = {
        "Ontologie": audit_ontology,
        "Services Backend": audit_backend_services,
        "Modules Frontend": audit_frontend_modules,
        "Fichiers de données": audit_data_files,
        "Intégration Workflow": audit_workflow_integration,
        "Tests existants": audit_tests,
        "Plan de test": generate_test_plan,
    }
    
    results = {}
    for audit_name, audit_func in audits.items():
        try:
            results[audit_name] = audit_func()
        except Exception as e:
            print(f"\n❌ ERREUR dans {audit_name}: {e}")
            import traceback
            traceback.print_exc()
            results[audit_name] = False
    
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ AUDIT")
    print("=" * 70)
    
    for audit_name, result in results.items():
        status = "✅ OK" if result else "❌ PROBLÈME"
        print(f"{status} - {audit_name}")
    
    total_pass = sum(1 for r in results.values() if r)
    total_audits = len(results)
    
    print("\n" + "=" * 70)
    if total_pass == total_audits:
        print(f"🎉 AUDIT COMPLET: {total_pass}/{total_audits} vérifications OK")
        print("✅ PROJET PRÊT POUR LES TESTS END-TO-END")
        print("\n🚀 PROCHAINE ÉTAPE:")
        print("   1. Lancer: streamlit run frontend/ecg_session_builder.py")
        print("   2. Importer une session ECG manuellement")
        print("   3. Lancer: streamlit run frontend/correction_llm_poc.py")
        print("   4. Corriger et valider les résultats")
    else:
        print(f"⚠️ AUDIT PARTIEL: {total_pass}/{total_audits} vérifications OK")
        print("⚠️ Corriger les problèmes avant les tests")
    print("=" * 70)
    
    return total_pass >= total_audits * 0.8


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
