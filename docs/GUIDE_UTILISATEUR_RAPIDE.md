# 🎯 Guide Utilisateur Rapide - Edu-CG

## 🚀 **Démarrage en 3 minutes**

### **Étape 1 : Lancement** ⚡
```bash
# Méthode simple
python launch_light.py

# Si erreurs Windows
python launch_safe.py
```
➡️ **Ouvre automatiquement http://localhost:8501**

### **Étape 2 : Choisir votre profil** 👤
- **👨‍⚕️ Administrateur/Expert** : Import, annotation, gestion
- **🎓 Étudiant** : Consultation, exercices, apprentissage

---

## 👨‍⚕️ **Mode Administrateur/Expert**

### **🎯 Import Intelligent** - Ajouter des ECG
1. **📤 Upload** : Glissez votre fichier (PDF, PNG, JPG)
2. **📄 Sélection page** : Choisissez la page (si PDF multi-pages)
3. **✂️ Recadrage** : Ajustez la zone d'intérêt avec les curseurs
4. **💾 Export** : Ajoutez métadonnées et sauvegardez

### **📺 Liseuse ECG** - Annoter intelligemment
1. **📂 Sélection cas** : Choisissez un ECG importé
2. **✍️ Annotation smart** : 
   - **Experts** : Tags cliquables avec ontologie
   - **Mode unifié** : Un seul champ, suggestions intelligentes
3. **💾 Sauvegarde** : Annotation unique par cas (pas d'accumulation)

### **📊 Gestion BDD** - Administrer vos cas
- **✏️ Renommer** : Modifier le nom des cas
- **📝 Annoter** : Redirection vers liseuse
- **🔍 Détails** : Métadonnées complètes
- **🗑️ Supprimer** : Suppression sécurisée avec confirmation

---

## 🎓 **Mode Étudiant**

### **📚 Cas ECG** - Explorer et apprendre
1. **📋 Parcourir** : Liste des cas disponibles avec aperçu
2. **🔍 Sélectionner** : Cas avec/sans annotation experte
3. **🎯 S'exercer** : Bouton direct vers les exercices

### **🎯 Exercices** - Pratiquer avec IA
1. **📝 Interface smart** : Autocomplétion avec ontologie ECG
2. **💡 Suggestions** : Menu déroulant qui s'affine en temps réel
3. **🎯 Évaluation** : Comparaison intelligente avec annotation experte
4. **📊 Scoring** : Feedback nuancé basé sur 281 concepts ECG

---

## 🔧 **Résolution de problèmes**

### **❌ Erreur watchdog Windows**
```bash
# Solution immédiate
python launch_safe.py
```

### **🌐 Port occupé**
```bash
# L'app trouve automatiquement un port libre
# Ou forcez l'arrêt
./stop_app.bat
```

### **📄 PDF ne s'affiche pas**
- ✅ **Normal** : Conversion automatique tentée
- 🎯 **Solution** : Interface de capture d'écran fournie
- 📱 **Tip** : Windows+Shift+S pour capturer

### **🧠 Ontologie non chargée**
- ✅ **Vérifiez** : Fichier `data/ontologie.owx` présent
- 🔄 **Rechargez** : Bouton dans les paramètres

---

## 💡 **Conseils d'utilisation**

### **📤 Import optimal**
- **PDFs** : Privilégiez les fichiers < 2MB pour affichage direct
- **Images** : PNG/JPG haute résolution recommandés
- **Recadrage** : Ajustez finement pour capturer uniquement l'ECG

### **📝 Annotation efficace**
- **Experts** : Utilisez les tags cliquables pour rapidité
- **Étudiants** : Tapez les premières lettres, l'autocomplétion fait le reste
- **Progression** : Une annotation par cas, pas d'accumulation

### **🎯 Pédagogie**
- **Ordre** : Expert annote → Étudiant s'exerce → Comparaison automatique
- **Feedback** : Scoring nuancé (pas tout/rien)
- **Progression** : Interface de suivi intégrée

---

## 📞 **Support rapide**

### **🆘 Problème urgent**
1. **Ctrl+C** dans le terminal
2. **./stop_app.bat** en cas de blocage
3. **Relancer** avec `python launch_safe.py`

### **🐛 Bug ou suggestion**
- **GitHub Issues** : [À définir selon hébergement]
- **Email** : [À définir selon institution]

---

## 🎉 **Prêt à commencer !**

**🚀 L'interface est intuitive - explorez et découvrez !**

*Ce guide couvre 80% des cas d'usage. Pour plus de détails, consultez le README.md complet.*
