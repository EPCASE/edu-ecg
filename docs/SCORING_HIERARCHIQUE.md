# 🎯 Scoring Hiérarchique Directionnel

## Problème résolu

Avant cette implémentation, le système ne faisait pas de différence entre :
- Un étudiant qui donne un **diagnostic complet** (ex: "BAV 1")
- Un étudiant qui ne donne qu'un **signe** (ex: "PR allongé")

Or, en médecine, il est crucial de distinguer :
- **Diagnostic** : La pathologie complète identifiée
- **Signe** : Une manifestation électrocardiographique

## Solution : Scoring bidirectionnel

### Hiérarchie médicale (requiresFindings)

```
DIAGNOSTIC (haut niveau, poids élevé)
    ↓ ecg:requiresFindings
SIGNE (bas niveau, descripteur ECG)

Exemple :
BAV de type 1 (diagnostic)
    ↓ requiresFindings
    - PR allongé (signe)
    - Onde P présente (signe)
    - Rythme sinusal (signe)
```

### Règles de scoring

| Situation | Attendu | Réponse | Relation | Score | Explication |
|-----------|---------|---------|----------|-------|-------------|
| **Exact match** | BAV 1 | BAV 1 | Identique | 100% | Parfait |
| **Diagnostic → Signe** | PR allongé | BAV 1 | Student implique Expected | 100% | ✅ L'étudiant a donné le diagnostic complet qui implique le signe |
| **Signe → Diagnostic** | BAV 1 | PR allongé | Expected implique Student | 40% | ⚠️ L'étudiant n'a identifié qu'un signe, pas le diagnostic complet |
| **Autre relation** | - | - | LLM sémantique | Variable | Dépend de la similarité |

## Exemples concrets

### ✅ Exemple 1 : Diagnostic complet reconnu

**Cas :** ECG avec BAV 1
- **Attendu :** "PR allongé" (signe)
- **Réponse étudiant :** "BAV de type 1" (diagnostic)
- **Résultat :**
  - Score : **100%**
  - Type : **CHILD** (implication médicale)
  - Feedback : *"✅ Validé par implication médicale : 'BAV de type 1' implique 'PR allongé'"*

**Raisonnement :** L'étudiant a compris la pathologie complète et l'a nommée correctement. Le diagnostic BAV 1 implique nécessairement un PR allongé.

---

### ⚠️ Exemple 2 : Signe seul (incomplet)

**Cas :** ECG avec BAV 1
- **Attendu :** "BAV de type 1" (diagnostic)
- **Réponse étudiant :** "PR allongé" (signe)
- **Résultat :**
  - Score : **40%**
  - Type : **PARTIAL**
  - Feedback : *"⚠️ Signe correct mais incomplet : 'PR allongé' est un signe de 'BAV de type 1', mais pas le diagnostic complet"*

**Raisonnement :** L'étudiant a identifié un signe correct, mais n'a pas fait l'intégration diagnostique complète. PR allongé peut correspondre à plusieurs pathologies.

---

### ✅ Exemple 3 : Bloc de branche → QRS larges

**Cas :** ECG avec BBG complet
- **Attendu :** "QRS large" (signe)
- **Réponse étudiant :** "Bloc de branche gauche complet" (diagnostic)
- **Résultat :**
  - Score : **100%**
  - Type : **CHILD**
  - Feedback : *"✅ Validé par implication médicale"*

**Raisonnement :** BBG complet implique nécessairement des QRS larges (> 120ms).

---

### ⚠️ Exemple 4 : QRS larges → Bloc de branche

**Cas :** ECG avec BBG complet
- **Attendu :** "Bloc de branche gauche complet" (diagnostic)
- **Réponse étudiant :** "QRS large" (signe)
- **Résultat :**
  - Score : **40%**
  - Type : **PARTIAL**
  - Feedback : *"⚠️ Signe correct mais incomplet"*

