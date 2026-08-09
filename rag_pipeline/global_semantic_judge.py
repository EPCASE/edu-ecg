"""
🧱 Juge Sémantique Global — prototype (Phase 2 de la proposition d'itération)
==============================================================================
Un seul appel LLM lit TOUTE la réponse étudiante d'un coup et produit un
GlobalSemanticReport structuré (cf. global_semantic_schema.py), au lieu de
fragmenter le texte en entités résolues séparément (pipeline actuel : Brique
2 NER → Brique 3 recherche hybride → Brique 4 juge local par concept).

Ce module est autonome : il n'importe ni ne modifie ner_extractor.py,
neurosymbolic_judge.py ni scoring_v3.py. Il peut tourner en parallèle du
pipeline actuel sans aucun risque de régression (shadow mode).

Stratégie de récupération de contexte ontologique (cf. proposition §11) :
  1. Récupération lexicale légère (BM25 + dense, réutilise HybridSearchEngine)
     sur le texte entier découpé en fenêtres, pour obtenir un pool de
     concepts candidats plausibles — SANS trancher le sens.
  2. Enrichissement du pool avec parents/enfants/requires/supports/excludes.
  3. Ajout systématique des concepts validants/exclusions du contrat du cas
     (golden_ids), pour que le juge puisse toujours au moins comparer à la
     cible attendue.
  4. Jugement global du LLM sur ce sous-graphe compact (10-30 concepts),
     jamais sur les 349 concepts complets de l'ontologie.

Auteur : BMad Team
Date   : 2026-08-02
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from dotenv import load_dotenv
from openai import OpenAI

from global_semantic_schema import GlobalSemanticReport
from hybrid_search import HybridSearchEngine
from semantic_layer import get_concept, normalize_key, _get_ontology_v2

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-2024-08-06"

# Nombre maximal de concepts candidats soumis au juge (garde-fou §12 :
# catalogue compact, pas les 349 concepts de l'ontologie).
MAX_CANDIDATES = 30


# ---------------------------------------------------------------------------
# Client OpenAI (singleton module-level)
# ---------------------------------------------------------------------------

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        env_candidates = [
            Path(".env"),
            Path(__file__).parent / ".env",
            Path(__file__).parent.parent / "ECG lecture" / ".env",
        ]
        for env_path in env_candidates:
            if env_path.exists():
                load_dotenv(env_path)
                break
        else:
            load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY non trouvée. "
                "Ajoutez-la dans un fichier .env ou en variable d'environnement."
            )
        _client = OpenAI(api_key=api_key)
    return _client


_engine: Optional[HybridSearchEngine] = None


def _get_engine() -> HybridSearchEngine:
    global _engine
    if _engine is None:
        index_dir = str(Path(__file__).parent / "rag_index")
        _engine = HybridSearchEngine(index_dir)
    return _engine


# ---------------------------------------------------------------------------
# Étape 1-3 : construction du catalogue candidat compact
# ---------------------------------------------------------------------------

def _naive_windows(texte: str, window_words: int = 6) -> List[str]:
    """
    Découpage naïf en fenêtres glissantes de mots, pour donner à la
    recherche lexicale/dense plusieurs points d'ancrage sur le texte
    entier (contrairement au NER actuel, on ne cherche PAS ici à isoler
    des entités précises — juste à récupérer un pool de candidats).
    """
    mots = texte.split()
    if not mots:
        return []
    if len(mots) <= window_words:
        return [texte]
    windows = []
    step = max(1, window_words // 2)
    for i in range(0, len(mots), step):
        chunk = " ".join(mots[i : i + window_words])
        if chunk:
            windows.append(chunk)
    return windows


def _expand_with_relations(concept_id: str, onto: Dict, depth: int = 1) -> Set[str]:
    """Retourne concept_id + parents directs + enfants directs + requires + supports + excludes."""
    out = {concept_id}
    c = get_concept(concept_id)
    if not c:
        return out
    for rel in ("parents", "requires", "supports", "excludes"):
        for rid in c.get(rel, []) or []:
            out.add(normalize_key(rid) if isinstance(rid, str) else rid)
    # Enfants directs : parcours O(n_concepts), acceptable pour ~350 concepts
    for cid, cdata in onto.get("concepts", {}).items():
        if concept_id in (cdata.get("parents") or []):
            out.add(cid)
    return out


def build_candidate_catalog(
    texte_etudiant: str,
    golden_ids: Optional[List[str]] = None,
    max_candidates: int = MAX_CANDIDATES,
) -> List[Dict]:
    """
    Construit le catalogue ontologique compact soumis au juge global.

    Returns:
        Liste de dicts {ontology_id, concept_name, categorie, poids,
        parents, requires, excludes} — un par concept candidat retenu.
    """
    engine = _get_engine()
    onto = _get_ontology_v2()

    pool: Set[str] = set()

    # 1. Récupération lexicale/dense sur des fenêtres du texte entier
    for window in _naive_windows(texte_etudiant):
        for cand in engine.search_top_k(window, k=5):
            pool.add(cand["ontology_id"])

    # 2. Toujours inclure les concepts du contrat du cas (validants/exclusions)
    for gid in golden_ids or []:
        pool.add(normalize_key(gid))

    # 3. Enrichissement relationnel (parents/enfants/requires/supports/excludes)
    enriched: Set[str] = set()
    for cid in list(pool):
        enriched |= _expand_with_relations(cid, onto)
    pool |= enriched

    # 4. Troncature au budget si nécessaire (priorité : golden_ids d'abord)
    ordered = [normalize_key(g) for g in (golden_ids or [])]
    ordered += [c for c in pool if c not in ordered]
    ordered = ordered[:max_candidates]

    catalog = []
    for cid in ordered:
        c = get_concept(cid)
        if not c:
            continue
        catalog.append(
            {
                "ontology_id": cid,
                "concept_name": c.get("concept_name", cid),
                "categorie": c.get("categorie", ""),
                "poids": c.get("poids", 1),
                "parents": c.get("parents", []),
                "requires": c.get("requires", []),
                "excludes": c.get("excludes", []),
            }
        )
    return catalog


# ---------------------------------------------------------------------------
# Prompt système — Juge Sémantique Global
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
Tu es un cardiologue expert en lecture d'ECG. Tu lis la réponse COMPLÈTE d'un étudiant à propos d'un tracé ECG, et tu dois produire une représentation structurée de ce que l'étudiant affirme, sans calculer aucune note.

RÈGLES STRICTES :

1. Choisis les `concept_id` UNIQUEMENT parmi le catalogue de concepts fourni. N'invente jamais un ID absent du catalogue.

2. Pour chaque proposition clinique clairement exprimée (explicite, paraphrasée, ou déduite d'une combinaison de signes), crée un `claim` avec :
   - `polarity` : present (affirmé vrai) / absent (nié) / discussed (évoqué sans trancher) / rejected (évoqué puis explicitement écarté au profit d'un autre diagnostic).
   - `certainty` : asserted / probable / possible / uncertain — reflète la formulation de l'étudiant (ex: "certain", "probable", "pourrait être", "évoque").
   - `expression_mode` :
     - explicit : le concept est nommé tel quel.
     - paraphrased : le concept est nommé mais avec un vocabulaire très différent.
     - implicit_complete : le concept n'est PAS nommé mais une combinaison COMPLÈTE et non ambiguë de signes le désigne sans autre interprétation possible.
     - implicit_partial : des signes évoquent le concept mais de façon incomplète (manque un critère clé).
     - unsupported : le concept est affirmé SANS AUCUN argument descriptif dans le texte.
   - `evidence_spans` : cite le ou les segments EXACTS du texte étudiant qui justifient la proposition (recopie littérale, pas de paraphrase).
   - `inferred_from` : si `expression_mode` est implicite, liste les `claim_id` des propositions explicites (mesures, signes) qui permettent l'inférence.

3. NÉGATION PUIS AFFIRMATION : si le texte nie un concept puis l'affirme ensuite (ou l'inverse) pour le MÊME concept, crée DEUX claims distincts (l'un absent, l'autre present) — ne fusionne jamais, ne fais pas «gagner» la dernière mention silencieusement. Signale-le aussi comme contradiction.

4. CONTRADICTIONS : détecte toute paire de propositions mutuellement incompatibles cliniquement (ex: deux diagnostics rythmiques exclusifs affirmés tous deux comme certains, normalité globale + anomalie majeure simultanées). Ajoute une entrée dans `contradictions` avec les `claim_id` concernés.

5. MESURES NUMÉRIQUES : pour chaque valeur chiffrée mentionnée (PR, QRS, QTc, fréquence, axe...), crée une entrée `measurements` avec la valeur, l'unité, l'interprétation donnée par l'étudiant, et `coherent=false` si cette interprétation est cliniquement incompatible avec la valeur (ex: QRS à 90 ms mais bloc de branche complet affirmé).

6. DIAGNOSTIC GRAVE NON SOUTENU : si un diagnostic à `categorie` DIAGNOSTIC_URGENT ou DIAGNOSTIC_MAJEUR est affirmé sans AUCUN argument descriptif dans le texte, ajoute une entrée dans `unsupported_claims` avec une sévérité appropriée.

7. Si un segment du texte semble cliniquement pertinent mais ne correspond à AUCUN concept du catalogue fourni, ajoute-le dans `unresolved_mentions` plutôt que d'inventer un concept.

8. NE CALCULE AUCUNE NOTE. Ta seule sortie est la structure demandée.
""".strip()


# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def judge_global(
    texte_etudiant: str,
    golden_ids: Optional[List[str]] = None,
    catalog: Optional[List[Dict]] = None,
) -> GlobalSemanticReport:
    """
    Appelle le juge sémantique global sur une réponse étudiante complète.

    Args:
        texte_etudiant: Texte libre complet de l'étudiant.
        golden_ids: IDs golden du cas (toujours inclus dans le catalogue,
                    même si le texte ne les mentionne pas lexicalement).
        catalog: Catalogue pré-construit (optionnel, pour éviter de
                 reconstruire le pool à chaque appel dans une boucle de test).

    Returns:
        GlobalSemanticReport structuré (aucune note).
    """
    client = _get_client()
    catalog = catalog if catalog is not None else build_candidate_catalog(
        texte_etudiant, golden_ids
    )

    catalog_lines = []
    for c in catalog:
        catalog_lines.append(
            f"- {c['concept_name']} (ID: {c['ontology_id']}) "
            f"[catégorie: {c['categorie']}, poids: {c['poids']}]"
        )
    catalog_text = "\n".join(catalog_lines) if catalog_lines else "(catalogue vide)"

    user_prompt = (
        f"Réponse complète de l'étudiant :\n\"\"\"\n{texte_etudiant}\n\"\"\"\n\n"
        f"Catalogue de concepts disponibles pour ce cas :\n{catalog_text}\n"
    )

    logger.info(
        f"🧑‍⚖️ Juge global : texte de {len(texte_etudiant)} caractères, "
        f"{len(catalog)} concepts candidats"
    )

    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format=GlobalSemanticReport,
        temperature=0,
        seed=42,
    )

    result = response.choices[0].message.parsed
    if result is None:
        result = GlobalSemanticReport()

    # Validation minimale (garde-fou §12) : ne garder que les claims dont le
    # concept_id appartient réellement au catalogue soumis.
    valid_ids = {c["ontology_id"] for c in catalog}
    filtered_claims = []
    for claim in result.claims:
        if claim.concept_id in valid_ids:
            filtered_claims.append(claim)
        else:
            logger.warning(
                f"⚠️ Juge global : concept_id hors catalogue rejeté : "
                f"'{claim.concept_id}' (claim {claim.claim_id})"
            )
    result.claims = filtered_claims

    logger.info(
        f"✅ Juge global : {len(result.claims)} claims, "
        f"{len(result.contradictions)} contradictions, "
        f"{len(result.unsupported_claims)} unsupported"
    )

    return result


# ---------------------------------------------------------------------------
# Point d'entrée CLI pour test rapide
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    texte_test = (
        "Il n'y a pas de fibrillation atriale sur ce tracé. "
        "Le diagnostic final est une fibrillation atriale."
    )
    golden_test = ["FIBRILLATION_ATRIALE"]

    print(f"\n📝 Texte étudiant :\n   {texte_test}\n")
    report = judge_global(texte_test, golden_ids=golden_test)

    print(f"\n🧑‍⚖️ {len(report.claims)} claims :")
    for c in report.claims:
        print(f"  [{c.polarity:>9}|{c.certainty:>9}|{c.expression_mode:>18}] {c.concept_id}")
    print(f"\n⚠️ {len(report.contradictions)} contradictions :")
    for ct in report.contradictions:
        print(f"  {ct.claim_ids} — {ct.explanation}")

    print("\n✅ Juge Sémantique Global — test terminé.")
