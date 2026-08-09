# ECG Online — Corpus ciblé de 100 réponses synthétiques

**Version :** 0.1  
**Date :** 2 août 2026  
**Branche de référence :** `main`  
**Statut :** corpus synthétique de développement, à relire et adjudiquer par des cardiologues avant utilisation comme gold standard.

## Objectif

Ce corpus complète le corpus historique par 100 réponses conçues pour tester les phénomènes que le pipeline fragmenté évalue difficilement : implicites, relations entre propositions, contradictions, polarité, degré de certitude, cohérence entre mesures et interprétation, et robustesse aux paraphrases.

Il comporte **10 strates de 10 réponses**. Les cas indiqués sont des ancrages dans la banque actuelle ; les textes sont synthétiques et ne prétendent pas reproduire des réponses étudiantes déjà recueillies.

## Schéma d’annotation

Chaque réponse comprend :

- un identifiant stable ;
- le cas ECG auquel elle est rattachée ;
- le phénomène principal testé ;
- les éléments corrects que le juge global devrait conserver ;
- les éléments faux, contradictoires ou insuffisants ;
- le type de jugement sémantique attendu ;
- un niveau de criticité.

Le fichier JSONL associé constitue la version machine-readable.

## Répartition

| Code | Strate | N |
|---|---|---:|
| `EXPLICIT` | Diagnostic explicitement nommé | 10 |
| `IMPLICIT` | Diagnostic seulement décrit | 10 |
| `PARTIAL` | Description partielle | 10 |
| `CORRECT_FALSE` | Diagnostic correct avec un élément faux | 10 |
| `CONTRADICTORY` | Deux diagnostics ou conclusions contradictoires | 10 |
| `NEG_THEN_ASSERT` | Négation puis affirmation du même concept | 10 |
| `UNSUPPORTED_CRITICAL` | Diagnostic grave non soutenu | 10 |
| `HEDGED` | Formulation hésitante ou différentielle | 10 |
| `NUMERIC_CONFLICT` | Mesure numérique incompatible avec son interprétation | 10 |
| `LEXICAL_DISTANCE` | Réponse correcte mais lexicalement éloignée du gold | 10 |

---

## Diagnostic explicitement nommé

### EXPLICIT-01 — Cas 3 · ECG normal

> Rythme sinusal à 70/min, axe normal, PR et QRS normaux, sans anomalie de repolarisation. Il s’agit d’un ECG strictement normal.

- **Jugement attendu :** `explicit_correct`
- **Éléments corrects à préserver :** rythme sinusal ; fréquence normale ; ECG normal
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### EXPLICIT-02 — Cas 6 · Hypertrophie ventriculaire gauche électrique

> Le tracé montre une hypertrophie ventriculaire gauche électrique avec voltages précordiaux élevés et indice de Sokolow positif.

- **Jugement attendu :** `explicit_correct`
- **Éléments corrects à préserver :** hypertrophie ventriculaire gauche ; voltages élevés ; Sokolow positif
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### EXPLICIT-03 — Cas 9 · Bloc de branche droit complet

> Rythme sinusal avec bloc de branche droit complet : QRS élargis, aspect rSR’ en V1 et onde S terminale large en DI-V6.

- **Jugement attendu :** `explicit_correct`
- **Éléments corrects à préserver :** bloc de branche droit complet ; QRS larges
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### EXPLICIT-04 — Cas 24 · BAV du deuxième degré Mobitz I

> BAV du deuxième degré de type Mobitz I, avec allongement progressif du PR avant une onde P bloquée.

- **Jugement attendu :** `explicit_correct`
- **Éléments corrects à préserver :** BAV Mobitz I ; allongement progressif du PR
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### EXPLICIT-05 — Cas 25 · BAV du deuxième degré Mobitz II

> BAV du deuxième degré de type Mobitz II : les PR conduits restent constants et une onde P est bloquée brutalement.

- **Jugement attendu :** `explicit_correct`
- **Éléments corrects à préserver :** BAV Mobitz II ; PR constants ; onde P bloquée
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### EXPLICIT-06 — Cas 37 · Fibrillation atriale

> Fibrillation atriale avec absence d’ondes P organisées et réponse ventriculaire totalement irrégulière.

- **Jugement attendu :** `explicit_correct`
- **Éléments corrects à préserver :** fibrillation atriale ; absence d’ondes P ; irrégularité complète
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### EXPLICIT-07 — Cas 41 · Flutter atrial typique

> Flutter atrial commun typique, avec activité atriale en dents de scie et conduction atrioventriculaire régulière.

- **Jugement attendu :** `explicit_correct`
- **Éléments corrects à préserver :** flutter atrial typique ; ondes F en dents de scie
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### EXPLICIT-08 — Cas 48 · Tachycardie ventriculaire certaine

> Tachycardie ventriculaire monomorphe, certifiée par une dissociation atrioventriculaire et un complexe de capture.

- **Jugement attendu :** `explicit_correct`
- **Éléments corrects à préserver :** tachycardie ventriculaire ; dissociation atrioventriculaire ; capture
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

### EXPLICIT-09 — Cas 55 · Péricardite aiguë

> Péricardite aiguë avec sus-décalage ST diffus, concave, et sous-décalage du segment PR.

- **Jugement attendu :** `explicit_correct`
- **Éléments corrects à préserver :** péricardite aiguë ; sus-décalage ST diffus ; sous-décalage PR
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### EXPLICIT-10 — Cas 74 · Syndrome de Brugada type 1

