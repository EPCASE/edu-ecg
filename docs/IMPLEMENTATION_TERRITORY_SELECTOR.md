# 🗺️ Implémentation Territory Selector - Documentation Complète

**Date:** 2026-01-13  
**Auteur:** Grégoire + BMAD  
**Status:** ✅ Backend complet | 🚧 Intégration frontend en cours

---

## 📋 Vue d'ensemble

Le **Territory Selector** est un système contextuel qui affiche automatiquement des sélecteurs de territoires (et de miroirs) lorsque l'utilisateur choisit un concept nécessitant cette précision (STEMI, NSTEMI, ESV, faisceau accessoire, etc.).

### Principes clés

1. **Approche générique** : Le système utilise les relations `hasTerritory` de l'ontologie pour résoudre les territoires de manière universelle
2. **Résolution récursive** : Les territoires parents (Localisation IDM) sont résolus en leurs enfants (Antérieur, Postérieur, etc.)
3. **Validation obligatoire** : Les concepts avec `importanceTerritoire: critique` exigent un territoire
4. **Bonus de scoring** : La précision du territoire ajoute jusqu'à +8% au score

---

## 🏗️ Architecture

### Composants créés

```
backend/
  ├── territory_resolver.py          # 🧠 Logique de résolution des territoires
  └── rdf_owl_extractor.py           # Extraction métadonnées OWL (déjà modifié)

frontend/
  └── components/
      ├── __init__.py                # Module components
      └── territory_selector_ui.py   # 🎨 Interface Streamlit

tests/
  ├── test_territory_resolver.py     # Tests unitaires resolver
  └── demo_territory_selector.py     # 🎯 Démo interactive Streamlit
```

---

## 🔧 Backend - `territory_resolver.py`

### Fonctions principales

#### 1. `resolve_territories(concept_data, ontology)`

Résout récursivement les territoires possibles pour un concept.

```python
territories, mirrors = resolve_territories(stemi_data, ontology)
# territories: ['Antérieur', 'Apicale', 'Circonférentiel', 'Latéral', 'Postérieur', 'Septal']
# mirrors: ['Antérieur', 'Apicale', 'Circonférentiel', 'Latéral', 'Postérieur', 'Septal']
```

**Algorithme :**
- Parcourt `territoires_possibles` du concept
- Si territoire parent (ex: "Localisation IDM"), résout ses enfants via hiérarchie
- Si "Miroir", suit `hasTerritory` → "Localisation IDM" → enfants
- Retourne deux listes distinctes : territoires principaux et miroirs

#### 2. `get_territory_config(concept_name, ontology)`

Point d'entrée principal - retourne la configuration complète d'un concept.

```python
config = get_territory_config("STEMI", ontology)
# {
#   'concept_name': 'Syndrome coronarien...',
#   'show_territory_selector': True,
#   'show_mirror_selector': True,
#   'is_required': True,
#   'importance': 'critique',
#   'territories': ['Antérieur', 'Apicale', ...],
#   'mirrors': ['Antérieur', 'Apicale', ...]
# }
```

#### 3. `should_show_territory_selector(concept_data)`

Détermine si le sélecteur doit être affiché.

```python
show, required, importance = should_show_territory_selector(concept_data)
# show: True si may_have_territory=true
# required: True si importance="critique"
# importance: "critique" | "importante" | "optionnelle"
```

---

## 🎨 Frontend - `territory_selector_ui.py`

### Composants Streamlit

#### 1. `render_territory_selectors(concept_name, ontology, key_prefix)`

Affiche les `st.multiselect` pour territoires et miroirs.

```python
territories, mirrors = render_territory_selectors(
    "Syndrome coronarien à la phase aigue avec sus-décalage du segment ST",
    ontology,
    key_prefix="correction"
)
```

**Affichage adaptatif :**
- 🔴 OBLIGATOIRE (importance: critique)
- 🟠 Recommandé (importance: importante)
- 🟢 Optionnel (importance: optionnelle)

