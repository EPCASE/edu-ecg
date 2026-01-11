# 🧪 Guide de Test - ECG Session Builder

**Date:** 2026-01-11  
**URL:** http://localhost:8502  
**Statut:** 🟢 Serveur actif

---

## 📋 Checklist de Test

### ✅ Test #1: Interface de Base

**Vérifications:**
- [ ] La page s'affiche correctement
- [ ] Titre "🎓 ECG Session Builder" visible
- [ ] Barre de progression avec 4 étapes
- [ ] Étape 1 "📤 Upload" active (en bleu)
- [ ] Sidebar avec statistiques visible

**Sidebar attendue:**
```
📊 Statistiques
📁 Total Cas: X
📚 Total Sessions: Y

🚀 Cache LLM
Hit Rate: XX%
Hits: XX
Misses: XX
```

---

### ✅ Test #2: Upload ECG (Mode Simple)

**Actions:**
1. Sélectionner **"📄 ECG Unique"**
2. Cliquer sur zone de drop ou "Browse files"
3. Uploader le fichier: `data/ecg_pdfs/bav2m1a.png` (si disponible)
   - OU n'importe quelle image PNG/JPG d'ECG

**Résultat attendu:**
- [ ] Image s'affiche en prévisualisation
- [ ] Bouton "✅ Valider cet ECG" apparaît
- [ ] Clic sur bouton → Passage à l'étape 2

**Si erreur 403:**
- Vérifier que CORS est activé (voir config.toml)
- Essayer dans Firefox au lieu de VS Code browser

---

### ✅ Test #3: Mode Recherche Rapide 🔍

**Actions:**
1. Dans "Mode d'annotation", sélectionner **"🔍 Recherche Rapide"**
2. Dans le champ de recherche, taper: **"BAV"**

**Résultat attendu:**
```
✅ 6 concepts trouvés

[Concept]                         [Action]
BAV 2 Mobitz 2                    [➕ Ajouter]
Catégorie: DIAGNOSTIC_MAJEUR

BAV complet                       [➕ Ajouter]
Catégorie: DIAGNOSTIC_MAJEUR

BAV 2 Mobitz 1                    [➕ Ajouter]
Catégorie: DIAGNOSTIC_MAJEUR

... etc
```

**Test:**
- [ ] Recherche "BAV" → 6 résultats
- [ ] Recherche "sinusal" → 7 résultats
- [ ] Recherche "normal" → 9 résultats
- [ ] Clic "➕ Ajouter" fonctionne
- [ ] Concept apparaît dans "📋 Annotations ajoutées"

---

### ✅ Test #4: Mode Manuel ✍️

**Actions:**
1. Sélectionner **"✍️ Manuel"**
2. Observer le message: "✅ 214 concepts chargés depuis l'ontologie"
3. Dans "Catégorie", sélectionner **"DIAGNOSTIC_MAJEUR"**
4. Dans "Concept", choisir **"BAV 2 Mobitz 1"**
5. Ajuster coefficient (0.5 → 1.0)
6. Cliquer "➕ Ajouter ce concept"

**Résultat attendu:**
- [ ] Liste déroulante "Catégorie" contient 4 catégories
- [ ] Liste "Concept" affiche ~70 concepts pour DIAGNOSTIC_MAJEUR
- [ ] Bouton "➕ Ajouter" fonctionne
- [ ] Concept apparaît dans annotations
- [ ] Message "✅ BAV 2 Mobitz 1 ajouté!"

---

### ✅ Test #5: Mode LLM 🤖

**Actions:**
1. Sélectionner **"🤖 Assisté par LLM"**
2. Dans le champ "Description de l'ECG", entrer:
   ```
   BAV du 2e degré Mobitz 1 avec allongement progressif de l'intervalle PR, 
   rythme sinusal, fréquence ventriculaire à 60 bpm
   ```
3. Cliquer "🔍 Analyser avec LLM"
4. Attendre 15-30 secondes

**Résultat attendu:**
- [ ] Spinner "🤖 Analyse LLM en cours..."
- [ ] Message "🔍 Analyse de 214 concepts de l'ontologie..."
- [ ] Après analyse: "✅ X concepts détectés!"
- [ ] Liste de concepts avec confiance colorée:
  - 🟢 95% BAV 2 Mobitz 1
  - 🟡 72% Allongement PR
  - 🟠 68% Rythme sinusal
- [ ] Boutons "➕" fonctionnent
- [ ] Cache stats mis à jour (hit/miss)