> Aspect diagnostique de syndrome de Brugada de type 1 avec sus-décalage ST en dôme en V1-V2 suivi d’une onde T négative.

- **Jugement attendu :** `explicit_correct`
- **Éléments corrects à préserver :** Brugada type 1 ; sus-décalage en dôme V1-V2
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

## Diagnostic seulement décrit

### IMPLICIT-01 — Cas 6 · Hypertrophie ventriculaire gauche électrique

> Ondes R très amples en V5-V6, ondes S profondes en V1-V2 et indice de Sokolow mesuré à 42 mm.

- **Jugement attendu :** `implicit_complete`
- **Éléments corrects à préserver :** critères d’HVG ; Sokolow > 35 mm
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible
- **Note de conception :** Le diagnostic d’HVG n’est pas nommé.

### IMPLICIT-02 — Cas 9 · Bloc de branche droit complet

> QRS à 145 ms, morphologie rSR’ en V1 et large onde S terminale en DI et V6.

- **Jugement attendu :** `implicit_complete`
- **Éléments corrects à préserver :** QRS larges ; rSR’ V1 ; S terminale DI-V6
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### IMPLICIT-03 — Cas 13 · Bloc de branche gauche complet

> QRS à 160 ms, complexe négatif en V1, grande onde R empâtée en DI et V6, avec repolarisation secondaire discordante.

- **Jugement attendu :** `implicit_complete`
- **Éléments corrects à préserver :** QRS larges ; morphologie de BBG ; discordance secondaire
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### IMPLICIT-04 — Cas 24 · BAV du deuxième degré Mobitz I

> L’intervalle PR s’allonge d’un battement à l’autre, puis une onde P n’est pas suivie d’un QRS avant reprise du cycle.

- **Jugement attendu :** `implicit_complete`
- **Éléments corrects à préserver :** allongement progressif du PR ; onde P bloquée
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### IMPLICIT-05 — Cas 25 · BAV du deuxième degré Mobitz II

> Les intervalles PR des battements conduits sont identiques, puis survient sans avertissement une onde P non conduite.

- **Jugement attendu :** `implicit_complete`
- **Éléments corrects à préserver :** PR constants ; blocage inopiné d’une onde P
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### IMPLICIT-06 — Cas 32 · Extrasystole ventriculaire

> Complexe prématuré large, sans onde P visible avant lui, de morphologie différente des QRS sinusaux et suivi d’un repos compensateur complet.

- **Jugement attendu :** `implicit_complete`
- **Éléments corrects à préserver :** complexe prématuré large ; absence de P préalable ; repos compensateur
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### IMPLICIT-07 — Cas 37 · Fibrillation atriale

> Aucune onde P répétitive n’est identifiable et les intervalles RR varient de façon anarchique.

- **Jugement attendu :** `implicit_complete`
- **Éléments corrects à préserver :** absence d’ondes P organisées ; irrégularité complète
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### IMPLICIT-08 — Cas 41 · Flutter atrial typique

> Activité atriale continue proche de 300/min, en dents de scie dans les dérivations inférieures, avec plusieurs activations atriales pour un QRS.

- **Jugement attendu :** `implicit_complete`
- **Éléments corrects à préserver :** ondes F en dents de scie ; activité atriale rapide ; bloc AV fonctionnel
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### IMPLICIT-09 — Cas 51 · Préexcitation ventriculaire

> PR à 95 ms, début du QRS empâté par une onde delta et durée totale du QRS augmentée.

- **Jugement attendu :** `implicit_complete`
- **Éléments corrects à préserver :** PR court ; onde delta ; QRS élargi
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### IMPLICIT-10 — Cas 55 · Péricardite aiguë

> Sus-décalage ST concave dans de nombreuses dérivations, sans territoire coronaire unique, associé à un sous-décalage du PR.

- **Jugement attendu :** `implicit_complete`
- **Éléments corrects à préserver :** sus-décalage ST diffus ; sous-décalage PR
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

## Description partielle

### PARTIAL-01 — Cas 3 · ECG normal

> Rythme sinusal à 70/min avec QRS fins.

- **Jugement attendu :** `implicit_partial`
- **Éléments corrects à préserver :** rythme sinusal ; fréquence normale ; QRS fins
- **Éléments problématiques à détecter :** normalité globale non démontrée
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### PARTIAL-02 — Cas 6 · Hypertrophie ventriculaire gauche électrique

> Indice de Sokolow à 40 mm.

- **Jugement attendu :** `implicit_partial`
- **Éléments corrects à préserver :** Sokolow positif
- **Éléments problématiques à détecter :** diagnostic non formulé ; autres critères non décrits
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### PARTIAL-03 — Cas 9 · Bloc de branche droit complet

> QRS larges avec un aspect rSR’ en V1.

- **Jugement attendu :** `implicit_partial`
- **Éléments corrects à préserver :** QRS larges ; rSR’ V1
- **Éléments problématiques à détecter :** critères latéraux non décrits
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### PARTIAL-04 — Cas 20 · Pause sinusale

> Il existe une longue pause avec un rythme lent après celle-ci.

- **Jugement attendu :** `insufficient`
- **Éléments corrects à préserver :** pause ; échappement possible
- **Éléments problématiques à détecter :** mécanisme sinusal ou atrioventriculaire non résolu
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### PARTIAL-05 — Cas 24 · BAV du deuxième degré Mobitz I

