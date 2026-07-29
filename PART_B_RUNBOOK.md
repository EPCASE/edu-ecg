# PARTIE B — Rebuild sûr de l'ontologie depuis un `.owl` réannoté

> **But** : réintégrer un `.owl` réannoté (hiérarchie corrigée dans WebProtégé)
> **sans perdre** la couche d'enrichissement qui fait vivre la décision « B »
> (inférence `ECG_NORMAL`, cohérence par `excludes_families`, polarité `negation_of`).

---

## 0. Le piège (à lire absolument)

`data/ontology_v2.json` **n'est PAS** un simple export du `.owl`. Il porte une
**couche d'enrichissement manuelle** qui **n'existe pas** dans l'OWL exporté :

| Enrichissement | Présent dans le `.owl` ? | Effet si on régénère naïvement |
|---|---|---|
| `ECG_NORMAL.infer_from_requires` | ❌ non | **l'inférence disparaît** (sensibilité 83 % → 42 %) |
| `ECG_NORMAL.excludes_families` (+9 familles manuelles) | ❌ non | la décision « B » ne bloque plus rien |
| `negation_of` (polarité des requires « normaux ») | ❌ non | les requires négatifs ne sont plus satisfaits |
| `requires` curados (`ECG_NORMAL`, `QRS_NORMAL`, `PAS_*`) | partiel | la composition ECG normal casse |
| `VOLTAGE_NORMAL_DU_QRS` (concept créé main) | ❌ non | référence cassée dans `QRS_NORMAL` |
| ~83 concepts à synonymes enrichis | partiel | perte de rappel NER |

➡️ **Ne JAMAIS lancer `convert_owl_to_v2.py` seul vers `data/`.** Toujours passer
par `rebuild_ontology_from_owl.py`, qui **réapplique** cette couche.

---

## 1. Les fichiers de la Partie B

| Fichier | Rôle |
|---|---|
| `convert_owl_to_v2.py` | Convertisseur OWL → JSON. **Rendu déterministe** (voir §4). |
| `_build_overlay.py` | Capture la couche d'enrichissement dans `onto_overlay.json`. |
| `onto_overlay.json` | **Artefact versionné** = tout le « savoir Partie B » hors OWL. |
| `rebuild_ontology_from_owl.py` | **Le script à lancer.** Convertit + réapplique l'overlay + valide + écrit (backups). |
| `validate_golden_coherence.py` | (côté données) signale/retire un `ECG_NORMAL` incohérent dans le golden. |

