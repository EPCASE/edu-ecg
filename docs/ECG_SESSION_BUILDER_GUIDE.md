# 🎓 ECG Session Builder - Guide Complet

**Date:** 2026-01-11  
**Version:** 1.0  
**Auteur:** BMad Team

---

## 🎯 Vue d'ensemble

L'**ECG Session Builder** est une interface POC complète permettant aux enseignants/experts de :

1. **📤 Importer** des ECG (simples ou multiples)
2. **🏷️ Annoter** intelligemment avec assistance LLM
3. **✅ Valider** les cas créés
4. **📚 Créer** des sessions de formation

---

## 🚀 Accès à l'interface

### Lancement

```bash
streamlit run frontend/ecg_session_builder.py --server.port 8502
```

### URL
```
http://localhost:8502
```

---

## 📋 Workflow Complet

### **Étape 1: 📤 Upload ECG**

#### Mode ECG Unique
1. Sélectionner **"📄 ECG Unique"**
2. Uploader un fichier PNG/JPG/JPEG
3. Visualiser la prévisualisation
4. Cliquer **"✅ Valider cet ECG"**

#### Mode Multi-ECG (Cas Complexes)
1. Sélectionner **"📁 Cas Multi-ECG"**
2. Pour chaque ECG :
   - Uploader le fichier
   - Définir un **libellé** (ex: "ECG_Initial")
   - Choisir le **moment** (Initial, Post-traitement, Contrôle, Suivi)
   - Cliquer **"➕ Ajouter cet ECG"**
3. Répéter pour tous les ECG du cas
4. Cliquer **"✅ Passer à l'annotation"**