> BAV du deuxième degré avec une onde P bloquée.

- **Jugement attendu :** `implicit_partial`
- **Éléments corrects à préserver :** BAV du deuxième degré ; onde P bloquée
- **Éléments problématiques à détecter :** type Mobitz non caractérisé
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### PARTIAL-06 — Cas 32 · Extrasystole ventriculaire

> Présence de quelques extrasystoles.

- **Jugement attendu :** `implicit_partial`
- **Éléments corrects à préserver :** extrasystoles
- **Éléments problématiques à détecter :** origine atriale ou ventriculaire non précisée
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### PARTIAL-07 — Cas 41 · Flutter atrial typique

> Tachyarythmie atriale régulière.

- **Jugement attendu :** `implicit_partial`
- **Éléments corrects à préserver :** tachyarythmie atriale ; régularité
- **Éléments problématiques à détecter :** flutter non démontré
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### PARTIAL-08 — Cas 48 · Tachycardie ventriculaire certaine

> Tachycardie régulière à QRS larges.

- **Jugement attendu :** `implicit_partial`
- **Éléments corrects à préserver :** tachycardie régulière ; QRS larges
- **Éléments problématiques à détecter :** origine ventriculaire non certifiée ; signes de certitude absents
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

### PARTIAL-09 — Cas 55 · Péricardite aiguë

> Sus-décalage ST diffus.

- **Jugement attendu :** `implicit_partial`
- **Éléments corrects à préserver :** sus-décalage ST diffus
- **Éléments problématiques à détecter :** segment PR non décrit ; différentiel coronaire non discuté
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### PARTIAL-10 — Cas 59 · Syndrome coronarien aigu ST+ territorialisé

> Sus-décalage ST inférieur.

- **Jugement attendu :** `implicit_partial`
- **Éléments corrects à préserver :** sus-décalage ST inférieur
- **Éléments problématiques à détecter :** miroir et extension non décrits ; diagnostic non nommé
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

## Diagnostic correct avec un élément faux

### CORRECT_FALSE-01 — Cas 3 · ECG normal

> ECG strictement normal, avec toutefois un QTc très allongé à 520 ms.

- **Jugement attendu :** `correct_with_internal_error`
- **Éléments corrects à préserver :** ECG normal
- **Éléments problématiques à détecter :** QTc 520 ms incompatible avec ECG strictement normal
- **Incertitude/différentiel :** aucun
- **Criticité :** modérée

### CORRECT_FALSE-02 — Cas 6 · Hypertrophie ventriculaire gauche électrique

> Hypertrophie ventriculaire gauche électrique avec microvoltage diffus des QRS.

- **Jugement attendu :** `correct_with_internal_error`
- **Éléments corrects à préserver :** hypertrophie ventriculaire gauche
- **Éléments problématiques à détecter :** microvoltage diffus incompatible avec les voltages élevés décrits
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### CORRECT_FALSE-03 — Cas 9 · Bloc de branche droit complet

> Bloc de branche droit complet avec des QRS fins mesurés à 90 ms.

- **Jugement attendu :** `correct_with_internal_error`
- **Éléments corrects à préserver :** bloc de branche droit complet
- **Éléments problématiques à détecter :** QRS à 90 ms incompatible avec un bloc complet
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### CORRECT_FALSE-04 — Cas 24 · BAV du deuxième degré Mobitz I

> BAV Mobitz I, mais les intervalles PR restent strictement constants avant l’onde P bloquée.

- **Jugement attendu :** `correct_with_internal_error`
- **Éléments corrects à préserver :** BAV Mobitz I
- **Éléments problématiques à détecter :** PR constants incompatibles avec Mobitz I
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### CORRECT_FALSE-05 — Cas 25 · BAV du deuxième degré Mobitz II

> BAV Mobitz II avec allongement progressif du PR jusqu’au blocage d’une onde P.

- **Jugement attendu :** `correct_with_internal_error`
- **Éléments corrects à préserver :** BAV Mobitz II
- **Éléments problématiques à détecter :** allongement progressif compatible avec Mobitz I, pas Mobitz II
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### CORRECT_FALSE-06 — Cas 37 · Fibrillation atriale

> Fibrillation atriale, avec des ondes P sinusales régulières avant chaque QRS.

- **Jugement attendu :** `correct_with_internal_error`
- **Éléments corrects à préserver :** fibrillation atriale
- **Éléments problématiques à détecter :** ondes P sinusales régulières incompatibles avec FA
- **Incertitude/différentiel :** aucun
- **Criticité :** modérée

### CORRECT_FALSE-07 — Cas 41 · Flutter atrial typique

> Flutter atrial typique, sans aucune activité atriale organisée et avec une irrégularité ventriculaire anarchique.

- **Jugement attendu :** `correct_with_internal_error`
- **Éléments corrects à préserver :** flutter atrial typique
- **Éléments problématiques à détecter :** absence d’activité atriale organisée ; irrégularité anarchique évoquant FA
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### CORRECT_FALSE-08 — Cas 48 · Tachycardie ventriculaire certaine

> Tachycardie ventriculaire, alors que chaque QRS fin est précédé d’une onde P avec un PR fixe.

- **Jugement attendu :** `correct_with_internal_error`
- **Éléments corrects à préserver :** tachycardie ventriculaire
- **Éléments problématiques à détecter :** QRS fins ; conduction AV 1:1 fixe incompatible avec la justification donnée
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

