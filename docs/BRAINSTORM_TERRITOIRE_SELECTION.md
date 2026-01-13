# 🎯 Brainstorming : Sélection Intelligente de Territoires

**Date** : 2026-01-13  
**Objectif** : Système de sélection contextuelle de territoires pour STEMI, ESV, Faisceaux accessoires  
**Mode** : Party Mode Analysis

---

## 📊 État des lieux ontologique

### ✅ Propriétés disponibles dans l'ontologie OWL

#### Annotation Properties
- **`importanceTerritoire`** (IRI: `RBiXCmVuqDW3Kzzg8N1v6i3`)
  - Valeurs : `critique`, `importante`, `optionnelle`
  - Usage : Définir si le territoire est obligatoire

- **`mayHaveTerritory`** (IRI: `RvQtNXH9Cp7Ss5k9ocYaZD`)
  - Valeurs : `true`/`false`
  - Usage : Indique si le concept peut avoir un territoire

- **`mayHaveMirror`** (IRI: `R81WX84pmfiju3JOXA5ub0A`)
  - Valeurs : `true`/`false`
  - Usage : Indique si le concept peut avoir un miroir

#### Object Property
- **`hasTerritory`** (IRI: `R86MFl68gsSAS3kHPEgghC3`)
  - Déjà extrait et utilisé !
  - Pointe vers : Localisation IDM, Localisation ESV, etc.

### 📍 Exemple concret : STEMI

```xml
<owl:Class rdf:about="http://webprotege.stanford.edu/R8MM7HcF7ZAoeDCLbPHkUmQ">
    <webprotege:R81WX84pmfiju3JOXA5ub0A xml:lang="fr">true</webprotege:R81WX84pmfiju3JOXA5ub0A>
    <webprotege:RBiXCmVuqDW3Kzzg8N1v6i3 xml:lang="fr">critique</webprotege:RBiXCmVuqDW3Kzzg8N1v6i3>
    <webprotege:RvQtNXH9Cp7Ss5k9ocYaZD xml:lang="fr">true</webprotege:RvQtNXH9Cp7Ss5k9ocYaZD>
    <rdfs:label xml:lang="fr">Syndrome coronarien à la phase aigue avec sus-décalage du segment ST</rdfs:label>
    <skos:altLabel xml:lang="fr">STEMI</skos:altLabel>
</owl:Class>
```

**Interprétation** :
- ✅ `mayHaveTerritory: true` → Peut avoir un territoire : et on peut en choisir plusieurs 
- ✅ `mayHaveMirror: true` → Peut avoir un miroir et on peut en choisir plusieurs 
- ⚠️ `importanceTerritoire: critique` → **OBLIGATOIRE** de préciser le territoire !

### 🗺️ Hiérarchie des territoires

**Localisation IDM** (classe parente)
- Antérieur
- Inférieur
- Latéral
- Septal
- Apicale
- Antéro-septal
- Antéro-latéral
- Postéro-septal
- Etc.

**Miroir** (classe parente)
- [À définir dans ontologie]
a comme relatioship : hasTerritory : Localisation IDM
---

## 💡 Proposition de solution

### Phase 1 : Extraction des métadonnées (Backend)

#### Fichier : `backend/rdf_owl_extractor.py`

Ajouter extraction de 3 nouvelles annotation properties :

```python
def extract_territory_metadata(self):
    """
    Extrait les métadonnées de territoire pour chaque concept
    - importanceTerritoire : critique/importante/optionnelle
    - mayHaveTerritory : true/false
    - mayHaveMirror : true/false
    """
    print("\n🗺️ Extraction métadonnées territoire...")
    
    # IRIs des annotation properties
    importance_iri = "http://webprotege.stanford.edu/RBiXCmVuqDW3Kzzg8N1v6i3"
    mayhave_territory_iri = "http://webprotege.stanford.edu/RvQtNXH9Cp7Ss5k9ocYaZD"
    mayhave_mirror_iri = "http://webprotege.stanford.edu/R81WX84pmfiju3JOXA5ub0A"
    
    for owl_class in self.root.findall('.//owl:Class', self.ns):
        class_iri = owl_class.get('{%s}about' % self.ns['rdf'])
        if not class_iri:
            continue
        
        # Chercher les annotations
        importance = self._extract_annotation_value(owl_class, importance_iri)
        may_have_territory = self._extract_annotation_value(owl_class, mayhave_territory_iri)
        may_have_mirror = self._extract_annotation_value(owl_class, mayhave_mirror_iri)
        
        # Stocker
        if importance or may_have_territory or may_have_mirror:
            self.territory_metadata[class_iri] = {
                'importance': importance,
                'may_have_territory': may_have_territory == 'true',
                'may_have_mirror': may_have_mirror == 'true'
            }
```

