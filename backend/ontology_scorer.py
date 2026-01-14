"""
Ontology Scorer - Scoring déterministe basé sur relations ontologiques.

Architecture two-stage:
1. llm_concept_extractor.py : Texte → IDs ontologie (LLM)
2. Ce module : IDs → Score (100% déterministe)

Relations utilisées:
- EXACT: IDs identiques ou synonymes
- CHILD: Student concept dans requiresFindings de expected (student dit signe, attendu diagnostic)
- PARENT: Expected concept dans requiresFindings de student (student dit diagnostic, attendu signe)
- SIBLING: Concepts voisins dans ontologie
- MISSING: Concept attendu pas trouvé
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum


class MatchType(Enum):
    """Type de correspondance ontologique."""
    EXACT = "EXACT"          # 100% - Même concept ou synonyme
    CHILD = "CHILD"          # 90-100% - Student a donné signe du diagnostic attendu
    PARENT = "PARENT"        # 40% - Student a donné diagnostic pour signe attendu
    SIBLING = "SIBLING"      # 50% - Concepts voisins/apparentés
    MISSING = "MISSING"      # 0% - Concept attendu non trouvé


@dataclass
class ConceptMatch:
    """Résultat du matching d'un concept attendu."""
    expected_id: str
    expected_name: str
    expected_poids: int
    
    match_type: MatchType
    score_percentage: float  # 0-100
    
    matched_student_id: Optional[str] = None
    matched_student_name: Optional[str] = None
    
    explanation: str = ""
    ontology_relation: Optional[str] = None  # Ex: "requiresFindings", "parent-child", etc.


@dataclass
class OntologyScore:
    """Score final calculé sur base ontologique pure."""
    matches: List[ConceptMatch]
    
    total_score: float  # 0-20
    score_percentage: float  # 0-100
    
    expected_weight_sum: float
    obtained_weight_sum: float
    
    territory_penalty_applied: bool = False
    territory_penalty_reason: str = ""
    
    # Statistiques
    exact_count: int = 0
    child_count: int = 0
    parent_count: int = 0
    sibling_count: int = 0
    missing_count: int = 0