**Si "⚠️ Aucun concept détecté":**
- Description trop vague
- Essayer une description plus médicale
- Ou utiliser mode Recherche Rapide

---

### ✅ Test #6: Informations du Cas

**Actions:**
1. Remplir le formulaire:
   - **Nom:** "BAV 2 Mobitz 1 - Cas pédagogique"
   - **Catégorie:** "Bloc de Conduction"
   - **Difficulté:** Déplacer slider sur 🟡 Intermédiaire
   - **Description:** "Patient de 65 ans avec asthénie..."

**Résultat attendu:**
- [ ] Tous les champs sauvegardés dans session state
- [ ] Slider de difficulté fonctionne
- [ ] Catégories affichées correctement

---

### ✅ Test #7: Gestion des Annotations

**Actions:**
1. Ajouter 3-4 concepts (mode Recherche Rapide recommandé)
2. Observer la section "📋 Annotations ajoutées"
3. Cliquer sur "🗑️" pour supprimer une annotation

**Résultat attendu:**
```
📋 Annotations ajoutées: 4

[Concept]              [Catégorie]        [Coeff] [Action]
BAV 2 Mobitz 1         DIAGNOSTIC_MAJEUR   1.0     [🗑️]
Rythme sinusal         DESCRIPTEUR_ECG     0.9     [🗑️]
QRS normal             DESCRIPTEUR_ECG     0.8     [🗑️]
ST normal              DESCRIPTEUR_ECG     0.8     [🗑️]
```

**Test:**
- [ ] Annotations s'affichent
- [ ] Bouton "🗑️" supprime l'annotation
- [ ] Message "✅ ... ajouté!" apparaît
- [ ] Compteur mis à jour

---

### ✅ Test #8: Navigation entre Étapes

**Actions:**
1. Depuis l'étape 2 (Annotation), cliquer "◀ Retour à l'upload"
2. Vérifier que l'ECG est toujours là
3. Remonter à l'étape 2
4. Ajouter au moins 1 annotation
5. Cliquer "Valider le cas ▶"

**Résultat attendu:**
- [ ] Navigation fonctionne
- [ ] Données conservées entre étapes
- [ ] Étape 3 (Validation) s'affiche
- [ ] Bouton "Valider" désactivé si 0 annotation

---

### ✅ Test #9: Validation du Cas

**À l'étape 3, vérifier:**
- [ ] Résumé du cas complet:
  - Nom, catégorie, difficulté
  - Nombre ECG, nombre annotations
- [ ] Description affichée
- [ ] Liste des annotations avec coefficients
- [ ] Prévisualisation de l'ECG
- [ ] Boutons "◀ Retour" et "💾 Sauvegarder"

**Actions:**
1. Cliquer "💾 Sauvegarder le cas"

**Résultat attendu:**
```
✅ Cas sauvegardé: case_20260111_XXXXXX_YYYYYYYY
📁 Dossier: data/ecg_cases/case_20260111_XXXXXX_YYYYYYYY/
```

- [ ] Message de succès
- [ ] Passage automatique à l'étape 4
- [ ] Cas ajouté à la liste "Cas validés"

---

### ✅ Test #10: Création de Session

**À l'étape 4, vérifier:**
- [ ] Liste "📋 Cas validés: 1" (ou plus si plusieurs cas créés)
- [ ] Aperçu du cas avec détails

**Actions:**
1. Remplir:
   - **Nom:** "Blocs de Conduction - Niveau 1"
   - **Description:** "Session d'entraînement sur les BAV"
   - **Difficulté:** 🟡 Intermédiaire
   - **Temps:** 30 minutes
2. Cliquer "🚀 Créer la session"

**Résultat attendu:**
```
✅ Session créée: session_20260111_XXXXXX
🎉 La session est maintenant disponible pour les étudiants!
```

- [ ] Message de succès
- [ ] Balloons animation 🎉
- [ ] Retour à l'étape 1
- [ ] Sidebar "Total Sessions" incrémenté

---

### ✅ Test #11: Multi-ECG (Avancé)

**Recommencer depuis l'étape 1:**

**Actions:**
1. Sélectionner **"📁 Cas Multi-ECG"**
2. Uploader premier ECG:
   - Libellé: "ECG_01"
   - Moment: "Initial"
   - Cliquer "➕ Ajouter cet ECG"
3. Uploader deuxième ECG:
   - Libellé: "ECG_02"
   - Moment: "Post-traitement"
   - Cliquer "➕ Ajouter cet ECG"
