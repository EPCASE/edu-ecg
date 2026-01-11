"""
🎯 Ontology Relation Resolver
Service pour extraire les relations ontologiques depuis OWL

Remplace le code hardcodé par lecture dynamique de l'ontologie.
Utilisé par le module de correction pour exploiter les relations OWL.

Auteur: Edu-ECG Team (Migration OWL)
Date: 2026-01-11
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set

logger = logging.getLogger(__name__)


class OntologyRelationResolver:
    """
    Résout les relations ontologiques depuis ontology_from_owl.json
    
    Relations supportées:
    - implications : Un concept implique d'autres concepts (ex: BAV1 → PR allongé)
    - is_a : Hiérarchie parent/enfant
    - territoires : Relations anatomiques
    - synonymes : Variantes linguistiques
    """
    
    def __init__(self, ontology_path: Optional[str] = None):
        """
        Args:
            ontology_path: Chemin vers ontology_from_owl.json
                          Si None, utilise le chemin par défaut
        """
        if ontology_path is None:
            ontology_path = Path(__file__).parent.parent.parent / "data" / "ontology_from_owl.json"
        
        self.ontology_path = Path(ontology_path)
        self.ontology = self._load_ontology()
        self.concept_mappings = self.ontology.get('concept_mappings', {})
        
        logger.info(f"✅ OntologyRelationResolver loaded: {len(self.concept_mappings)} concepts")
    
    def _load_ontology(self) -> Dict:
        """Charge l'ontologie OWL depuis le fichier JSON"""
        try:
            with open(self.ontology_path, 'r', encoding='utf-8') as f:
                ontology = json.load(f)
            logger.info(f"✅ Ontology loaded from {self.ontology_path}")
            return ontology
        except FileNotFoundError:
            logger.error(f"❌ Ontology file not found: {self.ontology_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in ontology: {e}")
            return {}
    
    def get_implications(self, concept: str) -> List[str]:
        """
        Retourne les concepts impliqués par un concept donné
        
        Exemple:
            get_implications('BAV 1er degré') → ['PR allongé', 'PR > 200ms']
        
        Args:
            concept: Le concept source (normalisé ou non)
        
        Returns:
            Liste des concepts impliqués (vide si aucune implication)
        """
        concept_normalized = self._normalize_text(concept)
        
        # Chercher dans l'ontologie
        concept_data = self._find_concept_data(concept_normalized)
        
        if not concept_data:
            logger.debug(f"⚠️ Concept not found in ontology: '{concept}'")
            return []
        
        # Extraire les implications
        implications = concept_data.get('implications', [])
        
        if implications:
            logger.info(f"🎯 Found {len(implications)} implications for '{concept}'")
        
        return implications
    
    def get_synonyms(self, concept: str) -> List[str]:
        """
        Retourne les synonymes d'un concept
        
        Args:
            concept: Le concept source
        
        Returns:
            Liste des synonymes
        """
        concept_normalized = self._normalize_text(concept)
        concept_data = self._find_concept_data(concept_normalized)
        
        if not concept_data:
            return []
        
        return concept_data.get('synonymes', concept_data.get('synonyms', []))
    
    def get_parents(self, concept: str) -> List[str]:
        """
        Retourne les concepts parents (hiérarchie is_a)
        
        Args:
            concept: Le concept source
        
        Returns:
            Liste des concepts parents
        """
        concept_normalized = self._normalize_text(concept)
        concept_data = self._find_concept_data(concept_normalized)
        
        if not concept_data:
            return []
        
        # Chercher relations "is_a" ou "parent"
        parents = concept_data.get('is_a', concept_data.get('parent', []))
        
        return parents if isinstance(parents, list) else [parents]
    
    def get_territories(self, concept: str) -> List[str]:
        """
        Retourne les territoires anatomiques associés
        
        Args:
            concept: Le concept source
        
        Returns:
            Liste des territoires possibles
        """
        concept_normalized = self._normalize_text(concept)
        concept_data = self._find_concept_data(concept_normalized)
        
        if not concept_data:
            return []
        
        return concept_data.get('territoires_possibles', [])
    
    def get_weight(self, concept: str) -> int:
        """
        Retourne le poids (importance) d'un concept
        
        Args:
            concept: Le concept source
        
        Returns:
            Poids (1-5, défaut: 1)
        """
        concept_normalized = self._normalize_text(concept)
        concept_data = self._find_concept_data(concept_normalized)
        
        if not concept_data:
            return 1  # Poids par défaut
        
        return concept_data.get('poids', concept_data.get('hasWeight', 1))
    
    def get_category(self, concept: str) -> str:
        """
        Retourne la catégorie d'un concept
        
        Args:
            concept: Le concept source
        
        Returns:
            Catégorie (ex: 'DIAGNOSTIC', 'DESCRIPTEUR_ECG')
        """
        concept_normalized = self._normalize_text(concept)
        concept_data = self._find_concept_data(concept_normalized)
        
        if not concept_data:
            return 'UNKNOWN'
        
        return concept_data.get('categorie', concept_data.get('category', 'UNKNOWN'))
    
    def concept_implies(self, source_concept: str, target_concept: str) -> bool:
        """
        Vérifie si source_concept implique target_concept
        
        Exemple:
            concept_implies('BAV 1er degré', 'PR allongé') → True
        
        Args:
            source_concept: Le concept source
            target_concept: Le concept cible à vérifier
        
        Returns:
            True si source implique target
        """
        implications = self.get_implications(source_concept)
        target_normalized = self._normalize_text(target_concept)
        
        # Vérifier si target est dans les implications (normalisé)
        for impl in implications:
            if self._normalize_text(impl) == target_normalized:
                return True
        
        return False
    
    def _find_concept_data(self, concept_normalized: str) -> Optional[Dict]:
        """
        Trouve les données d'un concept dans l'ontologie
        
        Cherche par:
        1. concept_name exact (normalisé)
        2. Synonymes
        3. Match partiel
        
        Args:
            concept_normalized: Concept normalisé (lowercase, sans accents)
        
        Returns:
            Dictionnaire de données du concept ou None
        """
        # 1. Recherche exacte par concept_name
        for concept_id, data in self.concept_mappings.items():
            if not isinstance(data, dict):
                continue
            
            concept_name = data.get('concept_name', '')
            if self._normalize_text(concept_name) == concept_normalized:
                return data
        
        # 2. Recherche par synonymes
        for concept_id, data in self.concept_mappings.items():
            if not isinstance(data, dict):
                continue
            
            synonyms = data.get('synonymes', data.get('synonyms', []))
            for syn in synonyms:
                if self._normalize_text(syn) == concept_normalized:
                    return data
        
        # 3. Match partiel (contient)
        for concept_id, data in self.concept_mappings.items():
            if not isinstance(data, dict):
                continue
            
            concept_name = data.get('concept_name', '')
            concept_name_norm = self._normalize_text(concept_name)
            
            # Si l'un contient l'autre
            if concept_normalized in concept_name_norm or concept_name_norm in concept_normalized:
                return data
        
        return None
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalise un texte pour la comparaison
        
        Args:
            text: Texte à normaliser
        
        Returns:
            Texte normalisé (lowercase, stripped)
        """
        if not text:
            return ''
        
        # Normalisation basique (pas d'unidecode pour éviter dépendance)
        return text.lower().strip()
    
    def get_all_concepts(self) -> List[str]:
        """
        Retourne la liste de tous les concepts disponibles
        
        Returns:
            Liste des noms de concepts
        """
        concepts = []
        for data in self.concept_mappings.values():
            if isinstance(data, dict):
                concept_name = data.get('concept_name')
                if concept_name:
                    concepts.append(concept_name)
        
        return concepts
    
    def get_stats(self) -> Dict:
        """
        Retourne des statistiques sur l'ontologie
        
        Returns:
            Dictionnaire avec statistiques
        """
        total_concepts = len(self.concept_mappings)
        concepts_with_implications = 0
        total_implications = 0
        
        for data in self.concept_mappings.values():
            if isinstance(data, dict):
                implications = data.get('implications', [])
                if implications:
                    concepts_with_implications += 1
                    total_implications += len(implications)
        
        return {
            'total_concepts': total_concepts,
            'concepts_with_implications': concepts_with_implications,
            'total_implications': total_implications,
            'avg_implications_per_concept': round(total_implications / max(concepts_with_implications, 1), 2)
        }


# Instance singleton pour réutilisation
_resolver_instance = None

def get_resolver(ontology_path: Optional[str] = None) -> OntologyRelationResolver:
    """
    Retourne une instance singleton du resolver
    
    Args:
        ontology_path: Chemin optionnel vers l'ontologie
    
    Returns:
        Instance du resolver
    """
    global _resolver_instance
    
    if _resolver_instance is None:
        _resolver_instance = OntologyRelationResolver(ontology_path)
    
    return _resolver_instance


# Helper functions pour compatibilité avec ancien code
def get_implications(concept: str) -> List[str]:
    """Helper function - retourne implications d'un concept"""
    resolver = get_resolver()
    return resolver.get_implications(concept)


def concept_implies(source: str, target: str) -> bool:
    """Helper function - vérifie si source implique target"""
    resolver = get_resolver()
    return resolver.concept_implies(source, target)
