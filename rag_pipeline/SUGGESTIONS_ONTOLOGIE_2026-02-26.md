# 🩺 Suggestions d'Annotations Manuelles — Ontologie ECG

**Date** : 26 février 2026  
**Source** : Benchmark RAG Neurosymbolique — Score actuel : **48.9%**  
**Fichier cible** : `ECG lecture/data/ontology_from_owl.json` → section `concept_mappings`  
**Action post-modification** : Relancer `ontology_index.py` pour reconstruire `rag_index/`

---

## 📊 Constat Global

| Métrique | Valeur |
|----------|--------|
| Concepts dans le JSON actuel (obsolète) | 280 |
| Concepts dans l'OWL (source de vérité) | **289** |
| **Concepts manquants** (OWL → JSON) | **12** (dont MICROVOLTAGE !) |
| Concepts avec synonymes | 64 (23%) |
| Concepts **sans** synonymes | 216 (77%) |
| Concepts poids ≥ 4 sans synonymes | 17 / 24 (71%) |
| Concepts poids = 3 sans synonymes | 51 / 70 (73%) |
| Concepts poids = 2 sans synonymes | 37 / 49 (76%) |

> ⚠️ **77% des concepts n'ont que leur nom canonique dans l'index** — pas de synonyme, pas d'abréviation, pas de variante courante. Le RAG ne peut matcher que si l'étudiant écrit *exactement* le nom ontologique.

---

## 🚨 PRIORITÉ 0 — Régénérer `ontology_from_owl.json` depuis l'OWL

### Le JSON est obsolète !

Le fichier `ontology_from_owl.json` (280 concepts) est **désynchronisé** de la source OWL `BrYOzRZIu7jQTwmfcGsi35.owl` (289 concepts). **12 concepts manquent** dont MICROVOLTAGE :

| Concept manquant | Catégorie | Poids |
|---|---|---|
| **MICROVOLTAGE** | DIAGNOSTIC_MAJEUR | **3** |
| **ESV_MONOMORPHE** | SIGNE_ECG_PATHOLOGIQUE | **2** |
| BRADYCARDIE | DESCRIPTEUR_ECG | 1 |
| ONDE_T_AMPLE | DESCRIPTEUR_ECG | 1 |
| RYTHME_RÉGULIER | DESCRIPTEUR_ECG | 1 |
| BRANCHE_DROITE | DESCRIPTEUR_ECG | 1 |
| BRANCHE_GAUCHE | DESCRIPTEUR_ECG | 1 |
| HÉMI_BRANCHE_ANTÉRIEURE_DROITE | DESCRIPTEUR_ECG | 1 |
| HÉMI_BRANCHE_ANTÉRIEURE_GAUCHE | DESCRIPTEUR_ECG | 1 |
| RÉSEAU_DE_PURKINJE | DESCRIPTEUR_ECG | 1 |
| BANDELETTE_MODÉRATRICE | DESCRIPTEUR_ECG | 1 |
| INFÉRIEUR | DESCRIPTEUR_ECG | 1 |

3 concepts renommés/supprimés dans l'OWL :
- `FLUTTER_ATRIAL` → ⚠️ **DISPARU** — vérifier si renommé dans WebProtégé
- `RHYTME_RÉGULIER` → corrigé en `RYTHME_RÉGULIER`
- `ESV_ATYPIQUE_DE_LA_CCVD` → supprimé

### ⚠️ Action : Régénérer AVEC PRÉCAUTION