4. Observer "📋 ECG ajoutés: 2"
5. Cliquer "✅ Passer à l'annotation"

**Résultat attendu:**
- [ ] 2 ECG dans la liste
- [ ] Chaque ECG a son libellé et timing
- [ ] Bouton "🗑️ Supprimer" fonctionne
- [ ] Passage à l'étape 2 avec 2 ECG

---

### ✅ Test #12: Vérification Fichiers

**Dans l'explorateur Windows:**

1. Aller dans `data/ecg_cases/`
2. Vérifier présence du dossier `case_20260111_*`
3. Ouvrir le dossier
4. Vérifier présence de:
   - [ ] `metadata.json`
   - [ ] `ecg_1.png`
   - [ ] `ecg_2.png` (si multi-ECG)

**Ouvrir `metadata.json` et vérifier:**
```json
{
  "case_id": "case_...",
  "name": "BAV 2 Mobitz 1 - Cas pédagogique",
  "category": "Bloc de Conduction",
  "difficulty": "🟡 Intermédiaire",
  "description": "...",
  "annotations": [
    {
      "concept": "BAV 2 Mobitz 1",
      "category": "DIAGNOSTIC_MAJEUR",
      "type": "expert",
      "coefficient": 1.0
    }
  ],
  "num_ecg": 1,
  "created_date": "2026-01-11T...",
  "type": "simple"
}
```

5. Dans `data/ecg_sessions/`
6. Vérifier présence de `session_20260111_*.json`

**Ouvrir `session_*.json` et vérifier:**
```json
{
  "session_id": "session_...",
  "name": "Blocs de Conduction - Niveau 1",
  "description": "Session d'entraînement...",
  "difficulty": "🟡 Intermédiaire",
  "time_limit": 30,
  "cases": [
    "case_20260111_..."
  ],
  "created_date": "2026-01-11T...",
  "status": "active",
  "show_feedback": true,
  "allow_retry": true,
  "participants": []
}
```

---

### ✅ Test #13: Cache Redis

**Observer la sidebar pendant les tests LLM:**

**Premier appel LLM:**
- Hits: 0
- Misses: X
- Hit Rate: 0%

**Deuxième appel LLM (même description):**
- Hits: Y
- Misses: X
- Hit Rate: Y/(X+Y) %

**Test:**
1. Mode LLM avec description "BAV 2 Mobitz 1"
2. Noter les stats
3. Rafraîchir la page
4. Re-tester avec EXACTEMENT la même description
5. Observer le hit rate augmenter

**Résultat attendu:**
- [ ] Cache stats s'affichent
- [ ] Hit rate augmente à chaque requête identique
- [ ] Deuxième appel plus rapide (~0ms vs ~1.2s)

---

## 🐛 Problèmes Connus & Solutions

### Erreur 403 Upload
**Solution:** Déjà corrigé avec `enableCORS=true`

### Aucun concept détecté (LLM)
**Solutions:**
1. Utiliser mode "🔍 Recherche Rapide" (plus fiable)
2. Enrichir la description
3. Vérifier que Redis fonctionne

### Liste vide (Mode Manuel)
**Déjà corrigé:** 214 concepts chargés

### Spinner LLM infini
**Solution:** Limité à 100 concepts (timeout 30s max)

---

## 📊 Résultats Attendus

### Performance
- **Upload:** < 1s
- **Recherche Rapide:** 0ms (instantané)
- **Mode Manuel:** 0ms (sélection)
- **LLM (cache miss):** 15-30s
- **LLM (cache hit):** 0ms
- **Sauvegarde cas:** < 1s
- **Création session:** < 1s

### Données
- **Concepts chargés:** 214
- **Catégories:** 4
- **Recherche "BAV":** 6 résultats
- **Recherche "sinusal":** 7 résultats
- **Recherche "normal":** 9 résultats

---

## ✅ Checklist Finale

**Fonctionnalités testées:**
- [ ] Upload ECG simple
- [ ] Upload multi-ECG
- [ ] Mode Recherche Rapide
- [ ] Mode LLM
- [ ] Mode Manuel
- [ ] Gestion annotations
- [ ] Navigation entre étapes
- [ ] Validation cas
- [ ] Sauvegarde cas
- [ ] Création session
- [ ] Cache Redis
- [ ] Fichiers créés correctement

**Si tous les tests passent:**
🎉 **L'interface est validée et prête pour la production !**

---

**📅 Date du test:** 2026-01-11  
**🧪 Testeur:** [Votre nom]  
**✅ Statut:** En cours...
