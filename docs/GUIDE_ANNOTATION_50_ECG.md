# 📋 Guide d'Annotation - 50 ECG pour Dataset

**Objectif :** Constituer un dataset de 50 ECG annotés de qualité pour collecter 5000 réponses étudiants

**Temps estimé :** 50 × 20min = ~17 heures (4 semaines à 4h/semaine)

**Annotateur :** Dr. Grégoire (Cardiologue)

---

## 🎯 Répartition des Cas (50 ECG)

### **Niveau 1 - Facile (10 cas)** 🟢
*Cible : DFASM2, score attendu >80%*

| # | Pathologie | Concepts clés | Difficulté |
|---|------------|---------------|------------|
| 1 | Rythme sinusal normal | ✅ Fait (RYTHME_SINUSAL_001) | ⭐ |
| 2 | Rythme sinusal + tachycardie | Rythme, FC élevée | ⭐ |
| 3 | Rythme sinusal + bradycardie | Rythme, FC basse | ⭐ |
| 4 | Rythme sinusal + axe gauche | Rythme, axe dévié | ⭐ |
| 5 | Rythme sinusal + axe droit | Rythme, axe dévié | ⭐ |
| 6 | Extrasystoles auriculaires | Rythme, ESA | ⭐⭐ |
| 7 | Extrasystoles ventriculaires | Rythme, ESV | ⭐⭐ |
| 8 | PR limite (0.20s) | Conduction normale limite | ⭐ |
| 9 | QT normal limite | Mesures normales limites | ⭐ |
| 10 | Variante normale du jeune | Repolarisation précoce | ⭐⭐ |

### **Niveau 2 - Intermédiaire (20 cas)** 🟡
*Cible : DFASM3, score attendu 60-80%*

| # | Pathologie | Concepts clés | Difficulté |
|---|------------|---------------|------------|
| 11 | BAV 1er degré | Conduction, PR allongé | ⭐⭐ |
| 12 | BAV 2 Mobitz I (Wenckebach) | Conduction, PR variable | ⭐⭐⭐ |
| 13 | Bloc de branche droit (BBD) | Conduction, QRS larges | ⭐⭐ |
| 14 | Bloc de branche gauche (BBG) | Conduction, QRS larges | ⭐⭐ |
| 15 | Hémibloc antérieur gauche (HAG) | Conduction, axe gauche | ⭐⭐⭐ |
| 16 | Fibrillation auriculaire (FA) | Rythme irrégulier, pas d'onde P | ⭐⭐ |
| 17 | FA rapide | Rythme irrégulier, FC élevée | ⭐⭐ |
| 18 | Flutter auriculaire 2/1 | Rythme régulier, ondes F | ⭐⭐⭐ |
| 19 | Hypertrophie ventriculaire gauche (HVG) | Morphologie, voltage élevé | ⭐⭐ |
| 20 | Hypertrophie ventriculaire droite (HVD) | Morphologie, axe droit | ⭐⭐⭐ |
| 21 | QT long congénital | Mesures, QT >480ms | ⭐⭐ |
| 22 | QT court | Mesures, QT <340ms | ⭐⭐⭐ |
| 23 | Ischémie antérieure | Pathologie, ondes T négatives | ⭐⭐⭐ |
| 24 | Ischémie inférieure | Pathologie, ondes T en V5-V6 | ⭐⭐⭐ |
| 25 | Onde epsilon (dysplasie VD) | Morphologie rare | ⭐⭐⭐⭐ |
| 26 | Syndrome de Wolff-Parkinson-White | Conduction, onde delta | ⭐⭐⭐ |
| 27 | Syndrome de Brugada type 1 | Pathologie, sus-ST V1-V2 | ⭐⭐⭐⭐ |
| 28 | Péricardite aiguë | Pathologie, sus-ST diffus | ⭐⭐ |
| 29 | Hyperkaliémie modérée | Morphologie, T amples | ⭐⭐⭐ |
| 30 | Hypokaliémie | Morphologie, onde U | ⭐⭐⭐ |

### **Niveau 3 - Avancé (15 cas)** 🔴
*Cible : Internes, score attendu 40-60%*

