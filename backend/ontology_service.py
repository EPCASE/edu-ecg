"""
🎯 Service d'Ontologie ECG
Charge et interroge l'ontologie pour enrichir le matching sémantique

Fonctionnalités:
- Charger l'ontologie OWL
- Trouver synonymes (rdfs:label)
- Trouver relations (subClassOf, requiresFinding, etc.)
- Vérifier implications médicales (BAV1 → PR allongé)
"""

import logging
from typing import List, Dict, Optional, Set
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal
from pathlib import Path

logger = logging.getLogger(__name__)

# Namespaces
WEBPROTEGE = Namespace("http://webprotege.stanford.edu/")


class OntologyService:
    """Service pour interroger l'ontologie ECG"""
    
    def __init__(self, ontology_path: str = "data/ontologie.owx"):
        self.graph = Graph()
        self.ontology_path = ontology_path
        self._load_ontology()
        self._build_indexes()
    
    def _load_ontology(self):
        """Charge l'ontologie OWL"""
        try:
            logger.info(f"📚 Chargement ontologie: {self.ontology_path}")
            self.graph.parse(self.ontology_path, format="xml")
            logger.info(f"✅ Ontologie chargée: {len(self.graph)} triples")
        except Exception as e:
            logger.error(f"❌ Erreur chargement ontologie: {e}")
            raise
    
    def _build_indexes(self):
        """Construit des index pour accès rapide"""
        # Index: label → URI
        self.label_to_uri: Dict[str, URIRef] = {}
        
        # Index: URI → labels (fr + en + synonymes)
        self.uri_to_labels: Dict[URIRef, Set[str]] = {}
        
        # Parcourir tous les labels
        for subject, predicate, obj in self.graph.triples((None, RDFS.label, None)):
            if isinstance(obj, Literal):
                label = str(obj).lower().strip()
                
                # Label → URI
                self.label_to_uri[label] = subject
                
                # URI → Labels
                if subject not in self.uri_to_labels:
                    self.uri_to_labels[subject] = set()
                self.uri_to_labels[subject].add(label)
        
        logger.info(f"📇 Index créé: {len(self.label_to_uri)} labels uniques")
    
    def find_concept_uri(self, concept_text: str) -> Optional[URIRef]:
        """
        Trouve l'URI d'un concept par son label
        
        Args:
            concept_text: Texte du concept (ex: "BAV 1er degré")
        
        Returns:
            URI du concept dans l'ontologie, ou None
        """
        normalized = concept_text.lower().strip()
        
        # Essai direct
        if normalized in self.label_to_uri:
            return self.label_to_uri[normalized]
        
        # Variations courantes
        variations = [
            normalized.replace("1er", "1"),
            normalized.replace("1er degré", "1"),
            normalized.replace("degré", "").strip(),
            normalized.replace(" ", ""),
        ]
        
        for variant in variations:
            if variant in self.label_to_uri:
                return self.label_to_uri[variant]
        
        return None
    
    def get_synonyms(self, concept_text: str) -> List[str]:
        """
        Récupère tous les synonymes d'un concept
        
        Args:
            concept_text: Texte du concept
        
        Returns:
            Liste de synonymes (labels fr + en)
        """
        uri = self.find_concept_uri(concept_text)
        if not uri:
            return []
        
        return list(self.uri_to_labels.get(uri, set()))
    
    def are_synonyms(self, concept1: str, concept2: str) -> bool:
        """
        Vérifie si deux concepts sont synonymes (même URI)
        
        Example:
            are_synonyms("BAV 1", "BAV de type 1") → True
        """
        uri1 = self.find_concept_uri(concept1)
        uri2 = self.find_concept_uri(concept2)
        
        return uri1 is not None and uri1 == uri2
    
    def get_parent_concepts(self, concept_text: str) -> List[str]:
        """
        Récupère les concepts parents (via rdfs:subClassOf)
        
        Example:
            get_parent_concepts("BAV 1") → ["BAV", "Trouble de conduction"]
        """
        uri = self.find_concept_uri(concept_text)
        if not uri:
            return []
        
        parents = []
        for parent_uri in self.graph.objects(uri, RDFS.subClassOf):
            if parent_uri in self.uri_to_labels:
                # Prendre le premier label français
                labels = list(self.uri_to_labels[parent_uri])
                if labels:
                    parents.append(labels[0])
        
        return parents
    
    def get_related_findings(self, concept_text: str) -> Dict[str, List[str]]:
        """
        Récupère les findings liés via propriétés objet
        
        Returns:
            Dict avec relations: {'requiresFinding': [...], 'localize': [...]}
        """
        uri = self.find_concept_uri(concept_text)
        if not uri:
            return {}
        
        findings = {}
        
        # Parcourir toutes les propriétés objet
        for predicate, obj in self.graph.predicate_objects(uri):
            # Ignorer les propriétés RDF/RDFS standards
            if predicate in [RDF.type, RDFS.label, RDFS.subClassOf]:
                continue
            
            # Si c'est une URI (relation vers autre concept)
            if isinstance(obj, URIRef) and obj in self.uri_to_labels:
                # Nom de la propriété
                prop_labels = list(self.graph.objects(predicate, RDFS.label))
                prop_name = str(prop_labels[0]) if prop_labels else str(predicate).split('/')[-1]
                
                # Labels du concept cible
                target_labels = list(self.uri_to_labels[obj])
                if target_labels:
                    if prop_name not in findings:
                        findings[prop_name] = []
                    findings[prop_name].append(target_labels[0])
        
        return findings
    
    def implies_finding(self, diagnostic: str, finding: str) -> bool:
        """
        Vérifie si un diagnostic implique un finding
        
        Example:
            implies_finding("BAV 1", "PR allongé") → True
            implies_finding("BBG complet", "QRS larges") → True
        
        Logique:
        1. Vérifier relation directe dans ontologie
        2. Vérifier règles médicales connues (fallback)
        """
        # 1. Vérifier relations ontologie
        relations = self.get_related_findings(diagnostic)
        
        for relation_type, related_concepts in relations.items():
            for concept in related_concepts:
                if self.are_synonyms(concept, finding):
                    logger.info(f"✅ Ontologie: '{diagnostic}' {relation_type} '{finding}'")
                    return True
        
        # 2. Règles médicales hardcodées (fallback)
        diagnostic_lower = diagnostic.lower()
        finding_lower = finding.lower()
        
        medical_rules = {
            # BAV
            ('bav 1', 'pr allongé'),
            ('bav 1er degré', 'pr allongé'),
            ('bav de type 1', 'pr allongé'),
            
            # Blocs de branche
            ('bloc de branche gauche', 'qrs larges'),
            ('bbg', 'qrs larges'),
            ('bbg complet', 'qrs larges'),
            ('bloc de branche droit', 'qrs larges'),
            ('bbd', 'qrs larges'),
            ('bbd complet', 'qrs larges'),
            
            # FA
            ('fibrillation auriculaire', 'absence onde p'),
            ('fa', 'absence onde p'),
            ('fibrillation auriculaire', 'rythme irrégulier'),
            
            # Tachycardies/bradycardies
            ('tachycardie', 'fréquence élevée'),
            ('bradycardie', 'fréquence basse'),
        }
        
        for diag_rule, finding_rule in medical_rules:
            if diag_rule in diagnostic_lower and finding_rule in finding_lower:
                logger.info(f"✅ Règle médicale: '{diagnostic}' implique '{finding}'")
                return True
        
        return False
    
    def get_concept_hierarchy(self, concept_text: str) -> Dict:
        """
        Récupère la hiérarchie complète d'un concept
        
        Returns:
            {
                'uri': '...',
                'labels': [...],
                'parents': [...],
                'children': [...],
                'findings': {...}
            }
        """
        uri = self.find_concept_uri(concept_text)
        if not uri:
            return {}
        
        return {
            'uri': str(uri),
            'labels': list(self.uri_to_labels.get(uri, set())),
            'parents': self.get_parent_concepts(concept_text),
            'findings': self.get_related_findings(concept_text)
        }


