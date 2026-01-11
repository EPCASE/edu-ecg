# 📝 Guide d'Annotation pour Cardiologue

**Objectif:** Créer 3-5 cas test annotés pour valider le POC LLM de correction automatique

**Durée estimée:** 20-30 min par cas → **1h30-2h30 total**

---

## 🎯 Principe de l'Annotation

Le système LLM compare la **réponse étudiant** avec vos **concepts attendus** annotés.

**Scoring:**
- Concept exact = 100 points
- Concept enfant (plus précis) = 85-90 points  
  *Ex: "BAV 1er degré" vs "BAV"*
- Concept parent (moins précis) = 60-80 points  
  *Ex: "Trouble conduction" vs "BAV 1er degré"*
- Concept voisin (même famille) = 40-60 points  
  *Ex: "BBG" vs "BBD"*
- Concept manquant = 0 point
- Contradiction = -20 points  
  *Ex: "Rythme sinusal" vs "Fibrillation auriculaire"*

**Pondération catégories:**
- Rhythm (rythme) = ×1.2
- Conduction = ×1.1
- Pathology (pathologie) = ×1.0
- Morphology (morphologie) = ×0.9
- Measurement (mesure) = ×0.8

---

## 📋 Étapes d'Annotation

### 1. Choisir 3-5 ECG Représentatifs

**Sélection recommandée (TOP 5 pathologies):**

✅ **Cas 1: Rythme Sinusal Normal**  
→ Baseline, niveau débutant

✅ **Cas 2: BAV 1er Degré**  
→ Trouble conduction simple, niveau intermédiaire

✅ **Cas 3: Fibrillation Auriculaire**  
→ Trouble rythme fréquent, niveau intermédiaire

✅ **Cas 4: Bloc de Branche Droit**  
→ Morphologie typique, niveau intermédiaire

✅ **Cas 5: STEMI Antérieur**  
→ Pathologie critique, niveau avancé

**Critères:**
- Couvrir 5 catégories (rhythm, conduction, morphology, measurement, pathology)
- Varier difficultés (beginner, intermediate, advanced)
- Préférer cas "typiques" vs "atypiques" pour POC

---

### 2. Préparer les Fichiers PDF

```bash
# Placer vos ECG PDF dans le dossier
ECG/
├── ECG1.pdf                    # Rythme sinusal normal (déjà présent)
├── bav1_exemple.pdf            # À ajouter
├── fa_exemple.pdf              # À ajouter
├── bbd_exemple.pdf             # À ajouter
└── stemi_anterieur.pdf         # À ajouter
```

**Format accepté:**
- PDF standard (1 page = 1 ECG)
- Résolution ≥ 150 DPI
- Taille < 5 MB

---

### 3. Annoter avec Template JSON

**Ouvrir:** `data/test_cases.json`

**Copier bloc template** pour chaque cas:

```json
{
  "case_id": "BAV1_001",
  "title": "BAV 1er Degré Simple",
  "category": "conduction",
  "difficulty": "intermediate",
  "description": "Bloc auriculo-ventriculaire du premier degré isolé",
  "pdf_path": "ECG/bav1_exemple.pdf",
  "expected_concepts": [
    {
      "text": "Rythme sinusal",
      "category": "rhythm"
    },
    {
      "text": "BAV 1er degré",
      "category": "conduction"
    },
    {
      "text": "PR > 200ms",
      "category": "measurement"
    },
    {
      "text": "PR constant",
      "category": "conduction"
    },
    {
      "text": "QRS fins",
      "category": "morphology"
    }
  ],
  "teaching_notes": "Critères BAV 1: PR > 200ms et constant. Différencier du BAV 2 Mobitz 1"
}
```

---

### 4. Remplir Champs Obligatoires

#### **case_id** (unique)
Format: `CATEGORIE_NNN`  
Exemples: `BAV1_001`, `FA_002`, `BBD_003`

#### **title** (court, descriptif)
✅ Bon: "BAV 1er Degré Simple"  
❌ Mauvais: "Bloc auriculo-ventriculaire du premier degré avec fréquence cardiaque normale et axe normal sans anomalie de repolarisation"

#### **category** (choisir 1 parmi 5)
- `rhythm` → Troubles du rythme (FA, Flutter, Tachycardie, etc.)
- `conduction` → Blocs (BAV, BBD, BBG, Hémiblocs)
- `morphology` → Anomalies morphologiques (Hypertrophie, Axe, QRS)
- `measurement` → Mesures (FC, PR, QT, QRS)
- `pathology` → Pathologies (STEMI, Péricardite, Embolie, etc.)

#### **difficulty** (choisir 1 parmi 3)
- `beginner` → DFASM2-3, cas typiques, diagnostics simples
- `intermediate` → DFASM3-Interne, cas fréquents, plusieurs anomalies
- `advanced` → Interne-Senior, cas complexes, diagnostics différentiels

#### **expected_concepts** (liste des concepts à trouver)

**Structure:**
```json
{
  "text": "Libellé exact du concept",
  "category": "rhythm|conduction|morphology|measurement|pathology"
}
```

