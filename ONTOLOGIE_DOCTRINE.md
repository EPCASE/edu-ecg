# Doctrine de structuration de l'ontologie ECG (v1)

> Référentiel de décision pour **auditer, filtrer et structurer** les concepts.
> Utilisé comme *system prompt* par `critical_review_concepts.py`.
> Rédigé à partir de l'arbitrage humain (juillet 2026) sur l'audit GPT-5.5.

---

## Principe fondateur

**Nous construisons LA référence.** Le texte de Pierre est **une** lecture
possible d'un ECG, pas la vérité ultime. L'ontologie doit être **robuste,
généraliste et réutilisable** sur plusieurs cas — jamais le décalque d'un texte.
Une structure peut donc être plus ou moins alignée avec Pierre, tant qu'elle
reste cliniquement correcte et suffisamment générale pour couvrir ces cas.

## Règle d'or : composer, ne pas empiler

La puissance de l'ontologie vient de la **composition via relations**
(`requires`, `supports`, `has_qualifiers`, `parents`), **pas** de la
multiplication de concepts monolithiques. Un concept doit être **atomique** et
**réutilisable**.

---

## D1 — Distinguer diagnostic et description

| Niveau | Type | Rôle | Exemple |
|--------|------|------|---------|
| Description | `finding` | Signe observable brut | onde S large, sus-décalage ST, onde Q |
| Diagnostic | `pattern` | Composite = `requires`(findings) + `has_qualifiers` | BBD complet, SCA ST+, ECG normal |
| Modificateur | `qualifier` | Réutilisable, transverse | large, lent, ample, complet, **limite** |
| Localisation | `topography` | Dimension séparée (cf. T1) | V1, inférieur, précordiales droites |

**Ne jamais fusionner ces niveaux dans un seul concept.** Un sus-décalage ST est
une *description* ; le SCA ST+ est le *diagnostic* qui le `requires`.

## T1 — Pas de territoire en v1

La **topographie est une dimension séparée**, **non prise en compte** dans le
scoring v1. Conséquence :

- Tout concept qui n'existe **que par sa localisation** est **rejeté** ou réduit
  à son finding atomique.
- `ONDE_S_LARGE_TRAINANTE_EN_V6` → `ONDE_S_LARGE` (le « en V6 » est ignoré).
- `ONDE_R_AMPLE_PRECORDIALES_DROITES` → `ONDE_R_AMPLE` (localisation ignorée).
- `DERIVATION_V1`, `DERIVATIONS_PRECORDIALES_DROITES`, `LATERAL_HAUT`… →
  **rejetés en v1** (réservés à une future couche topographique).

La localisation est **notée** (champ `territoire`) mais **marquée ignorée v1**.

> **Décision (arbitrage juillet 2026, point 3 « ok ») :** la topographie extraite
> est **conservée** dans le champ `territoire_ignore_v1` de chaque verdict, mais
> **exclue du socle et du scoring v1**. Elle constituera une **couche
> topographique v2** dédiée (dérivations, territoires IDM, oreillettes, veines
> pulmonaires…), branchée ultérieurement sans re-auditer les cas.

## C1 — Décomposer les composés

Un concept dont le nom « raconte une phrase » doit être **décomposé** en atomes
reliés.

- `ECHAPPEMENT_ATRIAL_LENT` = `ECHAPPEMENT_ATRIAL` + qualifier `LENT` (fréquence).
- `PAUSE_MULTIPLE_DU_RYTHME_SINUSAL_DE_BASE` = `PAUSE` + qualifier `MULTIPLE`
  (le « rythme sinusal de base » est le contexte, pas le concept).

## C2 — Un qualifier qui n'ajoute rien au diagnostic est redondant

- `SUS_DECALAGE_ST_DE_GRANDE_AMPLITUDE` = SCA ST+ + « grande amplitude ».
  « Grande amplitude » **n'ajoute rien** au diagnostic ST+ → **rejeté**, ou au
  mieux un qualifier générique `AMPLE` réutilisable (jamais un concept dédié).

## C3 — Ne pas recréer l'existant

**Vérifier systématiquement l'ontologie** avant de proposer.

- `ASPECT_QS_DU_QRS` ≈ onde Q / `PRESENCE_D_ONDE_Q_PATHOLOGIQUE` →
  **synonyme**, pas concept.

## C4 — Un attendu d'un pattern normal n'est pas un concept

- `COMPOSANTE_NEGATIVE_TERMINALE_ONDE_P_V1` = attendu de l'onde P physiologique
  → intégré à `MORPHOLOGIE_ONDE_P_SINUSALE`, **pas** un concept séparé.

## C5 — Rejeter le trop vague

- `QRS_GLOBALEMENT_NEGATIF` — non différenciant → **rejeté** sauf rattachement
  clinique précis (p. ex. concordance négative précordiale, qui elle est utile).

## C6 — Champ lexical de l'incertitude (nouveau)

Certaines mesures sont **à la frontière** (à la fois normales et pathologiques).
Créer un **qualifier réutilisable d'incertitude** plutôt qu'un concept.

