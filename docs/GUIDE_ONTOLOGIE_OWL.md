# 🏗️ Guide d'Édition de l'Ontologie ECG avec Protégé

## 📋 Objectif

Créer une ontologie ECG **médicalement robuste** avec :
- ✅ Hiérarchie diagnostics (Urgent → Majeur → Signe → Descripteur)
- ✅ Territoires ECG mappés aux électrodes
- ✅ Poids cliniques (1-4)
- ✅ Règles d'implication formalisées

---

## 🛠️ Étape 1 : Ouvrir l'Ontologie dans Protégé

1. **Télécharger Protégé** : https://protege.stanford.edu/
2. **Ouvrir** : `data/ontologie.owx`
3. **Vue recommandée** : Class Hierarchy

---

## 📐 Étape 2 : Créer la Hiérarchie de Classes

### **Structure cible :**

```
Thing
├── Concept_ECG
│   ├── Diagnostic
│   │   ├── Diagnostic_Urgent
│   │   │   ├── STEMI_Anteroseptal
│   │   │   └── TV_Soutenue
│   │   └── Diagnostic_Majeur
│   │       ├── NSTEMI
│   │       ├── BAV2_Mobitz2
│   │       └── FA_Rapide
│   ├── Signe_ECG_Pathologique
│   │   ├── Sus_ST_Anterieur
│   │   ├── Onde_Q_Anteroseptale
│   │   ├── Onde_T_Negative_V4V6
│   │   ├── Onde_T_Negative_DII
│   │   ├── BAV1
│   │   ├── BBG_Complet
│   │   ├── BBD
│   │   └── HBAG
│   └── Descripteur_ECG
│       ├── Rythme_Sinusal
│       ├── FC_Normale
│       ├── PR_Normal
│       ├── QRS_Fins
│       ├── Axe_Normal
│       ├── Repolarisation_Normale
│       ├── QRS_Elargi
│       ├── HAG_Atrial
│       └── Axe_Gauche
│
├── Territoire_ECG
│   ├── Anteroseptal
│   ├── Apical
│   ├── Lateral
│   ├── Inferieur
│   └── Posterieur
│
└── Electrode
    ├── V1, V2, V3, V4, V5, V6
    ├── DI, DII, DIII
    └── AVR, AVL, AVF
```

### **Création dans Protégé :**

1. **Clic droit sur `Thing`** → Add subclass → `Concept_ECG`
2. **Clic droit sur `Concept_ECG`** → Add subclass → `Diagnostic`
3. **Répéter** pour toute la hiérarchie ci-dessus

---

## 🏷️ Étape 3 : Créer les Object Properties

### **Properties nécessaires :**

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `hasElectrode` | Territoire_ECG | Electrode | Territoire → Électrodes |
| `hasTerritory` | Concept_ECG | Territoire_ECG | Concept → Territoire |
| `hasWeight` | Concept_ECG | integer | Poids clinique (1-4) |
| `impliesSign` | Diagnostic | Signe_ECG_Pathologique | Diagnostic → Signes auto-validés |
| `hasSynonym` | Concept_ECG | string | Synonymes du concept |
| `hasArtery` | Territoire_ECG | string | Artère principale |

### **Création :**

1. Onglet **Object Properties**
2. Clic **+** → Créer property
3. Définir **Domain** et **Range**
4. Répéter pour chaque property

---

## 🗺️ Étape 4 : Mapper Territoires → Électrodes

### **Exemple : Territoire Anteroseptal**

1. **Sélectionner** classe `Anteroseptal`
2. **Onglet Annotations** → Add annotation
   - `rdfs:label` = "Antéroseptal"
   - `rdfs:comment` = "Territoire V1-V4, artère IVA proximale"

3. **Onglet Class Assertions** → Add restriction
   - `hasElectrode some V1`
   - `hasElectrode some V2`
   - `hasElectrode some V3`
   - `hasElectrode some V4`

4. **Add Data Property**
   - `hasArtery` = "IVA proximale"
   - `paroi` = "Septum + paroi antérieure VG"

### **Répéter pour tous les territoires :**

| Territoire | Électrodes | Artère |
|------------|-----------|--------|
| Anteroseptal | V1, V2, V3, V4 | IVA proximale |
| Apical | V4, V5 | IVA distale |
| Lateral | V5, V6, DI, AVL | Circonflexe |
| Inferieur | DII, DIII, AVF | Coronaire droite |
| Posterieur | V7, V8, V9 | Circonflexe |

---

## ⚖️ Étape 5 : Ajouter Poids aux Concepts

### **Pour chaque concept, ajouter Data Property `hasWeight` :**