# Instance globale (singleton)
_ontology_service: Optional[OntologyService] = None


def get_ontology_service() -> OntologyService:
    """Récupère l'instance singleton du service d'ontologie"""
    global _ontology_service
    if _ontology_service is None:
        _ontology_service = OntologyService()
    return _ontology_service


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    service = OntologyService()
    
    # Test 1: Synonymes
    print("\n🔍 Test 1: Synonymes de 'BAV 1'")
    synonyms = service.get_synonyms("BAV 1")
    print(f"Synonymes: {synonyms}")
    
    # Test 2: BAV1 vs BAV de type 1
    print("\n🔍 Test 2: 'BAV 1' == 'BAV de type 1' ?")
    are_same = service.are_synonyms("BAV 1", "BAV de type 1")
    print(f"Résultat: {are_same}")
    
    # Test 3: Parents
    print("\n🔍 Test 3: Parents de 'BAV 1'")
    parents = service.get_parent_concepts("BAV 1")
    print(f"Parents: {parents}")
    
    # Test 4: Relations
    print("\n🔍 Test 4: Relations de 'BAV 1'")
    findings = service.get_related_findings("BAV 1")
    print(f"Relations: {findings}")
    
    # Test 5: Implications
    print("\n🔍 Test 5: 'BAV 1' implique 'PR allongé' ?")
    implies = service.implies_finding("BAV 1", "PR allongé")
    print(f"Résultat: {implies}")
    
    # Test 6: Hiérarchie complète
    print("\n🔍 Test 6: Hiérarchie de 'BAV 1'")
    hierarchy = service.get_concept_hierarchy("BAV 1")
    print(f"Hiérarchie: {hierarchy}")
