# 🔧 Réannotation WebProtégé — Modifications ontologie V2 (V3.1)

> **Date** : 2026-04-06  
> **Contexte** : Correctifs V3.1 suite à l'analyse du scoring sur 43 étudiants × 15 cas  
> **Fichier source** : `ECG lecture/data/ontology_v2.json` (345 concepts)

---

## 1. Concepts EXISTANTS modifiés (à patcher dans WebProtégé)

### 1.1 — ECG_NORMAL

**Propriété modifiée** : `excludes_families`

Avant (3 familles) :
```
TROUBLE_DE_REPOLARISATION
TROUBLE_DE_LA_DEPOLARISATION_VENTRICULAIRE
ARYTHMIE
```

Après (7 familles) — **ajouter les 4 suivantes** :
```diff
+ TROUBLES_DE_CONDUCTION_ET_DE_L_AUTOMATICITE
+ STIMULATION
+ EVENEMENTS_ECTOPIQUES
+ INTERFERENCE_EXTRA_CARDIAQUE
```

> **Raison** : Un BAV (enfant de TROUBLES_DE_CONDUCTION) n'excluait pas ECG_NORMAL. Idem pour les stimulateurs, ESV, etc.

---

### 1.2 — TROUBLE_DE_REPOLARISATION

**Propriété modifiée** : `synonymes`

```diff
+ "Trouble de la repolarisation"
```

