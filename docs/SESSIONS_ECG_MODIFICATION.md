# Guide de Modification des Sessions ECG

## 🎯 Nouvelle Fonctionnalité : Modifier les Sessions

La gestion des sessions ECG a été enrichie avec des fonctionnalités complètes de modification, suppression et duplication.

## 📋 Fonctionnalités disponibles

### 1. **Interface en onglets**
- **➕ Créer Session** : Création de nouvelles sessions (fonctionnalité existante)
- **✏️ Modifier Session** : Modification, suppression et duplication des sessions existantes

### 2. **Gestion des sessions existantes**

#### 📖 **Visualisation**
- Liste de toutes les sessions créées
- Informations détaillées pour chaque session :
  - Nom et description
  - Niveau de difficulté
  - Temps limite
  - Nombre de cas ECG
  - Date de création
  - Créateur

#### ✏️ **Modification**
- **Renommer** la session
- **Modifier la description** 
- **Changer le niveau de difficulté**
- **Ajuster le temps limite**
- **Ajouter/Supprimer des cas ECG** avec aperçu des changements
- **Modifier les paramètres avancés** (ordre aléatoire, feedback, tentatives multiples)

#### 📋 **Duplication**
- Créer une **copie** d'une session existante
- Modifier la copie sans affecter l'originale
- Nom automatique : "Session Originale - Copie"

#### 🗑️ **Suppression**
- Suppression sécurisée avec **double confirmation**
- Clic 1 : Avertissement
- Clic 2 : Suppression définitive

## 🛠️ Utilisation

### Accès à l'interface
1. Allez dans **"🏛️ Administration"**
2. Sélectionnez **"📋 BDD"** 
3. Cliquez sur **"📚 Sessions ECG"**
4. Choisissez l'onglet **"✏️ Modifier Session"**

### Modifier une session
1. **Sélectionnez** la session dans la liste déroulante
2. **Consultez** les informations actuelles dans l'expander
3. **Modifiez** les champs souhaités dans le formulaire
4. **Visualisez** l'aperçu des changements (cas ajoutés/supprimés)
5. **Sauvegardez** avec le bouton "✅ Sauvegarder"

### Dupliquer une session
1. Sélectionnez la session à dupliquer
2. Modifiez les paramètres selon vos besoins
3. Cliquez sur **"📋 Dupliquer"**
4. Une nouvelle session est créée avec le suffixe "- Copie"

### Supprimer une session
1. Sélectionnez la session à supprimer
2. Cliquez sur **"🗑️ Supprimer"** 
3. **Confirmez** en cliquant à nouveau
4. La session est définitivement supprimée

## 🔄 Aperçu des changements

### Lors de la modification des cas ECG :
```
🔄 Aperçu des changements :
➕ Ajoutés : ECG Fibrillation, ECG Tachycardie
➖ Supprimés : ECG Normal
```

### Métadonnées de modification :
- **modified_date** : Date de dernière modification
- **modified_by** : Utilisateur ayant modifié (admin par défaut)

## 📁 Structure des fichiers

### Localisation
- **Dossier** : `data/ecg_sessions/`
- **Format** : Fichiers JSON individuels
- **Nommage** : `{nom_session}.json`

### Structure JSON enrichie
```json
{
  "name": "Session Modifiée",
  "description": "Description mise à jour",
  "difficulty": "🟡 Intermédiaire", 
  "time_limit": 45,
  "cases": ["ECG1", "ECG2", "ECG3"],
  "randomize_order": true,
  "show_feedback": true,
  "allow_retry": true,
  "created_date": "2025-07-23T10:00:00",
  "created_by": "admin",
  "modified_date": "2025-07-23T15:30:00",
  "modified_by": "admin"
}
```

## ⚠️ Points d'attention

### Sécurité
- **Double confirmation** pour les suppressions
- **Sauvegarde automatique** des métadonnées de modification
- **Validation** des champs obligatoires

### Gestion des noms
- Si le **nom change**, l'ancien fichier est supprimé et un nouveau est créé
- Si le **nom reste identique**, le fichier existant est mis à jour

### Cas ECG
- Seuls les **cas disponibles** peuvent être sélectionnés
- **Aperçu temps réel** des ajouts/suppressions
- **Validation** : au moins un cas requis

## 🚀 Exemples d'utilisation

### Scénario 1 : Ajout de cas à une session
1. Session "Arythmies Niveau 1" avec 3 cas
2. Ajouter 2 nouveaux cas de fibrillation
3. Aperçu : "➕ Ajoutés : ECG Fibrillation A, ECG Fibrillation B"
4. Sauvegarder → Session mise à jour avec 5 cas

### Scénario 2 : Duplication pour adaptation
1. Session "Examen Final" complexe
2. Dupliquer → "Examen Final - Copie"
3. Réduire la difficulté et le temps
4. Utiliser pour un groupe d'étudiants différent

### Scénario 3 : Réorganisation des sessions
1. Plusieurs sessions similaires existantes
2. Modifier et regrouper les cas pertinents
3. Supprimer les sessions obsolètes
4. Résultat : structure plus claire

## 🔍 Dépannage

### Sessions introuvables
- Vérifiez le dossier `data/ecg_sessions/`
- Assurez-vous que les fichiers sont au format JSON valide

### Erreurs de modification
- Vérifiez que le nom n'est pas vide
- Au moins un cas ECG doit être sélectionné
- Rechargez la page si nécessaire

### Problèmes de suppression
- La session doit exister dans le système de fichiers
- Vérifiez les permissions d'écriture

---

*Cette fonctionnalité complète le système de gestion des sessions ECG avec tous les outils nécessaires pour une administration efficace.*