**Raisonnement :** QRS larges seuls ne suffisent pas à diagnostiquer un BBG (pourrait être BBD, hémibloc, etc.).

## Implémentation technique

### Code (backend/scoring_service_llm.py)

```python
# 2a. Étudiant → Attendu (ex: "BAV 1" implique "PR allongé")
if self._check_medical_implication(student_text, expected_text):
    return ConceptMatch(
        match_type=MatchType.CHILD,
        score=100.0,
        explanation=f"✅ Validé par implication médicale: '{student_text}' implique '{expected_text}'"
    )

# 2b. Attendu → Étudiant (ex: étudiant dit "PR allongé" pour "BAV 1")
if self._check_medical_implication(expected_text, student_text):
    return ConceptMatch(
        match_type=MatchType.PARTIAL,
        score=40.0,
        explanation=f"⚠️ Signe correct mais incomplet: '{student_text}' est un signe de '{expected_text}', mais pas le diagnostic complet"
    )
```

### Ontologie (data/ontology_from_owl.json)

```json
{
  "BAV_DE_TYPE_1": {
    "concept_name": "BAV de type 1",
    "implications": ["PR allongé"],
    "categorie": "DESCRIPTEUR_ECG"
  },
  "BLOC_DE_BRANCHE_GAUCHE_COMPLET": {
    "concept_name": "Bloc de branche gauche complet",
    "implications": ["QRS large", "QRS > 120 ms"],
    "categorie": "SIGNE_ECG_PATHOLOGIQUE"
  }
}
```

## Tests de validation

Voir `test_scoring_hierarchique.py` pour les tests automatisés.

**Résultats :**
```
✅ TEST 1: BAV 1 → BAV 1 = 100% (exact)
✅ TEST 2: PR allongé → PR allongé = 100% (exact)
✅ TEST 3: BAV 1 → PR allongé = 100% (implication validée)
✅ TEST 4: PR allongé → BAV 1 = 40% (signe incomplet)
✅ TEST 5: BBG complet → QRS large = 100% (implication validée)
✅ TEST 6: QRS large → BBG complet = 40% (signe incomplet)
```

## Avantages pédagogiques

1. **Feedback précis :**
   - L'étudiant comprend la différence entre identifier un signe et poser un diagnostic
   - Messages clairs : "Signe correct mais diagnostic incomplet"

2. **Encouragement :**
   - Un étudiant qui identifie correctement un signe reçoit 40% (pas 0%)
   - Cela valorise la progression de l'apprentissage

3. **Alignement médical :**
   - Reflète la hiérarchie réelle : Signe → Syndrome → Diagnostic
   - Encourage le raisonnement clinique complet

## Ajustements possibles

### Score partiel configurable

Le score de 40% pour un signe incomplet peut être ajusté selon le niveau :
- **Débutant (L2)** : 50% (encouragement)
- **Intermédiaire (L3)** : 40% (standard actuel)
- **Avancé (M1)** : 30% (exigence élevée)

### Catégories d'implications

On pourrait affiner avec :
- **Implication forte** (BAV 1 → PR allongé) : 40%
- **Implication faible** (Hypertrophie VG → Ondes R amples) : 30%
- **Signe suggestif** (QRS larges → possiblement BBG) : 20%

## Maintenance

### Mise à jour de l'ontologie

Les implications sont extraites automatiquement de WebProtégé via `ecg:requiresFindings`.

Pour ajouter une nouvelle implication :
1. Ouvrir WebProtégé
2. Sélectionner le diagnostic (ex: "BAV 1")
3. Ajouter une relation `ecg:requiresFindings` vers le signe (ex: "PR allongé")
4. Régénérer l'ontologie : `python backend/rdf_owl_extractor.py`
5. Redémarrer les interfaces

**Aucune modification de code n'est nécessaire !**

---

**Auteur :** BMAD Party Mode (Winston, Amelia, Murat, John, Mary)  
**Date :** 2026-01-11  
**Version :** 1.0
