"""
🗄️ LLM Cache Service - Redis Cache Layer
==========================================

Réduit les appels API OpenAI de ~70% via cache intelligent.

Architecture:
- Cache key: hash(student_concept + expected_concept)
- TTL: 24h (configurable)
- Fallback gracieux si Redis indisponible

Date: 2026-01-10
Sprint: 2 - Production Hardening
Ticket: #1
"""

import os
import json
import hashlib
import redis
from typing import Optional, Dict
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL_SECONDS = int(os.getenv("LLM_CACHE_TTL", "86400"))  # 24h par défaut
CACHE_ENABLED = os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"

# Métriques (simples compteurs, seront exposés via Prometheus plus tard)
cache_stats = {
    "hits": 0,
    "misses": 0,
    "errors": 0,
    "total_requests": 0
}

# ============================================================================
# REDIS CLIENT
# ============================================================================

try:
    if CACHE_ENABLED:
        redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2
        )
        # Test connection
        redis_client.ping()
        print("[OK] Redis cache connecte : " + str(REDIS_URL))
    else:
        redis_client = None
        print("[INFO] Cache LLM desactive (LLM_CACHE_ENABLED=false)")
except Exception as e:
    redis_client = None
    print("[WARN] Redis non disponible - cache desactive : " + str(e))


# ============================================================================
# CACHE FUNCTIONS
# ============================================================================

def generate_cache_key(student_concept: str, expected_concept: str) -> str:
    """
    Génère une clé de cache unique basée sur les concepts.
    
    Utilise un hash pour:
    - Normaliser les concepts (case-insensitive)
    - Limiter la taille de la clé
    - Anonymiser les données
    
    Args:
        student_concept: Concept écrit par l'étudiant
        expected_concept: Concept attendu de l'ontologie
    
    Returns:
        Cache key (str): "llm_match:{hash}"
    """
    # Normaliser (lowercase, strip whitespace)
    student_norm = student_concept.lower().strip()
    expected_norm = expected_concept.lower().strip()
    
    # Combiner et hasher
    combined = f"{student_norm}|{expected_norm}"
    hash_value = hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    return f"llm_match:{hash_value}"


def get_cached_match(student_concept: str, expected_concept: str) -> Optional[Dict]:
    """
    Récupère un résultat de matching depuis le cache.
    
    Args:
        student_concept: Concept étudiant
        expected_concept: Concept attendu
    
    Returns:
        Dict résultat LLM si trouvé en cache, None sinon
    """
    global cache_stats
    cache_stats["total_requests"] += 1
    
    if not redis_client:
        return None
    
    try:
        cache_key = generate_cache_key(student_concept, expected_concept)
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            cache_stats["hits"] += 1
            result = json.loads(cached_data)
            
            # Ajouter flag cached pour transparence
            result["cached"] = True
            result["cached_at"] = result.get("cached_at", datetime.now().isoformat())
            
            return result
        else:
            cache_stats["misses"] += 1
            return None
            
    except Exception as e:
        cache_stats["errors"] += 1
        print(f"⚠️ Erreur lecture cache: {e}")
        return None


def set_cached_match(
    student_concept: str,
    expected_concept: str,
    match_result: Dict,
    ttl: Optional[int] = None
) -> bool:
    """
    Stocke un résultat de matching dans le cache.
    
    Args:
        student_concept: Concept étudiant
        expected_concept: Concept attendu
        match_result: Résultat LLM à cacher
        ttl: Time-to-live en secondes (défaut: CACHE_TTL_SECONDS)
    
    Returns:
        True si succès, False sinon
    """
    if not redis_client:
        return False
    
    try:
        cache_key = generate_cache_key(student_concept, expected_concept)
        
        # Enrichir avec métadonnées cache
        cached_result = {
            **match_result,
            "cached_at": datetime.now().isoformat(),
            "ttl": ttl or CACHE_TTL_SECONDS
        }
        
        # Sérializer et stocker
        serialized = json.dumps(cached_result, ensure_ascii=False)
        redis_client.setex(
            cache_key,
            ttl or CACHE_TTL_SECONDS,
            serialized
        )
        
        return True
        
    except Exception as e:
        cache_stats["errors"] += 1
        print(f"⚠️ Erreur écriture cache: {e}")
        return False


def invalidate_cache(student_concept: str, expected_concept: str) -> bool:
    """
    Invalide une entrée spécifique du cache.
    
    Args:
        student_concept: Concept étudiant
        expected_concept: Concept attendu
    
    Returns:
        True si supprimé, False sinon
    """
    if not redis_client:
        return False
    
    try:
        cache_key = generate_cache_key(student_concept, expected_concept)
        deleted = redis_client.delete(cache_key)
        return deleted > 0
    except Exception as e:
        print(f"⚠️ Erreur invalidation cache: {e}")
        return False


