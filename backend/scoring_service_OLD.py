"""
🎯 Service de Scoring Hiérarchique
Compare réponse étudiant vs concepts attendus avec ontologie médicale

Auteur: Edu-ECG Team
Date: 2026-01-10
"""

from typing import List, D    def _normalize_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """Normalise les concepts pour comparaison (lowercase, trim)"""
        normalized = []
        for concept in concepts:
            text = concept['text'].lower().strip()
            
            normalized.append({
                'text': text,
                'original_text': concept['text'],  # Garder le texte original pour affichage
                'category': concept.get('category', 'unknown'),
                'confidence': concept.get('confidence', 1.0)
            })
        return normalizedonal
from dataclasses import dataclass
from enum import Enum
import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client for semantic matching
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class MatchType(Enum):
    """Types de correspondance entre concepts"""
    EXACT = "exact"              # Correspondance parfaite
    PARENT = "parent"            # Étudiant trop général (parent du concept attendu)
    CHILD = "child"              # Étudiant trop spécifique (enfant du concept attendu)
    SIBLING = "sibling"          # Concepts frères (même parent)
    CONTRADICTION = "contradiction"  # Concepts contradictoires
    MISSING = "missing"          # Concept attendu manquant
    EXTRA = "extra"              # Concept non attendu


@dataclass
class ConceptMatch:
    """Résultat de correspondance d'un concept"""
    student_concept: str
    expected_concept: Optional[str]
    match_type: MatchType
    score: float
    explanation: str
    category: str  # rhythm, conduction, morphology, measurement, pathology


@dataclass
class ScoringResult:
    """Résultat complet du scoring"""
    total_score: float          # Score global sur 100
    max_score: float            # Score maximum possible
    percentage: float           # Pourcentage (total/max)
    matches: List[ConceptMatch] # Détails par concept
    
    # Statistiques
    exact_matches: int
    partial_matches: int
    missing_concepts: int
    extra_concepts: int
    contradictions: int
    
    # Par catégorie
    category_scores: Dict[str, float]  # {category: score}


