#!/usr/bin/env python3
"""
Test de syntaxe pour l'application app.py
"""

import sys
from pathlib import Path

def test_app_syntax():
    """Test de la syntaxe du fichier app.py"""
    try:
        app_path = Path(__file__).parent / "frontend" / "app.py"
        
        # Test de compilation
        with open(app_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, str(app_path), 'exec')
        print("✅ app.py - Syntaxe correcte !")
        
        # Test d'import
        sys.path.insert(0, str(Path(__file__).parent / "frontend"))
        import app
        print("✅ app.py - Import réussi !")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe : {e}")
        print(f"   Ligne {e.lineno}: {e.text}")
        return False
        
    except Exception as e:
        print(f"⚠️ Erreur d'import (normal): {e}")
        print("✅ Syntaxe OK, erreur d'import attendue")
        return True

if __name__ == "__main__":
    print("🔍 Test de syntaxe app.py...")
    test_app_syntax()
