"""
🧠 LLM Semantic Matcher - Matching Sémantique Intelligent
=========================================================

Architecture Hybride :
- LLM = Traducteur sémantique (comprendre variations linguistiques)
- Système = Contrôle total du scoring (ontologie, poids, hiérarchie)

Date : 2026-01-10
Sprint : 1 - Phase Prototype
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv

# Charger variables d'environnement
load_dotenv()

# Import cache service (Sprint 2)
try:
    from llm_cache_service import (
        get_cached_match,
        set_cached_match,
        get_cache_stats,
        health_check as cache_health_check
    )
    CACHE_AVAILABLE = True
except ImportError:
    try:
        # Fallback pour import depuis racine projet
        from backend.services.llm_cache_service import (
            get_cached_match,
            set_cached_match,
            get_cache_stats,
            health_check as cache_health_check
        )
        CACHE_AVAILABLE = True
    except ImportError:
        CACHE_AVAILABLE = False
        print("⚠️ Cache service non disponible - fonctionnement sans cache")

# ============================================================================
# CONFIGURATION
# ============================================================================

# Initialiser client OpenAI (peut être None si pas de clé)
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = None
        print("⚠️ OPENAI_API_KEY non trouvée - LLM Semantic Matcher désactivé")
except Exception as e:
    client = None
    print(f"⚠️ Erreur initialisation OpenAI client : {e}")

# Types de match possibles
MATCH_TYPE_EXACT = "exact"              # "BAV 2 Mobitz 1" == "BAV 2 Mobitz 1"
MATCH_TYPE_SYNONYM = "synonym"          # "BAV2M1" ~= "BAV 2 Mobitz 1"
MATCH_TYPE_ABBREVIATION = "abbreviation"  # "RS" ~= "Rythme sinusal"
MATCH_TYPE_PARENT = "parent"            # "QRS normal" ~= "QRS fins" (parent)
MATCH_TYPE_CHILD = "child"              # "QRS fins" ~= "QRS normal" (child)
MATCH_TYPE_EQUIVALENT = "equivalent"    # "Sinusal" ~= "Rythme sinusal"
MATCH_TYPE_NO_MATCH = "no_match"        # Aucune correspondance

# Seuil de confiance minimum pour accepter un match (0-100)
CONFIDENCE_THRESHOLD = 70


# ============================================================================
# PROMPT SYSTÈME POUR LE LLM
# ============================================================================

SYSTEM_PROMPT = """Tu es un expert en électrocardiographie (ECG) et en terminologie médicale.

**TON RÔLE UNIQUE : MATCHING SÉMANTIQUE**

Tu NE dois PAS :
- Calculer de score
- Décider de la validité médicale
- Attribuer des points
- Évaluer la qualité d'une réponse

Tu DOIS SEULEMENT :
- Déterminer si deux concepts ECG sont équivalents, synonymes, ou reliés
- Identifier le type de relation (exact, synonyme, abréviation, parent/enfant)
- Estimer ta confiance dans le match (0-100%)
- Expliquer ta logique de matching

**CONTEXTE MÉDICAL :**
- Les étudiants en médecine utilisent souvent des abréviations (BAV2M1, RS, BBG)
- Les termes peuvent varier (Sinusal vs Rythme sinusal, QRS fin vs QRS normal)
- La hiérarchie médicale est importante (QRS normal inclut QRS fins, Axe normal, etc.)
- Les fautes de frappe sont courantes (Sinusl, BAV2 M1 avec espace)

**TYPES DE MATCH À IDENTIFIER :**

1. **exact** : Identiques (casse insensible)
   - Ex: "BAV 2 Mobitz 1" == "bav 2 mobitz 1"

2. **synonym** : Synonymes médicaux
   - Ex: "Wenckebach" ~= "BAV 2 Mobitz 1"

3. **abbreviation** : Abréviation standard
   - Ex: "BAV2M1" ~= "BAV 2 Mobitz 1"
   - Ex: "RS" ~= "Rythme sinusal"
   - Ex: "BBG" ~= "Bloc de branche gauche"

4. **equivalent** : Variantes équivalentes
   - Ex: "Sinusal" ~= "Rythme sinusal"
   - Ex: "QRS fin" ~= "QRS fins" (singulier/pluriel)

5. **parent** : Concept étudiant est parent du concept attendu
   - Ex: Étudiant dit "QRS normal", attendu "QRS fins"
   - QRS normal (parent) inclut QRS fins (enfant)
   - Match partiel acceptable

