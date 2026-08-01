# 📚 Index `audit_doc/` — quel document lire selon le besoin (figé 2026-07-30)

> **But de ce fichier** : éviter de se tromper de document de travail. Après
> plusieurs cycles d'audit/cadrage (juillet 2026), certains documents sont
> devenus **historiques** (utiles pour comprendre le raisonnement passé, mais
> plus à mettre à jour) et un seul document fait aujourd'hui foi pour la suite
> du travail. Si un document n'est pas listé ci-dessous comme "actif", ne pas
> l'utiliser pour décider de la prochaine action.

---

## 🟢 Document actif — à lire et mettre à jour en premier

### [`roadmap_scientifique_2026.md`](./roadmap_scientifique_2026.md)

**LA référence pour toute décision de priorité à partir du 30/07/2026.**
Remplace et absorbe l'intégralité de `FEUILLE_DE_ROUTE_ALIGNEE.md` et de
`ECG_Online_Architecture_Cible_Feuille_de_Route.md` (voir ci-dessous). Contient :
- les 4 objets à garder distincts (ontologie / golden d'extraction / golden de
  scoring / golden de décision) ;
- la roadmap priorisée P0→P8 ;
- le backlog concret ("à faire maintenant" / "après pilote" / "à ne pas faire") ;
- **une section "État d'avancement"** (ajoutée le 30/07/2026, à tenir à jour à
  chaque session de travail — cf. juste en dessous du titre du document).

Séquence retenue par l'équipe (30/07/2026) : **P1 → P3 → P4** (voir section
"Séquence retenue" dans le document lui-même). P0.1/P0.2 (baseline + tri
public/privé) à faire en tâche de fond, en parallèle, car peu coûteux.

### [`METRICS_LEDGER.md`](./METRICS_LEDGER.md) — P0.3 fait (2026-08-01)

Source de vérité unique pour toutes les métriques citées dans le projet
(extraction, coupe-circuit, golden de scoring, tests). Toute nouvelle mention
de chiffre dans un README/audit doit pointer vers ce fichier ou vers
`ecg-online/data/baseline_report.json` (P0.1), plutôt que d'être recopiée.

---

## 🟡 Documents historiques — figés, ne plus modifier, gardés pour traçabilité

Ces documents ont rempli leur rôle (diagnostic, cadrage initial) et sont
**remplacés** par `roadmap_scientifique_2026.md`. On les garde pour comprendre
*pourquoi* certaines décisions ont été prises, pas pour décider de la suite.

| Document | Rôle historique | Statut |
|---|---|---|
| [`ECG_Online_Architecture_Cible_Feuille_de_Route.md`](./ECG_Online_Architecture_Cible_Feuille_de_Route.md) | Document de cadrage stratégique initial (vision cible, 1882 lignes) | 🔒 Figé — son contenu scientifique est repris et affiné dans `roadmap_scientifique_2026.md` |
| [`FEUILLE_DE_ROUTE_ALIGNEE.md`](./FEUILLE_DE_ROUTE_ALIGNEE.md) | Pont entre le cadrage ci-dessus et le code réel — Paliers 1/2/3 | 🔒 Figé — **Palier 1 et 2 sont terminés et mergés sur `main`** (`ecg-online`, commit `e6a7180`). Le "Palier 3" y décrit est remplacé par P1/P3/P4 de `roadmap_scientifique_2026.md`, qui est plus précis. |
| [`AUDIT.md`](./AUDIT.md) | Audit scientifique initial (précision/rappel, golden set) | 🔒 Figé — chiffres historiques, désormais consolidés dans `METRICS_LEDGER.md` (P0.3, fait) |
| [`AUDIT_ARCHITECTURE_2026.md`](./AUDIT_ARCHITECTURE_2026.md) | Audit hygiène de repo/code (duplication, fichiers morts) | 🔒 Figé — constat, aucune action destructive exécutée. À reprendre seulement si un chantier de nettoyage repo est décidé explicitement |
| [`AUDIT_TECHNOLOGIQUE_2026.md`](./AUDIT_TECHNOLOGIQUE_2026.md) | Choix IA/techno futurs (fine-tuning, local, ontologie↔LLM) | 🔒 Figé — conclusions reprises dans P7 (réduction dépendance techno) de `roadmap_scientifique_2026.md` |
| [`AUDITS.md`](./AUDITS.md) | Index des audits (avant celui-ci) | 🔒 Figé — remplacé par le présent fichier comme point d'entrée |
| [`_AUDIT_TRAME_TRAVAIL.md`](./_AUDIT_TRAME_TRAVAIL.md) | Journal de travail jetable (session d'audit archi) | 🗑️ Jetable — conservé sur demande explicite, aucune valeur de décision |

---

## ⚪ Documents non consultés dans ce cycle (à trier si besoin un jour)

`ARCHITECTURE.md`, `ONTOLOGIE_DOCTRINE.md`, `RUNBOOK_REBUILD_ONTOLOGIE.md` —
non concernés par le cadrage scientifique 2026-07-30, gardés en l'état.

---

## Autres documents de suivi (hors `audit_doc/`, à connaître)

| Document | Rôle | Statut |
|---|---|---|
| `ecg-online/ROADMAP.md` | Suivi d'exécution technique fin grain (P0-P2 historique + Phase A→E golden) | 🟡 Actif mais **partiel** — décrit l'exécution jusqu'à Phase E + Palier 1/2. Les prochaines actions (P1 golden scoring V2 etc.) doivent être ajoutées ici au fur et à mesure, en miroir de `roadmap_scientifique_2026.md` §3/§4. |
| `ecg-online/docs/DATA_DICTIONARY.md` | Contrat JSON `/api/grade` (référence technique stable) | 🟢 Actif, à jour (Palier 2 mergé) |
| `ecg-online/GOLDEN_EXTRACTION.md` | Documentation du golden d'extraction actuel (100 réponses) | 🟢 Actif — base de P1.3/P2.2 du roadmap scientifique |

---

## Règle à partir de maintenant

1. Toute nouvelle priorité/décision se documente dans `roadmap_scientifique_2026.md`
   (section "État d'avancement" + cases à cocher du backlog §5).
2. Ne pas créer de nouveau document `AUDIT_*`/`FEUILLE_DE_ROUTE_*` sans
   d'abord vérifier si `roadmap_scientifique_2026.md` peut simplement être
   étendu — la prolifération de documents de cadrage est ce que ce fichier
   index cherche à arrêter.
3. Si un document historique doit être rouvert (ex. reprendre le nettoyage
   repo de `AUDIT_ARCHITECTURE_2026.md`), le signaler explicitement et créer
   une section dédiée dans `roadmap_scientifique_2026.md` plutôt que de
   reprendre l'ancien fichier isolément.
