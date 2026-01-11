# services/ontology_service.py
"""
Ontology Service with Redis Caching
Loads OWL ontology once and caches in Redis for 24h
"""

import redis
import pickle
import logging
from rdflib import Graph, Namespace, URIRef
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class OntologyService:
    """Service for loading and querying ECG ontology with Redis cache"""
    
    def __init__(
        self,
        redis_url: str = "redis://redis:6379/0",
        ontology_path: str = "/app/data/ontology/ontologie.owx"
    ):
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=False  # Keep binary for pickle
        )
        self.cache_ttl = 86400  # 24 hours
        self.cache_key = "ontology:graph:v1"
        self.ontology_path = Path(ontology_path)
        
        # Define namespaces
        self.ECG = Namespace("http://ontology.chu/ecg#")
        self.RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    
    def get_ontology(self) -> Graph:
        """
        Get ontology graph from cache or load from file
        
        Returns:
            rdflib.Graph: Parsed ontology graph
        """
        # Try cache first
        cached = self.redis_client.get(self.cache_key)
        if cached:
            logger.info("✅ Ontology loaded from Redis cache")
            return pickle.loads(cached)
        
        # Cache miss - load from file
        logger.info(f"📂 Loading ontology from file (cache miss): {self.ontology_path}")
        graph = self._load_from_file()
        
        # Store in cache
        try:
            self.redis_client.setex(
                self.cache_key,
                self.cache_ttl,
                pickle.dumps(graph)
            )
            logger.info(f"💾 Ontology cached in Redis (TTL: {self.cache_ttl}s)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to cache ontology: {e}")
        
        return graph
    
    def _load_from_file(self) -> Graph:
        """Load ontology from OWL file"""
        if not self.ontology_path.exists():
            raise FileNotFoundError(f"Ontology file not found: {self.ontology_path}")
        
        graph = Graph()
        graph.parse(str(self.ontology_path), format="xml")
        
        concept_count = len(list(graph.subjects()))
        logger.info(f"📊 Loaded {concept_count} concepts from ontology")
        
        return graph
    
    def invalidate_cache(self):
        """Invalidate Redis cache (call after ontology update)"""
        deleted = self.redis_client.delete(self.cache_key)
        if deleted:
            logger.info("🗑️ Ontology cache invalidated")
        else:
            logger.warning("⚠️ No cache to invalidate")
    
    def find_concept_by_label(self, label: str, language: str = "fr") -> Optional[str]:
        """
        Find concept URI by label (French or English)
        
        Args:
            label: Concept label to search for
            language: Language code ('fr' or 'en')
        
        Returns:
            Concept URI or None if not found
        """
        graph = self.get_ontology()
        
        # Normalize label
        label_normalized = label.strip().lower()
        
        # Search in all subjects
        for subject in graph.subjects():
            # Get labels
            for _, _, label_literal in graph.triples((subject, self.RDFS.label, None)):
                if hasattr(label_literal, 'language'):
                    if label_literal.language == language:
                        if label_literal.value.lower() == label_normalized:
                            return str(subject)
                else:
                    if str(label_literal).lower() == label_normalized:
                        return str(subject)
        
        return None
    
    def get_concept_label(self, uri: str, language: str = "fr") -> Optional[str]:
        """Get label for a concept URI"""
        graph = self.get_ontology()
        uri_ref = URIRef(uri)
        
        for _, _, label_literal in graph.triples((uri_ref, self.RDFS.label, None)):
            if hasattr(label_literal, 'language'):
                if label_literal.language == language:
                    return str(label_literal.value)
            else:
                return str(label_literal)
        
        return None
    
    def get_related_concepts(
        self, 
        uri: str, 
        relation_type: str = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
    ) -> List[str]:
        """
        Get concepts related via specific relation
        
        Args:
            uri: Source concept URI
            relation_type: Relation URI (e.g., subClassOf, plusPrecisQue)
        
        Returns:
            List of related concept URIs
        """
        graph = self.get_ontology()
        uri_ref = URIRef(uri)
        relation_ref = URIRef(relation_type)
        
        related = []
        for _, _, obj in graph.triples((uri_ref, relation_ref, None)):
            related.append(str(obj))
        
        return related
    
    def has_relation(self, uri1: str, relation: str, uri2: str) -> bool:
        """Check if two concepts are related via specific relation"""
        graph = self.get_ontology()
        
        return (URIRef(uri1), URIRef(relation), URIRef(uri2)) in graph


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    service = OntologyService()
    
    # Test cache
    import time
    
    start = time.time()
    graph1 = service.get_ontology()
    print(f"First load: {(time.time() - start) * 1000:.2f}ms")
    
    start = time.time()
    graph2 = service.get_ontology()
    print(f"Cached load: {(time.time() - start) * 1000:.2f}ms")
    
    # Test search
    bav1_uri = service.find_concept_by_label("BAV 1er degré", "fr")
    print(f"BAV1 URI: {bav1_uri}")