6. **child** : Concept étudiant est enfant du concept attendu
   - Ex: Étudiant dit "QRS fins", attendu "QRS normal"
   - Plus précis qu'attendu (bon signe)

7. **no_match** : Aucune relation
   - Ex: "Bloc de branche gauche" ≠ "Rythme sinusal"

**FORMAT DE RÉPONSE STRICT :**

Réponds UNIQUEMENT en JSON valide :

{
  "match": true/false,
  "match_type": "exact|synonym|abbreviation|equivalent|parent|child|no_match",
  "confidence": 0-100,
  "explanation": "Explication courte du matching"
}

**EXEMPLES :**

Input: student="BAV2M1", expected="BAV 2 Mobitz 1"
Output: {"match": true, "match_type": "abbreviation", "confidence": 95, "explanation": "BAV2M1 est l'abréviation standard de BAV 2 Mobitz 1"}

Input: student="Sinusal", expected="Rythme sinusal"
Output: {"match": true, "match_type": "equivalent", "confidence": 90, "explanation": "Sinusal est une variante courante de Rythme sinusal"}

Input: student="QRS normal", expected="QRS fins"
Output: {"match": true, "match_type": "parent", "confidence": 80, "explanation": "QRS normal est le concept parent qui inclut QRS fins"}

Input: student="BBG", expected="Bloc de branche droit"
Output: {"match": false, "match_type": "no_match", "confidence": 100, "explanation": "BBG signifie Bloc de branche gauche, pas droit"}

**RAPPEL : Tu es un traducteur sémantique, PAS un correcteur. Le scoring est géré par l'ontologie système.**
"""


# ============================================================================
# FONCTION PRINCIPALE : SEMANTIC MATCH
# ============================================================================

def semantic_match(
    student_concept: str,
    expected_concept: str,
    ontology_context: Optional[Dict] = None
) -> Dict:
    """
    Détermine si un concept étudiant correspond sémantiquement à un concept attendu.
    
    ARCHITECTURE SPRINT 2 :
    1. Essayer cache Redis (si disponible)
    2. Si cache miss → Appel LLM
    3. Stocker résultat en cache
    
    LE LLM NE CALCULE PAS LE SCORE ! Il fait seulement du matching sémantique.
    Le système utilise ensuite l'ontologie pour scorer selon poids/hiérarchie.
    
    Args:
        student_concept: Concept écrit par l'étudiant (ex: "BAV2M1")
        expected_concept: Concept attendu de l'ontologie (ex: "BAV 2 Mobitz 1")
        ontology_context: Contexte ontologique optionnel (hiérarchie, synonymes OWL)
    
    Returns:
        {
            "match": bool,                  # Est-ce un match ?
            "match_type": str,              # Type de match (exact, synonym, etc.)
            "confidence": int,              # Confiance 0-100
            "explanation": str,             # Explication du matching
            "student_concept": str,         # Concept étudiant (echo)
            "expected_concept": str,        # Concept attendu (echo)
            "ontology_context_used": bool,  # Contexte ontologie utilisé ?
            "cached": bool,                 # Résultat vient du cache ?
            "latency_ms": float             # Temps de réponse en ms
        }
    """
    start_time = time.time()
    
    # ====================================================================
    # PHASE 1 : ESSAYER LE CACHE (Sprint 2)
    # ====================================================================
    
    if CACHE_AVAILABLE:
        try:
            cached_result = get_cached_match(student_concept, expected_concept)
            if cached_result:
                # Cache HIT - retourner immédiatement
                latency_ms = (time.time() - start_time) * 1000
                cached_result["latency_ms"] = latency_ms
                return cached_result
        except Exception as e:
            # Cache error - continuer sans cache
            print(f"⚠️ Erreur cache (continuing without): {e}")
    
    # ====================================================================
    # PHASE 2 : APPEL LLM (Cache miss ou cache indisponible)
    # ====================================================================
    
    # Construire le prompt utilisateur
    user_prompt = f"""
Détermine si ces deux concepts ECG correspondent :