> **ATTENTION** : `regenerate_ontology.py` écrase les synonymes manuels ! Le script fusionne avec `epic1_ontology_mapping.json` (s'il existe), mais les synonymes ajoutés manuellement directement dans `ontology_from_owl.json` seront **perdus**.
>
> **Procédure recommandée** :
> 1. D'abord ajouter les synonymes manuels (Priorité 2 ci-dessous) dans `ontology_from_owl.json`
> 2. Puis régénérer en sauvegardant les synonymes existants
> 3. Ou bien : régénérer d'abord, puis ajouter les synonymes après

### MICROVOLTAGE — Synonymes à ajouter après régénération

Microvoltage existe dans l'OWL (poids=3, DIAGNOSTIC_MAJEUR, label_en="Low amplitude QRS") mais sera généré avec `"synonymes": []`. Ajouter :

```json
"MICROVOLTAGE": {
  "synonymes": [
    "Bas voltage",
    "Low voltage",
    "Low amplitude QRS",
    "QRS de faible amplitude",
    "Microvoltage diffus",
    "Voltage diminué"
  ]
}
```

### FLUTTER_ATRIAL — Concept disparu ?

⚠️ `FLUTTER_ATRIAL` (poids=3, DIAGNOSTIC_MAJEUR) existe dans le JSON actuel mais **n'est plus généré** par l'extracteur OWL. Vérifier dans WebProtégé s'il a été renommé ou fusionné. **Ce concept a 2 synonymes importants à préserver (FA, AFL si ajoutés).**

> Si le concept a été supprimé de l'OWL, il faudra le **ré-ajouter manuellement** dans le JSON après régénération.

---

## 🔴 PRIORITÉ 1 — Concepts du Golden Set sans Synonymes (Impact Benchmark Direct)

Ces concepts apparaissent dans les 15 cas du benchmark. Chaque synonyme ajouté améliore directement le score.

### 2.1 — VALIDANTS (comptent dans le score) — Poids ≥ 3

| Concept | Poids | Catégorie | Cas | Synonymes suggérés |
|---------|-------|-----------|-----|-------------------|
| **FLUTTER_DROIT_TYPIQUE** | 3 | DIAGNOSTIC_MAJEUR | 8 | `"Flutter commun"`, `"Flutter typique"`, `"Typical atrial flutter"`, `"Flutter isthmique"`, `"Flutter isthmus-dependent"` |
| **FAISCEAU_ACCESSOIRE_À_CONDUCTION_ANTÉROGRADE** | 3 | DIAGNOSTIC_MAJEUR | 13 | `"Faisceau accessoire"`, `"Voie accessoire"`, `"Accessory pathway"`, `"Pré-excitation"`, `"Kent bundle"`, `"Faisceau de Kent"` |
| **ECG_NORMAL** | 3 | DIAGNOSTIC_MAJEUR | 1 | `"ECG sans anomalie"`, `"Tracé normal"`, `"Normal ECG"`, `"Pas d'anomalie"`, `"ECG physiologique"` |
| **BAV_DE_HAUT_GRADE** | 3 | DIAGNOSTIC_MAJEUR | 5 | `"BAV haut degré"`, `"High-grade AV block"`, `"BAV avancé"`, `"BAV de haut degré"` |
| **BAV_2_MOBITZ_2** | 4 | DIAGNOSTIC_URGENT | 9 | `"BAV 2:1"`, `"Mobitz II"`, `"BAV de type 2 Mobitz 2"`, `"Second degree AV block type 2"`, `"BAV2M2"` |
| **HYPERKALIÉMIE** | 4 | DIAGNOSTIC_URGENT | 5 | `"Hyperkaliemie"`, `"Hyperkalemia"`, `"Hyperpotassémie"`, `"Potassium élevé"`, `"K+ élevé"` |
| **TACHYCARDIE_VENTRICULAIRE** | 4 | DIAGNOSTIC_URGENT | 11 | `"TV"`, `"VT"`, `"Tachy V"`, `"Ventricular tachycardia"`, `"Tachycardie V"` |

### 2.2 — VALIDANTS — Poids ≤ 2

| Concept | Poids | Catégorie | Cas | Synonymes suggérés |
|---------|-------|-----------|-----|-------------------|
| **STIMULATION_ATRIALE** | 1 | DESCRIPTEUR_ECG | 6 | `"Pacing atrial"`, `"Atrial pacing"`, `"Stimulation auriculaire"`, `"Pace atrial"`, `"AAI"` |
| **RYTHME_SINUSAL** | 2 | SIGNE_ECG_PATHOLOGIQUE | 10 | `"RS"`, `"Sinusal"`, `"Sinus rhythm"`, `"Rythme régulier sinusal"`, `"NSR"` |

### 2.3 — DESCRIPTEURS (ne comptent pas directement mais complètent le diagnostic)

| Concept | Poids | Catégorie | Cas | Synonymes suggérés |
|---------|-------|-----------|-----|-------------------|
| **AMYLOSE** | 3 | DIAGNOSTIC_MAJEUR | 4 | `"Amyloïdose"`, `"Amyloidosis"`, `"Amylose cardiaque"`, `"Cardiac amyloidosis"` |
| **ECHAPPEMENT_VENTRICULAIRE** | 1 | DESCRIPTEUR_ECG | 2 | `"Rythme d'échappement ventriculaire"`, `"Ventricular escape"`, `"Échappement V"`, `"Rythme idioventriculaire"` |

---

## 🟠 PRIORITÉ 2 — Diagnostics Critiques (Poids ≥ 4) sans Synonymes

Ces concepts ne sont pas dans le golden set actuel mais sont des **urgences vitales**. Quand un étudiant les mentionne avec une variante, le pipeline rate.

| Concept | Synonymes suggérés |
|---------|-------------------|
| **ASYSTOLIE** | `"Asystole"`, `"Flat line"`, `"Ligne plate"`, `"Absence d'activité électrique"` |
| **EMBOLIE_PULMONAIRE** | `"EP"`, `"PE"`, `"Pulmonary embolism"`, `"Embolie pulm"` |
| **EXTRASYSTOLE_À_COUPLAGE_COURT** | `"ESV à couplage court"`, `"Short-coupled PVC"`, `"R sur T"`, `"R on T"` |
| **ISCHÉMIE_SOUS_ENDOCARDIQUE** | `"Ischémie sous-endo"`, `"Subendocardial ischemia"`, `"Ischémie sous endocardique"` |
| **TACHYCARDIE_PAR_RÉENTRÉE_DE_BRANCHE_À_BRANCHE** | `"Bundle branch reentry"`, `"BBR"`, `"TV par réentrée de branche"` |
| **TACHYCARDIE_VENTRICULAIRE_BIDIRECTIONNELLE** | `"TV bidirectionnelle"`, `"Bidirectional VT"` |
| **TACHYCARDIE_VENTRICULAIRE_CATHÉCHOLAMINERGIQUE** | `"TVPC"`, `"CPVT"`, `"TV catécholaminergique"`, `"TV polymorphe catécholaminergique"` |
| **TAMPONNADE** | `"Tamponade"`, `"Cardiac tamponade"`, `"Tamponnade cardiaque"` |
| **TORSADE_DE_POINTES** | `"TdP"`, `"Torsades"`, `"Torsade de pointe"`, `"Torsades de pointes"` |
| **FIBRILLATION_VENTRICULAIRE** | `"FV"`, `"VF"`, `"V-fib"`, `"Ventricular fibrillation"` |
| **ALTERNANCE_DES_QRS** | `"Alternance électrique"`, `"Electrical alternans"`, `"QRS alternans"` |
| **STIMULATION_DANS_L'ONDE_T** | `"Pacing sur onde T"`, `"T-wave pacing"`, `"Spike dans l'onde T"` |
| **CARDIOVERSION_ÉLECTRIQUE** | `"Choc électrique"`, `"DC shock"`, `"Cardioversion"`, `"CEE"` |

---

## 🟡 PRIORITÉ 3 — Diagnostics Majeurs (Poids = 3) sans Synonymes

| Concept | Synonymes suggérés |
|---------|-------------------|
| **FLUTTER_ATRIAL** | `"Flutter auriculaire"`, `"AFL"`, `"Atrial flutter"`, `"Flutter"` |
| **FLUTTER_ATRIAL_ATYPIQUE** | `"Flutter atypique"`, `"Atypical flutter"`, `"Flutter non isthmique"` |
| **FLUTTER_ATRIAL_ANTIHORAIRE_DÉPENDANT_DE_L'ICT** | `"Flutter antihoraire"`, `"CCW flutter"`, `"Flutter typique antihoraire"` |
| **FLUTTER_ATRIAL_HORAIRE_DÉPENDANT_DE_L'ICT** | `"Flutter horaire"`, `"CW flutter"`, `"Reverse typical flutter"` |
| **ASPECT_DE_BRUGADA_DE_TYPE_1** | `"Brugada type 1"`, `"Aspect en dôme"`, `"Coved-type Brugada"` |
| **ASPECT_DE_BRUGADA_DE_TYPE_2** | `"Brugada type 2"`, `"Saddleback Brugada"` |
| **SYNDROME_DE_BRUGADA** | `"Brugada"`, `"Brugada syndrome"` |
| **SYNDROME_DU_QT_LONG** | `"QT long"`, `"LQTS"`, `"Long QT"`, `"Syndrome du QT prolongé"` |
| **SYNDROME_DE_REPOLARISATION_PRÉCOCE** | `"Repolarisation précoce pathologique"`, `"Early repolarization syndrome"`, `"ERS pathologique"` |
| **BAV_2_MOBITZ_1** | `"Wenckebach"`, `"BAV 2 type 1"`, `"Mobitz I"`, `"Luciani-Wenckebach"`, `"Second degree AV block type 1"` |
| **PERICARDITE** | `"Péricardite"`, `"Pericarditis"`, `"Péricardite aiguë"` |
| **ANÉVRYSME_VENTRICULAIRE** | `"Anévrisme ventriculaire"`, `"Ventricular aneurysm"`, `"Anévrisme du VG"` |
| **CARDIOMYOPATHIE_HYPERTROPHIQUE** | `"CMH"`, `"HCM"`, `"Hypertrophic cardiomyopathy"`, `"Cardio hypertrophique"` |
| **CARDIOMYOPATHIE_HYPERTROPHIQUE_APICALE** | `"CMH apicale"`, `"Yamaguchi"`, `"Apical HCM"` |
| **DYSPLASIE_ARRHYTHMOGÈNE_DU_VENTRICULE_DROIT** | `"DAVD"`, `"ARVC"`, `"ARVD"`, `"Dysplasie VD"` |
| **DYSFONCTION_SINUSALE** | `"Maladie du sinus"`, `"Sick sinus syndrome"`, `"SSS"`, `"Maladie de l'oreillette"` |
| **PARALYSIE_SINUSALE** | `"Arrêt sinusal"`, `"Sinus arrest"`, `"Pause sinusale"` |
| **HYPERTROPHIE_VENTRICULAIRE_DROITE** | `"HVD"`, `"RVH"`, `"Right ventricular hypertrophy"` |
| **DIGITALIQUES** | `"Digoxine"`, `"Digitale"`, `"Digitalis"` |
| **IMPRÉGNATION_DIGITALIQUE** | `"Effet digitalique"`, `"Cupule digitalique"`, `"Digitalis effect"` |
| **INTOXICATION_DIGITALIQUE** | `"Surdosage digitalique"`, `"Digitalis toxicity"`, `"Intoxication à la digoxine"` |
| **TACHYCARDIE_JONCTIONELLE** | `"TJ"`, `"Junctional tachycardia"`, `"Tachycardie jonctionnelle"` |
| **TACHYCARDIE_JONCTIONNELLE_PAR_RÉENTRÉE_INTRA_NODALE** | `"RIN"`, `"AVNRT"`, `"Réentrée intra-nodale"`, `"Réentrée nodale"` |
| **TACHYCARDIE_ATRIALE_FOCALE** | `"TAF"`, `"Focal atrial tachycardia"`, `"TA focale"` |
| **HYPERKALIÉMIE** | *(voir Priorité 2 — déjà listé)* |
| **HYPOKALIÉMIE** | `"Hypokalemia"`, `"Hypopotassémie"`, `"K+ bas"`, `"Potassium bas"` |
| **HYPERCALCÉMIE** | `"Hypercalcemia"`, `"Calcium élevé"`, `"Ca++ élevé"` |
| **HYPOCALCÉMIE** | `"Hypocalcemia"`, `"Calcium bas"`, `"Ca++ bas"` |
| **QT_COURT** | `"Short QT"`, `"SQTS"`, `"QT raccourci"` |
| **ECG_NORMAL** | *(voir Priorité 2 — déjà listé)* |
| **AMYLOSE** | *(voir Priorité 2 — déjà listé)* |
| **HYPOTHERMIE** | `"Hypothermic ECG"`, `"Hypothermia"` |

---

## ⚪ PRIORITÉ 4 — Signes ECG Pathologiques (Poids = 2) sans Synonymes

> Ces concepts sont moins critiques pour le score mais améliorent le matching pour les descriptions fines.

| Concept | Synonymes suggérés |
|---------|-------------------|
| **RYTHME_SINUSAL** | *(voir Priorité 2)* |
| **EXTRASYSTOLE_ATRIALE** | `"ESA"`, `"PAC"`, `"Premature atrial contraction"`, `"Extrasystole auriculaire"` |
| **EXTRASYSTOLE_ATRIALE_BIGÉMINÉE** | `"Bigéminisme auriculaire"`, `"ESA bigéminée"`, `"Bigeminal PACs"` |
| **HYPERTROPHIE_ATRIALE_DROITE** | `"HAD"`, `"RAE"`, `"P pulmonaire"`, `"Right atrial enlargement"` |
| **HYPERTROPHIE_ATRIALE_GAUCHE** | `"HAG"`, `"LAE"`, `"P mitrale"`, `"Left atrial enlargement"` |
| **TACHYCARDIE_ATRIALE** | `"TA"`, `"Atrial tachycardia"`, `"Tachycardie auriculaire"` |
| **TACHYCARDIE_VENTRICULAIRE_POLYMORPHE** | `"TV polymorphe"`, `"Polymorphic VT"`, `"PMVT"` |
| **SÉQUELLE_DE_NÉCROSE** | `"Onde Q pathologique"`, `"Nécrose myocardique"`, `"Old MI"`, `"Séquelle d'IDM"` |
| **BIGEMINISME_VENTRICULAIRE** | `"Bigéminisme ESV"`, `"Ventricular bigeminy"` |
| **CAPTURE_SUPRAVENTRICULAIRE** | `"Capture sinusale"`, `"Sinus capture beat"` |
| **INVERSION_D'ÉLECTRODES** | `"Électrodes inversées"`, `"Lead reversal"`, `"Inversion de dérivations"` |
| **ARYTHMIE_SINUSALE** | `"Arythmie respiratoire"`, `"Sinus arrhythmia"`, `"Arythmie sinusale respiratoire"` |
| **ONDE_J_D'OSBORN** | `"Onde J"`, `"Osborn wave"`, `"J wave"`, `"Onde d'Osborn"` |
| **ABERRATION_VENTRICULAIRE** | `"Conduction aberrante"`, `"Aberrant conduction"` |
| **EFFET_CHATTERJEE** | `"Mémoire cardiaque"`, `"Cardiac memory"`, `"Chatterjee effect"` |
| **VOIE_LENTE** | `"Slow pathway"`, `"Voie nodale lente"` |
| **RYTHME_ATRIAL_ECTOPIQUE** | `"Rythme ectopique auriculaire"`, `"Ectopic atrial rhythm"`, `"Rythme atrial non sinusal"` |
| **PERTE_DE_CAPTURE_ATRIALE** | `"Défaut de capture atriale"`, `"Atrial loss of capture"`, `"Pacing atrial inefficace"` |

---

## 📋 Mode d'Emploi

### Étape 1 — Modifier `ontology_from_owl.json`

Pour chaque concept listé ci-dessus, modifier le champ `"synonymes"` dans la section `concept_mappings` :

```json
// AVANT
"FLUTTER_DROIT_TYPIQUE": {
  "concept_name": "Flutter droit typique",
  "synonymes": [],
  ...
}

// APRÈS
"FLUTTER_DROIT_TYPIQUE": {
  "concept_name": "Flutter droit typique",
  "synonymes": [
    "Flutter commun",
    "Flutter typique",
    "Typical atrial flutter",
    "Flutter isthmique",
    "Flutter isthmus-dependent"
  ],
  ...
}
```

Pour **MICROVOLTAGE** : ajouter à la fois dans `concept_categories.SIGNE_ECG_PATHOLOGIQUE.concepts` ET dans `concept_mappings`.

### Étape 2 — Reconstruire l'index RAG

```bash
cd "C:\Users\Administrateur\bmad\RAG ontologique"
python ontology_index.py
```

Cela régénère `rag_index/vecteurs_ontologie.npy` et `rag_index/metadata_ontologie.json` avec les nouveaux synonymes.

### Étape 3 — Re-exécuter le benchmark

Dans le notebook `benchmark_evaluation.ipynb`, relancer les cellules 1 à 4.

---

## 🎯 Impact Estimé

| Action | Cas impactés | Gain estimé |
|--------|-------------|-------------|
| Ajouter MICROVOLTAGE + synonymes | Cas 4 (×5 participants) | +5-10 évals qui passent de 0% à >0% |
| Synonymes FLUTTER_DROIT_TYPIQUE | Cas 8 (×5) | Coupe-circuit sur "flutter commun" → match exact |
| Synonymes FAISCEAU_ACCESSOIRE | Cas 13 (×5) | Meilleur ranking dans le Search |
| Synonymes HYPERKALIÉMIE | Cas 5 (×5) | Coupe-circuit si NER extrait une variante |
| Synonymes BAV_2_MOBITZ_2 | Cas 9 (×5) | Coupe-circuit sur "Mobitz II", "BAV 2:1" |
| Synonymes TACHYCARDIE_VENTRICULAIRE | Cas 11 (×5) | Coupe-circuit sur "TV", "VT" |
| **Total Priorité 0+1** | **~30-35 évals** | **Score global +5 à +15 pts** |

> ⚡ Le gain le plus massif viendra des **synonymes courts** (abréviations : TV, FV, BBD, HBAG, ESV...) car ce sont les termes que les étudiants utilisent en pratique quotidienne.

---

## ⚠️ Rappels Importants

1. **Les synonymes sont sensibles à la casse** dans le matching exact (coupe-circuit). Ils sont normalisés (lowercase, sans accents) avant comparaison. Donc `"TV"` et `"tv"` matcheront.

2. **Ne pas dupliquer** : si un synonyme est déjà le `concept_name` d'un AUTRE concept, ne pas l'ajouter. Ex : `"Flutter atrial"` est le concept_name de FLUTTER_ATRIAL → ne pas l'ajouter comme synonyme de FLUTTER_DROIT_TYPIQUE.

3. **Implications ≠ Synonymes** : Les implications sont des concepts parents/enfants logiques. Les synonymes sont des formes alternatives du MÊME concept.

4. **Le NER (Brique 2) reste le point d'entrée** : si le NER n'extrait pas un terme, même avec des synonymes parfaits le pipeline ne le trouvera pas. Cas 5 (hyperkaliémie) nécessite aussi un fix côté NER.