**Règles:**
1. **Granularité:** Niveau attendu pour un étudiant de ce niveau
   - Beginner: "BAV" suffit
   - Intermediate: "BAV 1er degré" requis
   - Advanced: "BAV 1er degré d'origine nodal" attendu

2. **Nombre:** 3-8 concepts par cas
   - Trop peu (1-2) → Score facile à 100%
   - Trop (>10) → Score difficile, décourageant

3. **Catégories:** Varier les catégories
   - ✅ 1 rhythm + 2 conduction + 2 morphology + 1 measurement
   - ❌ 6 morphology seulement

4. **Formulation:** Utiliser vocabulaire médical standard
   - ✅ "Fibrillation auriculaire"
   - ❌ "FA" ou "ACFA" (abbréviations)
   - ✅ "PR > 200ms"
   - ❌ "Intervalle PR allongé au-delà de la normale"

---

### 5. Exemples Annotés Complets

#### **Exemple 1: Cas Simple (Beginner)**

```json
{
  "case_id": "RYTHME_SINUSAL_001",
  "title": "Rythme Sinusal Normal",
  "category": "rhythm",
  "difficulty": "beginner",
  "description": "ECG normal, tracé de référence",
  "pdf_path": "ECG/ECG1.pdf",
  "expected_concepts": [
    {"text": "Rythme sinusal", "category": "rhythm"},
    {"text": "Fréquence cardiaque normale", "category": "measurement"},
    {"text": "PR normal", "category": "measurement"},
    {"text": "QRS fins", "category": "morphology"},
    {"text": "Axe normal", "category": "morphology"},
    {"text": "Pas d'anomalie de repolarisation", "category": "morphology"}
  ],
  "teaching_notes": "Méthodologie systématique : Rythme → Fréquence → Conduction → Morphologie → Repolarisation"
}
```

**Réponse étudiant attendue (100%):**
> "ECG normal. Rythme sinusal à fréquence normale. PR et QRS dans les limites de la normale. Axe normal. Repolarisation normale."

---

#### **Exemple 2: Cas Intermédiaire (Intermediate)**

```json
{
  "case_id": "FA_001",
  "title": "Fibrillation Auriculaire Rapide",
  "category": "rhythm",
  "difficulty": "intermediate",
  "description": "FA à réponse ventriculaire rapide",
  "pdf_path": "ECG/fa_exemple.pdf",
  "expected_concepts": [
    {"text": "Fibrillation auriculaire", "category": "rhythm"},
    {"text": "Absence d'onde P", "category": "rhythm"},
    {"text": "Rythme irrégulier", "category": "rhythm"},
    {"text": "Réponse ventriculaire rapide", "category": "measurement"},
    {"text": "Fréquence > 100 bpm", "category": "measurement"},
    {"text": "QRS fins", "category": "morphology"}
  ],
  "teaching_notes": "FA = 3 critères obligatoires (absence P + irrégularité + QRS fins). Différencier rapide/lente/contrôlée"
}
```

**Réponse étudiant attendue (100%):**
> "Fibrillation auriculaire à réponse ventriculaire rapide. Absence d'ondes P, rythme totalement irrégulier. Fréquence ventriculaire environ 120 bpm. QRS fins."

**Réponse partielle (70%):**
> "Rythme irrégulier sans ondes P visibles. Fréquence rapide."  
→ Manque: diagnostic FA explicite, QRS fins, mesure précise

---

#### **Exemple 3: Cas Avancé (Advanced)**

```json
{
  "case_id": "STEMI_001",
  "title": "STEMI Antérieur",
  "category": "pathology",
  "difficulty": "advanced",
  "description": "IDM avec ST+ territoire antérieur - URGENCE",
  "pdf_path": "ECG/stemi_anterieur.pdf",
  "expected_concepts": [
    {"text": "STEMI", "category": "pathology"},
    {"text": "Sus-décalage ST", "category": "morphology"},
    {"text": "Territoire antérieur", "category": "pathology"},
    {"text": "Ondes Q de nécrose", "category": "morphology"},
    {"text": "Ondes T négatives", "category": "morphology"},
    {"text": "Atteinte V2-V3-V4", "category": "pathology"},
    {"text": "Urgence coronarienne", "category": "pathology"}
  ],
  "teaching_notes": "STEMI = URGENCE <120min. Critères: ST+ ≥2mm dans 2 dérivations contiguës précordiales. Territoire antérieur = IVA"
}
```

**Réponse attendue (100%):**
> "STEMI en territoire antérieur. Sus-décalage du segment ST ≥2mm en V2-V3-V4 avec ondes Q de nécrose débutantes et ondes T négatives. Urgence coronarienne absolue : angioplastie primaire à réaliser dans les 120 minutes."

---

## ✅ Validation de Vos Annotations

### Checklist Qualité