### CORRECT_FALSE-09 — Cas 55 · Péricardite aiguë

> Péricardite aiguë avec un sus-décalage ST limité au territoire inférieur et un miroir antérieur net.

- **Jugement attendu :** `correct_with_internal_error`
- **Éléments corrects à préserver :** péricardite aiguë
- **Éléments problématiques à détecter :** territorialité et miroir évocateurs d’un SCA plutôt que d’une péricardite diffuse
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

### CORRECT_FALSE-10 — Cas 74 · Syndrome de Brugada type 1

> Brugada type 1 avec un sus-décalage exclusivement inférieur et aucun changement en V1-V2.

- **Jugement attendu :** `correct_with_internal_error`
- **Éléments corrects à préserver :** Brugada type 1
- **Éléments problématiques à détecter :** topographie incompatible avec Brugada type 1
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

## Deux diagnostics ou conclusions contradictoires

### CONTRADICTORY-01 — Cas 3 · ECG normal

> Le tracé est strictement normal. Il existe néanmoins un bloc de branche gauche complet.

- **Jugement attendu :** `global_contradiction`
- **Éléments corrects à préserver :** ECG normal ; bloc de branche gauche complet
- **Éléments problématiques à détecter :** normalité et BBG complet simultanés
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### CONTRADICTORY-02 — Cas 2 · Artéfact de tremblement avec rythme sinusal

> Le rythme est sinusal avec une onde P avant chaque QRS, et il s’agit en même temps d’une fibrillation atriale.

- **Jugement attendu :** `global_contradiction`
- **Éléments corrects à préserver :** rythme sinusal ; fibrillation atriale
- **Éléments problématiques à détecter :** rythme sinusal et FA affirmés simultanément
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### CONTRADICTORY-03 — Cas 24 · BAV du deuxième degré Mobitz I

> Il s’agit à la fois d’un Mobitz I avec Wenckebach et d’un Mobitz II à PR constants.

- **Jugement attendu :** `global_contradiction`
- **Éléments corrects à préserver :** Mobitz I ; Mobitz II
- **Éléments problématiques à détecter :** mécanismes contradictoires
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### CONTRADICTORY-04 — Cas 28 · BAV complet avec échappement jonctionnel

> BAV complet avec dissociation atrioventriculaire, mais toutes les ondes P sont conduites en 1:1 avec un PR fixe.

- **Jugement attendu :** `global_contradiction`
- **Éléments corrects à préserver :** BAV complet ; conduction AV 1:1
- **Éléments problématiques à détecter :** dissociation AV et conduction 1:1
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

### CONTRADICTORY-05 — Cas 37 · Fibrillation atriale

> Fibrillation atriale certaine sur un rythme sinusal régulier.

- **Jugement attendu :** `global_contradiction`
- **Éléments corrects à préserver :** fibrillation atriale ; rythme sinusal régulier
- **Éléments problématiques à détecter :** FA et rythme sinusal
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### CONTRADICTORY-06 — Cas 41 · Flutter atrial typique

> Flutter atrial typique et fibrillation atriale simultanée sur tout le tracé.

- **Jugement attendu :** `global_contradiction`
- **Éléments corrects à préserver :** flutter atrial ; fibrillation atriale
- **Éléments problématiques à détecter :** deux organisations atriales exclusives affirmées simultanément
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### CONTRADICTORY-07 — Cas 44 · Tachycardie par réentrée intranodale

> Tachycardie par réentrée intranodale, mais également tachycardie sinusale avec ondes P sinusales avant chaque QRS.

- **Jugement attendu :** `global_contradiction`
- **Éléments corrects à préserver :** AVNRT ; tachycardie sinusale
- **Éléments problématiques à détecter :** mécanismes simultanément affirmés
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### CONTRADICTORY-08 — Cas 48 · Tachycardie ventriculaire certaine

> Il s’agit d’une tachycardie ventriculaire certifiée par dissociation AV et, simultanément, d’une AVNRT conduite avec aberration.

- **Jugement attendu :** `global_contradiction`
- **Éléments corrects à préserver :** tachycardie ventriculaire ; AVNRT avec aberration
- **Éléments problématiques à détecter :** diagnostics mécanistiquement exclusifs
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

### CONTRADICTORY-09 — Cas 55 · Péricardite aiguë

> Péricardite aiguë certaine et infarctus inférieur ST+ certain sur le même aspect.

- **Jugement attendu :** `global_contradiction`
- **Éléments corrects à préserver :** péricardite aiguë ; SCA ST+ inférieur
- **Éléments problématiques à détecter :** deux diagnostics définitifs concurrents sans hiérarchisation
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

### CONTRADICTORY-10 — Cas 73 · Hyperkaliémie menaçante

> Hyperkaliémie sévère avec QRS très élargis, mais ECG par ailleurs strictement normal.

- **Jugement attendu :** `global_contradiction`
- **Éléments corrects à préserver :** hyperkaliémie sévère ; ECG normal
- **Éléments problématiques à détecter :** anomalie grave et normalité simultanées
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

## Négation puis affirmation du même concept

### NEG_THEN_ASSERT-01 — Cas 3 · ECG normal

> Il n’y a pas d’hypertrophie ventriculaire gauche. En conclusion, il existe une hypertrophie ventriculaire gauche nette.

