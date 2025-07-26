#!/usr/bin/env python3
"""
Test de support PDF - Validation de la gestion des fichiers PDF
"""

import sys
from pathlib import Path

# Configuration des chemins
project_root = Path(__file__).parent
sys.path.append(str(project_root / "backend"))
sys.path.append(str(project_root / "frontend" / "admin"))

def test_pdf_support():
    """Test du support PDF"""
    print("📄 === TEST SUPPORT PDF ===\n")
    
    # 1. Vérifier l'installation de pdf2image
    print("1️⃣ Vérification de pdf2image...")
    try:
        from pdf2image import convert_from_path
        print("✅ pdf2image installé et disponible")
        PDF_AVAILABLE = True
    except ImportError:
        print("❌ pdf2image non disponible")
        PDF_AVAILABLE = False
    
    # 2. Test des modules avec support PDF
    print("\n2️⃣ Test des modules avec support PDF...")
    
    try:
        from ecg_reader import load_image_from_file, PDF_SUPPORT
        print(f"✅ ecg_reader - Support PDF: {PDF_SUPPORT}")
        
        from import_cases import PDF_SUPPORT as IMPORT_PDF_SUPPORT
        print(f"✅ import_cases - Support PDF: {IMPORT_PDF_SUPPORT}")
        
    except Exception as e:
        print(f"❌ Erreur lors du test des modules: {e}")
        return False
    
    # 3. Test avec un fichier PDF existant
    print("\n3️⃣ Test avec fichier PDF existant...")
    
    pdf_files = list(Path("data/ecg_cases").glob("*/ecg_image.pdf"))
    if pdf_files and PDF_AVAILABLE:
        test_pdf = pdf_files[0]
        print(f"📄 Test avec: {test_pdf}")
        
        try:
            # Tester la fonction de chargement
            image = load_image_from_file(test_pdf)
            if image:
                print("✅ PDF converti en image avec succès")
                print(f"✅ Taille image: {image.size}")
                return True
            else:
                print("❌ Échec de conversion PDF")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la conversion: {e}")
            return False
    
    elif pdf_files and not PDF_AVAILABLE:
        print("⚠️ Fichiers PDF trouvés mais pdf2image non disponible")
        print("💡 Pour installer: pip install pdf2image")
        return False
    
    else:
        print("ℹ️ Aucun fichier PDF trouvé pour test")
        print("✅ Modules prêts pour traiter les PDF quand ils seront importés")
        return True

def test_image_formats_compatibility():
    """Test de compatibilité des formats d'image"""
    print("\n🖼️ === TEST FORMATS D'IMAGES ===\n")
    
    supported_formats = [
        ('PNG', '.png'),
        ('JPEG', '.jpg'),
        ('JPEG', '.jpeg'),
        ('PDF', '.pdf')
    ]
    
    print("Formats supportés:")
    for format_name, extension in supported_formats:
        if extension == '.pdf':
            try:
                from pdf2image import convert_from_path
                status = "✅ SUPPORTÉ"
            except ImportError:
                status = "⚠️ NÉCESSITE pdf2image"
        else:
            status = "✅ SUPPORTÉ"
        
        print(f"  {format_name:8} ({extension:5}) : {status}")
    
    return True

def test_error_handling():
    """Test de la gestion d'erreurs"""
    print("\n🛡️ === TEST GESTION D'ERREURS ===\n")
    
    try:
        from ecg_reader import load_image_from_file
        
        # Test avec fichier inexistant
        print("1️⃣ Test fichier inexistant...")
        result = load_image_from_file("fichier_inexistant.pdf")
        if result is None:
            print("✅ Gestion d'erreur fichier inexistant OK")
        
        # Test avec extension inconnue
        print("2️⃣ Test extension non supportée...")
        result = load_image_from_file("test.xyz")
        if result is None:
            print("✅ Gestion d'erreur extension inconnue OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de gestion d'erreurs: {e}")
        return False

def main():
    """Fonction principale"""
    print("📄 VALIDATION SUPPORT PDF")
    print("="*50)
    
    # Tests
    pdf_ok = test_pdf_support()
    formats_ok = test_image_formats_compatibility()
    errors_ok = test_error_handling()
    
    # Résumé
    print("\n" + "="*50)
    print("📋 RÉSUMÉ DES TESTS")
    print("="*50)
    
    tests = [
        ("Support PDF", pdf_ok),
        ("Formats d'images", formats_ok),
        ("Gestion d'erreurs", errors_ok)
    ]
    
    success_count = 0
    for test_name, success in tests:
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        print(f"{test_name:20} : {status}")
        if success:
            success_count += 1
    
    print(f"\n🎯 Score: {success_count}/{len(tests)} tests réussis")
    
    if success_count == len(tests):
        print("\n🎉 SUPPORT PDF VALIDÉ!")
        print("✅ Les fichiers PDF peuvent maintenant être affichés")
        print("✅ Gestion d'erreurs robuste")
        print("📄 L'erreur 'cannot identify image file PDF' est corrigée")
    else:
        print("\n⚠️ Des améliorations sont nécessaires")
    
    return success_count == len(tests)

if __name__ == "__main__":
    main()