#### Structure JSON générée

```json
{
  "concept_mappings": {
    "SYNDROME_CORONARIEN_À_LA_PHASE_AIGUE_AVEC_SUS-DÉCALAGE_DU_SEGMENT_ST": {
      "concept_name": "Syndrome coronarien à la phase aigue avec sus-décalage du segment ST",
      "poids": 4,
      "categorie": "DIAGNOSTIC_URGENT",
      "territoires_possibles": ["Antérieur", "Inférieur", "Latéral", ...],
      "territory_metadata": {
        "importance": "critique",
        "may_have_territory": true,
        "may_have_mirror": true,
        "required_territory": true  // Dérivé de importance == "critique"
      }
    }
  }
}
```

---

### Phase 2 : Interface de sélection (Frontend)

#### Fichier : `frontend/pages/correction_llm.py`

**Workflow proposé :**

1. **Détection automatique** après saisie d'un concept
   ```python
   if concept_metadata.get('may_have_territory'):
       # Afficher sélecteur de territoire
       show_territory_selector(concept, territories_list, required=...)
   ```

2. **Interface visuelle** :

```python
def show_territory_selector(concept_name, territories, required=False):
    """
    Affiche un sélecteur de territoire contextuel
    
    Args:
        concept_name: Nom du concept (ex: "STEMI")
        territories: Liste des territoires possibles
        required: Si True, rend la sélection obligatoire
    """
    
    st.markdown(f"### 🗺️ Précision du territoire pour : **{concept_name}**")
    
    if required:
        st.warning("⚠️ **Territoire OBLIGATOIRE** (importance: critique)")
    else:
        st.info("💡 Territoire optionnel - Aide à la précision diagnostique")
    
    # Sélecteur de territoire principal
    selected_territory = st.selectbox(
        "Localisation de l'infarctus :",
        options=["Aucun" if not required else None] + territories,
        key=f"territory_{concept_name}"
    )
    
    # Si miroir possible
    if metadata.get('may_have_mirror'):
        col1, col2 = st.columns(2)
        
        with col1:
            has_mirror = st.checkbox("Présence d'un miroir", key=f"mirror_check_{concept_name}")
        
        with col2:
            if has_mirror:
                mirror_territory = st.selectbox(
                    "Localisation du miroir :",
                    options=territories,
                    key=f"mirror_{concept_name}"
                )
    
    # Validation
    if required and (not selected_territory or selected_territory == "Aucun"):
        st.error("❌ Vous devez sélectionner un territoire pour ce diagnostic")
        return None
    
    return {
        'territory': selected_territory,
        'mirror': mirror_territory if has_mirror else None
    }
```

#### Variantes d'interface

**Option A : Modal popup** (recommandé pour UX)
```python
@st.dialog("🗺️ Sélection du territoire")
def territory_dialog(concept_name):
    st.markdown(f"Vous avez sélectionné : **{concept_name}**")
    # ... sélecteurs ...
    
    if st.button("Valider"):
        return territory_data
```

**Option B : Expander intégré**
```python
with st.expander(f"🗺️ Préciser le territoire pour {concept_name}", expanded=True):
    # ... sélecteurs ...
```

**Option C : Étape dédiée** (après annotation)
```python
# Étape 1: Annotation des concepts
# Étape 2: Précision des territoires (nouveau!)
# Étape 3: Validation
# Étape 4: Scoring
```

---

### Phase 3 : Validation et scoring

#### Validation des territoires obligatoires

```python
def validate_required_territories(annotated_concepts, ontology):
    """
    Vérifie que tous les concepts avec territoire obligatoire ont un territoire sélectionné
    """
    missing_territories = []
    
    for concept in annotated_concepts:
        metadata = ontology['concept_mappings'][concept['id']].get('territory_metadata', {})
        
        if metadata.get('required_territory') and not concept.get('territory'):
            missing_territories.append({
                'concept': concept['text'],
                'importance': metadata['importance']
            })
    
    return missing_territories
```

#### Scoring avec bonus de précision : pour le scoring, il se fait apres le matching, on ne demande rien à l'étudiant. En gros le worflow actuel doit etre respecté juste on attribue des points spécifiquement pour le territoire en cas de STEMI si il est present (complet ou non) ou absent 