- **Jugement attendu :** `same_concept_polarity_conflict`
- **Éléments corrects à préserver :** hypertrophie ventriculaire gauche absente ; hypertrophie ventriculaire gauche présente
- **Éléments problématiques à détecter :** conflit de polarité sur le même concept
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NEG_THEN_ASSERT-02 — Cas 9 · Bloc de branche droit complet

> Pas de bloc de branche droit. L’aspect est finalement celui d’un bloc de branche droit complet.

- **Jugement attendu :** `same_concept_polarity_conflict`
- **Éléments corrects à préserver :** BBD absent ; BBD présent
- **Éléments problématiques à détecter :** conflit de polarité
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NEG_THEN_ASSERT-03 — Cas 24 · BAV du deuxième degré Mobitz I

> Il n’existe pas de phénomène de Wenckebach. Le diagnostic retenu est pourtant un Mobitz I avec Wenckebach.

- **Jugement attendu :** `same_concept_polarity_conflict`
- **Éléments corrects à préserver :** Wenckebach absent ; Mobitz I/Wenckebach présent
- **Éléments problématiques à détecter :** conflit de polarité et de mécanisme
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NEG_THEN_ASSERT-04 — Cas 25 · BAV du deuxième degré Mobitz II

> Aucun argument pour un Mobitz II. Il s’agit d’un BAV Mobitz II certain.

- **Jugement attendu :** `same_concept_polarity_conflict`
- **Éléments corrects à préserver :** Mobitz II absent ; Mobitz II présent
- **Éléments problématiques à détecter :** conflit de polarité
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NEG_THEN_ASSERT-05 — Cas 37 · Fibrillation atriale

> Pas de fibrillation atriale sur ce tracé. Le diagnostic final est une fibrillation atriale.

- **Jugement attendu :** `same_concept_polarity_conflict`
- **Éléments corrects à préserver :** FA absente ; FA présente
- **Éléments problématiques à détecter :** conflit de polarité
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NEG_THEN_ASSERT-06 — Cas 41 · Flutter atrial typique

> Je n’identifie aucun flutter. En conclusion, flutter atrial typique.

- **Jugement attendu :** `same_concept_polarity_conflict`
- **Éléments corrects à préserver :** flutter absent ; flutter présent
- **Éléments problématiques à détecter :** conflit de polarité
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NEG_THEN_ASSERT-07 — Cas 48 · Tachycardie ventriculaire certaine

> Cette tachycardie n’est pas ventriculaire. Il s’agit finalement d’une tachycardie ventriculaire certaine.

- **Jugement attendu :** `same_concept_polarity_conflict`
- **Éléments corrects à préserver :** TV absente ; TV présente
- **Éléments problématiques à détecter :** conflit de polarité
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

### NEG_THEN_ASSERT-08 — Cas 55 · Péricardite aiguë

> Pas d’argument pour une péricardite. Le tracé est typique d’une péricardite aiguë.

- **Jugement attendu :** `same_concept_polarity_conflict`
- **Éléments corrects à préserver :** péricardite absente ; péricardite présente
- **Éléments problématiques à détecter :** conflit de polarité
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NEG_THEN_ASSERT-09 — Cas 59 · Syndrome coronarien aigu ST+

> Il n’y a aucun sus-décalage ST. Je conclus à un infarctus ST+ avec sus-décalage inférieur.

- **Jugement attendu :** `same_concept_polarity_conflict`
- **Éléments corrects à préserver :** sus-décalage absent ; sus-décalage présent ; SCA ST+
- **Éléments problématiques à détecter :** conflit de polarité
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

### NEG_THEN_ASSERT-10 — Cas 74 · Syndrome de Brugada type 1

> Aucun aspect de Brugada. En conclusion, syndrome de Brugada type 1.

- **Jugement attendu :** `same_concept_polarity_conflict`
- **Éléments corrects à préserver :** Brugada absent ; Brugada présent
- **Éléments problématiques à détecter :** conflit de polarité
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

## Diagnostic grave non soutenu

### UNSUPPORTED_CRITICAL-01 — Cas 3 · ECG normal

> Infarctus antérieur ST+ massif.

- **Jugement attendu :** `critical_unsupported_wrong_diagnosis`
- **Éléments corrects à préserver :** aucun
- **Éléments problématiques à détecter :** diagnostic urgent faux et sans description justificative
- **Incertitude/différentiel :** aucun
- **Criticité :** critique

### UNSUPPORTED_CRITICAL-02 — Cas 2 · Artéfact de tremblement avec rythme sinusal

> Tachycardie ventriculaire polymorphe.

- **Jugement attendu :** `critical_unsupported_wrong_diagnosis`
- **Éléments corrects à préserver :** aucun
- **Éléments problématiques à détecter :** diagnostic rythmique grave non soutenu
- **Incertitude/différentiel :** aucun
- **Criticité :** critique

### UNSUPPORTED_CRITICAL-03 — Cas 6 · Hypertrophie ventriculaire gauche électrique

> Bloc atrioventriculaire complet nécessitant une stimulation urgente.

- **Jugement attendu :** `critical_unsupported_wrong_diagnosis`
- **Éléments corrects à préserver :** aucun
- **Éléments problématiques à détecter :** BAV complet non soutenu
- **Incertitude/différentiel :** aucun
- **Criticité :** critique

### UNSUPPORTED_CRITICAL-04 — Cas 9 · Bloc de branche droit complet

> Embolie pulmonaire massive avec cœur pulmonaire aigu.

