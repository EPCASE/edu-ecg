import os
import sys
from pathlib import Path

print("🫀 EDU-CG - DIAGNOSTIC RAPIDE")
print("=" * 40)

# Répertoire de travail
current_dir = Path.cwd()
print(f"📁 Répertoire actuel: {current_dir}")

# Structure de base
backend_path = current_dir / "backend"
frontend_path = current_dir / "frontend"
admin_path = frontend_path / "admin"
data_path = current_dir / "data"

print(f"\n📂 Vérification des dossiers:")
print(f"Backend: {'✅' if backend_path.exists() else '❌'} {backend_path}")
print(f"Frontend: {'✅' if frontend_path.exists() else '❌'} {frontend_path}")
print(f"Admin: {'✅' if admin_path.exists() else '❌'} {admin_path}")
print(f"Data: {'✅' if data_path.exists() else '❌'} {data_path}")

# Fichiers clés
key_files = {
    "app.py": frontend_path / "app.py",
    "correction_engine.py": backend_path / "correction_engine.py",
    "import_cases.py": admin_path / "import_cases.py",
    "ecg_reader.py": admin_path / "ecg_reader.py",
    "annotation_tool.py": admin_path / "annotation_tool.py",
    "user_management.py": admin_path / "user_management.py",
    "ontologie.owx": data_path / "ontologie.owx"
}

print(f"\n📄 Vérification des fichiers clés:")
for name, path in key_files.items():
    status = "✅" if path.exists() else "❌"
    size = f"({path.stat().st_size} bytes)" if path.exists() else ""
    print(f"{name}: {status} {size}")

# Test des imports Python
print(f"\n🐍 Test des imports Python:")
try:
    import streamlit
    print("✅ streamlit")
except ImportError:
    print("❌ streamlit")

try:
    import owlready2
    print("✅ owlready2")
except ImportError:
    print("❌ owlready2")

try:
    from PIL import Image
    print("✅ PIL")
except ImportError:
    print("❌ PIL")

try:
    import pandas
    print("✅ pandas")
except ImportError:
    print("❌ pandas")

try:
    import matplotlib
    print("✅ matplotlib")
except ImportError:
    print("❌ matplotlib")

print(f"\n✅ Diagnostic terminé !")
