# 🔐 Guide Complet : Système d'Authentification Edu-CG

## 🎯 **Vue d'Ensemble**

Le nouveau système d'authentification Edu-CG propose **3 types d'utilisateurs** avec des permissions différenciées pour un contrôle d'accès granulaire.

---

## 👥 **Types d'Utilisateurs et Permissions**

### 🎓 **Étudiant**
**Accès limité à l'apprentissage :**
- ✅ **Cas ECG** : Consultation et annotation des cas disponibles
- ✅ **Mes Sessions** : Historique personnel des sessions d'apprentissage
- ✅ **Mes Statistiques** : Suivi de progression personnelle
- ❌ Pas d'import ECG
- ❌ Pas de création de cas
- ❌ Pas d'accès administration

### 👨‍⚕️ **Expert** 
**Accès création et supervision :**
- ✅ **Import ECG** : Ajout de nouveaux cas via Import Intelligent
- ✅ **Liseuse ECG** : Annotation experte avec ontologie complète
- ✅ **Cas ECG** : Gestion de ses propres cas créés
- ✅ **Sessions** : Création et gestion de sessions d'apprentissage
- ✅ **Mes Statistiques** : Analytics personnels et étudiants supervisés
- ❌ Pas d'accès administration globale

### 👑 **Administrateur**
**Accès complet au système :**
- ✅ **Toutes les fonctionnalités Expert**
- ✅ **Base de Données** : Gestion complète (6 onglets)
- ✅ **Utilisateurs** : Création, modification, suppression comptes
- ✅ **Analytics** : Vue globale système et utilisateurs
- ✅ **Configuration** : Paramètres système avancés

---

## 🚀 **Mise en Route**

### **1. Lancement avec Authentification**
```bash
# Nouveau mode sécurisé
python launch_auth.py
# ou sous Windows
launch_auth.bat

# Application disponible : http://localhost:8501
```

### **2. Comptes de Démonstration**
Le système est livré avec 3 comptes de test :

```
🎓 Étudiant Demo
   Login : etudiant_demo
   Password : etudiant123
   
👨‍⚕️ Expert Demo  
   Login : expert_demo
   Password : expert123
   
👑 Admin
   Login : admin
   Password : admin123
```

### **3. Première Connexion**
1. **Accéder** à http://localhost:8501
2. **Choisir** un compte de démonstration
3. **Se connecter** avec les identifiants
4. **Explorer** les fonctionnalités selon votre rôle

---

## 🔧 **Gestion des Utilisateurs (Admin)**

### **Créer un Nouvel Utilisateur**
1. **Se connecter** en tant qu'Admin
2. **Aller** dans "👥 Utilisateurs"
3. **Onglet** "➕ Créer Utilisateur"
4. **Remplir** le formulaire :
   - Nom d'utilisateur (unique)
   - Nom complet
   - Email
   - Mot de passe (min. 6 caractères)
   - Rôle (étudiant/expert/admin)

### **Gérer les Utilisateurs Existants**
- **Voir** la liste complète dans l'onglet "👤 Liste des Utilisateurs"
- **Réinitialiser** les mots de passe
- **Voir** les dernières connexions
- **Filtrer** par rôle et statut

---

## 🎮 **Expérience Utilisateur par Rôle**

### 🎓 **Workflow Étudiant**
```
1. Connexion → Page d'accueil personnalisée
2. Cas ECG → Sélection et annotation
3. Sessions → Révision de son historique  
4. Statistiques → Suivi de progression
```

**Interface simplifiée :**
- Navigation claire limitée à l'essentiel
- Pas de boutons d'administration
- Focus sur l'apprentissage

### 👨‍⚕️ **Workflow Expert**
```
1. Connexion → Dashboard avec ses statistiques
2. Import ECG → Ajout de nouveaux cas
3. Liseuse ECG → Annotation experte
4. Sessions → Création d'exercices
5. Statistiques → Suivi étudiants
```

**Outils avancés :**
- Import Intelligent complet
- Annotation avec ontologie experte
- Création de contenus pédagogiques