- **Jugement attendu :** `critical_unsupported_wrong_diagnosis`
- **Éléments corrects à préserver :** aucun
- **Éléments problématiques à détecter :** diagnostic étiologique grave non soutenu par la réponse
- **Incertitude/différentiel :** aucun
- **Criticité :** critique

### UNSUPPORTED_CRITICAL-05 — Cas 20 · Pause sinusale

> Syndrome coronarien aigu inférieur avec indication de reperfusion immédiate.

- **Jugement attendu :** `critical_unsupported_wrong_diagnosis`
- **Éléments corrects à préserver :** aucun
- **Éléments problématiques à détecter :** SCA ST+ non soutenu
- **Incertitude/différentiel :** aucun
- **Criticité :** critique

### UNSUPPORTED_CRITICAL-06 — Cas 32 · Extrasystole ventriculaire

> Fibrillation ventriculaire.

- **Jugement attendu :** `critical_unsupported_wrong_diagnosis`
- **Éléments corrects à préserver :** aucun
- **Éléments problématiques à détecter :** FV non soutenue et incompatible avec un tracé analysable en battements
- **Incertitude/différentiel :** aucun
- **Criticité :** critique

### UNSUPPORTED_CRITICAL-07 — Cas 39 · Arythmie sinusale respiratoire

> Fibrillation atriale préexcitée maligne.

- **Jugement attendu :** `critical_unsupported_wrong_diagnosis`
- **Éléments corrects à préserver :** aucun
- **Éléments problématiques à détecter :** diagnostic grave non soutenu
- **Incertitude/différentiel :** aucun
- **Criticité :** critique

### UNSUPPORTED_CRITICAL-08 — Cas 40 · Tachycardie sinusale réactionnelle

> Tachycardie ventriculaire soutenue.

- **Jugement attendu :** `critical_unsupported_wrong_diagnosis`
- **Éléments corrects à préserver :** aucun
- **Éléments problématiques à détecter :** TV non soutenue par aucun argument
- **Incertitude/différentiel :** aucun
- **Criticité :** critique

### UNSUPPORTED_CRITICAL-09 — Cas 55 · Péricardite aiguë

> Occlusion aiguë du tronc commun gauche.

- **Jugement attendu :** `critical_unsupported_wrong_diagnosis`
- **Éléments corrects à préserver :** aucun
- **Éléments problématiques à détecter :** diagnostic coronaire majeur non soutenu
- **Incertitude/différentiel :** aucun
- **Criticité :** critique

### UNSUPPORTED_CRITICAL-10 — Cas 75 · Amylose cardiaque

> Syndrome de Brugada type 1.

- **Jugement attendu :** `critical_unsupported_wrong_diagnosis`
- **Éléments corrects à préserver :** aucun
- **Éléments problématiques à détecter :** canalopathie grave non soutenue
- **Incertitude/différentiel :** aucun
- **Criticité :** critique

## Formulation hésitante ou différentielle

### HEDGED-01 — Cas 2 · Artéfact de tremblement avec rythme sinusal

> La ligne de base pourrait faire penser à une FA, mais la présence d’ondes P régulières et de QRS réguliers rend un artéfact de tremblement nettement plus probable.

- **Jugement attendu :** `ranked_differential_correct`
- **Éléments corrects à préserver :** artéfact de tremblement probable ; rythme sinusal
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** FA discutée puis rejetée
- **Criticité :** faible

### HEDGED-02 — Cas 9 · Bloc de branche droit complet

> L’aspect évoque surtout un bloc de branche droit complet ; une hypertrophie droite associée peut être discutée mais n’est pas certaine.

- **Jugement attendu :** `hedged_correct`
- **Éléments corrects à préserver :** BBD complet probable
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** HVD possible
- **Criticité :** faible

### HEDGED-03 — Cas 20 · Pause sinusale

> Je discute une pause sinusale plutôt qu’un BAV paroxystique, car aucune onde P ne semble poursuivre son activité pendant la pause.

- **Jugement attendu :** `ranked_differential_correct`
- **Éléments corrects à préserver :** pause sinusale probable
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** BAV paroxystique moins probable
- **Criticité :** faible

### HEDGED-04 — Cas 24 · BAV du deuxième degré Mobitz I

> BAV du deuxième degré probablement Mobitz I devant l’allongement du PR ; un Mobitz II me paraît moins probable.

- **Jugement attendu :** `ranked_differential_correct`
- **Éléments corrects à préserver :** Mobitz I probable
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** Mobitz II moins probable
- **Criticité :** faible

### HEDGED-05 — Cas 37 · Fibrillation atriale

> Le diagnostic le plus probable est une fibrillation atriale ; un flutter à conduction variable est un différentiel moins convaincant.

- **Jugement attendu :** `ranked_differential_correct`
- **Éléments corrects à préserver :** FA probable
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** flutter variable possible mais moins probable
- **Criticité :** faible

### HEDGED-06 — Cas 41 · Flutter atrial typique

> Aspect très évocateur d’un flutter typique ; une tachycardie atriale macro-réentrante reste théoriquement possible.

- **Jugement attendu :** `hedged_correct`
- **Éléments corrects à préserver :** flutter typique très probable
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** tachycardie atriale alternative
- **Criticité :** faible

### HEDGED-07 — Cas 44 · Tachycardie par réentrée intranodale

> Tachycardie régulière à QRS fins, probablement une réentrée intranodale, sans pouvoir exclure formellement une tachycardie orthodromique sur voie accessoire.