| # | Pathologie | Concepts clés | Difficulté |
|---|------------|---------------|------------|
| 31 | STEMI antérieur aigu | Pathologie, sus-ST V1-V4, onde Q | ⭐⭐⭐⭐ |
| 32 | STEMI inférieur | Pathologie, sus-ST DII-DIII-aVF | ⭐⭐⭐⭐ |
| 33 | STEMI latéral | Pathologie, sus-ST V5-V6-DI-aVL | ⭐⭐⭐⭐ |
| 34 | STEMI postérieur | Pathologie, onde R en V1-V2 | ⭐⭐⭐⭐⭐ |
| 35 | Infarctus séquellaire antérieur | Pathologie, onde Q sans sus-ST | ⭐⭐⭐ |
| 36 | BAV 2 Mobitz II | Conduction, PR fixe + QRS manquants | ⭐⭐⭐⭐ |
| 37 | BAV 3 (complet) | Conduction, dissociation AV | ⭐⭐⭐⭐ |
| 38 | Tachycardie ventriculaire | Rythme, QRS larges rapides | ⭐⭐⭐⭐ |
| 39 | Torsades de pointes | Rythme, QRS torsadés | ⭐⭐⭐⭐⭐ |
| 40 | BBG + STEMI (critère Sgarbossa) | Combinaison difficile | ⭐⭐⭐⭐⭐ |
| 41 | FA + BBG (rythme irrégulier + QRS larges) | Combinaison complexe | ⭐⭐⭐⭐ |
| 42 | Hyperkaliémie sévère (QRS larges) | Urgence vitale | ⭐⭐⭐⭐ |
| 43 | Embolie pulmonaire (S1Q3T3) | Signes indirects | ⭐⭐⭐⭐ |
| 44 | Hypothermie (onde d'Osborn) | Morphologie rare | ⭐⭐⭐⭐⭐ |
| 45 | Cardiomyopathie hypertrophique | Pathologie, voltage + T négatives | ⭐⭐⭐⭐ |

### **Niveau 4 - Pièges (5 cas)** 🟣
*Cible : Test robustesse système*

| # | Pathologie | Piège | Difficulté |
|---|------------|-------|------------|
| 46 | Repolarisation précoce vs STEMI | Différenciation cruciale | ⭐⭐⭐⭐⭐ |
| 47 | BBD + HVG | 2 anomalies simultanées | ⭐⭐⭐⭐ |
| 48 | Pace-maker ventriculaire | Spike + QRS larges | ⭐⭐⭐⭐ |
| 49 | Dextrocardie | Inversion toutes dérivations | ⭐⭐⭐⭐⭐ |
| 50 | Artefacts massifs (tremblements) | Qualité technique | ⭐⭐ |

---

## 📝 Template d'Annotation (Copier pour chaque cas)

### **Cas #__ : [NOM_PATHOLOGIE]**

**Fichier ECG :** `ECG/ECG_[NUMERO].pdf`

**Date annotation :** __________

**Difficulté :** ⭐ (1-5 étoiles)

**Niveau cible :** ☐ DFASM2  ☐ DFASM3  ☐ Interne

---

#### 1️⃣ Concepts Attendus (Gold Standard)

```json
{
  "case_id": "ECG_[NUMERO]",
  "title": "[Titre descriptif]",
  "difficulty": "[facile|intermediaire|avance|piege]",
  "target_level": "[DFASM2|DFASM3|Interne]",
  "expected_concepts": [
    {
      "text": "rythme sinusal",
      "category": "rhythm",
      "importance": "critique",
      "points": 20
    },
    {
      "text": "fréquence cardiaque normale",
      "category": "measurement",
      "importance": "important",
      "points": 15
    }
    // ... ajouter tous les concepts
  ],
  "total_points": 100,
  "learning_objectives": [
    "Identifier le rythme de base",
    "Mesurer les intervalles PR et QT",
    "Détecter les anomalies de conduction"
  ]
}
```

**Nombre total concepts :** _____ (recommandé 4-8)

---

#### 2️⃣ Réponse Modèle (Expert)

*Ce que dirait un cardiologue senior :*

```
_______________________________________________
_______________________________________________
_______________________________________________
```

*(Servira de référence pour évaluer qualité des feedbacks)*

---

#### 3️⃣ Réponse Typique DFASM2

*Ce que dirait un étudiant de 4ème année :*

```
_______________________________________________
_______________________________________________
```

**Score attendu :** _____ %

---

#### 4️⃣ Réponse Typique DFASM3

*Ce que dirait un étudiant de 5ème année :*

```
_______________________________________________
_______________________________________________
```

**Score attendu :** _____ %

---

#### 5️⃣ Erreurs Fréquentes Anticipées

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

---

#### 6️⃣ Synonymes Acceptables

*Variantes d'expression équivalentes :*

| Concept Gold Standard | Synonymes acceptés |
|----------------------|-------------------|
| "rythme sinusal" | "rythme régulier", "activité sinusale" |
| | |
| | |

---

#### 7️⃣ Pièges à Éviter

☐ Confusion avec : _______________________________  
☐ Oubli fréquent de : ____________________________  
☐ Sur-interprétation de : _________________________

---

#### 8️⃣ Feedback Pédagogique Clé

*Points essentiels à mentionner dans feedback IA :*

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

---

#### 9️⃣ Validation Qualité

- [ ] ECG de bonne qualité (lisible)
- [ ] Tous les concepts gold standard listés
- [ ] Réponse modèle rédigée
- [ ] Synonymes identifiés
- [ ] Pièges documentés
- [ ] JSON valide (testé dans POC)

**Temps annotation :** _____ minutes

**Notes :** _______________________________________

---

## 🔄 Workflow d'Annotation

```
1. Sélectionner ECG (scanner ou base existante)
   ↓
2. Ouvrir template annotation
   ↓
3. Analyser ECG (5 min)
   ↓
4. Lister concepts gold standard (5 min)
   ↓
5. Rédiger réponse modèle (3 min)
   ↓
6. Identifier synonymes (2 min)
   ↓
7. Documenter pièges (3 min)
   ↓
8. Créer fichier JSON (2 min)
   ↓
9. Tester dans POC (2 min)
   ↓
10. Valider & archiver (1 min)
```

**Total par ECG :** ~20-25 minutes

---

## 📊 Suivi Progression

| Semaine | Objectif | Réalisé | Cumul |
|---------|----------|---------|-------|
| S1 | 10 faciles | _____ | _____ / 50 |
| S2 | 15 intermédiaires | _____ | _____ / 50 |
| S3 | 15 avancés | _____ | _____ / 50 |
| S4 | 10 restants + pièges | _____ | 50 / 50 ✅ |

---

## 🎯 Critères de Qualité

**Un ECG annoté est VALIDÉ si :**

1. ✅ **Complet :** 4-8 concepts gold standard
2. ✅ **Précis :** Réponse modèle cardiologue rédigée
3. ✅ **Pédagogique :** Erreurs fréquentes anticipées
4. ✅ **Robuste :** ≥3 synonymes par concept principal
5. ✅ **Testé :** JSON chargé dans POC sans erreur
6. ✅ **Documenté :** Pièges et learning objectives clairs

---

## 📁 Organisation Fichiers

```
data/
├── ecg_cases/
│   ├── ECG_001_rythme_sinusal.json ✅
│   ├── ECG_002_tachycardie_sinusale.json
│   ├── ECG_003_bradycardie_sinusale.json
│   └── ... (jusqu'à 050)
│
ECG/
├── ECG_001.pdf ✅
├── ECG_002.pdf
└── ... (fichiers source)
```

---

## 🚀 Prochaines Étapes

**Après 50 ECG annotés :**

1. ✅ Import dans POC (batch)
2. ✅ Validation croisée (2ème cardiologue si possible)
3. ✅ **PHASE 3** : Collecte réponses 100 étudiants
4. ✅ Mining synonymes automatique
5. ✅ Fine-tuning système

---

**Version :** 1.0  
**Auteur :** Dr. Grégoire + GitHub Copilot  
**Date :** 2026-01-10