**Interface :**
```
🔴 Territoire OBLIGATOIRE
  └─ Multiselect: [Antérieur, Apicale, Circonférentiel, ...]

🪞 Territoire Miroir (optionnel)
  └─ Multiselect: [Antérieur, Apicale, Circonférentiel, ...]
```

#### 2. `check_territory_completeness(concept_name, selected_territories, ontology)`

Valide que les territoires obligatoires sont bien sélectionnés.

```python
is_complete, error_msg = check_territory_completeness(
    "STEMI",
    [],  # Aucun territoire sélectionné
    ontology
)
# is_complete: False
# error_msg: "Le territoire est obligatoire pour **STEMI** (importance: critique)"
```

#### 3. `calculate_territory_bonus(concept, student_terr, student_mirr, expected_terr, expected_mirr, ontology)`

Calcule le bonus de scoring pour la précision du territoire.

**Barème :**
- ✅ Territoire exact : **+5%**
- ⚠️ Territoire partiel : **+2%**
- ✅ Miroir exact : **+3%**
- ⚠️ Miroir partiel : **+1%**

```python
bonus, explanation = calculate_territory_bonus(
    "STEMI",
    ["Antérieur", "Septal"],     # Étudiant
    ["Postérieur"],              # Miroir étudiant
    ["Antérieur", "Septal"],     # Attendu
    ["Postérieur"],              # Miroir attendu
    ontology
)
# bonus: 0.08 (8%)
# explanation: "✅ Territoire exact (+5%) | ✅ Miroir exact (+3%)"
```

---

## 🧪 Tests et Validation

### Test 1: Backend Resolver

```bash
python test_territory_resolver.py
```

**Résultats attendus :**
```
✅ STEMI trouvé: importance=critique, required=True
🗺️  6 territoires: [Antérieur, Apicale, Circonférentiel, Latéral, Postérieur, Septal]
🪞 6 miroirs: [Antérieur, Apicale, Circonférentiel, Latéral, Postérieur, Septal]
```

### Test 2: Démo Interactive

```bash
streamlit run demo_territory_selector.py
```

**Tests manuels :**
1. Sélectionner "STEMI" → doit afficher 2 multiselects (territoire + miroir) avec label 🔴 OBLIGATOIRE
2. Sélectionner "Hypertrophie VG" → aucun sélecteur (pas de métadonnées territoire)
3. Tester scoring avec territoires exacts/partiels

---

## 🔄 Intégration dans `correction_llm.py`

### Workflow proposé

```python
# 1. Après extraction LLM des concepts
student_concepts = llm_service.extract_concepts(student_answer)

# 2. Pour chaque concept extrait, vérifier besoin territoire
territories_selections = {}  # {concept_name: (territories, mirrors)}

for concept in student_concepts:
    concept_name = concept.get('text')
    config = get_territory_config(concept_name, ONTOLOGY)
    
    if config and config['show_territory_selector']:
        # Afficher sélecteur
        st.markdown(f"### 📍 Précision territoire pour **{concept_name}**")
        
        territories, mirrors = render_territory_selectors(
            concept_name,
            ONTOLOGY,
            key_prefix=f"correction_{concept_name}"
        )
        
        # Valider complétude
        is_complete, error = check_territory_completeness(
            concept_name,
            territories,
            ONTOLOGY
        )
        
        if not is_complete:
            st.error(error)
            return  # Bloquer la correction
        
        territories_selections[concept_name] = (territories, mirrors)

# 3. Intégrer dans le scoring
for concept in matched_concepts:
    if concept in territories_selections:
        student_terr, student_mirr = territories_selections[concept]
        expected_terr, expected_mirr = get_expected_territories(concept, case_data)
        
        bonus, explanation = calculate_territory_bonus(
            concept,
            student_terr, student_mirr,
            expected_terr, expected_mirr,
            ONTOLOGY
        )
        
        concept_scores[concept] += bonus * 100
```

---

## 📊 Métadonnées Ontologie

### Structure dans `ontology_from_owl.json`