- **Jugement attendu :** `appropriate_uncertainty`
- **Éléments corrects à préserver :** AVNRT probable
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** AVRT orthodromique possible
- **Criticité :** faible

### HEDGED-08 — Cas 48 · Tachycardie ventriculaire certaine

> Une tachycardie ventriculaire est de très loin la plus probable ; une TSV avec aberration est beaucoup moins vraisemblable, notamment en raison de la dissociation AV et d’un complexe de capture.

- **Jugement attendu :** `ranked_differential_correct`
- **Éléments corrects à préserver :** TV très probable ; dissociation AV ; capture
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** TSV aberrante moins probable
- **Criticité :** élevée

### HEDGED-09 — Cas 55 · Péricardite aiguë

> Péricardite aiguë plus probable qu’un SCA ST+ devant le caractère diffus du sus-décalage et l’anomalie du PR.

- **Jugement attendu :** `ranked_differential_correct`
- **Éléments corrects à préserver :** péricardite probable
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** SCA ST+ discuté mais moins probable
- **Criticité :** faible

### HEDGED-10 — Cas 74 · Syndrome de Brugada type 1

> Aspect compatible avec un Brugada type 1 ; une ischémie antéroseptale doit néanmoins être éliminée selon le contexte.

- **Jugement attendu :** `appropriate_uncertainty`
- **Éléments corrects à préserver :** Brugada type 1 possible/probable
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** ischémie antérieure à exclure
- **Criticité :** élevée

## Mesure numérique incompatible avec son interprétation

### NUMERIC_CONFLICT-01 — Cas 3 · ECG normal

> Fréquence à 45/min, donc normocardie.

- **Jugement attendu :** `measurement_semantic_conflict`
- **Éléments corrects à préserver :** fréquence mesurée à 45/min
- **Éléments problématiques à détecter :** 45/min interprété à tort comme normocardie
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NUMERIC_CONFLICT-02 — Cas 3 · ECG normal

> PR mesuré à 260 ms, de durée normale.

- **Jugement attendu :** `measurement_semantic_conflict`
- **Éléments corrects à préserver :** PR 260 ms
- **Éléments problématiques à détecter :** 260 ms interprété à tort comme normal
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NUMERIC_CONFLICT-03 — Cas 9 · Bloc de branche droit complet

> QRS à 90 ms, donc bloc de branche droit complet.

- **Jugement attendu :** `measurement_semantic_conflict`
- **Éléments corrects à préserver :** QRS 90 ms ; BBD complet
- **Éléments problématiques à détecter :** durée incompatible avec un bloc complet
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NUMERIC_CONFLICT-04 — Cas 13 · Bloc de branche gauche complet

> QRS à 100 ms avec bloc de branche gauche complet.

- **Jugement attendu :** `measurement_semantic_conflict`
- **Éléments corrects à préserver :** QRS 100 ms ; BBG complet
- **Éléments problématiques à détecter :** durée incompatible avec un BBG complet
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NUMERIC_CONFLICT-05 — Cas 40 · Tachycardie sinusale réactionnelle

> Fréquence sinusale à 135/min correspondant à une bradycardie.

- **Jugement attendu :** `measurement_semantic_conflict`
- **Éléments corrects à préserver :** fréquence 135/min ; rythme sinusal
- **Éléments problématiques à détecter :** 135/min interprété à tort comme bradycardie
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NUMERIC_CONFLICT-06 — Cas 37 · Fibrillation atriale

> Fibrillation atriale à 150/min avec réponse ventriculaire lente.

- **Jugement attendu :** `measurement_semantic_conflict`
- **Éléments corrects à préserver :** FA ; fréquence 150/min
- **Éléments problématiques à détecter :** 150/min qualifié à tort de réponse lente
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NUMERIC_CONFLICT-07 — Cas 51 · Préexcitation ventriculaire

> PR à 220 ms, donc PR court en faveur d’une préexcitation.

- **Jugement attendu :** `measurement_semantic_conflict`
- **Éléments corrects à préserver :** PR 220 ms ; préexcitation
- **Éléments problématiques à détecter :** 220 ms interprété à tort comme PR court
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NUMERIC_CONFLICT-08 — Cas 55 · Péricardite aiguë

> QTc à 560 ms, considéré comme normal.

- **Jugement attendu :** `measurement_semantic_conflict`
- **Éléments corrects à préserver :** QTc 560 ms
- **Éléments problématiques à détecter :** QTc très prolongé interprété comme normal
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NUMERIC_CONFLICT-09 — Cas 59 · Syndrome coronarien aigu ST+

> Axe du QRS à +120°, correspondant à une déviation axiale gauche.

- **Jugement attendu :** `measurement_semantic_conflict`
- **Éléments corrects à préserver :** axe +120°
- **Éléments problématiques à détecter :** +120° interprété à tort comme déviation gauche
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### NUMERIC_CONFLICT-10 — Cas 73 · Hyperkaliémie menaçante

> QRS mesurés à 180 ms mais décrits comme fins.

- **Jugement attendu :** `measurement_semantic_conflict`
- **Éléments corrects à préserver :** QRS 180 ms
- **Éléments problématiques à détecter :** 180 ms interprété à tort comme QRS fins
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

## Réponse correcte mais lexicalement éloignée du gold

### LEXICAL_DISTANCE-01 — Cas 2 · Artéfact de tremblement avec rythme sinusal

