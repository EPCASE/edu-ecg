#!/usr/bin/env python3
"""
Script de correction rapide pour st.experimental_rerun -> st.rerun
"""

def fix_experimental_rerun():
    """Corrige les erreurs st.experimental_rerun dans les fichiers"""
    
    files_to_fix = [
        "frontend/admin/ecg_reader.py",
        "frontend/admin/import_cases.py"
    ]
    
    for file_path in files_to_fix:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacement simple
            corrected_content = content.replace('st.experimental_rerun()', 'st.rerun()')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(corrected_content)
            
            print(f"✅ {file_path} corrigé")
            
        except Exception as e:
            print(f"❌ Erreur dans {file_path}: {e}")

if __name__ == "__main__":
    print("🔧 Correction rapide st.experimental_rerun -> st.rerun")
    fix_experimental_rerun()
    print("✅ Correction terminée")