**Concept étudiant :** "{student_concept}"
**Concept attendu :** "{expected_concept}"
"""
    
    # Ajouter contexte ontologique si disponible
    if ontology_context:
        user_prompt += f"\n**Contexte ontologique :**\n```json\n{json.dumps(ontology_context, indent=2, ensure_ascii=False)}\n```\n"
    
    user_prompt += "\nRéponds en JSON uniquement."
    
    # Vérifier que le client est disponible
    if not client:
        result = {
            "match": False,
            "match_type": MATCH_TYPE_NO_MATCH,
            "confidence": 0,
            "explanation": "LLM non disponible (OPENAI_API_KEY manquante)",
            "student_concept": student_concept,
            "expected_concept": expected_concept,
            "ontology_context_used": False,
            "cached": False,
            "latency_ms": (time.time() - start_time) * 1000,
            "error": "No OpenAI client"
        }
        return result
    
    try:
        # Appel API OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Très bas pour cohérence maximale
            max_tokens=300,
            response_format={"type": "json_object"}  # Force JSON
        )
        
        # Parser la réponse
        result = json.loads(response.choices[0].message.content)
        
        # Validation structure
        if not all(k in result for k in ["match", "match_type", "confidence", "explanation"]):
            raise ValueError("Réponse LLM incomplète")
        
        # Normalisation confiance (au cas où LLM retourne float)
        result["confidence"] = int(result["confidence"])
        
        # Clamp confidence 0-100
        result["confidence"] = max(0, min(100, result["confidence"]))
        
        # Appliquer seuil de confiance
        if result["confidence"] < CONFIDENCE_THRESHOLD:
            result["match"] = False
            result["match_type"] = MATCH_TYPE_NO_MATCH
            result["explanation"] += f" (Confiance {result['confidence']}% < seuil {CONFIDENCE_THRESHOLD}%)"
        
        # Ajouter métadonnées
        result["student_concept"] = student_concept
        result["expected_concept"] = expected_concept
        result["ontology_context_used"] = ontology_context is not None
        result["cached"] = False
        result["latency_ms"] = (time.time() - start_time) * 1000
        
        # ====================================================================
        # PHASE 3 : STOCKER EN CACHE (Sprint 2)
        # ====================================================================
        
        if CACHE_AVAILABLE and result["match"]:
            try:
                set_cached_match(student_concept, expected_concept, result)
            except Exception as e:
                print(f"⚠️ Erreur stockage cache: {e}")
        
        return result
        
    except Exception as e:
        # Fallback en cas d'erreur API
        latency_ms = (time.time() - start_time) * 1000
        return {
            "match": False,
            "match_type": MATCH_TYPE_NO_MATCH,
            "confidence": 0,
            "explanation": f"Erreur LLM : {str(e)}",
            "student_concept": student_concept,
            "expected_concept": expected_concept,
            "ontology_context_used": False,
            "cached": False,
            "latency_ms": latency_ms,
            "error": str(e)
        }


# ============================================================================
# FONCTION BATCH : MATCHER PLUSIEURS CONCEPTS
# ============================================================================

def batch_semantic_match(
    student_concepts: List[str],
    expected_concepts: List[str],
    ontology: Dict
) -> List[Dict]:
    """
    Matche une liste de concepts étudiants contre des concepts attendus.
    
    Args:
        student_concepts: Liste concepts étudiants
        expected_concepts: Liste concepts attendus (ontologie)
        ontology: Ontologie complète (pour contexte)
    
    Returns:
        Liste de résultats de matching
    """
    results = []
    
    for student_concept in student_concepts:
        best_match = None
        best_confidence = 0
        
        # Chercher le meilleur match parmi tous les concepts attendus
        for expected_concept in expected_concepts:
            # Extraire contexte ontologique pour ce concept
            context = _extract_ontology_context(expected_concept, ontology)
            
            # Faire le matching
            match_result = semantic_match(student_concept, expected_concept, context)
            
            # Garder le meilleur match
            if match_result["match"] and match_result["confidence"] > best_confidence:
                best_match = match_result
                best_confidence = match_result["confidence"]
        
        # Ajouter résultat (ou no_match si rien trouvé)
        if best_match:
            results.append(best_match)
        else:
            results.append({
                "match": False,
                "match_type": MATCH_TYPE_NO_MATCH,
                "confidence": 0,
                "explanation": f"Aucun concept attendu ne correspond à '{student_concept}'",
                "student_concept": student_concept,
                "expected_concept": None,
                "ontology_context_used": False
            })
    
    return results


# ============================================================================
# HELPERS
# ============================================================================

def _extract_ontology_context(concept_name: str, ontology: Dict) -> Dict:
    """
    Extrait le contexte ontologique pertinent pour un concept.
    
    Args:
        concept_name: Nom du concept (ex: "BAV 2 Mobitz 1")
        ontology: Ontologie complète
    
    Returns:
        Contexte pertinent (synonymes, hiérarchie, catégorie)
    """
    context = {}
    
    # Chercher le concept dans l'ontologie
    for concept_id, concept_data in ontology.items():
        if concept_data.get("name") == concept_name:
            context = {
                "id": concept_id,
                "name": concept_data.get("name"),
                "synonyms": concept_data.get("synonyms", []),
                "category": concept_data.get("category"),
                "implications": concept_data.get("implications", []),
                "weight": concept_data.get("weight", 1)
            }
            break
    
    return context


def get_match_type_emoji(match_type: str) -> str:
    """Retourne un emoji pour visualiser le type de match."""
    emojis = {
        MATCH_TYPE_EXACT: "🎯",
        MATCH_TYPE_SYNONYM: "🔄",
        MATCH_TYPE_ABBREVIATION: "📝",
        MATCH_TYPE_EQUIVALENT: "≈",
        MATCH_TYPE_PARENT: "⬆️",
        MATCH_TYPE_CHILD: "⬇️",
        MATCH_TYPE_NO_MATCH: "❌"
    }
    return emojis.get(match_type, "❓")


def get_match_type_label(match_type: str) -> str:
    """Retourne un label français pour le type de match."""
    labels = {
        MATCH_TYPE_EXACT: "Correspondance exacte",
        MATCH_TYPE_SYNONYM: "Synonyme médical",
        MATCH_TYPE_ABBREVIATION: "Abréviation",
        MATCH_TYPE_EQUIVALENT: "Équivalent",
        MATCH_TYPE_PARENT: "Concept parent (partiel)",
        MATCH_TYPE_CHILD: "Concept enfant (précis)",
        MATCH_TYPE_NO_MATCH: "Aucune correspondance"
    }
    return labels.get(match_type, "Type inconnu")


def get_llm_stats() -> Dict:
    """
    Retourne les statistiques LLM + Cache.
    
    Returns:
        Dict avec cache stats + LLM info
    """
    stats = {
        "llm_available": client is not None,
        "cache_available": CACHE_AVAILABLE,
        "model": "gpt-4o",
        "temperature": 0.1,
        "confidence_threshold": CONFIDENCE_THRESHOLD
    }
    
    # Ajouter stats cache si disponible
    if CACHE_AVAILABLE:
        try:
            cache_stats = get_cache_stats()
            stats["cache"] = cache_stats
            
            # Ajouter cache health
            cache_health = cache_health_check()
            stats["cache_health"] = cache_health["status"]
        except Exception as e:
            stats["cache"] = {"error": str(e)}
            stats["cache_health"] = "error"
    
    return stats


# ============================================================================
# MAIN - TESTS
# ============================================================================

if __name__ == "__main__":
    """Tests de validation du matching sémantique."""
    
    print("🧠 Tests LLM Semantic Matcher\n")
    
    if not client:
        print("❌ OpenAI client non disponible - définir OPENAI_API_KEY dans .env")
        print("ℹ️  Pour tester, créer un fichier .env à la racine avec:")
        print("   OPENAI_API_KEY=sk-...")
        exit(1)
    
    # Test 1 : Abréviation
    print("Test 1 : BAV2M1 vs BAV 2 Mobitz 1")
    result = semantic_match("BAV2M1", "BAV 2 Mobitz 1")
    print(f"  Match: {result['match']} ({result['match_type']}, {result['confidence']}%)")
    print(f"  Explication: {result['explanation']}\n")
    
    # Test 2 : Équivalent
    print("Test 2 : Sinusal vs Rythme sinusal")
    result = semantic_match("Sinusal", "Rythme sinusal")
    print(f"  Match: {result['match']} ({result['match_type']}, {result['confidence']}%)")
    print(f"  Explication: {result['explanation']}\n")
    
    # Test 3 : Parent
    print("Test 3 : QRS normal vs QRS fins")
    result = semantic_match("QRS normal", "QRS fins")
    print(f"  Match: {result['match']} ({result['match_type']}, {result['confidence']}%)")
    print(f"  Explication: {result['explanation']}\n")
    
    # Test 4 : No match
    print("Test 4 : BBG vs Bloc de branche droit")
    result = semantic_match("BBG", "Bloc de branche droit")
    print(f"  Match: {result['match']} ({result['match_type']}, {result['confidence']}%)")
    print(f"  Explication: {result['explanation']}\n")
    
    print("✅ Tests terminés")
