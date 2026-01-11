# 📖 GUIDE DE CONVENTIONS - Ontologie ECG WebProtégé

**Version:** 3.0  
**Date:** 2026-01-11  
**Auteur:** BMad Team + Dr. Grégoire

---

## 🎯 OBJECTIF

Établir des **conventions strictes** pour l'édition de l'ontologie ECG dans WebProtégé afin de garantir :
- ✅ **Extraction automatique** sans modification de code
- ✅ **Backward compatibility** des systèmes existants
- ✅ **Robustesse** sur exports répétés

---

## 🏗️ STRUCTURE HIÉRARCHIQUE

### Catégories Principales (Classes racines)

```turtle
# 4 catégories OBLIGATOIRES (ne jamais renommer)
Diagnostic_Urgent       # Poids: 4, Urgence: immédiate
Diagnostic_Majeur       # Poids: 3, Urgence: différée  
Signe_ECG_Pathologique  # Poids: 2, Urgence: surveillance
Descripteur_ECG         # Poids: 1, Urgence: contexte
```

**RÈGLE :** Tout concept DOIT être sous-classe d'une de ces 4 catégories.

---

## 📋 PROPRIÉTÉS STANDARDS (SKOS)

### 1️⃣ Nom Officiel : `rdfs:label`

```turtle
:BAV1 a owl:Class ;
    rdfs:label "Bloc auriculo-ventriculaire du 1er degré"@fr ;
    rdfs:label "First-degree atrioventricular block"@en .
```

**RÈGLE :** 
- Obligatoire en français (`@fr`)
- Optionnel en anglais (`@en`)
- 1 seul label par langue

---

### 2️⃣ Synonymes : `skos:altLabel`

```turtle
:BAV1 a owl:Class ;
    rdfs:label "Bloc auriculo-ventriculaire du 1er degré"@fr ;
    skos:altLabel "BAV 1"@fr ;
    skos:altLabel "BAV1"@fr ;
    skos:altLabel "BAV du premier degré"@fr ;
    skos:altLabel "Bloc AV 1"@fr .
```

**RÈGLE :**
- Utiliser `skos:altLabel` (PAS de propriété custom `hasSynonym`)
- Multiples altLabel autorisés
- Inclure TOUTES les variantes (avec/sans espace, abréviations, etc.)
- Langue française `@fr` obligatoire

**Exemples critiques :**
```turtle
# Hémibloc = synonyme de bloc fasciculaire
:BlocFasciculaireAnterieurGauche
    rdfs:label "Bloc fasciculaire antérieur gauche"@fr ;
    skos:altLabel "Hémibloc antérieur gauche"@fr ;
    skos:altLabel "BFAG"@fr ;
    skos:altLabel "Hemibloc anterieur gauche"@fr .  # Sans accent aussi !
```

---

### 3️⃣ Définition : `skos:definition`

```turtle
:BAV1 a owl:Class ;
    skos:definition "Allongement de l'intervalle PR > 200 ms"@fr .
```

---

### 4️⃣ Note Pédagogique : `rdfs:comment`

```turtle
:BAV1 a owl:Class ;
    rdfs:comment "Attention : un PR > 200 ms est requis pour le diagnostic"@fr .
```

---

## 🔗 PROPRIÉTÉS OBJECT (Relations)

### 1️⃣ Implications Diagnostiques : `ecg:requiresFindings`

**Usage :** Diagnostic → Signes ECG requis

```turtle
:BAV1 a owl:Class ;
    rdfs:subClassOf Diagnostic_Majeur ;
    ecg:requiresFindings :PR_Allongé .

:NSTEMI a owl:Class ;
    rdfs:subClassOf Diagnostic_Urgent ;
    ecg:requiresFindings :Sous_Decalage_ST ;
    ecg:requiresFindings :Onde_T_Negative .
```

**RÈGLE :**
- Propriété : `ecg:requiresFindings` (object property)
- Pointe vers d'autres concepts (pas de string)
- Multiples valeurs autorisées

---

### 2️⃣ Électrodes : `ecg:hasElectrode`

**Usage :** Territoire d'infarctus → Dérivations concernées

```turtle
:Infarctus_Anterieur a owl:Class ;
    rdfs:subClassOf Diagnostic_Urgent ;
    ecg:hasElectrode :V1 ;
    ecg:hasElectrode :V2 ;
    ecg:hasElectrode :V3 ;
    ecg:hasElectrode :V4 .
```

**RÈGLE :**
- Propriété : `ecg:hasElectrode`
- Valeurs : Classes représentant dérivations (V1, V2, DI, DII, etc.)

---

### 3️⃣ Territoire : `ecg:hasTerritory`

**Usage :** Diagnostic → Territoire anatomique (optionnel)

```turtle
:NSTEMI a owl:Class ;
    ecg:hasTerritory :Myocarde_Anterieur .
```

---

### 4️⃣ Poids Explicite : `ecg:hasWeight` (OPTIONNEL)

**Usage :** Surcharge du poids déduit de la hiérarchie

```turtle
:ConceptSpecial a owl:Class ;
    rdfs:subClassOf Signe_ECG_Pathologique ;  # Poids par défaut: 2
    ecg:hasWeight :Poids_4 .  # Override: poids = 4
```