> Ce n’est pas l’oreillette qui est chaotique : le tracé est secoué par les mouvements du patient. Les ventricules restent réguliers et de vraies petites activations atriales précèdent les QRS.

- **Jugement attendu :** `paraphrased_or_implicit_correct`
- **Éléments corrects à préserver :** artéfact de mouvement ; rythme sinusal ; FA écartée
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### LEXICAL_DISTANCE-02 — Cas 3 · ECG normal

> Je ne trouve rien de pathologique : commande atriale physiologique, délais de conduction usuels, activation ventriculaire étroite et repolarisation sans particularité.

- **Jugement attendu :** `paraphrased_or_implicit_correct`
- **Éléments corrects à préserver :** ECG normal implicite ; rythme sinusal ; conduction normale ; repolarisation normale
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### LEXICAL_DISTANCE-03 — Cas 6 · Hypertrophie ventriculaire gauche électrique

> Le ventricule gauche se fait électriquement très entendre : grandes déflexions gauches et profondeur marquée en précordiales droites, avec un critère de voltage largement dépassé.

- **Jugement attendu :** `paraphrased_or_implicit_correct`
- **Éléments corrects à préserver :** HVG implicite ; voltages élevés
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### LEXICAL_DISTANCE-04 — Cas 9 · Bloc de branche droit complet

> L’activation du ventricule droit arrive en retard : deuxième sommet terminal en V1, complexes prolongés et fin de QRS traînante dans les dérivations latérales.

- **Jugement attendu :** `paraphrased_or_implicit_correct`
- **Éléments corrects à préserver :** BBD complet implicite ; retard terminal droit
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### LEXICAL_DISTANCE-05 — Cas 24 · BAV du deuxième degré Mobitz I

> La transmission atrioventriculaire fatigue progressivement : chaque délai s’allonge jusqu’à ce qu’une activation atriale ne passe plus, puis tout recommence.

- **Jugement attendu :** `paraphrased_or_implicit_correct`
- **Éléments corrects à préserver :** Mobitz I implicite ; allongement progressif du PR ; onde P bloquée
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### LEXICAL_DISTANCE-06 — Cas 32 · Extrasystole ventriculaire

> Un battement surgit trop tôt, large et différent, sans départ atrial visible, puis le rythme attend un cycle complet avant de repartir.

- **Jugement attendu :** `paraphrased_or_implicit_correct`
- **Éléments corrects à préserver :** ESV implicite ; QRS prématuré large ; repos compensateur
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### LEXICAL_DISTANCE-07 — Cas 37 · Fibrillation atriale

> Les oreillettes ne donnent plus de chef d’orchestre reconnaissable et les ventricules répondent à des intervalles imprévisibles.

- **Jugement attendu :** `paraphrased_or_implicit_correct`
- **Éléments corrects à préserver :** FA implicite ; absence d’ondes P ; irrégularité complète
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### LEXICAL_DISTANCE-08 — Cas 41 · Flutter atrial typique

> L’activité atriale tourne en boucle et dessine une succession régulière de dents, beaucoup plus rapide que la réponse ventriculaire.

- **Jugement attendu :** `paraphrased_or_implicit_correct`
- **Éléments corrects à préserver :** flutter implicite ; ondes F ; activité atriale rapide
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

### LEXICAL_DISTANCE-09 — Cas 48 · Tachycardie ventriculaire certaine

> Le rythme rapide naît des ventricules : les oreillettes poursuivent leur propre cadence et un battement normal parvient exceptionnellement à capturer les ventricules.

- **Jugement attendu :** `paraphrased_or_implicit_correct`
- **Éléments corrects à préserver :** TV implicite ; dissociation AV ; capture
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** élevée

### LEXICAL_DISTANCE-10 — Cas 75 · Amylose cardiaque

> Le cœur paraît épais mais produit étonnamment peu de signal électrique, avec de faux aspects de cicatrice alors qu’il n’existe pas de véritable territoire de nécrose.

- **Jugement attendu :** `paraphrased_or_implicit_correct`
- **Éléments corrects à préserver :** amylose implicite ; discordance épaisseur-voltage ; microvoltage ; pseudo-nécrose
- **Éléments problématiques à détecter :** aucun
- **Incertitude/différentiel :** aucun
- **Criticité :** faible

---

## Règles d’utilisation

1. Ne pas employer immédiatement ces annotations comme vérité définitive : effectuer une double relecture clinique indépendante.
2. Autoriser les annotateurs à corriger le cas d’ancrage, le niveau de criticité et la formulation du jugement attendu.
3. Conserver séparément la détection de ce que l’étudiant **a écrit** et l’évaluation de ce qui est **vrai pour le cas**.
4. Pour les diagnostics implicites, annoter le niveau de crédit pédagogique attendu : complet, partiel ou nul.
5. Pour les contradictions, conserver toutes les propositions et ne pas écraser automatiquement la première par la dernière.
6. Pour les formulations hésitantes, préserver le classement des hypothèses au lieu de convertir toute mention en affirmation.
7. Pour les mesures, extraire la valeur, l’unité et la conclusion linguistique afin de tester leur cohérence séparément.

## Sources internes utilisées pour l’ancrage

- `data/cases.json`
- `data/cases_golden.json`
- `data/scoring_config.json`
- `docs/ECG_Online_curriculum_75_ECG_feedback_IA_2026-07-31.md`