**Exemple:** Cas d'infarctus avec 3 ECG
- ECG_01 - Initial (moment de l'arrivée aux urgences)
- ECG_02 - Post-traitement (après fibrinolyse)
- ECG_03 - Contrôle (à J+3)

---

### **Étape 2: 🏷️ Annotation**

#### 📋 Informations du cas

Remplir les métadonnées :
- **Nom du cas** : Titre descriptif
- **Catégorie** : Troubles du Rythme, Infarctus, Bloc de Conduction, etc.
- **Difficulté** : 🟢 Débutant → 🔴 Expert
- **Description clinique** : Contexte patient

#### 🤖 Mode "Assisté par LLM" (Recommandé)

**Avantages :**
- ✅ Rapide
- ✅ Intelligent
- ✅ Détection automatique des concepts
- ✅ Utilise l'ontologie complète

**Utilisation :**
1. Sélectionner **"🤖 Assisté par LLM"**
2. Décrire l'ECG en langage naturel :
   ```
   BAV du 2e degré Mobitz 1, fréquence à 60 bpm, 
   axe normal, pas d'onde Q pathologique, 
   intervalle PR croissant jusqu'au bloc
   ```
3. Cliquer **"🔍 Analyser avec LLM"**
4. Le LLM trouve automatiquement les concepts correspondants dans l'ontologie
5. Pour chaque concept détecté :
   - Voir la **confiance** (%)
   - Voir la **catégorie** ontologique
   - Cliquer **"➕"** pour ajouter

**Exemple de résultat :**
```
📊 Concepts détectés (par confiance):
- BAV 2 Mobitz 1 (Bloc de Conduction) - 95% 🎯 [➕]
- Fréquence normale (Rythme) - 88% 🎯 [➕]
- Axe normal (Axe QRS) - 92% 🎯 [➕]
- Allongement PR (Intervalle) - 87% 🎯 [➕]
```

**🚀 Performance :**
- Utilise le **cache Redis** (réponses instantanées si déjà analysé)
- Hit rate ~70% → Économie de $0.02 par requête
- Latency <2s (ou 0ms si cache hit)

#### ✍️ Mode "Manuel"

**Avantages :**
- ✅ Contrôle total
- ✅ Sélection précise
- ✅ Ajustement des coefficients

**Utilisation :**
1. Sélectionner **"✍️ Manuel"**
2. Choisir une **catégorie** ontologique
3. Sélectionner un **concept** dans la liste
4. Définir le **coefficient** (0.5 → 1.0)
   - 1.0 = Concept obligatoire
   - 0.8 = Concept important
   - 0.5 = Concept optionnel
5. Cliquer **"➕ Ajouter ce concept"**

#### 📋 Gestion des annotations

Une fois ajoutées, les annotations apparaissent :
```
📋 Annotations ajoutées: 4

[Concept]             [Confiance] [Coeff] [Action]
BAV 2 Mobitz 1         95%         1.0     🗑️
Fréquence normale      88%         1.0     🗑️
Axe normal             92%         0.8     🗑️
Allongement PR         87%         0.9     🗑️
```

**Navigation :**
- **◀ Retour à l'upload** : Revenir à l'étape 1 (ECG conservés)
- **Valider le cas ▶** : Passer à l'étape 3 (désactivé si 0 annotations)

---

### **Étape 3: ✅ Validation**

#### Résumé du cas

Vérifier toutes les informations :

**📊 Métadonnées :**
- Nom du cas
- Catégorie
- Difficulté
- Nombre d'ECG
- Nombre d'annotations

**Description :**
- Contexte clinique complet

**🏷️ Annotations expertes :**
- Liste complète des concepts
- Catégories ontologiques
- Coefficients de pondération

**📸 ECG :**
- Prévisualisation de tous les ECG uploadés
- Libellés et timings

#### Actions

- **◀ Retour à l'annotation** : Modifier les annotations
- **💾 Sauvegarder le cas** : Enregistrer sur disque

**Résultat de la sauvegarde :**
```
✅ Cas sauvegardé: case_20260111_001245_a3f7b9c2
📁 Dossier: data/ecg_cases/case_20260111_001245_a3f7b9c2/

Structure:
├── metadata.json (métadonnées + annotations)
├── ecg_1.png (premier ECG)
├── ecg_2.png (deuxième ECG, si multi-ECG)
└── ecg_3.png (troisième ECG, si multi-ECG)
```

---

### **Étape 4: 📚 Création de Session**

#### Cas validés

Liste de tous les cas créés dans cette session de travail :
```
📋 Cas validés: 3

📄 BAV 2 Mobitz 1 - Cas clinique
   ID: case_20260111_001245_a3f7b9c2
   Catégorie: Bloc de Conduction
   Difficulté: 🟡 Intermédiaire
   Annotations: 4

📄 STEMI Antérieur - Évolution
   ID: case_20260111_001312_b8e4c6d1
   Catégorie: Infarctus
   Difficulté: 🔴 Expert
   Annotations: 6

📄 ECG Normal - Référence
   ID: case_20260111_001355_c2f9a8e3
   Catégorie: Normal
   Difficulté: 🟢 Débutant
   Annotations: 3
```

#### 🎓 Créer la session

**Paramètres :**
- **Nom de la session** : Ex: "Troubles du Rythme - Niveau 1"
- **Description** : Objectifs pédagogiques
- **Difficulté globale** : 🟢 Débutant / 🟡 Intermédiaire / 🔴 Avancé
- **Temps limite** : 5-180 minutes

**Actions :**
- **◀ Créer un autre cas** : Retour à l'étape 1 (cas validés conservés)
- **💾 Sauvegarder sans session** : Juste sauvegarder les cas
- **🚀 Créer la session** : Finaliser et créer la session complète

**Résultat :**
```
✅ Session créée: session_20260111_001420
🎉 La session est maintenant disponible pour les étudiants!

Fichier: data/ecg_sessions/session_20260111_001420.json
```

---

## 📊 Sidebar - Statistiques

Affichage en temps réel :

### 📁 Total Cas
Nombre de cas ECG enregistrés dans `data/ecg_cases/`

### 📚 Total Sessions
Nombre de sessions créées dans `data/ecg_sessions/`

### 🚀 Cache LLM (si activé)
- **Hit Rate** : % de requêtes servies depuis le cache
- **Hits** : Nombre de cache hits
- **Misses** : Nombre de cache misses

**Exemple :**
```
📊 Statistiques
📁 Total Cas: 12
📚 Total Sessions: 4

🚀 Cache LLM
Hit Rate: 73.5%
Hits: 48
Misses: 17
```

---

## 🎓 Cas d'Usage Typiques

### 📚 **Use Case 1: Session Débutant "ECG Normaux"**

**Objectif :** Familiariser les étudiants avec les ECG normaux

**Workflow :**
1. Importer 5 ECG normaux (différents âges, sexes)
2. Annoter chacun avec :
   - Rythme sinusal
   - Fréquence normale
   - Axe normal
   - Pas d'anomalie de repolarisation
3. Créer session "ECG Normaux - Niveau Débutant"
4. Temps limite : 15 minutes

**Résultat :** Session de 5 cas, facile, pour débuter

---

### 🔥 **Use Case 2: Cas Multi-ECG "Évolution d'un STEMI"**

**Objectif :** Montrer l'évolution d'un infarctus STEMI

**Workflow :**
1. **Mode Multi-ECG**
2. Importer 3 ECG :
   - ECG_01 - Initial (sus-décalage ST)
   - ECG_02 - Post-fibrinolyse (résolution partielle)
   - ECG_03 - J+3 (ondes Q de nécrose)
3. Annoter avec LLM :
   ```
   STEMI antérieur, sus-décalage ST en V1-V4,
   miroir en inférieur, évolution vers ondes Q
   ```
4. Valider et créer session "Infarctus - Évolution"

**Résultat :** Cas pédagogique complet montrant l'évolution temporelle

---

### 🎯 **Use Case 3: Session Avancée "Troubles du Rythme"**

**Objectif :** Créer une session complète avec 10 cas variés

**Workflow :**
1. Créer 10 cas individuellement :
   - BAV 1, BAV 2 Mobitz 1, BAV 2 Mobitz 2, BAV 3
   - FA, Flutter, TSV
   - ESV isolées, Bigéminisme, Salves TV
2. Pour chaque cas :
   - Upload ECG
   - Annotation LLM
   - Validation
3. À l'étape 4, créer session :
   - Nom : "Troubles du Rythme - Niveau Expert"
   - Temps : 60 minutes
   - Difficulté : 🔴 Avancé

**Résultat :** Session complète de 10 cas, prête à déployer

---

## 🔧 Fonctionnalités Techniques

### 🤖 Intégration LLM

**Modèle :** GPT-4o (OpenAI)  
**Température :** 0.1 (déterministe)  
**Cache :** Redis (TTL 24h)  
**Seuil confiance :** 70%  

**Méthode :** Semantic matching entre description libre et ontologie

**Exemple de requête LLM :**
```python
Description: "BAV 2 Mobitz 1 avec PR croissant"
Ontologie: ["BAV 2 Mobitz 1", "BAV 2 Mobitz 2", "BAV 3", ...]

Résultat:
{
  "match": true,
  "confidence": 95,
  "match_type": "exact",
  "explanation": "Correspondance directe avec BAV 2 Mobitz 1"
}
```

### 📁 Structure de Données

#### Cas ECG (`metadata.json`)
```json
{
  "case_id": "case_20260111_001245_a3f7b9c2",
  "name": "BAV 2 Mobitz 1 - Cas clinique",
  "category": "Bloc de Conduction",
  "difficulty": "🟡 Intermédiaire",
  "description": "Patient de 65 ans, asthénie...",
  "annotations": [
    {
      "concept": "BAV 2 Mobitz 1",
      "category": "Bloc de Conduction",
      "confidence": 95,
      "type": "expert",
      "coefficient": 1.0
    }
  ],
  "num_ecg": 1,
  "created_date": "2026-01-11T00:12:45.123456",
  "type": "simple"
}
```

#### Session (`session_*.json`)
```json
{
  "session_id": "session_20260111_001420",
  "name": "Troubles du Rythme - Niveau 1",
  "description": "Session d'entraînement sur les troubles du rythme",
  "difficulty": "🟡 Intermédiaire",
  "time_limit": 30,
  "cases": [
    "case_20260111_001245_a3f7b9c2",
    "case_20260111_001312_b8e4c6d1",
    "case_20260111_001355_c2f9a8e3"
  ],
  "created_date": "2026-01-11T00:14:20.789012",
  "status": "active",
  "show_feedback": true,
  "allow_retry": true,
  "participants": []
}
```

---

## 🎯 Bonnes Pratiques

### ✅ Création de Cas

1. **Nommer clairement** : "BAV 2 Mobitz 1" plutôt que "Cas 1"
2. **Décrire le contexte** : Âge, sexe, symptômes
3. **Annoter complètement** : Ne pas oublier les annotations "normales" (ex: axe normal)
4. **Utiliser le LLM** : Plus rapide et cohérent avec l'ontologie
5. **Vérifier les coefficients** : 1.0 pour concepts obligatoires

### ✅ Création de Sessions

1. **Homogénéité** : Grouper des cas de même niveau
2. **Progression** : Commencer facile, finir difficile
3. **Temps réaliste** : 2-3 min par cas simple, 5-7 min par cas complexe
4. **Nombre optimal** : 5-10 cas par session
5. **Description claire** : Objectifs pédagogiques explicites

### ✅ Utilisation du LLM

1. **Descriptions complètes** : Plus de détails = meilleure détection
2. **Vocabulaire médical** : Utiliser la terminologie ECG standard
3. **Valider les résultats** : Vérifier que les concepts détectés sont pertinents
4. **Ajuster les coefficients** : Modifier si nécessaire après détection LLM
5. **Combiner modes** : LLM pour détecter, manuel pour affiner

---

## 🐛 Troubleshooting

### ❌ "Aucun concept détecté avec confiance >70%"

**Cause :** Description trop vague ou concepts absents de l'ontologie

**Solution :**
- Enrichir la description avec plus de détails
- Utiliser le mode manuel pour ajouter les concepts
- Vérifier que les concepts existent dans l'ontologie

### ❌ "Cache LLM ne s'affiche pas dans la sidebar"

**Cause :** Redis non démarré ou cache service non disponible

**Solution :**
```bash
docker start edu-ecg-redis
```

### ❌ "Erreur lors de l'upload PDF"

**Cause :** Support PDF limité dans cette version POC

**Solution :**
- Convertir le PDF en PNG/JPG avant upload
- Utiliser capture d'écran (Windows+Shift+S)

### ❌ "Session créée mais invisible dans l'app principale"

**Cause :** Cache Streamlit

**Solution :**
- Rafraîchir la page principale (F5)
- Vérifier que le fichier JSON existe dans `data/ecg_sessions/`

---

## 🚀 Roadmap / Améliorations Futures

### 📅 Version 1.1 (Court terme)
- [ ] Support PDF natif (conversion automatique)
- [ ] Recadrage interactif des ECG
- [ ] Import batch (plusieurs fichiers simultanés)
- [ ] Templates d'annotation prédéfinis

### 📅 Version 1.2 (Moyen terme)
- [ ] Édition de cas existants
- [ ] Duplication de cas (templates)
- [ ] Drag & drop pour réorganiser les ECG
- [ ] Preview de la session avant création

### 📅 Version 2.0 (Long terme)
- [ ] Import depuis PACS/DICOM
- [ ] Annotations collaboratives (multi-experts)
- [ ] Versioning des cas
- [ ] Export SCORM pour LMS

---

## 📞 Support

**Questions :** GitHub Issues  
**Documentation :** Ce fichier  
**Vidéo tutoriel :** À venir  

---

**🎉 Félicitations ! Vous maîtrisez maintenant le Session Builder !**

*"Créer des sessions n'a jamais été aussi simple."*

---

**📅 Créé :** 2026-01-11  
**✍️ Auteur :** BMad Team  
**🔄 Dernière MAJ :** 2026-01-11
