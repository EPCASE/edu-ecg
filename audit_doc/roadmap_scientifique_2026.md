# Roadmap scientifique et produit — ECG-online

**Version : 30 juillet 2026**
**Statut : document de référence pour les développements à venir**

> 📌 **Ce document est LA référence active** (cf. `audit_doc/README.md` pour
> l'index complet). `FEUILLE_DE_ROUTE_ALIGNEE.md` et
> `ECG_Online_Architecture_Cible_Feuille_de_Route.md` sont désormais figés
> (historique). Toute décision de priorité se documente ici.

---

## 0. État d'avancement (à tenir à jour à chaque session)

### ✅ Déjà fait avant ce document (mergé sur `main`, `ecg-online`)

Correspond à ce que ce roadmap appelle **P0.1 (partiel)** et **P5.3** :

- `response_id`/`prediction_id` (UUID) sur chaque `/api/grade`.
- États `SUCCESS`/`LOW_CONFIDENCE`/`FALLBACK_GPT`/`TECHNICAL_ERROR` (`app/abstention.py`)
  — correspond à une partie de P5.3 (`HUMAN_REVIEW`/`ABSTAIN` réels restent à faire, cf. P5).
- `pipeline_version` + `ontology_version` exposés dans `/api/health` et `/api/grade`
  (`app/golden_config.ontology_version()`) — brique de P0.1, incomplet (pas encore
  de tag de release ni de version figée des cas/goldens/dépendances ensemble).
- `docs/DATA_DICTIONARY.md` — contrat JSON `/api/grade` documenté.
- `tests/test_negation_nonregression.py` (8 tests, données golden réelles) —
  premier jalon très partiel de P3.3 (challenge set), pas encore un vrai
  benchmark verrouillé (P3.2) ni un challenge set complet.
- Phase E (`ecg-online/ROADMAP.md`) : golden de scoring actuel (`cases_golden.json`,
  75 cas, mono-expert) nettoyé, 0 conflit réel, audité sur 343 réponses réelles.
- **P1.1 + P1.2 (01/08/2026)** : schéma `scoring_v2` défini et validé
  (`ecg-online/data/scoring_schema_v2.json` + `scripts/validate_scoring_v2.py`),
  pilote réalisé sur 10 cas contrastés (`ecg-online/data/scoring_pilot_v2.json`,
  27 critères, 0 erreur de schéma) — rapport complet dans
  `ecg-online/docs/P1.2_pilote_scoring_v2_rapport.md`. Critère de sortie P1.2
  atteint : aucune situation fréquente n'a nécessité de champ improvisé.
  **Prochaine étape : P1.3 (annotation indépendante multi-expert)**, pas
  encore démarrée (le pilote actuel est en `evidence_source: single_expert`).
- **Liaison curriculum ↔ scoring_v2 (01/08/2026)** : script de dérivation
  automatique `ecg-online/scripts/derive_curriculum_objectives.py`
  (`required_concepts`/`unsafe_errors` du curriculum dérivés des critères
  `role=required`/`role=exclusion` de scoring_v2), testé sur le pilote
  10 cas — voir `ecg-online/docs/curriculum_scoring_v2_liaison.md`. Verdict :
  mécanisme fonctionnel, à utiliser comme pré-remplissage humain (pas comme
  vérité automatique) lors de la Phase 2 du curriculum ; généralisable aux
  75 cas seulement après P1.4.

### 🔜 Séquence retenue par l'équipe (30/07/2026)

Ordre validé pour les prochains chantiers, **différent** de l'ordre suggéré en
§4 du document (qui reste une checklist utile pour le détail de chaque étape) :

1. **P1 — Golden conceptuel de scoring V2** (chantier principal de l'été) :
   schéma enrichi (§P1.1), pilote 8-12 cas (§P1.2), annotation multi-expert
   (§P1.3), puis migration des 75 cas (§P1.4).
2. **P3 — Splits et benchmark verrouillé** : une fois le schéma V2 stabilisé
   sur le pilote, verrouiller un test interne (§P3.2) et un challenge set
   (§P3.3) **avant** de migrer massivement — pas après.
3. **P4 — Refonte du scoring** (séparer adéquation/sécurité, calibrer les
   crédits ontologiques, restreindre la négation) — nécessite P1 (et
   idéalement des éléments de P2) pour être calibré contre du réel.

En tâche de fond, en parallèle (peu coûteux, ne pas laisser traîner) :
- **P0.1** : figer une baseline versionnée (tag Git + versions figées
  cas/goldens/dépendances/modèles). Actuellement partiel (pipeline_version/
  ontology_version existent déjà).
- **P0.2** : trier les fichiers publics/privés avant que leur nombre ne
  grossisse encore.

P2 (golden de décision humaine par réponse), P5-P8 : pas commencés,
volontairement après P1/P3/P4 (cf. §2.2 anti-scope-creep du document).

---

## 1. Positionnement du projet

ECG-online doit désormais être développé comme un système modulaire de correction sélective des interprétations ECG en texte libre.

Le système comprend six tâches distinctes :

1. comprendre ce que l’étudiant a réellement écrit ;
2. normaliser les formulations vers une ontologie ECG ;
3. déterminer leur validité clinique ;
4. calculer une décision pédagogique et un score ;
5. estimer la fiabilité de cette décision ;
6. s’abstenir ou demander une revue humaine lorsque la correction n’est pas suffisamment sûre.

La valeur durable du projet ne repose pas sur GPT-4o, GPT-5.6 ou un autre modèle particulier. Elle repose sur l’association de plusieurs actifs :

* ontologie ECG versionnée ;
* corpus de réponses authentiques ;
* annotations expertes ;
* goldens indépendants ;
* règles pédagogiques explicites ;
* benchmark verrouillé ;
* plateforme utilisée en conditions réelles ;
* validation prospective et multicentrique.

---

# 2. Principes directeurs

## 2.1 Maintenir quatre objets distincts

| Objet                          | Entrée           | Sortie                              | Finalité                          |
| ------------------------------ | ---------------- | ----------------------------------- | --------------------------------- |
| Ontologie                      | domaine ECG      | concepts, synonymes, relations      | représenter les connaissances     |
| Golden d’extraction            | réponse libre    | concepts réellement exprimés        | évaluer la compréhension du texte |
| Golden conceptuel de scoring   | cas ECG          | critères attendus et contradictions | définir le barème                 |
| Golden de décision par réponse | réponse à un cas | jugement global d’experts           | évaluer la correction finale      |

Une bonne extraction ne démontre pas que la note est juste.
Un barème cohérent ne démontre pas que le système corrige comme un enseignant.

## 2.2 Verrouiller l’évaluation avant l’optimisation

Une partie des cas et des réponses doit être retirée du développement avant les prochaines modifications importantes.

Ces données ne devront pas servir à ajuster :

* l’ontologie ;
* les synonymes ;
* les prompts ;
* les seuils ;
* les règles de scoring ;
* les mécanismes de confiance.

## 2.3 Conserver une architecture indépendante des modèles

Les briques suivantes doivent rester remplaçables :

* extracteur NER ;
* modèle d’embeddings ;
* moteur de recherche ;
* reranker ou juge ;
* modèle de feedback.

Les contrats d’entrée et de sortie doivent être stables et versionnés.

## 2.4 Mesurer le risque, pas seulement la performance moyenne

Les métriques centrales doivent inclure :

* fausse validation d’une réponse incorrecte ;
* surnotation ;
* contradiction majeure non détectée ;
* erreur cliniquement dangereuse ;
* proportion de réponses corrigées automatiquement ;
* risque d’erreur parmi les réponses corrigées automatiquement.

---

# 3. Roadmap priorisée

## P0 — Gouvernance et baseline

### P0.1 Figer une baseline scientifique

Créer une release ou un tag comprenant :

* `pipeline_version` ;
* `ontology_version` ;
* version des cas ;
* version du golden d’extraction ;
* version du golden de scoring ;
* versions des modèles ;
* dépendances Python ;
* rapport de métriques correspondant.

### Critère de sortie

Chaque prédiction historique peut être reliée à une configuration complète et identifiable.

---

### P0.2 Séparer les actifs publics et privés

Classer les fichiers en quatre catégories :

1. publiables ;
2. privés de recherche ;
3. données personnelles ou pédagogiques contrôlées ;
4. contenus soumis aux droits de tiers.

Les éléments à conserver hors du dépôt public comprennent notamment :

* réponses réelles ;
* annotations expertes ;
* jeux de test verrouillés ;
* cas et tracés non explicitement réutilisables ;
* rapports détaillés contenant des données individuelles.

### Critère de sortie

Un inventaire documenté indique pour chaque fichier son statut, son propriétaire et sa licence.

---

### P0.3 Créer une source de vérité unique pour les métriques

Chaque résultat doit préciser :

* tâche évaluée ;
* corpus ;
* split ;
* nombre de réponses ;
* version du pipeline ;
* version de l’ontologie ;
* définition de la métrique ;
* date d’exécution ;
* intervalle de confiance lorsque pertinent.

### Critère de sortie

Le README, les documents d’audit et les futurs manuscrits utilisent les mêmes chiffres.

---

## P1 — Golden conceptuel de scoring V2

L’extension du golden de scoring demeure la priorité principale.

Elle ne doit cependant pas commencer par l’ajout massif de concepts dans la structure actuelle. Le schéma doit d’abord être enrichi.

### P1.1 Définir le nouveau schéma

Chaque critère devrait pouvoir contenir :

```json
{
  "criterion_id": "case_12_diagnostic_principal",
  "concept_id": "BAV_COMPLET",
  "label": "Bloc auriculo-ventriculaire complet",
  "role": "required",
  "expected_status": "present",
  "importance": "major",
  "error_severity": "dangerous",
  "alternative_group": "diagnostic_principal",
  "group_logic": "ANY",
  "sufficient_alone": true,
  "minimum_specificity": "child_ok",
  "expert_confidence": "high",
  "evidence_source": "expert_consensus",
  "comment": ""
}
```

### Valeurs principales proposées

**Rôle**

* `required`
* `alternative`
* `optional`
* `exclusion`

**Statut attendu**

* `present`
* `absent`
* `hypothesis_acceptable`

**Importance**

* `major`
* `intermediate`
* `minor`

**Gravité d’une erreur**

* `none`
* `minor`
* `major`
* `dangerous`

**Logique de groupe**

* `ANY`
* `ALL`
* `AT_LEAST_N`

### Principe

Les pondérations numériques ne doivent pas encore être figées. Il faut d’abord formaliser correctement la logique clinique.

---

### P1.2 Réaliser un pilote avant les 75 cas

Tester le schéma sur 8 à 12 cas contrastés :

* ECG normal ;
* fibrillation atriale ;
* trouble de conduction ;
* tachycardie à QRS larges ;
* syndrome coronarien ;
* diagnostic étiologique ;
* cas comprenant une exclusion majeure ;
* cas comportant plusieurs réponses diagnostiques recevables.

### Critère de sortie

Aucune situation fréquente ne nécessite de champ improvisé ou de règle codée spécifiquement pour un cas.

---

### P1.3 Annotation indépendante multi-expert

Pour chaque cas :

1. expert 1 annote indépendamment ;
2. expert 2 annote indépendamment ;
3. les désaccords sont enregistrés ;
4. une adjudication est réalisée ;
5. la version consensuelle est produite ;
6. les annotations initiales restent conservées.

Les désaccords constituent eux-mêmes un résultat scientifique.

---

### P1.4 Migrer progressivement les 75 cas

Créer :

* un script de migration ;
* un validateur JSON ;
* un rapport de différences ;
* un audit des contradictions ;
* des tests de non-régression ;
* une interface d’annotation adaptée au nouveau schéma.

### Critère de sortie

Les 75 cas sont couverts sans modification silencieuse du comportement antérieur.

---

## P2 — Golden de décision humaine par réponse

Le golden conceptuel indique ce qui devrait être exigé.
Il ne remplace pas le jugement réel des enseignants devant une réponse complète.

### P2.1 Définir la grille d’évaluation humaine

Chaque réponse reçoit :

* classe globale :

  * exacte ;
  * acceptable ;
  * partielle ;
  * incorrecte ;
* score numérique ;
* présence d’une erreur clinique ;
* gravité maximale ;
* contradiction interne ;
* correction automatique acceptable ou non ;
* justification conceptuelle.

### P2.2 Constituer un corpus stratifié

Stratifier les réponses selon :

* famille ECG ;
* cas ;
* longueur ;
* niveau de performance ;
* négation ;
* hypothèse ;
* fautes orthographiques ;
* réponse télégraphique ou développée ;
* formulation fréquente ou rare.

### Cible initiale réaliste

Un premier corpus robuste pourrait comprendre :

* 400 à 600 réponses doublement annotées ;
* 30 à 40 cas suffisamment représentés ;
* adjudication des désaccords.

Un corpus plus large pourra être constitué ensuite.

### P2.3 Garder une vérité terrain humaine

Un LLM peut :

* proposer des concepts ;
* préremplir l’interface ;
* signaler les désaccords ;
* accélérer la saisie.

Il ne doit pas être l’arbitre final du golden utilisé pour l’évaluer.

---

## P3 — Splits et benchmark verrouillé

### P3.1 Organiser quatre niveaux d’évaluation

#### Niveau 1 — Nouvelles réponses sur des cas connus

Évalue la robustesse aux formulations.

#### Niveau 2 — Nouveaux ECG dans une famille connue

Évalue la généralisation à un nouveau tracé et à un nouveau barème.

#### Niveau 3 — Famille diagnostique non vue

Évalue le transfert conceptuel.

#### Niveau 4 — Centre externe

Évalue la généralisation pédagogique et linguistique.

---

### P3.2 Créer un test interne verrouillé

Sélectionner avant les prochaines modifications :

* plusieurs cas actuels ;
* leurs réponses ;
* idéalement de nouveaux cas jamais utilisés.

Le test doit être stocké séparément et ne pas être consulté lors du développement.

---

### P3.3 Construire un challenge set

Inclure volontairement :

* bon diagnostic avec contradiction majeure ;
* mauvais diagnostic utilisant les bons mots-clés ;
* double négation ;
* diagnostic seulement hypothétique ;
* description juste sans diagnostic ;
* diagnostic juste sans justification ;
* concept parent trop générique ;
* concept enfant plus spécifique ;
* abréviation ambiguë ;
* fautes importantes ;
* plusieurs diagnostics concurrents ;
* réponse cherchant à manipuler le barème.

---

## P4 — Refonte du scoring

### P4.1 Séparer adéquation et sécurité

Produire deux dimensions distinctes :

#### Score d’adéquation

Mesure la couverture des critères attendus.

#### Score de sécurité

Mesure :

* concepts faux ;
* contradictions ;
* exclusions violées ;
* erreurs graves.

Le score final peut combiner les deux, mais elles doivent rester visibles séparément.

---

### P4.2 Calibrer les crédits ontologiques

Les valeurs actuelles accordées aux :

* parents ;
* enfants ;
* `requires` ;
* qualifiers ;
* supports ;
* implications ;
* négations ;

doivent être comparées aux jugements humains.

Comparer plusieurs stratégies :

* règles fixes d’experts ;
* calibration statistique ;
* modèle ordinal ;
* pondérations dépendant de la catégorie clinique.

---

### P4.3 Restreindre les conversions de négation

Une phrase comme :

> « pas de trouble de repolarisation »

ne doit pas, à elle seule, valider automatiquement un ECG globalement normal.

La conversion doit dépendre :

* de la portée de la négation ;
* du niveau ontologique ;
* des critères requis ;
* des autres concepts présents ;
* des contradictions éventuelles.

---

## P5 — Confiance et abstention réelle

### P5.1 Enregistrer les signaux de confiance

Pour chaque correction :

* méthode de résolution ;
* score lexical ;
* score dense ;
* écart entre les deux premiers candidats ;
* confiance du juge ;
* concepts non résolus ;
* contradictions ;
* stabilité entre répétitions ;
* désaccord entre modèles ;
* couverture des critères ;
* proximité avec les données annotées.

### P5.2 Calibrer la confiance contre les erreurs réelles

La confiance ne doit pas être définie arbitrairement.

Elle doit prédire :

* probabilité que la correction soit fausse ;
* probabilité de fausse validation ;
* probabilité d’erreur grave.

### P5.3 Implémenter de véritables états

* `SUCCESS` : correction automatique ;
* `LOW_CONFIDENCE` : correction prudente ou signalée ;
* `HUMAN_REVIEW` : file de validation ;
* `ABSTAIN` : aucune note automatique ;
* `TECHNICAL_ERROR` : problème technique distinct.

### P5.4 Produire une courbe couverture–risque

Pour chaque seuil :

* proportion corrigée automatiquement ;
* taux d’erreur ;
* taux de fausse validation ;
* taux d’erreur grave.

Le seuil est choisi sur le jeu de validation, puis évalué une seule fois sur le test verrouillé.

---

## P6 — Baselines et ablations

### Baselines minimales

1. règles lexicales ;
2. LLM direct avec correction de référence ;
3. LLM direct avec rubrique structurée ;
4. extraction + scoring sans juge ;
5. pipeline complet ;
6. encodeur ou reranker spécialisé ;
7. modèle local ou ouvert.

### Ablations

Évaluer séparément la suppression de :

* recherche dense ;
* BM25 ;
* juge LLM ;
* lexical backstop ;
* pattern inference ;
* relations ontologiques ;
* exclusions ;
* feedback génératif.

### Métriques

* extraction ;
* décision finale ;
* fausse validation ;
* erreur grave ;
* latence ;
* coût ;
* reproductibilité.

---

## P7 — Réduction de la dépendance technologique

### P7.1 Évaluer un extracteur spécialisé

Entraîner ou adapter un encodeur sur le golden d’extraction.

Architecture cible possible :

* règles et exact match pour les formes fréquentes ;
* encodeur spécialisé pour les entités habituelles ;
* LLM seulement pour les formulations rares ou ambiguës.

### P7.2 Prévoir un mode local

Remplacer progressivement :

* embeddings OpenAI par embeddings locaux ;
* juge GPT par reranker ou modèle local ;
* NER GPT par modèle spécialisé ;
* feedback génératif par gabarits lorsque possible.

### Critère de sortie

Une indisponibilité d’un fournisseur externe ne rend pas toute la plateforme inutilisable.

---

## P8 — Validation externe et pédagogique

### P8.1 Validation technique externe

Tester sur :

* nouveaux ECG ;
* étudiants d’un autre centre ;
* autre niveau de formation ;
* corpus anglophone ultérieur ;
* autre organisation pédagogique.

### P8.2 Validation prospective

Mesurer :

* temps de correction ;
* acceptabilité ;
* taux d’abstention ;
* recours à l’enseignant ;
* erreurs signalées ;
* coût ;
* progression des étudiants.

### P8.3 Efficacité pédagogique

L’objectif supérieur est de déterminer si le système améliore :

* la qualité des interprétations ultérieures ;
* la structure de la lecture ECG ;
* la détection des erreurs ;
* la rétention ;
* le transfert vers de nouveaux ECG.

---

# 4. Séquence immédiate de développement

Ordre recommandé :

1. créer une baseline versionnée ;
2. séparer les données publiques et privées ;
3. définir le schéma `scoring_v2` ;
4. sélectionner le futur test verrouillé ;
5. tester le schéma sur un pilote ;
6. construire l’interface multi-expert ;
7. migrer progressivement les 75 cas ;
8. constituer le golden de décision par réponse ;
9. comparer le score automatique aux décisions humaines ;
10. calibrer la sécurité et l’abstention ;
11. exécuter les baselines et ablations ;
12. lancer une validation externe.

---

# 5. Backlog concret

## À faire maintenant

* [ ] Créer une release `baseline-2026-07`.
* [ ] Exporter les versions des modèles et dépendances.
* [ ] Créer `scoring_schema_v2.json`.
* [ ] Ajouter un validateur de schéma.
* [ ] Choisir 8 à 12 cas pilotes.
* [ ] Choisir les cas du test verrouillé.
* [ ] Concevoir l’interface d’annotation indépendante.
* [ ] Définir la grille de décision globale par réponse.
* [ ] Documenter les licences et droits de chaque type de contenu.

## À faire après validation du pilote

* [ ] Migrer les 75 cas.
* [ ] Organiser la double annotation.
* [ ] Mesurer les désaccords.
* [ ] Adjuger les critères discutés.
* [ ] Constituer le corpus de réponses notées.
* [ ] Recalibrer les règles de scoring.
* [ ] Développer l’abstention effective.

## À ne pas faire immédiatement

* [ ] Ajouter des centaines de critères dans le schéma actuel.
* [ ] Optimiser les pondérations avant les annotations humaines.
* [ ] Modifier le pipeline à partir du test verrouillé.
* [ ] Utiliser un LLM comme vérité terrain finale.
* [ ] Résumer les performances par un F1 unique.
* [ ] Ouvrir tous les goldens avant d’avoir daté la priorité scientifique.

---

# 6. Stratégie de publication

## Article 1 — Méthodologie et benchmark

Contenu :

* formalisation de la tâche ;
* ontologie ;
* golden d’extraction ;
* golden de scoring ;
* golden de décision ;
* baselines ;
* généralisation ;
* correction sélective ;
* abstention.

## Article 2 — Validation pédagogique prospective

Contenu :

* utilisation réelle ;
* acceptabilité ;
* charge enseignante ;
* progression ;
* sécurité ;
* recours à la supervision humaine.

## Article 3 éventuel — Extension multicentrique ou multilingue

Contenu :

* transfert anglais ;
* adaptation inter-centres ;
* évolution de l’ontologie ;
* robustesse linguistique.

---

# 7. Définition du succès

Le projet sera scientifiquement et technologiquement défendable lorsqu’il démontrera simultanément :

1. une extraction fiable des concepts exprimés ;
2. une décision concordante avec plusieurs experts ;
3. une faible fréquence de fausse validation ;
4. une détection des erreurs graves ;
5. une abstention calibrée ;
6. une généralisation à de nouveaux cas ;
7. une validation dans un autre centre ;
8. une architecture indépendante des fournisseurs ;
9. un bénéfice pédagogique ou organisationnel mesurable.

L’objectif n’est pas de construire un golden unique aussi volumineux que possible.

L’objectif est de construire plusieurs vérités terrain complémentaires, versionnées et indépendantes du développement, capables d’évaluer les générations successives du moteur.