**RÈGLE :**
- Optionnel : si absent, poids déduit de la catégorie parent
- Valeurs : `:Poids_1`, `:Poids_2`, `:Poids_3`, `:Poids_4`

---

## ✅ CHECKLIST AVANT EXPORT

Avant d'exporter l'ontologie depuis WebProtégé :

- [ ] Tous les concepts ont un `rdfs:label@fr`
- [ ] Synonymes en `skos:altLabel` (PAS `hasSynonym`)
- [ ] Hiérarchie correcte (sous-classe de Urgent/Majeur/Signe/Descripteur)
- [ ] Pas de doublons dans les labels
- [ ] Propriétés `ecg:requiresFindings` pointent vers concepts existants
- [ ] Électrodes définies pour territoires d'infarctus
- [ ] Test dans WebProtégé : rechercher "hemibloc" doit trouver "Bloc fasciculaire"

---

## 🔄 WORKFLOW RECOMMANDÉ

### Dans WebProtégé :
1. ✏️ Créer/modifier concepts
2. 🏷️ Ajouter `skos:altLabel` pour CHAQUE synonyme
3. 🔗 Définir relations `ecg:requiresFindings` si applicable
4. 📂 Classer sous bonne catégorie (Urgent/Majeur/Signe/Descripteur)
5. 💾 Sauvegarder dans WebProtégé
6. 📥 **Export** → `.owl` (RDF/XML format)

### Dans le projet Python :
```bash
# 1. Copier fichier exporté
cp ~/Downloads/BrYOzRZIu7jQTwmfcGsi35.owl C:\Users\Administrateur\bmad\

# 2. Régénérer JSON
cd "C:\Users\Administrateur\bmad\ECG lecture"
python backend/owl_to_json_converter.py "C:\Users\Administrateur\bmad\BrYOzRZIu7jQTwmfcGsi35.owl"

# 3. Tests de non-régression
python tests/test_ontology_backward_compatibility.py

# 4. Si OK → Relancer app
streamlit run frontend/ecg_session_builder.py
```

---

## 🚫 ERREURS COURANTES À ÉVITER

### ❌ Utiliser propriété custom au lieu de SKOS standard
```turtle
# MAUVAIS
:BAV1 hasSynonym "BAV 1" .

# BON
:BAV1 skos:altLabel "BAV 1"@fr .
```

### ❌ Oublier la langue @fr
```turtle
# MAUVAIS
:BAV1 rdfs:label "BAV 1" .

# BON
:BAV1 rdfs:label "BAV 1"@fr .
```

### ❌ Hardcoder poids au lieu d'utiliser hiérarchie
```turtle
# MAUVAIS (redondant)
:BAV1 rdfs:subClassOf Diagnostic_Majeur ;
      ecg:hasWeight :Poids_3 .  # Déjà déduit !

# BON (simple)
:BAV1 rdfs:subClassOf Diagnostic_Majeur .  # Poids = 3 automatique
```

### ❌ Synonyme incomplet
```turtle
# INCOMPLET
:BlocFasciculaireAnterieurGauche
    skos:altLabel "Hémibloc antérieur gauche"@fr .

# COMPLET
:BlocFasciculaireAnterieurGauche
    skos:altLabel "Hémibloc antérieur gauche"@fr ;
    skos:altLabel "Hemibloc anterieur gauche"@fr ;  # Sans accents
    skos:altLabel "BFAG"@fr ;
    skos:altLabel "Hémi-bloc antérieur gauche"@fr .  # Avec tiret
```

---

## 📊 EXEMPLE COMPLET

```turtle
@prefix : <http://webprotege.stanford.edu/project/BrYOzRZIu7jQTwmfcGsi35#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ecg: <http://example.org/ecg#> .

:BAV1 a owl:Class ;
    # Hiérarchie (détermine catégorie et poids par défaut)
    rdfs:subClassOf :Diagnostic_Majeur ;  # Poids = 3 automatique
    
    # Labels (obligatoire)
    rdfs:label "Bloc auriculo-ventriculaire du 1er degré"@fr ;
    rdfs:label "First-degree atrioventricular block"@en ;
    
    # Synonymes (SKOS standard)
    skos:altLabel "BAV 1"@fr ;
    skos:altLabel "BAV1"@fr ;
    skos:altLabel "BAV du premier degré"@fr ;
    skos:altLabel "Bloc AV 1"@fr ;
    
    # Définition (optionnel)
    skos:definition "Allongement constant de l'intervalle PR > 200 ms sans trouble de la conduction ventriculaire"@fr ;
    
    # Note pédagogique (optionnel)
    rdfs:comment "Attention : mesurer PR sur plusieurs dérivations pour confirmer"@fr ;
    
    # Implications diagnostiques (requiresFindings)
    ecg:requiresFindings :PR_Allongé .
```

---

## 🎯 BÉNÉFICES

En suivant ces conventions :

✅ **Export OWL → JSON = 100% automatique** (aucune modification de code)
✅ **Synonymes automatiquement extraits** (recherche "hémibloc" trouve "bloc fasciculaire")
✅ **Poids déduits** de la hiérarchie (pas de configuration manuelle)
✅ **Backward compatible** (ancien code continue de fonctionner)
✅ **Standard SKOS** (compatible autres outils d'ontologie)

---

**Questions ?** Contactez l'équipe BMad ou consultez ONTOLOGY_CONVENTIONS.md
