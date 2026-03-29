# 🩺 Le Problème du Diagnostic Implicite : le cas ECG Normal

## Le problème

Quand un cardiologue interprète un ECG normal, il peut répondre de plusieurs façons :

### Réponse explicite courte (détectée ✅)
> « **ECG normal** : rythme sinusal, QRS fins, pas de trouble de repolarisation »

Le pipeline trouve immédiatement "ECG normal" → match exact → **100%**.

### Réponse explicite en langage naturel (mal détectée ⚠️)
> « Fréquence cardiaque à 60/min, Rythme sinusal, QRS fins… **Je dirai que cet ECG est NORMAL**, cependant… »

L'étudiant écrit **explicitement** le diagnostic mais dans une phrase longue.
Le NER (GPT-4o) extrait les composants individuels (Rythme sinusal, QRS fins, etc.)
mais traite la phrase conclusive comme du texte narratif et ne reconstitue pas
"ECG normal" comme entité. Score via hiérarchie : **90%** (child_gen1).

### Réponse implicite (mal détectée ⚠️)
> « RS, 62bpm, QRS fins, pas de trouble repo ni séquelle de nécrose, QT normal »

L'étudiant décrit **tous les composants** d'un ECG normal (rythme sinusal, fréquence
normale, QRS fins, pas d'anomalie) mais ne formule jamais le mot "ECG normal".

Le pipeline trouve seulement "QRS fins" (enfant de génération 2 d'ECG_NORMAL)
→ score dégressif → **80%**.

## Pourquoi c'est un problème

En pratique clinique, décrire méthodiquement un ECG normal est **la bonne méthode**.
Un étudiant qui liste systématiquement chaque paramètre (rythme, fréquence, axe, PR,
QRS, repolarisation) démontre une approche rigoureuse et ne devrait pas être pénalisé
par rapport à un étudiant qui écrit simplement "ECG normal".

### Le problème structurel des concepts compositionnels

"ECG normal" n'est pas un signe ECG observable — c'est une **conclusion diagnostique**
qui se déduit quand *tous* les paramètres sont normaux ensemble (rythme sinusal +
fréquence normale + axe normal + PR normal + QRS fins + pas de trouble de repolarisation…).
C'est un concept **composé de ~5 paramètres**.

Le scoring hiérarchique traite ECG_NORMAL comme un parent avec des enfants. Si un seul
enfant est trouvé (ex: "Rythme sinusal"), le système attribue 90%. Or un ECG peut
avoir un rythme sinusal et être profondément pathologique (infarctus, HVG massive…).
Attribuer "ECG normal" sur la base d'un seul composant parmi 5 est **excessif**.

Par contraste, la hiérarchie fonctionne correctement pour les concepts **unitaires**
de spécialisation : "Flutter antihoraire" → "Flutter droit typique" est légitime.

### Comparaison d'étudiants réels

| Étudiant | Formulation | Score | Mécanisme |
|---|---|---|---|
| ECG-WY55 | `"ECG normal : rythme sinusal, régulier, QRS fins…"` | **100%** | Match exact (coupe-circuit) |
| ECG-1I3Q | `"…Ecg normal."` (fin de texte) | **100%** | Match exact (coupe-circuit) |
| ECG-3SIJ | `"…→ ECG normal"` (après flèche) | **100%** | Match exact (coupe-circuit) |
| **ECG-2DZE** | `"…Je dirai que cet ECG est NORMAL, cependant…"` | **90%** | child_gen1 via Rythme sinusal |
| ECG-3RMP | Composants décrits, jamais "ECG normal" | **80%** | child_gen2 via QRS fins |
| ECG-87P4 | `"normal"` seul | **0%** | Aucun match |

ECG-2DZE et ECG-3RMP sont **injustement pénalisés** : leurs réponses sont médicalement valides.

## Pourquoi le pipeline ne sait pas le faire

Le pipeline fonctionne en mode **bottom-up, concept par concept** :

```
Texte → [terme₁, terme₂, ...] → [concept₁, concept₂, ...] → comparaison avec golden set
```

Il n'a **pas de mécanisme d'inférence** qui dirait :

```
SI rythme_sinusal ∈ extraits
ET QRS_fins ∈ extraits
ET ¬trouble_repolarisation ∈ extraits
ET PR_normal ∈ extraits
ALORS inférer ECG_NORMAL
```

## L'ontologie contient l'information

Dans l'ontologie OWL, ECG_NORMAL a des **enfants** :
- Rythme sinusal
- QRS fins
- PR normal
- Axe normal
- Normocarde
- etc.

Ces relations existent mais sont utilisées **uniquement pour le scoring dégressif**
(si l'étudiant donne un composant, il obtient un score partiel). Elles ne sont pas
utilisées pour **inférer le concept parent** à partir de la conjonction des composants.

## Solutions proposées

### Solution 1 : Règles d'inférence explicites (court terme)
Définir des **règles logiques** dans l'ontologie pour certains concepts-parapluie :

```json
{
  "concept": "ECG_NORMAL",
  "inference_rule": {
    "type": "conjunction",
    "required": ["RYTHME_SINUSAL", "QRS_FINS"],
    "optional": ["PR_NORMAL", "AXE_NORMAL", "NORMOCARDE"],
    "min_required_optional": 1,
    "absence_required": ["ANOMALIE_DES_ONDES_T", "SÉQUELLE_DE_NÉCROSE"]
  }
}
```

**Avantage** : Déterministe, explicable, pas de coût API.
**Limite** : Nécessite de définir manuellement les règles pour chaque concept-parapluie.

### Solution 2 : Raisonnement LLM post-extraction (moyen terme)
Après extraction des concepts, demander au LLM :
> « L'étudiant a mentionné [rythme sinusal, QRS fins, pas de repolarisation, PR normal].
> Est-ce que la conjonction de ces concepts correspond à un diagnostic non explicitement
> nommé ? »

**Avantage** : Généraliste, pas besoin de règles manuelles.
**Limite** : Coût API supplémentaire, non déterministe.

### Solution 3 : Raisonnement ontologique formel (long terme)
Utiliser un **raisonneur OWL** (HermiT, Pellet) pour inférer automatiquement les
concepts parents à partir des propriétés définitionnelles de l'ontologie.

**Avantage** : Exploite pleinement la sémantique formelle de l'ontologie.
**Limite** : Complexité technique, nécessite de modéliser les conditions nécessaires
et suffisantes dans l'OWL.

## Impact

Ce problème concerne principalement ECG_NORMAL car c'est le diagnostic le plus
fréquemment décrit de manière implicite. Mais le même pattern peut se retrouver
pour d'autres diagnostics-parapluie où l'étudiant décrit les composants sans
nommer le diagnostic global.

## Données disponibles

- **15 cas golden set** annotés par un cardiologue expert
- **22 corrections étudiantes** avec trace pipeline complète
- **Cas de test spécifiques** : ECG-2DZE (explicite en phrase, 90%), ECG-3RMP (implicite, 80%) vs ECG-WY55 (explicite isolé, 100%)
- **Ontologie OWL** avec relations parent-enfant complètes