- `PR_LIMITE` = `INTERVALLE_PR` + qualifier `LIMITE` (à la fois normal et allongé).
- Qualifiers d'incertitude réutilisables proposés : **`LIMITE`**, `DOUTEUX`,
  `A_LA_FRONTIERE`.

## C7 — Composer aussi les patterns « normaux » (branches)

Un diagnostic composite (même « normal ») se définit par **branches composites**,
pas par une liste plate de findings. Chaque branche est elle-même diagnosticable.

- `ECG_NORMAL` = `RYTHME_SINUSAL` + **`QRS_NORMAL`** + `PAS_D_ANOMALIE_REPOLARISATION`
  + `PAS_DE_TROUBLES_DE_LA_CONDUCTION`.
- `QRS_NORMAL` = `MORPHOLOGIE_DU_QRS_NORMALE` (axe + absence d'onde Q) +
  **`VOLTAGE_NORMAL_DU_QRS`** (ni microvoltage, ni HVG).
- `PAS_D_ANOMALIE_REPOLARISATION` = `ONDE_T_NORMALES` + `ST_NORMAL` + `QT_NORMAL`.

> **Constat (arbitrage juillet 2026) :** `ECG_NORMAL` réel n'avait **aucune
> branche QRS** → une onde Q pathologique ou une HVG passait pour « normal ».
> Corrigé par l'ajout de `QRS_NORMAL` (cf. `build_normal_composition.py`).

**`requires` (définition) ≠ scoring (crédit partiel).** L'ontologie reste
**stricte-compositionnelle** : `requires` = ce qui rend l'ECG *réellement* normal.
Le crédit partiel (étudiant qui oublie le QT) est porté par la **couche
`scoring_v3`**, qui pondère chaque branche/atome — pas par un relâchement du
`requires`. La question « tout obligatoire vs requires/supports » **se dissout**.

---

## Grille de verdict (appliquée à chaque concept proposé)

| Verdict | Quand | Action |
|---------|-------|--------|
| **GARDER_ATOMIQUE** | Vrai concept atomique, différenciant, absent | Créer (finding/pattern/qualifier) |
| **REDUIRE_A_SYNONYME** | Existe déjà sous un autre nom | Ajouter comme `synonyme` du concept cible |
| **DECOMPOSER** | Composé (signe + qualifier/territoire) | Remplacer par finding + qualifier(s) + relations |
| **QUALIFIER_REUTILISABLE** | C'est un modificateur transverse | Créer/réutiliser un `qualifier` générique |
| **REJETER** | Territoire pur, phrase, trop vague, attendu du normal, redondant | Écarter (avec motif) |

Chaque verdict **cite le principe** appliqué (D1, T1, C1…C6) et précise la
**classe** (diagnostic / description / qualifier / topographie).

---

## Cas emblématiques (arbitrage de référence)

| Concept proposé | Verdict | Structure retenue | Principe |
|-----------------|---------|-------------------|----------|
| `P_QRS_T_NEGATIFS_EN_DI` | DECOMPOSER | signe d'inversion d'électrodes via `supports`, sans concept par dérivation | D1, T1 |
| `ONDE_S_LARGE_TRAINANTE_EN_V6` | DECOMPOSER | `ONDE_S_LARGE` (+ territoire V6 ignoré) | T1 |
| `SUS_DECALAGE_ST_DE_GRANDE_AMPLITUDE` | REJETER | SCA ST+ suffit ; au mieux qualifier `AMPLE` | C2 |
| `COMPOSANTE_NEGATIVE_TERMINALE_ONDE_P_V1` | REJETER | attendu de `MORPHOLOGIE_ONDE_P_SINUSALE` | C4 |
| `ONDE_R_AMPLE_PRECORDIALES_DROITES` | DECOMPOSER | `ONDE_R_AMPLE` (+ territoire ignoré) | T1 |
| `ASPECT_QS_DU_QRS` | REDUIRE_A_SYNONYME | → onde Q existante | C3 |
| `QRS_GLOBALEMENT_NEGATIF` | REJETER | trop vague | C5 |
| `PAUSE_MULTIPLE_DU_RYTHME_SINUSAL_DE_BASE` | DECOMPOSER | `PAUSE` + qualifier `MULTIPLE` | C1 |
| `ECHAPPEMENT_ATRIAL_LENT` | DECOMPOSER | `ECHAPPEMENT_ATRIAL` + qualifier `LENT` | C1 |
| `PR_LIMITE` | QUALIFIER_REUTILISABLE | `INTERVALLE_PR` + qualifier `LIMITE` | C6 |
| `ASPECT_S1Q3` / `ASPECT_S1Q3T3` | GARDER_ATOMIQUE | vrai pattern d'embolie, différenciant | D1 |
| `SYNDROME_DE_WOLFF_PARKINSON_WHITE` | REDUIRE_A_SYNONYME | → faisceau accessoire existant | C3 |

---

*Doctrine v1 — juillet 2026. Source de vérité pour la relecture critique de
l'ontologie. Modifiable : toute évolution de règle se répercute sur la relecture.*