**Format JSON:**
- [ ] Fichier `data/test_cases.json` valide (pas d'erreur syntaxe)
- [ ] Virgules entre objets (sauf dernier)
- [ ] Guillemets doubles `"` partout

**Contenu:**
- [ ] 3-5 cas annotés minimum
- [ ] Tous champs obligatoires remplis (`case_id`, `title`, `category`, `difficulty`, `expected_concepts`)
- [ ] PDF existent dans dossier `ECG/`
- [ ] 3-8 concepts par cas
- [ ] Catégories variées dans `expected_concepts`
- [ ] Formulation concepts = vocabulaire médical standard

**Cohérence:**
- [ ] Difficulty match complexité (beginner = 3-5 concepts simples, advanced = 6-8 concepts précis)
- [ ] Category principale match concepts (cas "rhythm" → majoritairement concepts rhythm)
- [ ] Teaching_notes ajoutent valeur pédagogique

---

## 🧪 Tester Vos Annotations

### 1. Lancer POC

```bash
streamlit run frontend/correction_llm_poc.py
```

### 2. Sélectionner Cas

Dans sidebar → Choisir votre cas annoté

### 3. Simuler Réponse Étudiant

**Test 1: Réponse Parfaite (attendu ~95-100%)**
Recopier tous vos `expected_concepts.text` dans zone réponse

**Test 2: Réponse Partielle (attendu ~60-70%)**
Omettre 2-3 concepts

**Test 3: Réponse Erronée (attendu ~20-40%)**
Inverser 1-2 diagnostics (ex: "BBG" au lieu de "BBD")

### 4. Vérifier Résultats

✅ **Score cohérent** avec qualité réponse  
✅ **Feedback pédagogique** bienveillant et constructif  
✅ **Concepts manquants** bien identifiés  
✅ **Pas de crash** ou erreur technique

---

## 📊 Métriques Cibles POC

**Semaine 1 (3-5 cas):**
- Precision > 70% (concepts identifiés corrects)
- Recall > 70% (concepts attendus trouvés)
- F1-Score > 70%
- Feedback jugé "utile" par vous (subjectif)

**Semaine 2 (10 cas):**
- F1-Score > 75%
- Temps réponse < 3s
- Démo formelle avec collègues cardio

**Production (30+ cas):**
- F1-Score > 80%
- Validation par 10 étudiants

---

## 🚀 Après Annotation

### Actions Immédiates

1. **Tester POC** avec vos 3-5 cas
2. **Ajuster prompts** si feedback pas assez pédagogique
3. **Tuner scoring** si scores incohérents
4. **Documenter observations** (fichier texte notes libres)

### Semaine 2 (Optionnel)

5. **Annoter 5 cas supplémentaires** (total 10)
6. **Calculer métriques** Precision/Recall/F1
7. **Démo informelle** avec 2 collègues cardio

### Semaine 3-4

8. **Backend PostgreSQL** pour sauvegarder corrections
9. **Module progression** long-terme par étudiant
10. **Test avec 10 étudiants DFASM2**

---

## 💡 Conseils Pratiques

### ⏱️ Gagner du Temps

- Commencer par cas que vous connaissez bien
- Utiliser template (copier-coller bloc)
- Annoter 1 cas → tester → ajuster méthode → annoter reste

### 🎯 Qualité > Quantité

- **3 cas bien annotés** > 10 cas bâclés
- Privilégier cas **typiques** vs cas **rares** pour POC
- Si doute formulation → **vocabulaire le plus courant**

### 🔄 Itération

- Annotations pas gravées dans marbre
- Ajuster après tests si scores incohérents
- Ajouter concepts oubliés après feedback étudiants

---

## ❓ FAQ

**Q: Combien de temps par cas ?**  
R: 20-30 min si ECG familier, 40-60 min si révision nécessaire

**Q: Dois-je annoter les valeurs exactes (ex: "PR = 220ms") ?**  
R: Non, "PR > 200ms" suffit. Le système n'extrait pas valeurs numériques précises (POC).

**Q: Que faire si plusieurs diagnostics possibles ?**  
R: Choisir diagnostic le plus probable. Ajouter alternatives dans `teaching_notes`.

**Q: Puis-je utiliser abréviations (FA, BBD, IDM) ?**  
R: Non, vocabulaire complet ("Fibrillation auriculaire", "Bloc de branche droit", "Infarctus du myocarde")

**Q: Combien de concepts minimum/maximum ?**  
R: Minimum 3, maximum 10. Recommandé: 5-7 pour intermediate.

**Q: Dois-je annoter tous les détails (ex: axe QRS précis) ?**  
R: Annoter ce qu'un étudiant de ce niveau **doit** identifier. Pas tous les détails exhaustifs.

---

## 📧 Support

**Problèmes techniques:**
- Erreur JSON → Utiliser validateur en ligne (jsonlint.com)
- POC ne démarre pas → Vérifier `OPENAI_API_KEY` dans `.env`
- Scoring incohérent → Documenter cas précis + résultat attendu vs obtenu

**Questions pédagogiques:**
- Granularité concepts → Adapter au niveau difficulty
- Formulation → Utiliser termes cours ECG standard CHU

---

**Durée totale annotation:** 1h30-2h30 pour 3-5 cas  
**Prochaine étape:** Tester POC et valider feedback LLM

🫀 **Bon courage !**
