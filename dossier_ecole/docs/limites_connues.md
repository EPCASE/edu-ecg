# ⚠️ Limites Connues du Pipeline

Ce document recense les limites identifiées du pipeline RAG Neurosymbolique,
classées par catégorie et niveau de criticité.

---

## 1. NER — Extraction des Termes Cliniques

### 1.1 Synonymes manquants dans l'ontologie
**Criticité : 🔴 Élevée**

Le coupe-circuit ne fonctionne que si le terme exact (ou un synonyme enregistré) existe
dans l'ontologie. Les abréviations cliniques courantes ne sont pas toutes couvertes.

| Terme étudiant | Concept attendu | Problème |
|---|---|---|
| "BAV 2 M 2" | BAV_2_MOBITZ_2 | Synonyme manquant → LLM confond avec BAV_2_POUR_1 |
| "flutter à conduction variable" | FLUTTER_DROIT_TYPIQUE | "flutter" seul non reconnu |
| "Ondes P bloqués par intermittence" | BAV_2_MOBITZ_2 | Expression descriptive non couverte |
| "RS" (rythme sinusal) | RYTHME_SINUSAL | Abréviation trop courte |

**Solution proposée** : Pipeline semi-automatique d'enrichissement des synonymes.

### 1.2 Expressions descriptives longues
**Criticité : 🟠 Moyenne**

Certains étudiants décrivent des phénomènes au lieu d'utiliser les termes canoniques :
- "2 ou 3 ondes P bloquées pour un QRS" → décrit un BAV de haut grade
- "QRS réguliers mais P et QRS dissociés" → décrit un BAV complet

Le pipeline segmente mal ces phrases longues et le LLM peut se tromper.

### 1.3 Gestion des abréviations ambiguës
**Criticité : 🟡 Faible**

Certaines abréviations sont ambiguës hors contexte :
- "BBD" = Bloc de Branche Droit (complet ? incomplet ?)
- "HAG" = Hypertrophie Atriale Gauche ou Hémibloc Antérieur Gauche ?

---

## 2. Matching — Correspondance Ontologique

### 2.1 Hallucinations du LLM juge
**Criticité : 🟠 Moyenne**

Le LLM juge peut forcer un match incorrect quand les candidats sémantiquement proches
ne sont pas le bon concept. Exemple :
- "BAV 2 M 2" → BAV_2_POUR_1 (au lieu de BAV_2_MOBITZ_2)
- "Dissociation AV" → BAV_COMPLET (alors que c'est un signe, pas un diagnostic)

**Facteur aggravant** : L'erreur est parfois masquée par le scoring hiérarchique
(les deux concepts étant enfants du même parent).

### 2.2 Coût et latence API
**Criticité : 🟡 Faible**

Chaque terme non résolu par le coupe-circuit génère un appel LLM (GPT-4).
Pour un étudiant typique avec 5 cas et ~7 termes par cas :
- ~15-20 appels LLM juge
- ~5 appels LLM feedback
- Latence totale : 30-60 secondes
- Coût estimé : ~0.10€ par étudiant

---

## 3. Scoring — Calcul du Score

### 3.1 Diagnostic implicite non inféré
**Criticité : 🔴 Élevée**

Voir le document détaillé : [`difficulte_ecg_normal.md`](./difficulte_ecg_normal.md)

Le pipeline ne sait pas inférer un diagnostic-parapluie à partir de la conjonction
de ses composants. Impact principal sur ECG_NORMAL.

### 3.2 Score moyen vs pondéré
**Criticité : 🟡 Faible**

Le score final est la moyenne des scores des concepts validants. Tous les validants
ont le même poids, même si certains sont plus importants cliniquement.

Exemple : Cas avec 2 validants (Hyperkaliémie + BAV de haut grade)
- Si l'étudiant trouve 1/2 : score = 50% (même si c'est l'hyperkaliémie,
  le diagnostic le plus urgent)

---

## 4. Feedback — Commentaire Pédagogique

### 4.1 Qualité variable du feedback LLM
**Criticité : 🟠 Moyenne**

La qualité du feedback pédagogique dépend du prompt et du contexte fourni au LLM.
Parfois le feedback est générique ou répétitif. Le commentaire du correcteur expert
n'est pas toujours bien intégré.

### 4.2 Pas de feedback sur les concepts "découverts"
**Criticité : 🟡 Faible**

Quand l'étudiant mentionne un concept pertinent non prévu dans le golden set
(ex: bradycardie dans un BAV complet), le pipeline le signale comme "découverte"
mais ne génère pas de feedback spécifique.

---

## 5. Ontologie — Couverture et Structure

### 5.1 Relations requiresFinding non exploitées
**Criticité : 🟠 Moyenne**

L'ontologie OWL contient 59 relations `requiresFinding` (ex: BAV complet
→ requiert Dissociation AV). Ces relations sont actuellement mergées avec
les relations parent-enfant et ne sont pas exploitées différemment.

**Potentiel** : Vérifier que les findings requis sont présents dans la réponse
de l'étudiant et ajuster le feedback en conséquence.

### 5.2 Niveaux hiérarchiques inconsistants
**Criticité : 🟡 Faible**

Certaines branches de l'ontologie sont plus profondes que d'autres, ce qui
affecte le scoring dégressif de manière non uniforme.

---

## Synthèse des axes de développement proposés

| # | Axe | Criticité | Complexité | Type de projet |
|---|-----|-----------|------------|----------------|
| 1 | Inférence de diagnostic implicite | 🔴 | Moyenne | Stage/Projet |
| 2 | Enrichissement automatique des synonymes | 🔴 | Moyenne | Stage/Projet |
| 3 | Évaluation systématique (métriques) | 🟠 | Faible | TP/Mini-projet |
| 4 | Exploitation des requiresFinding | 🟠 | Moyenne | Stage/Projet |
| 5 | Visualisation de l'espace sémantique | 🟡 | Faible | TP/Mini-projet |
| 6 | Réduction de la dépendance au LLM | 🟠 | Élevée | Stage long |
| 7 | Interface d'annotation collaborative | 🟡 | Moyenne | Projet |