En sachant que l'annotation territoire peut aussi etre associé à Onde T négative -> qui est un relationship de NSTEMI 
_> faut il mieux faire un lien par concept : en gros je mets hasTerritory / mayhaveterritory et mayhavemiror à tout les concepts concerné ou justele concept principal ?

```python
def score_with_territory_precision(student_concepts, expected_concepts):
    """
    Scoring amélioré avec bonus pour précision territoriale
    """
    base_score = calculate_base_score(...)
    
    # Bonus si territoire correct
    for student, expected in matched_pairs:
        if student.get('territory') == expected.get('territory'):
            precision_bonus += 5  # Bonus 5% pour précision territoriale
        
        if student.get('mirror') == expected.get('mirror'):
            precision_bonus += 3  # Bonus 3% pour miroir correct
    
    return base_score + precision_bonus
```

---

## 🎯 Plan d'implémentation (4 étapes)

### Étape 1 : Extraction backend ✅ (30 min)
- [ ] Ajouter `extract_territory_metadata()` dans `rdf_owl_extractor.py`
- [ ] Ajouter `territory_metadata` dans structure JSON
- [ ] Tester avec `python regenerate_ontology.py`
- [ ] Vérifier les métadonnées dans `data/ontology_from_owl.json`

### Étape 2 : Récupération des territoires possibles (30 min)
- [ ] Fonction pour lister les enfants de "Localisation IDM"
- [ ] Idem pour "Localisation ESV"
- [ ] Idem pour "Localisation faisceau accessoire"
- [ ] Caching des listes pour performance

### Étape 3 : Interface de sélection (1h)
- [ ] Créer composant `show_territory_selector()`
- [ ] Intégrer dans workflow d'annotation
- [ ] Gérer état Streamlit (session_state)
- [ ] Validation avant soumission

### Étape 4 : Tests et UX (30 min)
- [ ] Tester avec cas STEMI
- [ ] Tester avec ESV
- [ ] Tester validation territoire obligatoire
- [ ] Feedback utilisateur

**Total estimé : 2h30**

---

## 🚀 Recommandations

### Priorité 1 : MUST HAVE
- ✅ Extraction métadonnées territoire
- ✅ Validation territoire obligatoire (importanceTerritoire: critique)
- ✅ Sélecteur simple de territoire

### Priorité 2 : SHOULD HAVE
- ✅ Sélecteur de miroir
- ✅ Bonus scoring pour précision
- ⚠️ Interface modale élégante

### Priorité 3 : NICE TO HAVE
- ⚠️ Visualisation ECG avec territoire surligné
- ⚠️ Suggestions intelligentes basées sur signes ECG
- ⚠️ Historique des territoires fréquents par utilisateur

---

## 🎨 Mockup interface

```
┌─────────────────────────────────────────────────────────────┐
│ 🎯 Correction d'ECG                                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Concepts annotés :                                           │
│ • Rythme sinusal                            [✓]             │
│ • STEMI                                     [⚠️ Territoire !]│
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🗺️ Précision du territoire pour : STEMI                 │ │
│ │                                                          │ │
│ │ ⚠️ Territoire OBLIGATOIRE (importance: critique)         │ │
│ │                                                          │ │
│ │ Localisation de l'infarctus : [▼ Sélectionner ▼]       │ │
│ │   • Antérieur                                           │ │
│ │   • Inférieur                                           │ │
│ │   • Latéral                                             │ │
│ │   • Septal                                              │ │
│ │   • Antéro-septal                                       │ │
│ │   • ...                                                 │ │
│ │                                                          │ │
│ │ ☑ Présence d'un miroir                                  │ │
│ │                                                          │ │
│ │ Localisation du miroir : [▼ Postérieur ▼]              │ │
│ │                                                          │ │
│ │                     [Valider]                            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤔 Questions ouvertes

1. **Miroir** : Faut-il créer une classe "Miroir" dans l'ontologie ou utiliser les mêmes territoires ?
2. **ESV** : Même logique que STEMI ?
3. **Scoring** : Quel bonus pour territoire correct ? (proposition: 5%)
4. **Interface** : Modal ou intégré ? (recommandation: modal pour UX)
5. **Validation** : Bloquer ou warning si territoire manquant ?

---

## 💬 Prochaines actions

**Décision requise** :
- Choix interface (modal vs intégré)
- Valeur bonus scoring
- Gestion du miroir

**Puis** :
- Implémenter étape 1 (extraction)
- Tester terminal
- Implémenter interface
- Tests end-to-end

---

**🎉 Party Mode Analysis Complete !**