class OntologyScorer:
    """Scorer déterministe basé uniquement sur relations ontologiques."""
    
    def __init__(self, ontology: dict):
        """
        Args:
            ontology: Dict complet de l'ontologie (avec concept_mappings, concept_hierarchy, etc.)
        """
        self.concept_mappings = ontology.get("concept_mappings", {})
        self.concept_hierarchy = ontology.get("concept_hierarchy", {})
        self.territoires = ontology.get("territoires_ecg", {})
        self.scoring_rules = ontology.get("scoring_rules", {})
    
    def _get_concept_data(self, concept_id: str) -> Optional[dict]:
        """Récupère les données d'un concept."""
        return self.concept_mappings.get(concept_id)
    
    def _get_parent(self, concept_id: str) -> Optional[str]:
        """Récupère le parent d'un concept dans la hiérarchie."""
        return self.concept_hierarchy.get(concept_id)
    
    def _get_children(self, concept_id: str) -> List[str]:
        """Récupère tous les enfants d'un concept."""
        return [cid for cid, parent_id in self.concept_hierarchy.items() if parent_id == concept_id]
    
    def _are_synonyms(self, concept_id: str, other_text: str) -> bool:
        """Vérifie si other_text est un synonyme de concept_id."""
        concept_data = self._get_concept_data(concept_id)
        if not concept_data:
            return False
        
        # Normalisation pour comparaison
        def normalize(s):
            return s.lower().strip().replace("é", "e").replace("è", "e").replace("à", "a")
        
        other_norm = normalize(other_text)
        
        # Vérifier nom principal
        if normalize(concept_data.get("concept_name", "")) == other_norm:
            return True
        
        # Vérifier synonymes
        for syn in concept_data.get("synonymes", []):
            if normalize(syn) == other_norm:
                return True
        
        return False
    
    def _match_exact(self, expected_id: str, student_ids: List[str]) -> Optional[Tuple[str, str]]:
        """Cherche match EXACT (même ID ou synonyme).
        
        Returns:
            (student_id, relation) si trouvé, None sinon
        """
        # Match direct sur ID
        if expected_id in student_ids:
            return (expected_id, "exact_id")
        
        # Match sur synonymes
        expected_data = self._get_concept_data(expected_id)
        if not expected_data:
            return None
        
        expected_name = expected_data.get("concept_name", "")
        
        for student_id in student_ids:
            student_data = self._get_concept_data(student_id)
            if not student_data:
                continue
            
            # Vérifier si student_name est synonyme d'expected
            if self._are_synonyms(expected_id, student_data.get("concept_name", "")):
                return (student_id, "synonym")
        
        return None
    
    def _match_child(self, expected_id: str, student_ids: List[str]) -> Optional[Tuple[str, str]]:
        """Cherche match CHILD (student a donné un signe du diagnostic attendu).
        
        Logique: Expected concept a requiresFindings qui contient un concept de student.
        Ex: Attendu = BAV_1 (requiresFindings: ["PR_ALLONGÉ"])
            Student = PR_ALLONGÉ
            → CHILD match (student a donné le signe du diagnostic)
        
        Returns:
            (student_id, relation) si trouvé, None sinon
        """
        expected_data = self._get_concept_data(expected_id)
        if not expected_data:
            return None
        
        implications = expected_data.get("implications", [])
        if not implications:
            return None
        
        # Chercher si un concept student est dans les implications attendues
        for student_id in student_ids:
            student_data = self._get_concept_data(student_id)
            if not student_data:
                continue
            
            student_name = student_data.get("concept_name", "")
            
            # Match direct sur nom
            if student_name in implications:
                return (student_id, "requiresFindings")
            
            # Match sur synonymes
            for impl in implications:
                if self._are_synonyms(student_id, impl):
                    return (student_id, "requiresFindings_synonym")
        
        return None
    
    def _match_parent(self, expected_id: str, student_ids: List[str]) -> Optional[Tuple[str, str]]:
        """Cherche match PARENT (student a donné le diagnostic pour le signe attendu).
        
        Logique inverse de CHILD:
        Ex: Attendu = PR_ALLONGÉ (signe)
            Student = BAV_1 (qui requiresFindings: ["PR_ALLONGÉ"])
            → PARENT match (student a sur-diagnostiqué)
        
        Returns:
            (student_id, relation) si trouvé, None sinon
        """
        expected_data = self._get_concept_data(expected_id)
        if not expected_data:
            return None
        
        expected_name = expected_data.get("concept_name", "")
        
        for student_id in student_ids:
            student_data = self._get_concept_data(student_id)
            if not student_data:
                continue
            
            # Vérifier si expected est dans requiresFindings de student
            implications = student_data.get("implications", [])
            
            if expected_name in implications:
                return (student_id, "inverse_requiresFindings")
            
            # Match sur synonymes
            for impl in implications:
                if self._are_synonyms(expected_id, impl):
                    return (student_id, "inverse_requiresFindings_synonym")
        
        return None
    
    def _match_sibling(self, expected_id: str, student_ids: List[str]) -> Optional[Tuple[str, str]]:
        """Cherche match SIBLING (concepts voisins dans ontologie).
        
        Returns:
            (student_id, relation) si trouvé, None sinon
        """
        expected_data = self._get_concept_data(expected_id)
        if not expected_data:
            return None
        
        voisins = expected_data.get("voisins", [])
        if not voisins:
            return None
        
        for student_id in student_ids:
            student_data = self._get_concept_data(student_id)
            if not student_data:
                continue
            
            student_name = student_data.get("concept_name", "")
            
            if student_name in voisins:
                return (student_id, "voisin")
        
        return None
    
    def _calculate_match_score(self, match_type: MatchType, expected_poids: int) -> float:
        """Calcule le score % pour un type de match donné.
        
        Args:
            match_type: Type de correspondance
            expected_poids: Poids du concept attendu (1-4)
            
        Returns:
            Score en pourcentage (0-100)
        """
        base_scores = {
            MatchType.EXACT: 100,
            MatchType.CHILD: 85,     # Student a donné le signe (très bien)
            MatchType.PARENT: 70,    # Student a sur-diagnostiqué (pas terrible)
            MatchType.SIBLING: 90,   # Concept proche mais pas exact
            MatchType.MISSING: 0
        }
        
        return base_scores.get(match_type, 0)
    
    def match_concept(self, expected_id: str, student_ids: List[str]) -> ConceptMatch:
        """Match un concept attendu contre les concepts student.
        
        Ordre de priorité (cascade):
        1. EXACT (100%)
        2. CHILD (95%) - Student a donné signe du diagnostic
        3. SIBLING (50%) - Concepts voisins
        4. PARENT (40%) - Student a donné diagnostic pour signe
        5. MISSING (0%)
        
        Args:
            expected_id: ID du concept attendu
            student_ids: Liste des IDs extraits du texte student
            
        Returns:
            ConceptMatch avec type de match et score
        """
        expected_data = self._get_concept_data(expected_id)
        if not expected_data:
            return ConceptMatch(
                expected_id=expected_id,
                expected_name="UNKNOWN",
                expected_poids=1,
                match_type=MatchType.MISSING,
                score_percentage=0,
                explanation="Concept attendu inconnu dans ontologie"
            )
        
        expected_name = expected_data.get("concept_name", expected_id)
        expected_poids = expected_data.get("poids", 1)
        
        # 1. Chercher EXACT
        exact_match = self._match_exact(expected_id, student_ids)
        if exact_match:
            student_id, relation = exact_match
            student_data = self._get_concept_data(student_id)
            return ConceptMatch(
                expected_id=expected_id,
                expected_name=expected_name,
                expected_poids=expected_poids,
                match_type=MatchType.EXACT,
                score_percentage=100,
                matched_student_id=student_id,
                matched_student_name=student_data.get("concept_name", student_id) if student_data else student_id,
                explanation=f"Match exact ({relation})",
                ontology_relation=relation
            )
        
        # 2. Chercher CHILD (student a donné le signe)
        child_match = self._match_child(expected_id, student_ids)
        if child_match:
            student_id, relation = child_match
            student_data = self._get_concept_data(student_id)
            return ConceptMatch(
                expected_id=expected_id,
                expected_name=expected_name,
                expected_poids=expected_poids,
                match_type=MatchType.CHILD,
                score_percentage=95,
                matched_student_id=student_id,
                matched_student_name=student_data.get("concept_name", student_id) if student_data else student_id,
                explanation=f"Student a correctement identifié un signe du diagnostic attendu ({relation})",
                ontology_relation=relation
            )
        
        # 3. Chercher SIBLING
        sibling_match = self._match_sibling(expected_id, student_ids)
        if sibling_match:
            student_id, relation = sibling_match
            student_data = self._get_concept_data(student_id)
            return ConceptMatch(
                expected_id=expected_id,
                expected_name=expected_name,
                expected_poids=expected_poids,
                match_type=MatchType.SIBLING,
                score_percentage=50,
                matched_student_id=student_id,
                matched_student_name=student_data.get("concept_name", student_id) if student_data else student_id,
                explanation=f"Concept voisin identifié ({relation})",
                ontology_relation=relation
            )
        
        # 4. Chercher PARENT (moins bon que SIBLING, student a sur-diagnostiqué)
        parent_match = self._match_parent(expected_id, student_ids)
        if parent_match:
            student_id, relation = parent_match
            student_data = self._get_concept_data(student_id)
            return ConceptMatch(
                expected_id=expected_id,
                expected_name=expected_name,
                expected_poids=expected_poids,
                match_type=MatchType.PARENT,
                score_percentage=40,
                matched_student_id=student_id,
                matched_student_name=student_data.get("concept_name", student_id) if student_data else student_id,
                explanation=f"Student a sur-diagnostiqué (diagnostic donné au lieu du signe) ({relation})",
                ontology_relation=relation
            )
        
        # 5. MISSING
        return ConceptMatch(
            expected_id=expected_id,
            expected_name=expected_name,
            expected_poids=expected_poids,
            match_type=MatchType.MISSING,
            score_percentage=0,
            explanation="Concept attendu non mentionné"
        )
    
    def score(
        self,
        expected_concept_ids: List[str],
        student_concept_ids: List[str],
        territory_selections: Optional[Dict[str, str]] = None,
        annotations: Optional[List[dict]] = None
    ) -> OntologyScore:
        """Calcule le score basé sur matching ontologique pur.
        
        Args:
            expected_concept_ids: Liste des IDs attendus
            student_concept_ids: Liste des IDs extraits du texte student
            territory_selections: Territoires sélectionnés par l'expert {concept_id: territoire}
            annotations: Annotations complètes (pour pénalité territoire)
            
        Returns:
            OntologyScore complet avec détails
        """
        matches = []
        
        # Matcher chaque concept attendu
        for expected_id in expected_concept_ids:
            match = self.match_concept(expected_id, student_concept_ids)
            matches.append(match)
        
        # Calculer poids total attendu et obtenu
        expected_weight_sum = sum(m.expected_poids for m in matches)
        obtained_weight_sum = sum(
            m.expected_poids * (m.score_percentage / 100.0)
            for m in matches
        )
        
        # Score base (0-100%)
        if expected_weight_sum > 0:
            score_percentage = (obtained_weight_sum / expected_weight_sum) * 100
        else:
            score_percentage = 0
        
        # Statistiques
        stats = {
            MatchType.EXACT: 0,
            MatchType.CHILD: 0,
            MatchType.PARENT: 0,
            MatchType.SIBLING: 0,
            MatchType.MISSING: 0
        }
        for match in matches:
            stats[match.match_type] += 1
        
        # Pénalité territoire (si applicable)
        territory_penalty_applied = False
        territory_penalty_reason = ""
        
        if annotations and territory_selections is not None:
            # Vérifier si des concepts validants ont des territoires possibles non remplis
            for annotation in annotations:
                if annotation.get("annotation_role") != "🎯 Diagnostic validant":
                    continue
                
                concept_id = annotation.get("ontology_id")
                concept_data = self._get_concept_data(concept_id)
                
                if not concept_data:
                    continue
                
                territoires_possibles = concept_data.get("territoires_possibles", [])
                territory_meta = concept_data.get("territory_metadata", {})
                
                if territoires_possibles and territory_meta and territory_meta.get("may_have_territory"):
                    # Vérifier si territoire sélectionné
                    selected_territory = territory_selections.get(concept_id)
                    
                    if not selected_territory:
                        territory_penalty_applied = True
                        territory_penalty_reason = f"Territoire manquant pour {concept_data.get('concept_name')}"
                        score_percentage *= 0.5  # -50%
                        break
        
        # Conversion en note /20
        total_score = (score_percentage / 100.0) * 20
        
        return OntologyScore(
            matches=matches,
            total_score=total_score,
            score_percentage=score_percentage,
            expected_weight_sum=expected_weight_sum,
            obtained_weight_sum=obtained_weight_sum,
            territory_penalty_applied=territory_penalty_applied,
            territory_penalty_reason=territory_penalty_reason,
            exact_count=stats[MatchType.EXACT],
            child_count=stats[MatchType.CHILD],
            parent_count=stats[MatchType.PARENT],
            sibling_count=stats[MatchType.SIBLING],
            missing_count=stats[MatchType.MISSING]
        )
