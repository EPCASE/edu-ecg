# 👥 Guide Utilisateur : Authentification et Gestion des Sessions

## 🔐 **Système d'Authentification Actuel**

### **Mode de Fonctionnement**
Le système Edu-CG utilise actuellement un **commutateur de mode simple** :

**🎛️ Commutateur Admin/Étudiant :**
- ✅ **Bouton de basculement** en haut de l'interface
- 👨‍⚕️ **Mode Administrateur** : Accès complet (import, annotation, gestion)
- 🎓 **Mode Étudiant** : Consultation et exercices

### **📊 Profils Utilisateurs (WP4)**
Le système intègre une gestion avancée des utilisateurs via `👥 Utilisateurs` :

**Types de Profils :**
- 🎓 **Étudiant** : Consultation, exercices, progression
- 👨‍⚕️ **Résident** : Annotation supervisée
- 👨‍🏫 **Senior** : Création de cas, supervision
- 👑 **Admin** : Gestion complète du système

---

## 📤 **Envoi de Cas ECG par les Utilisateurs**

### **Workflow Actuel :**

#### **👨‍⚕️ Mode Administrateur/Expert :**
1. **Import ECG** : Import Intelligent → Recadrage → Export standardisé
2. **Annotation** : Liseuse ECG avec ontologie intégrée
3. **Publication** : Le cas devient disponible pour les étudiants

#### **🎓 Mode Étudiant :**
- **Consultation** des cas existants
- **Pas d'upload direct** (sécurité pédagogique)
- **Demandes via administrateur** pour nouveaux cas

### **💡 Amélioration Suggérée : Upload Étudiant**
Pour permettre aux étudiants d'envoyer des cas :

**Workflow Proposé :**
1. **Upload Étudiant** → Queue de validation admin
2. **Validation Admin** → Cas accepté/refusé avec feedback
3. **Publication** → Cas disponible pour tous

---

## 📝 **Création de Sessions ECG**

### **Sessions Actuelles :**
Les sessions sont créées automatiquement quand un étudiant :
- 🎯 **Commence un exercice**
- ✍️ **Annote un cas ECG**
- 📊 **Fait un quiz ontologique**

### **Structure d'une Session :**
```json
{
  "session_id": "session_2025_01_26_14h30",
  "user_id": "etudiant_123",
  "cas_ecg": "cas_001",
  "timestamp": "2025-01-26T14:30:00Z",
  "annotations_utilisateur": ["rythme sinusal", "PR normal"],
  "score_ontologique": 85,
  "feedback": "Bonne observation du rythme..."
}
```

### **Analytics de Session :**
- 📈 **Progression individuelle**
- 🎯 **Performance par cas**
- 🧠 **Évolution ontologique**
- 📊 **Comparaison avec experts**

---

## 🎮 **Interface Utilisateur Simplifiée**

### **🔑 Authentification Simplifiée**
**Actuellement :** Commutateur Admin/Étudiant sans login
**Avantage :** Accès immédiat, pas de gestion de mots de passe

### **🚀 Évolution vers Authentification Complète**
**Option A : Login Simple**
```
👤 Nom/Email → Sélection Profil → Accès Direct
```

**Option B : Authentification Sécurisée**
```
📧 Email + 🔒 Mot de passe → Profil Automatique
```

**Option C : Single Sign-On (SSO)**
```
🏥 Connexion Institution → Profil Synchronisé
```

---

## 📊 **Tableau de Bord Personnalisé**

### **👨‍⚕️ Vue Administrateur :**
- 📈 **Statistiques globales** : Nombre d'utilisateurs, cas, sessions
- 👥 **Gestion utilisateurs** : Création, modification, stats individuelles
- 📚 **Gestion contenu** : Validation cas étudiants, création exercices
- 🔧 **Configuration** : Paramètres système, sauvegardes

### **🎓 Vue Étudiant :**
- 📖 **Mes Cas** : Cas consultés, en cours, complétés
- 📊 **Ma Progression** : Score ontologique, évolution, badges
- 🎯 **Exercices** : Nouveaux défis, recommandations personnalisées
- 💬 **Feedback** : Commentaires experts, suggestions d'amélioration

---

## 🔄 **Workflow Collaboration**

### **Cycle de Vie d'un Cas :**

1. **📤 Soumission**
   - Étudiant/Expert uploade un ECG
   - Système : Import Intelligent automatique

2. **✅ Validation**
   - Expert/Admin révise et annote
   - Validation ontologique automatique

3. **📚 Publication**
   - Cas disponible pour tous les étudiants
   - Intégration dans les exercices

4. **📊 Analytics**
   - Suivi performance étudiants sur le cas
   - Feedback pour améliorer l'annotation experte

### **🎓 Exercices Guidés :**
- **Cas Progressifs** : Du simple au complexe
- **Parcours Thématiques** : Arythmies, infarctus, troubles conductifs
- **Défis Collaboratifs** : Cas difficiles en groupe
- **Évaluations** : Mode examen sécurisé

---

## 💡 **Recommandations d'Amélioration**

### **🚀 Priorité 1 : Authentification Utilisateur**
- Intégrer un système de login simple
- Profils persistants avec historique
- Session tracking automatique

### **📤 Priorité 2 : Upload Étudiant Supervisé**
- Interface upload sécurisée pour étudiants
- Queue de validation administrateur
- Feedback constructif sur les soumissions

### **🎯 Priorité 3 : Gamification**
- Système de points et badges
- Classements bienveillants
- Défis hebdomadaires

### **🌐 Priorité 4 : Collaboration Avancée**
- Annotations collaboratives en temps réel
- Discussions cas par cas
- Peer review entre étudiants

---

**🎯 Le système actuel est pleinement fonctionnel et prêt pour l'usage pédagogique !**
**🚀 Les améliorations proposées enrichiraient l'expérience collaborative.**