| Concept | Poids | Justification |
|---------|-------|---------------|
| STEMI_Anteroseptal | 4 | Urgence vitale <90min |
| NSTEMI | 3 | Urgence différée <24h |
| BAV2_Mobitz2 | 3 | Pacemaker urgent |
| FA_Rapide | 3 | Risque thrombo-embolique |
| Sus_ST_Anterieur | 2 | Signe STEMI |
| BBG_Complet | 2 | Surveillance, masque IDM |
| BAV1 | 2 | Surveillance |
| Rythme_Sinusal | 1 | Descriptif |
| QRS_Fins | 1 | Descriptif |

### **Création :**

1. Sélectionner concept (ex: `NSTEMI`)
2. Onglet **Data Property Assertions**
3. **+** → Sélectionner `hasWeight`
4. Valeur : `3` (type: integer)

---

## 🔗 Étape 6 : Créer Règles d'Implication

### **Exemple : NSTEMI → Onde_T_Negative**

1. Sélectionner `NSTEMI`
2. Onglet **Object Property Assertions**
3. **+** → `impliesSign` → Sélectionner `Onde_T_Negative_Ischemique`

### **Autres implications importantes :**

| Diagnostic | Implique (auto-validé) |
|------------|------------------------|
| STEMI_Anteroseptal | Sus_ST_Anterieur |
| BAV2_Mobitz1 | Onde_P_Bloquee, PR_Allonge |
| BAV2_Mobitz2 | Onde_P_Bloquee_Soudaine |
| FA | Absence_Onde_P, Rythme_Irregulier |
| BBG_Complet | QRS_Larges, Absence_Q_V5V6 |
| BBD | QRS_Larges, RSR_V1 |

---

## 🏷️ Étape 7 : Ajouter Synonymes

### **Pour chaque concept, ajouter `hasSynonym` :**

| Concept | Synonymes |
|---------|-----------|
| BAV2_Mobitz1 | "wenckebach", "bav2 m1", "luciani-wenckebach" |
| STEMI_Anteroseptal | "stemi antérieur", "imi antérieur", "sca st+ antérieur" |
| FA | "fa", "acfa", "fibrillation atriale" |

### **Création :**

1. Sélectionner concept
2. Onglet **Annotations**
3. **+** → `hasSynonym` (Data Property)
4. Ajouter chaque synonyme

---

## ✅ Étape 8 : Validation & Export

### **1. Vérifier cohérence :**

- **Reasoner** → Hermit ou Pellet
- **Start Reasoner**
- ✅ Pas d'incohérence = Ontologie valide

### **2. Exporter :**

- **File** → **Save As** → `data/ontologie.owx`
- Format : **OWL/XML**

### **3. Convertir en JSON :**

```bash
python backend/owl_to_json_converter.py
```

**Résultat** : `data/ontology_from_owl.json` prêt pour l'application

---

## 📊 Exemple Complet : NSTEMI

```owl
Class: NSTEMI
  SubClassOf: Diagnostic_Majeur
  
  Annotations:
    rdfs:label "NSTEMI"
    hasSynonym "infarctus non-st+", "sca non-st+", "imi non transmural"
    urgence "Hospitalisation USI, stratification risque <24h"
    note "⚠️ Pas de sus-ST mais troponines +"
  
  Object Properties:
    impliesSign Onde_T_Negative_Ischemique
  
  Data Properties:
    hasWeight 3 (integer)
```

---

## 🎯 Checklist Finale

Avant d'exporter, vérifier :

- [ ] Hiérarchie complète (Diagnostic/Signe/Descripteur)
- [ ] 5 territoires créés avec électrodes mappées
- [ ] Tous les concepts Epic 1 présents (28 concepts minimum)
- [ ] Poids (hasWeight) défini pour chaque concept
- [ ] Règles d'implication (impliesSign) créées
- [ ] Synonymes ajoutés aux diagnostics principaux
- [ ] Reasoner sans erreur
- [ ] Export .owx réussi

---

## 🚀 Utilisation Post-Export

Une fois `ontology_from_owl.json` généré :

```python
# Dans l'application
from pathlib import Path
import json

ontology_path = Path("data/ontology_from_owl.json")
with open(ontology_path) as f:
    ontology = json.load(f)

# Accès aux données
concepts = ontology["concept_mappings"]
territoires = ontology["territoires_ecg"]
poids_nstemi = concepts["nstemi"]["poids"]  # 3
```

---

## 💡 Conseils

✅ **Commencez simple** : 8 cas Epic 1 d'abord  
✅ **Validez médicalement** : Chaque territoire/poids doit être cliniquement juste  
✅ **Testez régulièrement** : Reasoner après chaque modification  
✅ **Documentez** : Annotations pour justifier choix médicaux  
✅ **Sauvegardez** : Versionnez l'ontologie (Git)

---

## 📚 Ressources

- **Protégé** : https://protege.stanford.edu/
- **OWL 2 Primer** : https://www.w3.org/TR/owl2-primer/
- **Tutoriel Protégé** : https://protegewiki.stanford.edu/wiki/Protege4UserDocs

---

**Auteur** : Dr. Grégoire + GitHub Copilot BMAD  
**Date** : 2026-01-10  
**Version** : 1.0
