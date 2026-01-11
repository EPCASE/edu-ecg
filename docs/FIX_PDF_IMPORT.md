# 🔧 Guide de Réparation Import PDF

## 🎯 Solution Rapide (5 minutes)

Vous avez un problème d'import PDF ? Voici la **solution en 3 étapes** :

---

## ✅ Étape 1: Installer PyMuPDF (Recommandé)

```powershell
# Dans le terminal PowerShell
pip install PyMuPDF
```

**Pourquoi PyMuPDF ?**
- ✅ Le plus rapide (×10 plus rapide que pdf2image)
- ✅ Extraction images + texte
- ✅ Pas de dépendances externes (pas besoin de Poppler)
- ✅ Haute qualité (300 DPI par défaut)

---

## ✅ Étape 2: Tester l'Import Réparé

```powershell
# Lancer le module de test PDF
streamlit run frontend/pdf_import_fix.py
```

Cela ouvrira une **interface de diagnostic** qui vous montrera :
- ✅ Quelles bibliothèques PDF sont installées
- ✅ Quelle méthode sera utilisée
- ✅ Un bouton de test d'import

---

## ✅ Étape 3: Intégrer dans l'App Principale

Une fois PyMuPDF installé, l'import PDF fonctionnera automatiquement dans votre application principale.

**Test rapide :**
1. Redémarrer Streamlit : `Ctrl+C` puis `streamlit run frontend/app.py`
2. Se connecter avec `admin` / `admin123`
3. Aller dans "Import ECG"
4. Uploader un PDF

---

## 🔍 Diagnostic Avancé

### Vérifier les bibliothèques installées

```powershell
# Vérifier PyMuPDF
python -c "import fitz; print('PyMuPDF OK:', fitz.__version__)"

# Vérifier PyPDF2 (déjà dans requirements)
python -c "import PyPDF2; print('PyPDF2 OK')"

# Vérifier pdf2image (optionnel)
python -c "from pdf2image import convert_from_bytes; print('pdf2image OK')"
```

### Si PyMuPDF ne s'installe pas

**Option Alternative 1: pdf2image** (nécessite Poppler)
```powershell
# Installer pdf2image
pip install pdf2image

# Télécharger Poppler pour Windows:
# https://github.com/oschwartz10612/poppler-windows/releases/
# Extraire dans C:\Program Files\poppler
# Ajouter C:\Program Files\poppler\Library\bin au PATH
```

**Option Alternative 2: Utiliser PDF.js** (déjà intégré)
- Pas d'installation nécessaire
- Affiche le PDF dans le navigateur
- Vous devez faire clic-droit > Enregistrer l'image manuellement

---

## 📊 Comparaison des Méthodes

| Méthode | Installation | Vitesse | Qualité | Images | Texte |
|---------|-------------|---------|---------|--------|-------|
| **PyMuPDF** | `pip install` | ⚡⚡⚡ | ✅ Excellente | ✅ Oui | ✅ Oui |
| **pdf2image** | `pip install` + Poppler | ⚡⚡ | ✅ Bonne | ✅ Oui | ❌ Non |
| **PyPDF2** | Déjà installé | ⚡⚡⚡ | ⚠️ Limitée | ❌ Non | ✅ Oui |
| **PDF.js** | Déjà intégré | ⚡ | ✅ Bonne | ⚠️ Manuel | ❌ Non |

**Recommandation:** Utilisez **PyMuPDF** pour la meilleure expérience.

---

## 🐛 Problèmes Connus et Solutions

### Erreur: "fitz module not found"

**Solution:**
```powershell
pip uninstall PyMuPDF
pip install PyMuPDF --upgrade
```

### Erreur: "PDF extraction failed"

**Solution:** Le module de fallback automatique essaiera d'autres méthodes.

Lancez le diagnostic:
```powershell
streamlit run frontend/pdf_import_fix.py
```

### Le PDF s'affiche mais aucune image n'est extraite

**Cause:** Peut-être que le PDF contient des ECG en format vectoriel (SVG) plutôt qu'image.

**Solution:** 
1. PyMuPDF convertit automatiquement les pages en images (300 DPI)
2. Utilisez l'option "Convertir page entière" dans l'interface

---

## ✨ Améliorations Apportées

Le nouveau module `pdf_import_fix.py` apporte :

1. ✅ **Fallback automatique** - 4 méthodes testées dans l'ordre
2. ✅ **Diagnostic intégré** - Voir quelles bibliothèques sont disponibles
3. ✅ **Messages d'erreur clairs** - Savoir exactement ce qui manque
4. ✅ **Recommandations d'installation** - Commandes pip prêtes à copier
5. ✅ **Haute résolution** - 300 DPI pour ECG lisibles
6. ✅ **Prévisualisation immédiate** - Voir le résultat avant sauvegarde

---

## 🚀 Utilisation dans le Code

```python
from pdf_import_fix import PDFImporter

# Créer l'importer
importer = PDFImporter()

# Importer un fichier
result = importer.import_pdf(uploaded_file)

if result['success']:
    print(f"Méthode utilisée: {result['method']}")
    print(f"Nombre d'images: {len(result['images'])}")
    
    for img_data in result['images']:
        # Afficher ou sauvegarder l'image
        img_data['image'].save(f"ecg_page_{img_data['page']}.png")
```

---

## 📞 Support

Si le problème persiste après avoir installé PyMuPDF :

1. **Vérifier la version Python:**
   ```powershell
   python --version
   # Devrait être Python 3.11+
   ```

2. **Réinstaller dans l'environnement virtuel:**
   ```powershell
   # Si vous utilisez un venv
   .\.venv\Scripts\activate
   pip install PyMuPDF
   ```

3. **Tester avec un PDF simple:**
   - Utilisez `frontend/pdf_import_fix.py` pour tester
   - Commencez par un PDF simple (1 page)
   - Vérifiez les logs dans le terminal

---

**Durée de réparation:** 5 minutes  
**Commande clé:** `pip install PyMuPDF`  
**Test:** `streamlit run frontend/pdf_import_fix.py`
