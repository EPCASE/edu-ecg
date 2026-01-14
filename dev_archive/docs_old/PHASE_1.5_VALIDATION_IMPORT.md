# 🔬 PHASE 1.5 - VALIDATION IMPORT ECG

**Objectif :** Valider pipeline d'import ECG **AVANT** Phase 2 (annotation)

**Durée :** 3-5 jours  
**Responsable :** Dr. Grégoire + Agent  
**Statut :** ⏳ À lancer

---

## 🎯 Pourquoi Phase 1.5 ?

### **Risque Identifié :**
```
POC validé avec 2 cas JSON ✅
Mais Phase 2 = 50 ECG PDF réels ❓

Si import ECG défaillant:
    → 25h annotation PERDUES
    → Dataset inutilisable
    → Retour Phase 1 (refonte)
```

### **Solution :**
**Valider import AVANT annotation** = Économie 25h + sécurité dataset

---

## 📋 Plan Phase 1.5 (3-5 jours)

### **Jour 1 : Sélection 10 ECG Test**

**Objectif :** Diversité maximale pour test robustesse

**Critères sélection :**
```
✅ 3 ECG normaux (différents services)
✅ 2 BAV (1er, 2e, 3e degré)
✅ 2 Blocs de branche (BBG, BBD)
✅ 1 Fibrillation auriculaire
✅ 1 STEMI
✅ 1 ECG complexe (multi-pathologie)
```

**Livrables :**
- [ ] 10 PDF ECG anonymisés dans `data/ecg_cases/phase1.5_test/`
- [ ] Fiche métadonnées par ECG (PR, QRS, FC, diagnostic)

---

### **Jour 2 : Test Import PDF**

**Test 1 - Import Manuel Simple**

**Action :**
```python
# Tester import 1 ECG via interface POC
1. Charger ECG1.pdf
2. Vérifier affichage PDF
3. Vérifier navigation pages
4. Vérifier zoom/qualité
```

**Critères succès :**
- [ ] PDF s'affiche correctement
- [ ] Toutes pages visibles
- [ ] Zoom fonctionnel
- [ ] Pas de corruption image

**Test 2 - Import Batch 10 ECG**

**Action :**
```python
# Script batch import
for ecg in test_ecgs:
    import_ecg(ecg)
    validate_display(ecg)
    log_errors(ecg)
```

**Critères succès :**
- [ ] 10/10 ECG importés
- [ ] Aucune erreur affichage
- [ ] Temps import <5s par ECG

---

### **Jour 3 : Test OCR/Extraction Métadonnées (Optionnel)**

**Si POC doit extraire automatiquement PR/QRS/FC du PDF :**

**Test :**
```
1. OCR header ECG (nom, date, FC)
2. Extraction mesures automatiques (PR, QRS, QT)
3. Validation exactitude vs ground truth
```

**Critères succès :**
- [ ] Précision OCR >95%
- [ ] Mesures exactes ±10%
- [ ] Pas de faux positifs

**⚠️ IMPORTANT :**
Si OCR défaillant → **Annotation manuelle métadonnées** (acceptable pour Phase 2)

---

### **Jour 4 : Test Pipeline Complet**

**Test End-to-End avec 1 ECG annoté :**

**Workflow :**
```
1. Import ECG test (ex: BAV1)
2. Annotation manuelle expected_concepts:
   {
     "text": "BAV 1er degré",
     "category": "conduction"
   }
3. Test correction avec réponse étudiant
4. Vérifier scoring
5. Vérifier feedback
```

**Critères succès :**
- [ ] Pipeline complet fonctionne
- [ ] Score cohérent
- [ ] Feedback pertinent
- [ ] Temps total <10s

---

### **Jour 5 : Décision GO/NO-GO Phase 2**

**Réunion décision :**

**Scénario 1 - Import ECG OK :**
```
✅ 10/10 ECG importés et affichés
✅ Pipeline complet testé
✅ Pas d'erreur bloquante
→ DÉCISION : GO PHASE 2 (annotation 50 ECG)
```

**Scénario 2 - Import ECG Partiel :**
```
⚠️ 8/10 ECG OK, 2 problèmes mineurs
⚠️ OCR défaillant mais contournable
⚠️ Correction nécessaire (1-2 jours)
→ DÉCISION : FIX puis GO PHASE 2
```

**Scénario 3 - Import ECG KO :**
```
❌ <7/10 ECG importés
❌ Erreurs affichage critiques
❌ Pipeline incomplet
→ DÉCISION : NO-GO, retour Phase 1 (refonte import)
```

---

## 🛠️ Infrastructure Technique

### **Fichiers à Valider :**

**1. Backend PDF Extraction**
```
✅ backend/pdf_extractor.py (existe)
❓ Fonctionne avec ECG réels ? (à tester)
❓ Gère multi-pages ? (à valider)
❓ Performance acceptable ? (à mesurer)
```

