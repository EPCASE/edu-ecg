"""
🎯 Service de Scoring Sémantique avec LLM
Compare réponse étudiant vs concepts attendus avec GPT-4o pour matching sémantique

Auteur: Edu-ECG Team
Date: 2026-01-10
Version: 2.0 (LLM-powered)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import os
import logging
import json
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client for semantic matching
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class MatchType(Enum):
    """Types de correspondance entre concepts"""
    EXACT = "exact"              # Correspondance parfaite
    PARENT = "parent"            # Étudiant trop général
    CHILD = "child"              # Étudiant trop spécifique
    SIBLING = "sibling"          # Concepts frères
    CONTRADICTION = "contradiction"  # Concepts contradictoires
    MISSING = "missing"          # Concept attendu manquant
    EXTRA = "extra"              # Concept non attendu


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


class SemanticScorer:
    """
    Scoring sémantique avec GPT-4o
    
    Utilise un LLM pour comprendre les équivalences sémantiques:
    - "QRS fins" = "QRS normal"
    - "fréquence normale" = "fréquence cardiaque normale"
    - "pas d'anomalie de repolarisation" = "repolarisation normale"
    """
    
    def __init__(self):
        self.category_weights = {
            'rhythm': 1.2,
            'conduction': 1.1,
            'pathology': 1.0,
            'morphology': 0.9,
            'measurement': 0.8
        }
    
    def score(
        self,
        student_concepts: List[Dict],
        expected_concepts: List[Dict]
    ) -> ScoringResult:
        """Score la réponse de l'étudiant avec matching sémantique LLM"""
        
        student_normalized = self._normalize_concepts(student_concepts)
        expected_normalized = self._normalize_concepts(expected_concepts)
        
        matches = []
        matched_expected = set()
        
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
        """Normalise les concepts (lowercase, trim)"""
        return [{
            'text': c['text'].lower().strip(),
            'original_text': c['text'],
            'category': c.get('category', 'unknown'),
            'confidence': c.get('confidence', 1.0)
        } for c in concepts]
    
    def _find_best_match(
        self,
        student_concept: Dict,
        expected_concepts: List[Dict],
        already_matched: set
    ) -> ConceptMatch:
        """Trouve la meilleure correspondance pour un concept étudiant"""
        
        best_match = None
        best_score = -100
        
        for expected in expected_concepts:
            if expected['text'] in already_matched:
                continue
            
            match = self._compare_concepts_llm(student_concept, expected)
            
            if match.score > best_score:
                best_score = match.score
                best_match = match
        
        # Si aucun match, c'est un concept extra
        if best_match is None or best_score < 30:
            return ConceptMatch(
                student_concept=student_concept['text'],
                expected_concept=None,
                match_type=MatchType.EXTRA,
                score=0.0,
                explanation="Concept non attendu (peut être correct)",
                category=student_concept['category']
            )
        
        return best_match
    
    def _compare_concepts_llm(
        self,
        student_concept: Dict,
        expected_concept: Dict
    ) -> ConceptMatch:
        """
        Compare deux concepts avec GPT-4o pour matching sémantique
        
        Le LLM comprend:
        - Synonymes médicaux
        - Relations hiérarchiques
        - Variations d'expression
        """
        student_text = student_concept['text']
        expected_text = expected_concept['text']
        category = expected_concept['category']
        
        # 1. Exact match textuel (rapide)
        if student_text == expected_text:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.EXACT,
                score=100.0,
                explanation="✅ Parfait ! Concept exact",
                category=category
            )
        
        # 2. Matching sémantique avec GPT-4o
        try:
            prompt = f"""Tu es un expert cardiologue. Compare ces deux concepts ECG:

Concept étudiant: "{student_text}"
Concept attendu: "{expected_text}"

Détermine leur relation sémantique:
- EQUIVALENT: Synonymes ou équivalents (ex: "QRS fins" = "QRS normal", "fréquence normale" = "fréquence cardiaque normale")
- CHILD: L'étudiant est plus spécifique (ex: "QRS fins" est un sous-type de "QRS normal")
- PARENT: L'étudiant est trop général (ex: "QRS" au lieu de "QRS normal")
- SIBLING: Concepts reliés mais différents (ex: "QRS larges" vs "QRS fins")
- DIFFERENT: Concepts différents

Réponds UNIQUEMENT avec ce JSON:
{{"relationship": "EQUIVALENT|CHILD|PARENT|SIBLING|DIFFERENT", "confidence": 0.0-1.0, "explanation": "courte explication en français"}}"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Plus rapide et économique
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=150,
                timeout=5
            )
            
            result = json.loads(response.choices[0].message.content)
            relationship = result['relationship']
            confidence = result['confidence']
            explanation = result['explanation']
            
            logger.info(f"🤖 LLM match: '{student_text}' vs '{expected_text}' → {relationship} ({confidence:.2f})")
            
            # Convertir relation LLM en score
            if relationship == 'EQUIVALENT' and confidence > 0.7:
                return ConceptMatch(
                    student_concept=student_text,
                    expected_concept=expected_text,
                    match_type=MatchType.EXACT,
                    score=100.0,
                    explanation=f"✅ {explanation}",
                    category=category
                )
            
            elif relationship == 'CHILD' and confidence > 0.6:
                return ConceptMatch(
                    student_concept=student_text,
                    expected_concept=expected_text,
                    match_type=MatchType.CHILD,
                    score=90.0,
                    explanation=f"✅ Très bien ! {explanation}",
                    category=category
                )
            
            elif relationship == 'PARENT' and confidence > 0.6:
                return ConceptMatch(
                    student_concept=student_text,
                    expected_concept=expected_text,
                    match_type=MatchType.PARENT,
                    score=70.0,
                    explanation=f"⚠️ {explanation}",
                    category=category
                )
            
            elif relationship == 'SIBLING' and confidence > 0.6:
                return ConceptMatch(
                    student_concept=student_text,
                    expected_concept=expected_text,
                    match_type=MatchType.SIBLING,
                    score=50.0,
                    explanation=f"⚠️ {explanation}",
                    category=category
                )
            
            else:  # DIFFERENT
                return ConceptMatch(
                    student_concept=student_text,
                    expected_concept=expected_text,
                    match_type=MatchType.MISSING,
                    score=0.0,
                    explanation=f"❌ {explanation}",
                    category=category
                )
        
        except Exception as e:
            logger.warning(f"⚠️ LLM matching failed: {e}, using fallback")
            
            # Fallback: similarité textuelle basique
            if self._text_similarity(student_text, expected_text) > 0.8:
                return ConceptMatch(
                    student_concept=student_text,
                    expected_concept=expected_text,
                    match_type=MatchType.EXACT,
                    score=95.0,
                    explanation="✅ Très proche (fallback textuel)",
                    category=category
                )
            else:
                return ConceptMatch(
                    student_concept=student_text,
                    expected_concept=expected_text,
                    match_type=MatchType.MISSING,
                    score=0.0,
                    explanation="❌ Différent (LLM indisponible)",
                    category=category
                )
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Similarité textuelle fallback (Jaccard)"""
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
        """Calcule le score total et les statistiques"""
        
        total_score = sum(m.score for m in matches if m.expected_concept)
        max_score = num_expected * 100.0
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Statistiques
        exact = sum(1 for m in matches if m.match_type == MatchType.EXACT)
        partial = sum(1 for m in matches if m.match_type in [MatchType.CHILD, MatchType.PARENT, MatchType.SIBLING])
        missing = sum(1 for m in matches if m.match_type == MatchType.MISSING)
        extra = sum(1 for m in matches if m.match_type == MatchType.EXTRA)
        contradictions = sum(1 for m in matches if m.match_type == MatchType.CONTRADICTION)
        
        # Scores par catégorie
        category_scores = {}
        for category in ['rhythm', 'conduction', 'morphology', 'measurement', 'pathology']:
            cat_matches = [m for m in matches if m.category == category and m.expected_concept]
            if cat_matches:
                cat_score = sum(m.score for m in cat_matches) / len(cat_matches)
                category_scores[category] = cat_score
        
        return ScoringResult(
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            matches=matches,
            exact_matches=exact,
            partial_matches=partial,
            missing_concepts=missing,
            extra_concepts=extra,
            contradictions=contradictions,
            category_scores=category_scores
        )