```json
{
  "concept_mappings": {
    "STEMI_ID": {
      "concept_name": "Syndrome coronarien à la phase aigue avec sus-décalage du segment ST",
      "territory_metadata": {
        "importance": "critique",
        "may_have_territory": true,
        "may_have_mirror": true,
        "required_territory": true
      },
      "territoires_possibles": [
        "Localisation IDM",
        "Miroir"
      ]
    }
  }
}
```

### Relations OWL source

**AnnotationProperties extraites :**
- `importanceTerritoire` → "critique" | "importante" | "optionnelle"
- `mayHaveTerritory` → boolean
- `mayHaveMirror` → boolean

**ObjectProperty utilisée :**
- `hasTerritory` → Relie concept à classe territoire (ex: STEMI → Localisation IDM)

**Hiérarchie :**
```
Localisation IDM (parent)
  ├─ Antérieur
  ├─ Apicale
  ├─ Circonférentiel
  ├─ Latéral
  ├─ Postérieur
  └─ Septal

Miroir
  └─ hasTerritory: Localisation IDM (résolu récursivement)
```

---

## ✅ Checklist Intégration

### Backend (Fait)
- [x] Extraction métadonnées territoire (`rdf_owl_extractor.py`)
- [x] Résolution récursive territoires (`territory_resolver.py`)
- [x] Tests unitaires (`test_territory_resolver.py`)

### Frontend (À faire)
- [x] Composant UI sélecteur (`territory_selector_ui.py`)
- [x] Démo interactive (`demo_territory_selector.py`)
- [ ] Intégration dans `correction_llm.py`
- [ ] Validation workflow complet
- [ ] Intégration bonus scoring

### Cas de test
- [ ] Créer cas STEMI avec territoires dans metadata
- [ ] Tester workflow end-to-end
- [ ] Valider bonus scoring avec territoires exacts/partiels

---

## 🎯 Prochaines étapes

### Phase 1: Intégration Correction LLM
1. Modifier `perform_correction()` pour détecter concepts avec métadonnées territoire
2. Afficher sélecteurs après extraction LLM
3. Valider complétude avant scoring
4. Intégrer bonus territoire dans calcul final

### Phase 2: Cas de test
1. Créer `data/cases/stemi_anterieur/` avec:
   - ECG STEMI antérieur
   - `metadata.json` avec `territories: ["Antérieur"]`, `mirrors: ["Postérieur"]`
2. Tester workflow complet
3. Valider scoring avec bonus

### Phase 3: Extension
1. Appliquer à ESV (Localisation ESV)
2. Appliquer à faisceau accessoire (Localisation faisceau accessoire)
3. Documenter patterns pour futurs concepts

---

## 📝 Notes de développement

### Choix d'architecture

**Q: Pourquoi résolution générique via `hasTerritory` ?**  
R: Permet d'appliquer automatiquement à tous concepts futurs ayant cette relation, sans code spécifique par pathologie.

**Q: Pourquoi deux listes (territories, mirrors) ?**  
R: Séparation claire UI et scoring différencié. Miroir optionnel, territoire parfois obligatoire.

**Q: Pourquoi `multiselect` et pas `selectbox` ?**  
R: STEMI peut toucher plusieurs territoires (ex: Antérieur + Septal), miroir aussi.

### Limitations connues

1. **Résolution récursive 1 niveau** : Ne gère pas hiérarchies >2 niveaux (non nécessaire actuellement)
2. **Synonymes** : `get_territory_config()` cherche par nom exact ou synonymes, mais pas fuzzy matching
3. **Pas de cache** : Résolution à chaque appel (acceptable car ontologie petite)

---

## 🔗 Références

- [BRAINSTORM_TERRITOIRE_SELECTION.md](./BRAINSTORM_TERRITOIRE_SELECTION.md) - Planning initial
- [backend/rdf_owl_extractor.py](../backend/rdf_owl_extractor.py) - Extraction OWL
- [backend/territory_resolver.py](../backend/territory_resolver.py) - Logique résolution
- [frontend/components/territory_selector_ui.py](../frontend/components/territory_selector_ui.py) - Interface Streamlit

---

**Status:** 🚀 Backend validé, UI testée, prêt pour intégration dans workflow correction