class HierarchicalScorer:
    """
    Scoring hiérarchique basé sur l'ontologie ECG
    
    Règles de scoring (sur 100 points par concept attendu):
    - Exact match: 100 points
    - Child (trop spécifique): 85-90 points
    - Parent (trop général): 60-80 points
    - Sibling (concept frère): 40-60 points
    - Contradiction: -20 points
    - Missing: 0 points
    - Extra (non attendu): 0 points (pas de pénalité)
    """
    
    def __init__(self, ontology_service=None):
        """
        Args:
            ontology_service: Instance de OntologyService pour requêtes ontologie
        """
        self.ontology_service = ontology_service
        
        # Poids par catégorie (importance relative)
        self.category_weights = {
            'rhythm': 1.2,        # Rythme crucial
            'conduction': 1.1,    # Conduction importante
            'pathology': 1.0,     # Pathologie standard
            'morphology': 0.9,    # Morphologie secondaire
            'measurement': 0.8    # Mesures moins critiques
        }
    
    def _semantic_match_llm(self, student_text: str, expected_text: str) -> Dict:
        """
        Utilise GPT-4o pour déterminer si deux concepts sont équivalents sémantiquement
        
        Args:
            student_text: Concept de l'étudiant
            expected_text: Concept attendu
            
        Returns:
            Dict avec 'equivalent' (bool), 'relationship' (str), 'confidence' (float)
        """
        try:
            prompt = f"""Tu es un expert cardiologue. Compare ces deux concepts ECG:

Concept étudiant: "{student_text}"
Concept attendu: "{expected_text}"

Détermine leur relation sémantique:
1. EQUIVALENT: Synonymes ou équivalents (ex: "QRS fins" = "QRS normal", "fréquence normale" = "fréquence cardiaque normale")
2. CHILD: L'étudiant est plus spécifique (ex: "QRS fins" est un type de "QRS normal")
3. PARENT: L'étudiant est trop général (ex: "QRS" au lieu de "QRS normal")
4. SIBLING: Concepts reliés mais différents (ex: "QRS larges" vs "QRS fins")
5. DIFFERENT: Concepts différents

Réponds UNIQUEMENT avec un JSON:
{{"relationship": "EQUIVALENT|CHILD|PARENT|SIBLING|DIFFERENT", "confidence": 0.0-1.0, "explanation": "courte explication"}}"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Plus rapide et moins cher pour ce cas
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Déterministe
                max_tokens=100
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"🤖 Semantic match: '{student_text}' vs '{expected_text}' → {result['relationship']} ({result['confidence']})")
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Semantic matching failed: {e}, falling back to text similarity")
            return {"relationship": "DIFFERENT", "confidence": 0.0, "explanation": "LLM unavailable"}
    
    def score(
        self, 
        student_concepts: List[Dict[str, str]], 
        expected_concepts: List[Dict[str, str]]
    ) -> ScoringResult:
        """
        Score la réponse de l'étudiant
        
        Args:
            student_concepts: Liste [{text, category, confidence}]
            expected_concepts: Liste [{text, category}]
            
        Returns:
            ScoringResult avec score détaillé
        """
        matches = []
        
        # Normaliser les concepts (lowercase, trim)
        student_normalized = self._normalize_concepts(student_concepts)
        expected_normalized = self._normalize_concepts(expected_concepts)
        
        # 1. Matcher concepts étudiants avec attendus
        matched_expected = set()
        
        for student_concept in student_normalized:
            best_match = self._find_best_match(
                student_concept, 
                expected_normalized,
                matched_expected
            )
            matches.append(best_match)
            
            if best_match.match_type != MatchType.EXTRA:
                matched_expected.add(best_match.expected_concept)
        
        # 2. Ajouter concepts manquants
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
        """Normalise les concepts pour comparaison (lowercase, trim)"""
        normalized = []
        for concept in concepts:
            text = concept['text'].lower().strip()
            
            # Appliquer les synonymes
            normalized_text = self.SYNONYMS.get(text, text)
            
            normalized.append({
                'text': normalized_text,
                'original_text': text,  # Garder le texte original pour affichage
                'category': concept.get('category', 'unknown'),
                'confidence': concept.get('confidence', 1.0)
            })
        return normalized
    
    def _find_best_match(
        self, 
        student_concept: Dict,
        expected_concepts: List[Dict],
        already_matched: set
    ) -> ConceptMatch:
        """
        Trouve la meilleure correspondance pour un concept étudiant
        
        Args:
            student_concept: Concept de l'étudiant
            expected_concepts: Liste concepts attendus
            already_matched: Set de concepts déjà matchés
            
        Returns:
            ConceptMatch avec meilleur score
        """
        best_match = None
        best_score = -100
        
        for expected in expected_concepts:
            # Skip déjà matché
            if expected['text'] in already_matched:
                continue
            
            # Calculer score de correspondance
            match = self._compare_concepts(student_concept, expected)
            
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
                explanation=f"Concept non attendu (peut être correct mais pas dans la liste)",
                category=student_concept['category']
            )
        
        return best_match
    
    def _compare_concepts(
        self, 
        student_concept: Dict, 
        expected_concept: Dict
    ) -> ConceptMatch:
        """
        Compare deux concepts et détermine type de correspondance
        
        Returns:
            ConceptMatch avec score et explication
        """
        student_text = student_concept['text']
        expected_text = expected_concept['text']
        category = expected_concept['category']
        
        # 1. Exact match (texte identique)
        if student_text == expected_text:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.EXACT,
                score=100.0,
                explanation="✅ Parfait ! Concept exact",
                category=category
            )
        
        # 2. Matching sémantique avec LLM (GPT-4o)
        semantic_result = self._semantic_match_llm(student_text, expected_text)
        
        if semantic_result['relationship'] == 'EQUIVALENT' and semantic_result['confidence'] > 0.7:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.EXACT,
                score=100.0,
                explanation=f"✅ Équivalent sémantique: {semantic_result['explanation']}",
                category=category
            )
        
        elif semantic_result['relationship'] == 'CHILD' and semantic_result['confidence'] > 0.6:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.CHILD,
                score=90.0,
                explanation=f"✅ Très bien ! Plus spécifique: {semantic_result['explanation']}",
                category=category
            )
        
        elif semantic_result['relationship'] == 'PARENT' and semantic_result['confidence'] > 0.6:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.PARENT,
                score=70.0,
                explanation=f"⚠️ Trop général: {semantic_result['explanation']}",
                category=category
            )
        
        elif semantic_result['relationship'] == 'SIBLING' and semantic_result['confidence'] > 0.6:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.SIBLING,
                score=50.0,
                explanation=f"⚠️ Concept proche mais différent: {semantic_result['explanation']}",
                category=category
            )
        
        # 3. Fallback: correspondance sémantique avec ontologie si disponible
        if self.ontology_service:
            ontology_match = self._ontology_match(student_text, expected_text)
            if ontology_match:
                return ontology_match
        
        # 4. Dernière option: similarité textuelle basique
        similarity_score = self._text_similarity(student_text, expected_text)
        
        if similarity_score > 0.8:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.EXACT,
                score=95.0,
                explanation="✅ Très proche du concept attendu",
                category=category
            )
        elif similarity_score > 0.6:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.SIBLING,
                score=50.0,
                explanation="⚠️ Concept similaire mais imprécis",
                category=category
            )
        else:
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.MISSING,
                score=0.0,
                explanation=f"❌ Différent de '{expected_text}'",
                category=category
            )
    
    def _ontology_match(self, student_text: str, expected_text: str) -> Optional[ConceptMatch]:
        """
        Utilise l'ontologie pour déterminer relation hiérarchique
        
        Returns:
            ConceptMatch si relation trouvée, None sinon
        """
        # TODO: Implémenter avec ontology_service
        # student_uri = self.ontology_service.find_concept_by_label(student_text)
        # expected_uri = self.ontology_service.find_concept_by_label(expected_text)
        # 
        # if self.ontology_service.has_relation(student_uri, expected_uri, 'subClassOf'):
        #     return ConceptMatch(CHILD, score=85-90)
        # elif self.ontology_service.has_relation(expected_uri, student_uri, 'subClassOf'):
        #     return ConceptMatch(PARENT, score=60-80)
        
        return None
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcul similarité textuelle amélioré
        
        Gère:
        - Inclusion de texte (ex: "fréquence normale" dans "fréquence cardiaque normale")
        - Similarité Jaccard sur les mots
        
        Returns:
            Score entre 0 et 1
        """
        # 1. Vérifier si l'un est inclus dans l'autre
        if text1 in text2 or text2 in text1:
            # Si inclusion, score élevé proportionnel à la longueur
            shorter = min(len(text1), len(text2))
            longer = max(len(text1), len(text2))
            return 0.7 + (shorter / longer) * 0.3  # Score entre 0.7 et 1.0
        
        # 2. Similarité Jaccard sur les mots
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _calculate_total_score(
        self, 
        matches: List[ConceptMatch], 
        num_expected: int
    ) -> ScoringResult:
        """
        Calcule le score total et statistiques
        
        Args:
            matches: Liste de tous les matches
            num_expected: Nombre de concepts attendus
            
        Returns:
            ScoringResult complet
        """
        # Statistiques
        exact_count = sum(1 for m in matches if m.match_type == MatchType.EXACT)
        partial_count = sum(1 for m in matches if m.match_type in [MatchType.CHILD, MatchType.PARENT, MatchType.SIBLING])
        missing_count = sum(1 for m in matches if m.match_type == MatchType.MISSING)
        extra_count = sum(1 for m in matches if m.match_type == MatchType.EXTRA)
        contradiction_count = sum(1 for m in matches if m.match_type == MatchType.CONTRADICTION)
        
        # Score par catégorie
        category_scores = {}
        for category in self.category_weights.keys():
            cat_matches = [m for m in matches if m.category == category and m.match_type != MatchType.EXTRA]
            if cat_matches:
                cat_score = sum(m.score for m in cat_matches) / len(cat_matches)
                category_scores[category] = cat_score
        
        # Score total pondéré
        total_score = 0.0
        max_possible = 0.0
        
        for match in matches:
            if match.match_type != MatchType.EXTRA:
                weight = self.category_weights.get(match.category, 1.0)
                total_score += match.score * weight
                max_possible += 100.0 * weight
        
        # Éviter division par zéro
        if max_possible == 0:
            percentage = 0.0
        else:
            percentage = (total_score / max_possible) * 100
        
        return ScoringResult(
            total_score=round(total_score, 2),
            max_score=round(max_possible, 2),
            percentage=round(percentage, 2),
            matches=matches,
            exact_matches=exact_count,
            partial_matches=partial_count,
            missing_concepts=missing_count,
            extra_concepts=extra_count,
            contradictions=contradiction_count,
            category_scores=category_scores
        )


# Exemple d'utilisation
if __name__ == "__main__":
    scorer = HierarchicalScorer()
    
    # Simulation
    student = [
        {"text": "Rythme sinusal", "category": "rhythm"},
        {"text": "BAV 1er degré", "category": "conduction"},
        {"text": "PR 220ms", "category": "measurement"}
    ]
    
    expected = [
        {"text": "Rythme sinusal", "category": "rhythm"},
        {"text": "BAV 1er degré", "category": "conduction"},
        {"text": "PR > 200ms", "category": "measurement"},
        {"text": "Axe normal", "category": "morphology"}  # Manquant
    ]
    
    result = scorer.score(student, expected)
    
    print(f"Score: {result.percentage}%")
    print(f"Exact: {result.exact_matches}, Partial: {result.partial_matches}")
    print(f"Manquants: {result.missing_concepts}, Extras: {result.extra_concepts}")
    
    for match in result.matches:
        print(f"  - {match.student_concept or '[MANQUANT]'}: {match.score} pts - {match.explanation}")