def flush_cache() -> bool:
    """
    Vide tout le cache LLM (pattern llm_match:*).
    
    ⚠️ Utiliser avec précaution !
    
    Returns:
        True si succès, False sinon
    """
    if not redis_client:
        return False
    
    try:
        # Récupérer toutes les clés llm_match:*
        keys = redis_client.keys("llm_match:*")
        if keys:
            redis_client.delete(*keys)
            print(f"🗑️ Cache vidé : {len(keys)} entrées supprimées")
        return True
    except Exception as e:
        print(f"⚠️ Erreur flush cache: {e}")
        return False


def get_cache_stats() -> Dict:
    """
    Retourne les statistiques d'utilisation du cache.
    
    Returns:
        Dict avec hits, misses, hit_rate, etc.
    """
    total = cache_stats["total_requests"]
    hits = cache_stats["hits"]
    misses = cache_stats["misses"]
    
    hit_rate = (hits / total * 100) if total > 0 else 0
    
    return {
        "total_requests": total,
        "cache_hits": hits,
        "cache_misses": misses,
        "cache_errors": cache_stats["errors"],
        "hit_rate_percent": round(hit_rate, 2),
        "cache_enabled": redis_client is not None,
        "redis_url": REDIS_URL if redis_client else None,
        "ttl_seconds": CACHE_TTL_SECONDS
    }


def get_cache_size() -> int:
    """
    Retourne le nombre d'entrées dans le cache.
    
    Returns:
        Nombre de clés llm_match:*
    """
    if not redis_client:
        return 0
    
    try:
        keys = redis_client.keys("llm_match:*")
        return len(keys)
    except Exception as e:
        print(f"⚠️ Erreur comptage cache: {e}")
        return 0


# ============================================================================
# HEALTH CHECK
# ============================================================================

def health_check() -> Dict:
    """
    Vérifie la santé du service cache.
    
    Returns:
        Dict avec status et détails
    """
    if not redis_client:
        return {
            "status": "disabled",
            "message": "Cache désactivé ou Redis non disponible",
            "cache_enabled": CACHE_ENABLED,
            "redis_url": REDIS_URL
        }
    
    try:
        # Test ping
        redis_client.ping()
        
        # Infos Redis
        info = redis_client.info("stats")
        
        return {
            "status": "healthy",
            "message": "Cache opérationnel",
            "cache_enabled": True,
            "redis_url": REDIS_URL,
            "cache_size": get_cache_size(),
            "stats": get_cache_stats(),
            "redis_info": {
                "total_connections_received": info.get("total_connections_received"),
                "total_commands_processed": info.get("total_commands_processed"),
                "used_memory_human": redis_client.info("memory").get("used_memory_human")
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Erreur Redis: {str(e)}",
            "cache_enabled": CACHE_ENABLED,
            "redis_url": REDIS_URL
        }


# ============================================================================
# MAIN - TESTS
# ============================================================================

if __name__ == "__main__":
    """Tests du service cache."""
    
    print("🧪 Tests LLM Cache Service\n")
    
    # Test 1: Health check
    print("Test 1: Health Check")
    health = health_check()
    print(f"  Status: {health['status']}")
    print(f"  Message: {health['message']}\n")
    
    if health["status"] == "disabled":
        print("⚠️ Cache désactivé - lancez Redis pour tester:")
        print("   docker run -d -p 6379:6379 redis:alpine")
        exit(0)
    
    # Test 2: Set + Get
    print("Test 2: Set + Get")
    test_result = {
        "match": True,
        "match_type": "abbreviation",
        "confidence": 95,
        "explanation": "Test cache"
    }
    
    success = set_cached_match("BAV2M1", "BAV 2 Mobitz 1", test_result)
    print(f"  Set: {'✅' if success else '❌'}")
    
    cached = get_cached_match("BAV2M1", "BAV 2 Mobitz 1")
    print(f"  Get: {'✅' if cached else '❌'}")
    print(f"  Cached flag: {cached.get('cached') if cached else 'N/A'}\n")
    
    # Test 3: Cache miss
    print("Test 3: Cache Miss")
    missed = get_cached_match("INCONNU", "INCONNU")
    print(f"  Miss: {'✅' if missed is None else '❌'}\n")
    
    # Test 4: Stats
    print("Test 4: Cache Stats")
    stats = get_cache_stats()
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Cache hits: {stats['cache_hits']}")
    print(f"  Cache misses: {stats['cache_misses']}")
    print(f"  Hit rate: {stats['hit_rate_percent']}%\n")
    
    # Test 5: Cache size
    print("Test 5: Cache Size")
    size = get_cache_size()
    print(f"  Entries: {size}\n")
    
    # Test 6: Invalidate
    print("Test 6: Invalidate Entry")
    invalidated = invalidate_cache("BAV2M1", "BAV 2 Mobitz 1")
    print(f"  Invalidated: {'✅' if invalidated else '❌'}")
    
    still_cached = get_cached_match("BAV2M1", "BAV 2 Mobitz 1")
    print(f"  Still cached: {'❌' if still_cached is None else '✅'}\n")
    
    print("✅ Tests terminés")