> **Raison** : Les étudiants écrivent souvent "trouble **de la** repolarisation" (avec l'article). Le concept_name est "Trouble de repolarisation" (sans "la"). Le synonyme permet au NER + recherche hybride de résoudre correctement.

---

### 1.3 — AXE_NORMAL_DU_QRS

**Propriété modifiée** : `synonymes`

```diff
+ "axe gauche physiologique"
+ "axe physiologique"
+ "Axe du coeur normal"
+ "Axe cardiaque normal"
```

> **Raison** : "axe gauche physiologique" était résolu par le juge LLM vers ECG_NORMAL (diagnostic global) au lieu de AXE_NORMAL_DU_QRS (descripteur spécifique). Le synonyme permet au coupe-circuit de l'attraper.

---

### 1.4 — BLOC_INTERATRIAL

**Propriété ajoutée** : `has_qualifier_families`

```diff
+ has_qualifier_families: ["ONDE_P_ANORMALE"]
```

> **Raison** : BLOC_INTERATRIAL a `has_qualifiers: [ONDE_P_PROLONGEE]` mais les étudiants citent souvent le parent ONDE_P_ANORMALE. Le `has_qualifier_families` permet au scoring de reconnaître les enfants de ONDE_P_ANORMALE comme qualifiers valides pour BLOC_INTERATRIAL.

---

## 2. Concepts NOUVEAUX ajoutés (lors de la conversion OWL → V2)

Ces concepts ont été ajoutés par `convert_owl_to_v2.py` lors de mises à jour précédentes de l'OWL. Vérifier qu'ils sont bien dans WebProtégé :

| Concept ID | Nom | Catégorie |
|------------|-----|-----------|
| `TACHYCARDIE_JONCTIONELLE` | Tachycardie jonctionelle | DIAGNOSTIC_MAJEUR |
| `TACHYCARDIE_JONCTIONNELLE_PAR_REENTREE_INTRA_NODALE` | TJ par réentrée intra-nodale | DIAGNOSTIC_MAJEUR |
| `TACHYCARDIE_JONCTIONNELLE_PAR_REENTREE_INTRA_NODALE_TYPIQUE` | TJ réentrée intra-nodale typique (slow-fast) | DIAGNOSTIC_MAJEUR |
| `TACHYCARDIE_JONCTIONNELLE_PAR_REENTREE_INTRA_NODALE_ATYPIQUE` | TJ réentrée intra-nodale atypique | DIAGNOSTIC_MAJEUR |
| `TACHYCARDIE_JONCTIONNELLE_PAR_REENTREE_INTRA_NODALE_FAST_SLOW` | TJ fast-slow | DIAGNOSTIC_MAJEUR |
| `TACHYCARDIE_JONCTIONELLE_PAR_REENTREE_INTRANODALE_SLOW_SLOW` | TJ slow-slow | DIAGNOSTIC_MAJEUR |
| `TACHYCARDIE_JONCTIONNELLE_ECTOPIQUE` | TJ ectopique | DIAGNOSTIC_MAJEUR |
| `TACHYCARDIE_JONCTIONELLE_UTILISANT_UNE_VOIE_ACCESSOIRE` | TJ utilisant voie accessoire | DIAGNOSTIC_MAJEUR |
| `TJ_ORTHODROMIQUE_UTILISANT_UNE_VOIE_ACCESSOIRE` | TJ orthodromique | DIAGNOSTIC_MAJEUR |
| `TJ_ANTIDROMIQUE_UTILISANT_UNE_VOIE_ACCESSOIRE` | TJ antidromique | DIAGNOSTIC_MAJEUR |
| `TACHYCARDIE_DE_COUMEL` | Tachycardie de Coumel | DIAGNOSTIC_MAJEUR |
| `TACHYCARDIE_SUR_FIBRE_DE_MAHAIM` | Tachycardie sur fibre de Mahaim | DIAGNOSTIC_MAJEUR |
| `MORPHOLOGIE_DU_QRS_NORMALE` | Morphologie du QRS normale | DESCRIPTION_ECG |
| `ONDE_F` | Onde F | DESCRIPTION_ECG |
| `PAS_DE_TROUBLE_DE_LA_DEPOLARISATION` | Pas de trouble de la dépolarisation | DESCRIPTION_ECG |
| `ST_RAIDE` | ST raide | QUALIFICATEUR |

---

## 3. Propriété nouvelle : `has_qualifier_families`

C'est une **nouvelle annotation property** à créer dans WebProtégé si elle n'existe pas :

- **Nom** : `has_qualifier_families`
- **Type** : Liste de concept IDs
- **Sémantique** : "Les enfants de ces familles sont des qualifiers valides pour ce concept"
- **Utilisé par** : `scoring_v3.py` — expanse les familles en leurs enfants pour vérifier les qualifiers
- **Concepts concernés** : `BLOC_INTERATRIAL` (pour l'instant)

---

## 4. Propriété nouvelle : `excludes_families`

Déjà dans WebProtégé mais **vérifier la complétude** pour ECG_NORMAL :

```
ECG_NORMAL.excludes_families = [
    "TROUBLE_DE_REPOLARISATION",
    "TROUBLE_DE_LA_DEPOLARISATION_VENTRICULAIRE",
    "ARYTHMIE",
    "TROUBLES_DE_CONDUCTION_ET_DE_L_AUTOMATICITE",   ← NOUVEAU
    "STIMULATION",                                    ← NOUVEAU
    "EVENEMENTS_ECTOPIQUES",                          ← NOUVEAU
    "INTERFERENCE_EXTRA_CARDIAQUE"                    ← NOUVEAU
]
```

---

## 5. Modifications code (pas WebProtégé mais pour référence)

| Fichier | Modification |
|---------|-------------|
| `scoring_v3.py` | Support `has_qualifier_families` dans `_score_one_concept()` et `_score_sub_require()` |
| `neurosymbolic_judge.py` | Règle 5b "DESCRIPTEUR SPÉCIFIQUE > DIAGNOSTIC GLOBAL" dans le prompt du juge |
| `ontology_index.py` → RAG index | Reconstruit (658 docs vs 652) suite aux nouveaux synonymes |

---

## 6. Checklist WebProtégé

- [ ] **ECG_NORMAL** : ajouter 4 `excludes_families`
- [ ] **TROUBLE_DE_REPOLARISATION** : ajouter synonyme "Trouble de la repolarisation"
- [ ] **AXE_NORMAL_DU_QRS** : ajouter 4 synonymes
- [ ] **BLOC_INTERATRIAL** : ajouter `has_qualifier_families: [ONDE_P_ANORMALE]`
- [ ] Créer la property `has_qualifier_families` si elle n'existe pas
- [ ] Vérifier la présence des 16 nouveaux concepts (section 2)
- [ ] Exporter le nouvel OWL et re-générer `ontology_v2.json` via `convert_owl_to_v2.py`
