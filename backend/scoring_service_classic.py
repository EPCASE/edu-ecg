"""
🏛️ Service de Scoring Classique (NLP + Ontologie OWL)
Approche Winston : NER → Normalisation → Raisonnement OWL

Pipeline:
1. Extraction concepts (regex patterns ECG)
2. Normalisation (lowercase, synonymes)
3. Matching avec ontologie (owlready2)
4. Scoring basé sur relations hiérarchiques

Avantages:
- Gratuit (pas d'API)
- Rapide (<100ms)
- Déterministe
- Offline

Auteur: Edu-ECG Team
Date: 2026-01-10
Version: 1.0 (Architect Approach)
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)

# Try to import owlready2 for ontology reasoning
try:
    from owlready2 import get_ontology, sync_reasoner_pellet
    OWLREADY2_AVAILABLE = True
except ImportError:
    OWLREADY2_AVAILABLE = False
    logger.warning("⚠️ owlready2 not installed. Install with: pip install owlready2")


class MatchType(Enum):
    """Types de correspondance entre concepts"""
    EXACT = "exact"
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    MISSING = "missing"
    EXTRA = "extra"


@dataclass
class ConceptMatch:
    """Résultat de correspondance d'un concept"""
    student_concept: Optional[str]
    expected_concept: Optional[str]
    match_type: MatchType
    score: float
    explanation: str
    category: str


@dataclass
class ScoringResult:
    """Résultat complet du scoring"""
    total_score: float
    max_score: float
    percentage: float
    matches: List[ConceptMatch]
    exact_matches: int
    partial_matches: int
    missing_concepts: int
    extra_concepts: int
    contradictions: int
    category_scores: Dict[str, float]