`onto_overlay.json` contient 5 blocs :
- `part_b_concepts` — `infer_from_requires`, `negation_of`, `requires` **exacts** (3 concepts).
- `excludes_families_additions` — familles ajoutées à la main (**union** avec l'OWL).
- `synonyms_additions` — synonymes ajoutés à la main (**union**, dédup casse).
- `curated_overrides` — hiérarchie/composition corrigée main, en **3-way** (voir §3).
- `concepts_add` — concepts créés main, ajoutés **seulement si absents** du nouveau `.owl`.

---

## 2. Procédure quand le `.owl` réannoté arrive

```powershell
# venv ecg-online
$py = "C:\Users\Administrateur\bmad\ECG lecture\ecg-online\.venv\Scripts\python.exe"
Set-Location "C:\Users\Administrateur\bmad\ECG lecture"
$env:PYTHONUTF8 = 1

# (A) DRY-RUN : ne rien écrire, juste voir le plan + garde-fous
& $py rebuild_ontology_from_owl.py --owl "C:\chemin\vers\REANNOTE.owl" --dry-run

# → lire attentivement la section [2/4] :
#    ~ « .owl réannoté prime »  = le reannotage a changé ce champ (attendu, OK)
#    ↺ « restauration édit curados » = le .owl n'a pas touché, on garde l'édit
#    [!] « concept Partie B ABSENT du .owl » = ALERTE : un ID a changé (voir §5)
# → la section [3/4] DOIT afficher : « ✓ tous les garde-fous passent »

# (B) APPLY : écrit les 3 copies runtime, chacune avec backup horodaté
& $py rebuild_ontology_from_owl.py --owl "C:\chemin\vers\REANNOTE.owl"
```

**Après l'application, re-tester** (voir §6).

---

## 3. Le merge 3-way (`curated_overrides`)

Certains champs de hiérarchie/composition ont été **corrigés à la main** dans le
JSON (ex. `MICROVOLTAGE` reclassé sous `VOLTAGE_DU_QRS_ANORMAL`). On ne peut ni
les jeter (édits cliniques valides) ni les imposer (le reannotage sert justement
à corriger la hiérarchie). D'où un **merge à 3 versions** :

```
base   = valeur du .owl au moment de la capture de l'overlay
ours   = valeur curados (le JSON live actuel)
theirs = valeur du NOUVEAU .owl réannoté
```

- Si **`theirs != base`** → le reannotage a *volontairement* changé ce champ →
  **le `.owl` gagne** (l'édit curados n'est pas restauré). Journalisé `~`.
- Si **`theirs == base`** → le reannotage n'a pas touché → **on restaure `ours`**
  (l'édit curados). Journalisé `↺`.

> Ainsi, corriger `MICROVOLTAGE` dans WebProtégé **remplace** l'édit curados ;
> ne pas y toucher **préserve** l'édit curados. Zéro surprise, tout est loggé.

---

## 4. Déterminisme du convertisseur (corrigé)

`convert_owl_to_v2.py` était **non déterministe** entre process : le nombre de
concepts variait (330 / 342 / 345) selon `PYTHONHASHSEED`. Deux causes, corrigées :

1. **`family_for_iri`** faisait un *last-write-wins* sur l'itération d'un `set`.
   → on itère désormais **trié**, avec **priorité aux familles cliniques** sur les
   familles de référence (`Poids`, `Anatomie`, `Dérivations`).
2. **Collision de clé** : deux classes OWL homonymes « Stimulation » écrasaient la
   même clé selon l'ordre du `set`. → tri secondaire par IRI + **fusion sans perte**
   des champs-listes + suppression des auto-références (self-parent).

Résultat : **345 concepts stables** quel que soit le seed. `rebuild_…` force en
plus `PYTHONHASHSEED=0`.

> ⚠️ **Doublon dans l'OWL** : le label « Stimulation » existe **deux fois**
> (une classe sous `ECG pas normal`, une auto-référencée). À nettoyer dans
> WebProtégé au prochain passage (fusionner les deux classes).

---

## 5. Si un ID de concept a changé au reannotage

Le rebuild le signale : `[!] concept Partie B ABSENT du .owl : <ID>`.
Cela veut dire qu'un concept portant `infer_from_requires` / `negation_of` /
un `requires` curados a été **renommé** (donc sa clé a changé). Deux options :

1. **Préféré** : garder le **même label** dans WebProtégé pour ces 3 concepts
   pivots (`ECG_NORMAL`, `PAS_D_ANOMALIE_DE_LE_REPOLARISATION`,
   `PAS_DE_TROUBLES_DE_LA_CONDUCTION`) → aucun souci.
2. Sinon, **mettre à jour les clés** dans `onto_overlay.json` (bloc concerné),
   puis relancer le dry-run. (Ne pas éditer le JSON live à la main.)

Le rebuild **échoue volontairement** (`exit 1`, section [3/4]) si un garde-fou
casse — il **n'écrit rien** et laisse `_rebuild_preview.json` pour diagnostic.

---

## 6. Tests de non-régression après rebuild

```powershell
# a) l'inférence fonctionne toujours (normal → infère, anomalie → bloque)
& $py -c "import sys; sys.path.insert(0,'rag_pipeline'); from pattern_inference import PatternInferencer; import json; C=json.load(open('data/ontology_v2.json',encoding='utf-8'))['concepts']; inf=PatternInferencer(C); print('normal :', inf.infer(['RYTHME_SINUSAL','QRS_NORMAL','PAS_D_ANOMALIE_DE_LE_REPOLARISATION'])); print('HAG    :', inf.infer(['RYTHME_SINUSAL','QRS_NORMAL','PAS_D_ANOMALIE_DE_LE_REPOLARISATION','HYPERTROPHIE_ATRIALE_GAUCHE']))"

# b) comparaison golden (côté ECG evaluation), si un rerun est dispo
#    python compare_rerun.py --rerun "C:\Users\Administrateur\bmad\RAG ontologique\_rerun_patched"
```

**Attendu** : `normal` → `ECG_NORMAL present` ; `HAG` → liste vide (bloqué).

---

## 7. Rollback

Chaque écriture crée un `*.AAAAMMJJ_HHMMSS.bak` **à côté** de chaque copie.
Pour revenir en arrière : restaurer le `.bak` le plus récent sur les 3 chemins :

- `ECG lecture\data\ontology_v2.json`
- `RAG ontologique\data\ontology_v2.json`
- `ECG lecture\_standalone\rag_pipeline\data\ontology_v2.json`

---

## 8. Prochaine étape (après le rebuild)

1. **Relire les 75 concepts** en curation (`ecg-online`) — cf. `ROADMAP.md`.
2. **Générer 2–3 corrections virtuelles/cas** (GPT-5.5, modèle du golden).
3. **Tester le pipeline sur les 75 ECG** (~150–225 corrections contrôlées).
4. **Déployer** si la fiabilité est au rendez-vous.
