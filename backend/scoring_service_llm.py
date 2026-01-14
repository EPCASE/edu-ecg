"""
🎯 Service de Scoring Sémantique - Two-Stage Architecture
Phase 1: LLM extraction (texte → IDs ontologie)
Phase 2: Scoring déterministe (relations ontologiques)

Auteur: Edu-ECG Team
Date: 2026-01-14
Version: 3.0 (Two-stage: LLM extraction + Ontology scoring)

BACKWARD COMPATIBLE: Garde l'interface SemanticScorer pour correction_llm.py
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import os
import logging
import json

logger = logging.getLogger(__name__)

# Import Two-Stage Architecture
try:
    from backend.scoring_service_two_stage import TwoStageScorer as _TwoStageScorer
    from backend.scoring_service_two_stage import ScoringResult as _TwoStageScoringResult
    TWO_STAGE_AVAILABLE = True
    logger.info("✅ Two-Stage Architecture loaded (LLM extraction + Ontology scoring)")
except Exception as e:
    TWO_STAGE_AVAILABLE = False
    logger.warning(f"⚠️ Two-Stage unavailable, using legacy: {e}")

# Legacy imports (fallback si two-stage pas dispo)
if not TWO_STAGE_AVAILABLE:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Import ontology services
    try:
        from backend.ontology_service import OntologyService
        _ontology = OntologyService()
        logger.info("✅ Ontology service loaded (legacy)")
    except Exception as e:
        logger.warning(f"⚠️ Ontology service unavailable: {e}")
        _ontology = None
    
    # Import OWL relation resolver
    try:
        from backend.services.ontology_relations import get_resolver
        _owl_resolver = get_resolver()
        logger.info("✅ OWL Relation Resolver loaded (legacy)")
    except Exception as e:
        logger.warning(f"⚠️ OWL Resolver unavailable: {e}")
        _owl_resolver = None


class MatchType(Enum):
    """Types de correspondance entre concepts"""
    EXACT = "exact"              # Correspondance parfaite
    PARENT = "parent"            # Étudiant trop général
    CHILD = "child"              # Étudiant trop spécifique (ou implication validée)
    PARTIAL = "partial"          # Signe correct mais diagnostic incomplet
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
    Scoring sémantique - NOW WITH TWO-STAGE ARCHITECTURE!
    
    Phase 1: LLM extrait concepts du texte → IDs ontologie
    Phase 2: Scoring déterministe sur relations ontologiques
    
    BACKWARD COMPATIBLE: Garde l'ancienne interface pour correction_llm.py
    """
    
    def __init__(self):
        """Initialize scorer avec two-stage architecture si disponible."""
        self.category_weights = {
            'rhythm': 1.2,
            'conduction': 1.1,
            'pathology': 1.0,
            'morphology': 0.9,
            'measurement': 0.8
        }
        
        # Utiliser Two-Stage si disponible
        if TWO_STAGE_AVAILABLE:
            self._scorer = _TwoStageScorer(extractor_type="gpt")
            self._mode = "two-stage"
            logger.info("✅ SemanticScorer using TWO-STAGE architecture")
        else:
            self._scorer = None
            self._mode = "legacy"
            logger.warning("⚠️ SemanticScorer using LEGACY mode (two-stage unavailable)")
    
    def score(
        self,
        student_concepts: List[Dict],
        expected_concepts: List[Dict],
        annotations: Optional[List[Dict]] = None,
        territory_selections: Optional[Dict] = None
    ) -> ScoringResult:
        """Score la réponse de l'étudiant.
        
        TWO-STAGE MODE (préféré):
        1. LLM extrait concepts → IDs ontologie
        2. Matching ontologique déterministe
        
        LEGACY MODE (fallback):
        3. LLM compare chaque paire de concepts
        
        Args:
            student_concepts: Concepts extraits de la réponse étudiant
            expected_concepts: Concepts attendus
            annotations: Annotations avec rôles (validant/description/exclusion)
            territory_selections: Territoires sélectionnés
        """
        
        # ===== TWO-STAGE MODE =====
        if self._mode == "two-stage" and self._scorer:
            try:
                result = self._scorer.score(
                    student_concepts,
                    expected_concepts,
                    annotations=annotations,
                    territory_selections=territory_selections
                )
                logger.debug(f"✅ Two-stage scoring: {result.percentage:.0f}% ({result.total_tokens} tokens)")
                return result
            except Exception as e:
                logger.error(f"❌ Two-stage failed: {e}, falling back to legacy")
                # Continue vers legacy mode en cas d'erreur
        
        # ===== LEGACY MODE (inchangé pour compatibilité) =====
        logger.info("Using LEGACY scoring mode")
        
        student_normalized = self._normalize_concepts(student_concepts)
        expected_normalized = self._normalize_concepts(expected_concepts)
        
        # 🎯 CAS SPÉCIAL: "ECG normal" valide TOUS les concepts normaux
        if self._is_global_normal_statement(student_normalized):
            return self._score_global_normal(expected_normalized)
        
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
        
        # 2. Concepts manquants - VÉRIFIER si impliqués par un diagnostic donné
        for expected_concept in expected_normalized:
            if expected_concept['text'] not in matched_expected:
                # Vérifier si un concept étudiant IMPLIQUE ce concept manquant
                implied_by = self._check_if_implied(student_normalized, expected_concept['text'])
                
                if implied_by:
                    # Concept validé par implication
                    matches.append(ConceptMatch(
                        student_concept=implied_by,
                        expected_concept=expected_concept['text'],
                        match_type=MatchType.CHILD,
                        score=100.0,
                        explanation=f"✅ Validé par implication: '{implied_by}' implique '{expected_concept['text']}'",
                        category=expected_concept['category']
                    ))
                else:
                    # Vraiment manquant
                    matches.append(ConceptMatch(
                        student_concept=None,
                        expected_concept=expected_concept['text'],
                        match_type=MatchType.MISSING,
                        score=0.0,
                        explanation=f"Concept manquant: {expected_concept['text']}",
                        category=expected_concept['category']
                    ))
        
        # 3. Calculer score total avec pénalités territoire
        return self._calculate_total_score(
            matches, 
            len(expected_normalized),
            annotations=annotations,
            territory_selections=territory_selections
        )
    
    def _normalize_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """Normalise les concepts (lowercase, trim)"""
        return [{
            'text': c['text'].lower().strip(),
            'original_text': c['text'],
            'category': c.get('category', 'unknown'),
            'confidence': c.get('confidence', 1.0)
        } for c in concepts]
    
    def _is_global_normal_statement(self, student_concepts: List[Dict]) -> bool:
        """
        Détecte si l'étudiant a donné une réponse globale "ECG normal"
        
        Patterns reconnus:
        - "ecg normal" (comme concept unique)
        - "ecg strictement normal"
        - "tracé normal"
        - "aucune anomalie"
        - "pas d'anomalie"
        
        NE PAS CONFONDRE avec des concepts spécifiques comme "onde P normale", "QRS normal", etc.
        """
        if not student_concepts:
            return False
        
        # 1. Si un seul concept avec catégorie "global" et texte contient "normal"
        if len(student_concepts) == 1:
            concept = student_concepts[0]
            if concept.get('category') == 'global' and 'normal' in concept['text']:
                logger.info(f"🎯 Détection 'ECG normal' global (concept unique): '{concept['text']}'")
                return True
        
        # 2. Si plusieurs concepts, chercher pattern strict "ECG normal" (pas juste "normal")
        full_text = " ".join(c['text'] for c in student_concepts)
        
        global_normal_patterns = [
            'ecg normal',
            'ecg strictement normal',
            'tracé normal',
            'tracé strictement normal',
            'électrocardiogramme normal',
            'aucune anomalie',
            "pas d'anomalie",
            'sans anomalie',
            'tout est normal',
            'rythme sinusal normale'  # Cas où l'étudiant dit juste "rythme sinusal normal" sans détails
        ]
        
        # Patterns SPÉCIFIQUES à EXCLURE (ne sont PAS des ECG globaux normaux)
        specific_patterns = [
            'onde p normale',
            'onde t normale',
            'qrs normal',
            'pr normal',
            'qt normal',
            'axe normal',
            'repolarisation normale',
            'fréquence normale',
            'fréquence cardiaque normale'
        ]
        
        # Si on trouve un pattern spécifique, ce n'est PAS un ECG global normal
        for specific in specific_patterns:
            if specific in full_text:
                return False
        
        # Sinon, chercher les patterns globaux
        for pattern in global_normal_patterns:
            if pattern in full_text:
                logger.info(f"🎯 Détection 'ECG normal' global: '{full_text}'")
                return True
        
        return False
    
    def _score_global_normal(self, expected_concepts: List[Dict]) -> ScoringResult:
        """
        Score une réponse "ECG normal" globale
        
        Logique:
        - Si TOUS les concepts attendus sont "normaux" → 100%
        - Si certains concepts sont pathologiques → score partiel avec explication
        """
        matches = []
        
        for expected in expected_concepts:
            # Vérifier si le concept attendu est "normal"
            is_normal_concept = self._is_normal_concept(expected['text'])
            
            if is_normal_concept:
                # Concept normal → validé par "ECG normal"
                matches.append(ConceptMatch(
                    student_concept="ecg normal",
                    expected_concept=expected['text'],
                    match_type=MatchType.PARENT,
                    score=100.0,
                    explanation=f"✅ Validé par 'ECG normal' (concept parent)",
                    category=expected['category']
                ))
            else:
                # Concept pathologique → manquant (l'étudiant aurait dû le préciser)
                matches.append(ConceptMatch(
                    student_concept="ecg normal",
                    expected_concept=expected['text'],
                    match_type=MatchType.CONTRADICTION,
                    score=0.0,
                    explanation=f"❌ Contradiction: 'ECG normal' mais '{expected['text']}' attendu",
                    category=expected['category']
                ))
        
        return self._calculate_total_score(matches, len(expected_concepts))
    
    def _is_normal_concept(self, concept_text: str) -> bool:
        """
        Détermine si un concept représente quelque chose de "normal"
        
        Exemples normaux:
        - "rythme sinusal"
        - "qrs normal", "qrs fins"
        - "fréquence normale"
        - "pr normal"
        - "repolarisation normale"
        
        Exemples pathologiques:
        - "bav", "fibrillation"
        - "qrs larges"
        - "tachycardie", "bradycardie"
        - "sus-décalage st"
        """
        concept_lower = concept_text.lower()
        
        # Mots-clés normaux
        normal_keywords = [
            'normal', 'sinusal', 'fin', 'fins', 'étroit', 'régulier',
            'régulière', 'sans anomalie', 'pas d', 'aucun', 'aucune'
        ]
        
        # Mots-clés pathologiques (prioritaires)
        pathology_keywords = [
            'bav', 'bloc', 'allongé', 'court', 'large', 'larges',
            'fibrillation', 'flutter', 'tachycardie', 'bradycardie',
            'sus-décalage', 'sous-décalage', 'infarctus', 'stemi',
            'ischémie', 'hypertrophie', 'déviation', 'pathologique'
        ]
        
        # Vérifier d'abord les pathologies (priorité)
        for keyword in pathology_keywords:
            if keyword in concept_lower:
                return False
        
        # Puis vérifier les mots normaux
        for keyword in normal_keywords:
            if keyword in concept_lower:
                return True
        
        # Par défaut: considérer comme normal si pas de pathologie détectée
        return True
    
    def _check_medical_implication(self, student_concept: str, expected_concept: str) -> bool:
        """
        Vérifie si le concept de l'étudiant IMPLIQUE le concept attendu
        basé sur les relations de l'ontologie médicale OWL
        
        Examples:
            - "BAV 1er degré" IMPLIQUE "PR allongé"
            - "Bloc de branche gauche complet" IMPLIQUE "QRS larges"
            - "Fibrillation auriculaire" IMPLIQUE "Absence d'onde P"
        
        Returns:
            True si le diagnostic de l'étudiant implique le finding attendu
        """
        if not _owl_resolver:
            logger.warning("⚠️ OWL Resolver not available, implication check skipped")
            return False
        
        # Utiliser le resolver OWL au lieu du dictionnaire hardcodé
        is_implied = _owl_resolver.concept_implies(student_concept, expected_concept)
        
        if is_implied:
            logger.info(f"🎯 Implication OWL détectée: '{student_concept}' → '{expected_concept}'")
        
        return is_implied
    
    def _check_if_implied(self, student_concepts: List[Dict], expected_finding: str) -> Optional[str]:
        """
        Vérifie si un finding attendu est IMPLIQUÉ par un diagnostic donné par l'étudiant
        
        Example:
            expected_finding = "PR allongé"
            student_concepts = ["BAV 1er degré", ...]
            → Returns "bav 1er degré" car BAV1 implique PR allongé
        
        Args:
            student_concepts: Tous les concepts donnés par l'étudiant
            expected_finding: Le finding attendu (potentiellement manquant)
        
        Returns:
            Le concept étudiant qui implique le finding, ou None
        """
        for student_concept in student_concepts:
            student_text = student_concept['text']
            
            # Vérifier implication médicale
            if self._check_medical_implication(student_text, expected_finding):
                logger.info(f"🎯 Finding '{expected_finding}' impliqué par '{student_text}'")
                return student_text
        
        return None
    
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
        
        ENRICHI avec ontologie médicale:
        - BAV 1 IMPLIQUE PR allongé
        - BBG IMPLIQUE QRS larges
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
        
        # 🆕 1b. Match par inclusion (étudiant a donné PLUS de détails)
        # Ex: Attendu "péricardite", Étudiant "péricardite sus-décalage inférieur"
        # → L'étudiant a donné le diagnostic + localisation/précision
        if expected_text in student_text:
            # L'étudiant a donné le concept attendu + des détails supplémentaires
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.EXACT,
                score=100.0,
                explanation=f"✅ Parfait ! Concept identifié avec précisions supplémentaires",
                category=category
            )
        
        # 1c. Match partiel inverse (étudiant a donné concept plus général)
        # Ex: Attendu "STEMI antérieur", Étudiant "STEMI"
        if student_text in expected_text:
            # L'étudiant a donné le concept de base mais sans les détails attendus
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.PARTIAL,
                score=70.0,
                explanation=f"⚠️ Concept correct mais manque de précision: '{student_text}' identifié, mais attendu '{expected_text}'",
                category=category
            )
        
        # 2. Vérifier implications médicales (basées sur ontologie)
        # 2a. Étudiant → Attendu (ex: "BAV 1" implique "PR allongé")
        if self._check_medical_implication(student_text, expected_text):
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.CHILD,
                score=100.0,
                explanation=f"✅ Validé par implication médicale: '{student_text}' implique '{expected_text}'",
                category=category
            )
        
        # 2b. Attendu → Étudiant (ex: étudiant dit "PR allongé" pour "BAV 1")
        # L'étudiant a donné un SIGNE au lieu du DIAGNOSTIC complet
        if self._check_medical_implication(expected_text, student_text):
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.PARTIAL,
                score=40.0,  # Score partiel
                explanation=f"⚠️ Signe correct mais incomplet: '{student_text}' est un signe de '{expected_text}', mais pas le diagnostic complet",
                category=category
            )
        
        # 3. Matching sémantique avec GPT-4o-mini
        try:
            prompt = f"""Tu es un expert cardiologue. Compare ces deux concepts ECG:

Concept étudiant: "{student_text}"
Concept attendu: "{expected_text}"

Détermine leur relation sémantique MÉDICALE:

- EQUIVALENT: Synonymes ou équivalents
  * "BAV 1" = "BAV de type 1" = "BAV du 1er degré"
  * "QRS fins" = "QRS normaux"
  * "Péricardite" = "Péricardite sus-décalage" (même diagnostic avec précision supplémentaire)
  * Si le concept étudiant CONTIENT le concept attendu + détails → EQUIVALENT

- CHILD: L'étudiant a donné un DIAGNOSTIC qui implique le SIGNE attendu
  * Étudiant dit "BAV 1" pour "PR allongé" attendu
  * Étudiant dit "BBG complet" pour "QRS larges" attendu
  * Le diagnostic EXPLIQUE le signe

- PARENT: L'étudiant a donné SEULEMENT un SIGNE pour un DIAGNOSTIC attendu
  * Étudiant dit "PR allongé" pour "BAV 1" attendu (manque le diagnostic)
  * Étudiant dit "onde P bloquée" pour "BAV 2" attendu (manque le diagnostic)
  * ⚠️ NE PAS confondre avec "diagnostic + signe" qui est EQUIVALENT

- SIBLING: Concepts reliés mais différents (ex: "QRS larges" vs "QRS fins")

- DIFFERENT: Concepts totalement différents

⚠️ RÈGLES IMPORTANTES:
1. Si l'étudiant donne le DIAGNOSTIC attendu + des détails (territoire, localisation) → EQUIVALENT, pas PARENT
2. PARENT uniquement si l'étudiant donne SEULEMENT un signe SANS le diagnostic
3. "Péricardite sus-décalage" contient "Péricardite" → EQUIVALENT

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
                # PARENT = L'étudiant a donné un SIGNE pour un DIAGNOSTIC attendu
                # Ex: "onde P bloquée" pour "BAV 2 Mobitz 2"
                # Score partiel car signe correct mais diagnostic incomplet
                return ConceptMatch(
                    student_concept=student_text,
                    expected_concept=expected_text,
                    match_type=MatchType.PARTIAL,
                    score=40.0,  # Score partiel cohérent avec requiresFindings inverse
                    explanation=f"⚠️ Signe correct mais diagnostic incomplet : {explanation}",
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
        num_expected: int,
        annotations: Optional[List[Dict]] = None,
        territory_selections: Optional[Dict] = None
    ) -> ScoringResult:
        """Calcule le score total et les statistiques
        
        Args:
            matches: Liste des correspondances concept étudiant/attendu
            num_expected: Nombre de concepts attendus
            annotations: Annotations avec rôles (pour pénalité territoire)
            territory_selections: Territoires sélectionnés par concept
        """
        
        # 🆕 APPLIQUER PÉNALITÉ TERRITOIRE (-50% pour diagnostics validants sans territoire)
        if annotations and territory_selections is not None:
            for match in matches:
                if match.expected_concept and match.score > 0:
                    # Trouver l'annotation correspondante
                    matching_annotation = None
                    for ann in annotations:
                        if ann['concept'] == match.expected_concept:
                            matching_annotation = ann
                            break
                    
                    if matching_annotation:
                        # Vérifier si c'est un diagnostic validant
                        is_validant = matching_annotation.get('annotation_role', '📝 Description') == '🎯 Diagnostic validant'
                        
                        # Vérifier si le concept nécessite un territoire
                        has_territory_possibles = bool(matching_annotation.get('territoires_possibles'))
                        
                        if is_validant and has_territory_possibles:
                            # Vérifier si un territoire a été sélectionné
                            concept_name = match.expected_concept
                            territories = territory_selections.get(concept_name, {}).get('territories', [])
                            
                            if not territories:
                                # Pénalité -50%
                                match.score = match.score * 0.5
                                match.explanation += " ⚠️ Territoire manquant (-50%)"
                                logger.info(f"Pénalité territoire appliquée à '{concept_name}': {match.score}")
        
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