class ClassicNLPScorer:
    """
    Scoring avec NLP classique + ontologie OWL
    
    Méthode:
    1. Extraction NER par regex patterns médicaux
    2. Normalisation avec dictionnaire synonymes
    3. Matching ontologie (si disponible)
    4. Fallback: similarité textuelle Jaccard
    """
    
    # Dictionnaire de synonymes médicaux ECG
    SYNONYMS = {
        # Fréquence
        'fréquence normale': 'fréquence cardiaque normale',
        'fc normale': 'fréquence cardiaque normale',
        'frequence normale': 'fréquence cardiaque normale',
        'fc normal': 'fréquence cardiaque normale',
        
        # QRS
        'qrs fins': 'qrs normal',
        'qrs fin': 'qrs normal',
        'qrs étroit': 'qrs normal',
        'qrs etroit': 'qrs normal',
        'qrs étroits': 'qrs normal',
        'qrs normaux': 'qrs normal',
        
        # PR
        'pr normal': 'intervalle pr normal',
        'pr normaux': 'intervalle pr normal',
        'espace pr normal': 'intervalle pr normal',
        
        # Axe
        'axe normal': 'axe cardiaque normal',
        'axe électrique normal': 'axe cardiaque normal',
        
        # Repolarisation
        "pas d'anomalie de repolarisation": 'repolarisation normale',
        "pas d anomalie de repolarisation": 'repolarisation normale',
        'repolarisation normale': 'repolarisation normale',
        'pas de trouble de repolarisation': 'repolarisation normale',
    }
    
    # Patterns regex pour extraction NER
    ECG_PATTERNS = {
        'rhythm': [
            r'rythme\s+(?:sinusal|auriculaire|ventriculaire)',
            r'fibrillation\s+(?:auriculaire|ventriculaire)',
            r'flutter\s+auriculaire',
            r'tachycardie(?:\s+sinusale)?',
            r'bradycardie(?:\s+sinusale)?',
        ],
        'conduction': [
            r'BAV\s*[123](?:er)?(?:\s+degré)?',
            r'bloc\s+(?:auriculo-ventriculaire|atrio-ventriculaire)',
            r'bloc\s+de\s+branche\s+(?:droit|gauche|complet)',
            r'BBD|BBG|BBDC|BBGC',
        ],
        'morphology': [
            r'QRS\s+(?:large|fin|normal|étroit|elargi)',
            r'onde\s+[PTU](?:\s+(?:ample|plate|negative|inversée))?',
            r'onde\s+Q\s+de\s+nécrose',
        ],
        'measurement': [
            r'PR\s+(?:allongé|court|normal)',
            r'QT\s+(?:allongé|court|normal)',
            r'(?:fréquence|fc)\s+(?:normale|cardiaque\s+normale)',
            r'axe\s+(?:normal|dévié|gauche|droit)',
        ],
        'pathology': [
            r'STEMI',
            r'infarctus',
            r'ischémie',
            r'hypertrophie\s+(?:ventriculaire|auriculaire)',
        ]
    }
    
    def __init__(self, ontology_path: Optional[str] = None):
        """
        Args:
            ontology_path: Chemin vers fichier ontologie.owx (optionnel)
        """
        self.ontology = None
        self.category_weights = {
            'rhythm': 1.2,
            'conduction': 1.1,
            'pathology': 1.0,
            'morphology': 0.9,
            'measurement': 0.8
        }
        
        # Charger ontologie si disponible
        if ontology_path and OWLREADY2_AVAILABLE:
            try:
                self.ontology = get_ontology(f"file://{ontology_path}").load()
                logger.info(f"✅ Ontologie chargée: {len(list(self.ontology.classes()))} classes")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de charger ontologie: {e}")
    
    def extract_concepts(self, text: str) -> List[Dict]:
        """
        Extraction NER par patterns regex
        
        Args:
            text: Texte libre de l'étudiant
            
        Returns:
            Liste de concepts avec catégorie
        """
        concepts = []
        text_lower = text.lower()
        
        for category, patterns in self.ECG_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    concept_text = match.group(0)
                    
                    # Normaliser avec synonymes
                    normalized = self.SYNONYMS.get(concept_text, concept_text)
                    
                    concepts.append({
                        'text': normalized,
                        'original_text': concept_text,
                        'category': category,
                        'confidence': 0.9  # Regex = haute confiance
                    })
        
        # Dédupliquer
        seen = set()
        unique_concepts = []
        for c in concepts:
            key = (c['text'], c['category'])
            if key not in seen:
                seen.add(key)
                unique_concepts.append(c)
        
        logger.info(f"📝 Extracted {len(unique_concepts)} concepts via NER patterns")
        return unique_concepts
    
    def score(
        self,
        student_concepts: List[Dict],
        expected_concepts: List[Dict]
    ) -> ScoringResult:
        """Score la réponse avec NLP classique"""
        
        matches = []
        matched_expected = set()
        
        # Normaliser
        student_normalized = self._normalize_concepts(student_concepts)
        expected_normalized = self._normalize_concepts(expected_concepts)
        
        # 1. Matcher chaque concept étudiant
        for student_concept in student_normalized:
            match = self._find_best_match(
                student_concept,
                expected_normalized,
                matched_expected
            )
            matches.append(match)
            
            if match.expected_concept and match.score > 50:
                matched_expected.add(match.expected_concept)
        
        # 2. Concepts manquants
        for expected_concept in expected_normalized:
            if expected_concept['text'] not in matched_expected:
                matches.append(ConceptMatch(
                    student_concept=None,
                    expected_concept=expected_concept['text'],
                    match_type=MatchType.MISSING,
                    score=0.0,
                    explanation=f"Concept manquant: {expected_concept['text']}",
                    category=expected_concept['category']
                ))
        
        # 3. Calculer score total
        return self._calculate_total_score(matches, len(expected_normalized))
    
    def _normalize_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """Normalise avec synonymes"""
        normalized = []
        for c in concepts:
            text = c['text'].lower().strip()
            text_normalized = self.SYNONYMS.get(text, text)
            
            normalized.append({
                'text': text_normalized,
                'original_text': c.get('original_text', text),
                'category': c.get('category', 'unknown'),
                'confidence': c.get('confidence', 1.0)
            })
        return normalized
    
    def _find_best_match(
        self,
        student_concept: Dict,
        expected_concepts: List[Dict],
        already_matched: Set[str]
    ) -> ConceptMatch:
        """Trouve meilleure correspondance"""
        
        best_match = None
        best_score = -100
        
        for expected in expected_concepts:
            if expected['text'] in already_matched:
                continue
            
            match = self._compare_concepts(student_concept, expected)
            
            if match.score > best_score:
                best_score = match.score
                best_match = match
        
        if best_match is None or best_score < 30:
            return ConceptMatch(
                student_concept=student_concept['text'],
                expected_concept=None,
                match_type=MatchType.EXTRA,
                score=0.0,
                explanation="Concept non attendu",
                category=student_concept['category']
            )
        
        return best_match
    
    def _compare_concepts(
        self,
        student_concept: Dict,
        expected_concept: Dict
    ) -> ConceptMatch:
        """Compare deux concepts"""
        
        student_text = student_concept['text']
        expected_text = expected_concept['text']
        category = expected_concept['category']
        
        # 1. Exact match
        if student_text == expected_text:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.EXACT,
                score=100.0,
                explanation="✅ Parfait ! (NLP)",
                category=category
            )
        
        # 2. Ontologie si disponible
        if self.ontology:
            onto_match = self._ontology_match(student_text, expected_text, category)
            if onto_match:
                return onto_match
        
        # 3. Similarité textuelle
        similarity = self._jaccard_similarity(student_text, expected_text)
        
        if similarity > 0.8:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.EXACT,
                score=95.0,
                explanation="✅ Très proche (NLP)",
                category=category
            )
        elif similarity > 0.6:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.SIBLING,
                score=50.0,
                explanation="⚠️ Similaire (NLP)",
                category=category
            )
        else:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.MISSING,
                score=0.0,
                explanation="❌ Différent (NLP)",
                category=category
            )
    
    def _ontology_match(
        self,
        student_text: str,
        expected_text: str,
        category: str
    ) -> Optional[ConceptMatch]:
        """Matching avec ontologie OWL (si disponible)"""
        # TODO: Implémenter recherche dans ontologie
        # Nécessite mapping texte → URI OWL
        return None
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Similarité Jaccard sur mots"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _calculate_total_score(
        self,
        matches: List[ConceptMatch],
        num_expected: int
    ) -> ScoringResult:
        """Calcule score total"""
        
        total_score = sum(m.score for m in matches if m.expected_concept)
        max_score = num_expected * 100.0
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        exact = sum(1 for m in matches if m.match_type == MatchType.EXACT)
        partial = sum(1 for m in matches if m.match_type in [MatchType.CHILD, MatchType.PARENT, MatchType.SIBLING])
        missing = sum(1 for m in matches if m.match_type == MatchType.MISSING)
        extra = sum(1 for m in matches if m.match_type == MatchType.EXTRA)
        
        category_scores = {}
        for cat in ['rhythm', 'conduction', 'morphology', 'measurement', 'pathology']:
            cat_matches = [m for m in matches if m.category == cat and m.expected_concept]
            if cat_matches:
                category_scores[cat] = sum(m.score for m in cat_matches) / len(cat_matches)
        
        return ScoringResult(
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            matches=matches,
            exact_matches=exact,
            partial_matches=partial,
            missing_concepts=missing,
            extra_concepts=extra,
            contradictions=0,
            category_scores=category_scores
        )


# Fonction helper pour comparaison
def compare_scorers(text: str, expected: List[Dict]):
    """Compare résultats NLP classique vs LLM"""
    
    # Scorer classique
    classic_scorer = ClassicNLPScorer()
    classic_concepts = classic_scorer.extract_concepts(text)
    classic_result = classic_scorer.score(classic_concepts, expected)
    
    print("\n🏛️ CLASSIC NLP APPROACH:")
    print(f"Score: {classic_result.percentage:.1f}%")
    print(f"Concepts extraits: {len(classic_concepts)}")
    print(f"Matches exacts: {classic_result.exact_matches}")
    
    return {
        'score': classic_result.percentage,
        'concepts': len(classic_concepts),
        'method': 'Classic NLP'
    }
