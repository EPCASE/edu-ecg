"""
Module de correction basé sur l'ontologie ECG
Fournit des fonctionnalités de correction intelligente pour les annotations ECG
"""

import json
from pathlib import Path
from typing import List, Dict, Set, Tuple
import difflib

class OntologyCorrector:
    """Moteur de correction basé sur l'ontologie ECG"""
    
    def __init__(self, ontology_path: str = None):
        """
        Initialise le correcteur avec l'ontologie
        
        Args:
            ontology_path: Chemin vers le fichier d'ontologie (JSON ou OWL)
        """
        self.concepts = {}
        self.synonyms = {}
        self.hierarchy = {}
        
        # Charger l'ontologie si un chemin est fourni
        if ontology_path and Path(ontology_path).exists():
            self.load_ontology(ontology_path)
        else:
            # Charger une ontologie de base si aucun fichier n'est fourni
            self.load_default_ontology()
    
    def load_default_ontology(self):
        """Charge une ontologie ECG de base avec les concepts principaux"""
        self.concepts = {
            # Rythmes
            "Rythme sinusal": {"category": "rythme", "severity": "normal"},
            "Fibrillation auriculaire": {"category": "rythme", "severity": "pathologique"},
            "Flutter auriculaire": {"category": "rythme", "severity": "pathologique"},
            "Tachycardie sinusale": {"category": "rythme", "severity": "anormal"},
            "Bradycardie sinusale": {"category": "rythme", "severity": "anormal"},
            
            # Conduction
            "BAV 1er degré": {"category": "conduction", "severity": "anormal"},
            "BAV 2ème degré": {"category": "conduction", "severity": "pathologique"},
            "BAV 3ème degré": {"category": "conduction", "severity": "pathologique"},
            "Bloc de branche droit": {"category": "conduction", "severity": "anormal"},
            "Bloc de branche gauche": {"category": "conduction", "severity": "anormal"},
            
            # Ischémie
            "Sus-décalage ST": {"category": "ischemie", "severity": "urgent"},
            "Sous-décalage ST": {"category": "ischemie", "severity": "pathologique"},
            "Onde T négative": {"category": "ischemie", "severity": "anormal"},
            "Onde Q pathologique": {"category": "ischemie", "severity": "pathologique"},
            
            # Hypertrophie
            "HVG": {"category": "hypertrophie", "severity": "anormal"},
            "HVD": {"category": "hypertrophie", "severity": "anormal"},
            "HAG": {"category": "hypertrophie", "severity": "anormal"},
            "HAD": {"category": "hypertrophie", "severity": "anormal"},
            
            # Autres
            "Extrasystole ventriculaire": {"category": "arythmie", "severity": "anormal"},
            "Extrasystole auriculaire": {"category": "arythmie", "severity": "anormal"},
            "QT long": {"category": "autre", "severity": "pathologique"},
            "QT court": {"category": "autre", "severity": "pathologique"},
        }
        
        # Synonymes courants
        self.synonyms = {
            "FA": "Fibrillation auriculaire",
            "ACFA": "Fibrillation auriculaire",
            "ESV": "Extrasystole ventriculaire",
            "ESA": "Extrasystole auriculaire",
            "BBD": "Bloc de branche droit",
            "BBG": "Bloc de branche gauche",
            "RS": "Rythme sinusal",
            "STEMI": "Sus-décalage ST",
            "NSTEMI": "Sous-décalage ST",
        }
    
    def load_ontology(self, ontology_path: str):
        """
        Charge l'ontologie depuis un fichier
        
        Args:
            ontology_path: Chemin vers le fichier d'ontologie
        """
        try:
            if ontology_path.endswith('.json'):
                with open(ontology_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.concepts = data.get('concepts', {})
                    self.synonyms = data.get('synonyms', {})
                    self.hierarchy = data.get('hierarchy', {})
            else:
                # Pour les fichiers OWL, utiliser owlready2 si disponible
                try:
                    import owlready2
                    # Code pour charger OWL...
                    pass
                except ImportError:
                    # Fallback vers l'ontologie par défaut
                    self.load_default_ontology()
        except Exception as e:
            print(f"Erreur lors du chargement de l'ontologie : {e}")
            self.load_default_ontology()
    
    def normalize_concept(self, concept: str) -> str:
        """
        Normalise un concept en utilisant les synonymes
        
        Args:
            concept: Le concept à normaliser
            
        Returns:
            Le concept normalisé
        """
        concept = concept.strip()
        
        # Vérifier les synonymes
        if concept in self.synonyms:
            return self.synonyms[concept]
        
        # Vérifier les synonymes en ignorant la casse
        for syn, normalized in self.synonyms.items():
            if concept.lower() == syn.lower():
                return normalized
        
        return concept
    
    def find_similar_concepts(self, concept: str, threshold: float = 0.7) -> List[str]:
        """
        Trouve des concepts similaires basés sur la similarité de chaîne
        
        Args:
            concept: Le concept à rechercher
            threshold: Seuil de similarité (0-1)
            
        Returns:
            Liste des concepts similaires
        """
        concept_lower = concept.lower()
        similar = []
        
        for known_concept in self.concepts.keys():
            # Similarité basique
            ratio = difflib.SequenceMatcher(None, concept_lower, known_concept.lower()).ratio()
            if ratio >= threshold:
                similar.append((known_concept, ratio))
        
        # Trier par similarité décroissante
        similar.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in similar]
    
    def correct_annotations(self, student_annotations: List[str], expert_annotations: List[str]) -> Dict:
        """
        Corrige les annotations étudiantes par rapport aux annotations expertes
        
        Args:
            student_annotations: Liste des annotations de l'étudiant
            expert_annotations: Liste des annotations de l'expert
            
        Returns:
            Dictionnaire avec le score et les détails de correction
        """
        # Normaliser les annotations
        student_normalized = {self.normalize_concept(ann) for ann in student_annotations}
        expert_normalized = {self.normalize_concept(ann) for ann in expert_annotations}
        
        # Calculer les intersections
        correct = student_normalized.intersection(expert_normalized)
        missing = expert_normalized - student_normalized
        extra = student_normalized - expert_normalized
        
        # Calculer le score
        if expert_normalized:
            precision = len(correct) / len(student_normalized) if student_normalized else 0
            recall = len(correct) / len(expert_normalized)
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        else:
            f1_score = 1.0 if not student_normalized else 0.0
        
        # Suggestions pour les concepts manqués
        suggestions = {}
        for missed in missing:
            # Chercher si l'étudiant a mis quelque chose de similaire
            for student_concept in extra:
                similar = self.find_similar_concepts(student_concept, 0.6)
                if missed in similar:
                    suggestions[student_concept] = missed
        
        return {
            'score': f1_score * 100,
            'correct': list(correct),
            'missing': list(missing),
            'extra': list(extra),
            'suggestions': suggestions,
            'precision': precision if expert_normalized else 1.0,
            'recall': recall if expert_normalized else 1.0
        }
    
    def get_concept_info(self, concept: str) -> Dict:
        """
        Retourne les informations sur un concept
        
        Args:
            concept: Le concept à rechercher
            
        Returns:
            Dictionnaire avec les informations du concept
        """
        normalized = self.normalize_concept(concept)
        return self.concepts.get(normalized, {})
    
    def get_all_concepts(self) -> List[str]:
        """Retourne tous les concepts de l'ontologie"""
        return list(self.concepts.keys())
    
    def get_concepts_by_category(self, category: str) -> List[str]:
        """
        Retourne tous les concepts d'une catégorie donnée
        
        Args:
            category: La catégorie à filtrer
            
        Returns:
            Liste des concepts de la catégorie
        """
        return [
            concept for concept, info in self.concepts.items()
            if info.get('category') == category
        ]
    
    def get_concepts_by_severity(self, severity: str) -> List[str]:
        """
        Retourne tous les concepts d'une sévérité donnée
        
        Args:
            severity: La sévérité à filtrer (normal, anormal, pathologique, urgent)
            
        Returns:
            Liste des concepts de la sévérité
        """
        return [
            concept for concept, info in self.concepts.items()
            if info.get('severity') == severity
        ]