### 👑 **Workflow Administrateur**
```
1. Connexion → Dashboard système global
2. Utilisateurs → Gestion des comptes
3. Base de Données → Administration complète
4. Analytics → Vue d'ensemble système
5. Configuration → Paramètres avancés
```

**Contrôle total :**
- Gestion utilisateurs
- Monitoring système
- Configuration avancée

---

## 🔒 **Sécurité et Conformité**

### **Hachage des Mots de Passe**
- Algorithme SHA-256
- Pas de stockage en clair
- Salage automatique

### **Sessions Sécurisées**
- Tokens de session Streamlit
- Déconnexion automatique
- Isolation des données utilisateur

### **Permissions Granulaires**
- Vérification à chaque action
- Décorateurs de protection
- Messages d'erreur explicites

### **Audit et Traçabilité**
- Logs de connexion
- Historique des actions
- Suivi des créations/modifications

---

## 📊 **Base de Données Utilisateurs**

### **Structure du Fichier `users/users_auth.json`**
```json
{
  "username": {
    "password_hash": "sha256_hash",
    "role": "etudiant|expert|admin",
    "name": "Nom Complet",
    "email": "email@domain.com",
    "created_date": "2025-01-26T10:30:00",
    "last_login": "2025-01-26T14:45:00",
    "active": true,
    "created_by": "admin_username"
  }
}
```

### **Sauvegarde Automatique**
- Backup automatique à chaque modification
- Format JSON lisible
- Intégrité vérifiée

---

## 🚀 **Migration depuis l'Ancien Système**

### **Coexistence des Systèmes**
- **Ancien** : `launch_light.py` (sans auth)
- **Nouveau** : `launch_auth.py` (avec auth)
- Les deux peuvent coexister

### **Migration Progressive**
1. **Tester** le nouveau système avec comptes démo
2. **Créer** les comptes utilisateurs réels
3. **Former** les utilisateurs
4. **Basculer** définitivement

### **Compatibilité**
- Même base de données ECG
- Mêmes fonctionnalités
- Interface similaire

---

## 🎯 **Cas d'Usage Concrets**

### **🏥 Hôpital/CHU**
- **Admins** : IT + Chef de service
- **Experts** : Cardiologues seniors
- **Étudiants** : Internes + externes

### **🎓 Faculté de Médecine**
- **Admins** : Responsables informatiques
- **Experts** : Enseignants cardiologie
- **Étudiants** : Étudiants en médecine

### **🔬 Centre de Formation**
- **Admins** : Gestionnaires plateforme
- **Experts** : Formateurs spécialisés
- **Étudiants** : Apprenants tous niveaux

---

## 🛠️ **Dépannage et Support**

### **Problèmes Courants**

**❌ "Nom d'utilisateur ou mot de passe incorrect"**
- Vérifier la casse (sensible)
- Utiliser les comptes démo pour tester
- Contacter l'admin pour réinitialisation

**❌ "Accès non autorisé"**
- Vérifier votre rôle utilisateur
- Certaines pages nécessitent des permissions élevées
- Demander à l'admin de modifier vos permissions

**❌ "Module d'auth non disponible"**
- Vérifier que `auth_system.py` est présent
- Relancer avec `launch_auth.py`
- Vérifier les dépendances Python

### **Reset du Système**
```bash
# Supprimer la base utilisateurs (attention !)
rm users/users_auth.json

# Relancer pour recréer les comptes démo
python launch_auth.py
```

---

## 📈 **Roadmap et Améliorations**

### **Version Actuelle (1.0)**
- ✅ 3 rôles utilisateur
- ✅ Authentification par mot de passe
- ✅ Permissions granulaires
- ✅ Interface adaptative

### **Améliorations Prévues (1.1)**
- 🔄 Intégration LDAP/AD
- 🔄 SSO (Single Sign-On)
- 🔄 Audit avancé
- 🔄 API REST pour intégrations

### **Évolutions Long Terme (2.0)**
- 🌐 Multi-tenant
- 📱 Application mobile
- 🤖 IA pour recommandations
- 📊 Analytics avancés

---

**🎯 Le système d'authentification Edu-CG offre un contrôle d'accès professionnel adapté aux environnements médicaux !**

**🔐 Sécurité + Simplicité + Pédagogie = Solution complète !**