**2. Frontend PDF Display**
```
✅ PDF.js intégré ? (vérifier)
❓ Zoom/navigation OK ? (tester)
❓ Mobile-friendly ? (optionnel Phase 2)
```

**3. Data Pipeline**
```
❓ Stockage ECG : data/ecg_cases/ (créer)
❓ Format attendu : PDF + JSON métadonnées
❓ Backup/versioning : Git LFS ? (discuter)
```

---

## 📊 Métriques Validation

### **Critères Acceptation Phase 1.5 :**

| Métrique | Cible | Critique |
|----------|-------|----------|
| **ECG importés** | 10/10 | 8/10 minimum |
| **Affichage correct** | 100% | 90% minimum |
| **Temps import** | <5s | <10s maximum |
| **Erreurs bloquantes** | 0 | 0 |
| **Pipeline end-to-end** | OK | OK |

**Décision GO si :**
- ✅ Toutes métriques critiques atteintes
- ✅ Aucune erreur bloquante identifiée
- ✅ Dr. Grégoire valide qualité affichage ECG

---

## 🚨 Risques & Mitigation

### **Risque 1 : PDF.js incompatible avec ECG CHU**
**Impact :** Affichage défaillant  
**Mitigation :** Tester conversion PDF→PNG si nécessaire  
**Coût :** +1 jour développement

### **Risque 2 : OCR header ECG imprécis**
**Impact :** Métadonnées erronées  
**Mitigation :** Annotation manuelle métadonnées (acceptable)  
**Coût :** +5min par ECG en Phase 2

### **Risque 3 : Stockage 50 ECG PDF trop lourd**
**Impact :** Git lent, déploiement compliqué  
**Mitigation :** Git LFS ou stockage externe (S3)  
**Coût :** +2h setup infrastructure

### **Risque 4 : Anonymisation ECG insuffisante**
**Impact :** RGPD non conforme  
**Mitigation :** Script suppression métadonnées PDF  
**Coût :** +3h développement + validation juridique

---

## 📝 Livrables Phase 1.5

**Documents :**
- [ ] `PHASE_1.5_VALIDATION_IMPORT.md` (ce document)
- [ ] `RAPPORT_TEST_IMPORT_ECG.md` (résultats tests)
- [ ] `GUIDE_IMPORT_ECG.md` (procédure import pour Phase 2)

**Code :**
- [ ] Script batch import ECG (`scripts/batch_import_ecg.py`)
- [ ] Tests validation affichage (`tests/test_pdf_display.py`)
- [ ] Anonymisation PDF si nécessaire (`scripts/anonymize_pdf.py`)

**Data :**
- [ ] 10 ECG test dans `data/ecg_cases/phase1.5_test/`
- [ ] Métadonnées JSON associées
- [ ] 1 ECG annoté complet (test pipeline)

---

## 🗓️ Timeline Phase 1.5

```
Jour 1 (Lundi)     : Sélection 10 ECG test
Jour 2 (Mardi)     : Test import + affichage
Jour 3 (Mercredi)  : Test OCR/métadonnées (optionnel)
Jour 4 (Jeudi)     : Test pipeline end-to-end
Jour 5 (Vendredi)  : Réunion GO/NO-GO Phase 2

Total : 1 semaine au lieu de démarrer Phase 2 directement
```

**Bénéfice :**
- ✅ Sécurise 25h annotation Phase 2
- ✅ Identifie problèmes AVANT investissement
- ✅ Valide infrastructure complète
- ✅ Coût : 5 jours vs risque 8 semaines perdues

---

## 🎯 Décision Attendue

**Option A - Lancer Phase 1.5 (RECOMMANDÉ)**
```
✅ Sécurise Phase 2
✅ 5 jours validation vs 25h annotation à risque
✅ Identifie blocages tôt
→ Démarrage Phase 1.5 immédiat
```

**Option B - Sauter Phase 1.5 (RISQUÉ)**
```
⚠️ Assume import ECG fonctionne (non testé)
⚠️ Risque découvrir problèmes après annotation
⚠️ Possible perte 25h travail
→ Démarrage Phase 2 direct (non recommandé)
```

---

## ✍️ Signatures

**Proposé par :** GitHub Copilot  
**Date :** 2026-01-10  

**Décision Dr. Grégoire :** ☐ Option A (Phase 1.5)  ☐ Option B (Phase 2 direct)  
**Date décision :** ___________  

---

## 📎 Ressources

**Existant validé :**
- ✅ `backend/pdf_extractor.py` (à tester avec ECG réels)
- ✅ `frontend/correction_llm_poc.py` (interface POC)
- ✅ `data/test_cases.json` (2 cas validés)

**À créer si Phase 1.5 validée :**
- ⏳ `scripts/batch_import_ecg.py`
- ⏳ `tests/test_pdf_display.py`
- ⏳ `data/ecg_cases/phase1.5_test/` (dossier 10 ECG)

---

**Version :** 1.0  
**Dernière mise à jour :** 2026-01-10  
**Prochaine étape :** Décision GO/NO-GO Phase 1.5
