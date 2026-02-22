"""
🎯 Service de Scoring Sémantique ECG
Scoring par LLM (GPT-4o-mini) avec support ontologie OWL

Auteur: Edu-ECG Team
Date: 2026-01-14
Version: 3.1 (Legacy LLM scoring with annotation roles)

RULES:
- 📝 Description concepts: EXCLUDED from scoring entirely
- 🎯 Diagnostic validant: scored (100% exact, 85% parent/signe→diag)
- ❌ Exclusion: auto-fail if present
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import os
import logging
import json

logger = logging.getLogger(__name__)

# OpenAI client
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import ontology services
try:
    from backend.ontology_service import OntologyService
    _ontology = OntologyService()
    logger.info("✅ Ontology service loaded")
except Exception as e:
    logger.warning(f"⚠️ Ontology service unavailable: {e}")
    _ontology = None

# Import OWL relation resolver
try:
    from backend.services.ontology_relations import get_resolver
    _owl_resolver = get_resolver()
    logger.info("✅ OWL Relation Resolver loaded")
except Exception as e:
    logger.warning(f"⚠️ OWL Resolver unavailable: {e}")
    _owl_resolver = None


class MatchType(Enum):
    """Types de correspondance entre concepts"""
    EXACT = "exact"              # Correspondance parfaite
    PARENT = "parent"            # Étudiant a donné un SIGNE pour DIAGNOSTIC attendu (85%)
    CHILD = "child"              # Étudiant a donné un DIAGNOSTIC pour SIGNE attendu (0% - non demandé)
    PARTIAL = "partial"          # Match partiel (PARENT avec score 85%)
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
    Scoring sémantique ECG par LLM (GPT-4o-mini).
    
    Compare concepts étudiants vs attendus avec support:
    - Relations ontologiques (parent/child/sibling)
    - Annotation roles (validant/description/exclusion)
    - Territoires ECG
    """
    
    def __init__(self):
        """Initialize scorer."""
        self.category_weights = {
            'rhythm': 1.2,
            'conduction': 1.1,
            'pathology': 1.0,
            'morphology': 0.9,
            'measurement': 0.8
        }
        logger.info("✅ SemanticScorer initialized")
    
    def score(
        self,
        student_concepts: List[Dict],
        expected_concepts: List[Dict],
        annotations: Optional[List[Dict]] = None,
        territory_selections: Optional[Dict] = None
    ) -> ScoringResult:
        """Score la réponse de l'étudiant.
        
        Compare chaque concept étudiant aux concepts attendus via LLM.
        Seuls les concepts 🎯 Diagnostic validant sont scorés.
        
        Args:
            student_concepts: Concepts extraits de la réponse étudiant
            expected_concepts: Concepts attendus
            annotations: Annotations avec rôles (validant/description/exclusion)
            territory_selections: Territoires sélectionnés
        """
        
        logger.info("Using LEGACY scoring mode")
        
        student_normalized = self._normalize_concepts(student_concepts)
        expected_normalized = self._normalize_concepts(expected_concepts)
        
        # 🎯 FILTRER les concepts "📝 Description" - Ne noter QUE les "🎯 Diagnostic validant"
        expected_validants = []
        for concept in expected_normalized:
            annotation_role = self._get_annotation_role(concept['text'], annotations)
            if annotation_role != '📝 Description':
                expected_validants.append(concept)
            else:
                logger.debug(f"⏭️ Concept descriptif ignoré (non noté): '{concept['text']}'")
        
        
        # 🎯 CAS SPÉCIAL: "ECG normal" valide TOUS les concepts normaux validants
        if self._is_global_normal_statement(student_normalized):
            return self._score_global_normal(expected_validants, annotations=annotations)
        
        matches = []
        matched_expected = set()
        
        # 1. Matcher chaque concept étudiant contre les concepts VALIDANTS uniquement
        for student_concept in student_normalized:
            match = self._find_best_match(
                student_concept,
                expected_validants,  # ← Utiliser seulement les validants
                matched_expected
            )
            matches.append(match)
            
            if match.expected_concept and match.score > 50:
                matched_expected.add(match.expected_concept)
        
        # 2. Concepts manquants - marquer comme MISSING (pas d'implication automatique)
        for expected_concept in expected_validants:  # ← Utiliser seulement les validants
            if expected_concept['text'] not in matched_expected:
                # Concept vraiment manquant (pas de vérification d'implication)
                matches.append(ConceptMatch(
                    student_concept=None,
                    expected_concept=expected_concept['text'],
                    match_type=MatchType.MISSING,
                    score=0.0,
                    explanation=f"❌ Concept manquant: {expected_concept['text']}",
                    category=expected_concept['category']
                ))
        
        # 3. Calculer score total avec pénalités territoire (seulement sur concepts validants)
        return self._calculate_total_score(
            matches, 
            len(expected_validants),  # ← Nombre de validants uniquement
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
    
    def _score_global_normal(
        self, 
        expected_concepts: List[Dict],
        annotations: Optional[List[Dict]] = None
    ) -> ScoringResult:
        """
        Score une réponse "ECG normal" globale
        
        RÈGLE IMPORTANTE: Seuls les concepts "🎯 Diagnostic validant" sont notés.
        Les concepts "📝 Description" ne comptent PAS dans le score (exclus du calcul).
        
        Logique:
        - Concepts "🎯 Diagnostic validant" normaux → 100% validés
        - Concepts "📝 Description" → IGNORÉS (ne comptent pas dans le score)
        - Concepts pathologiques → 0% (contradiction)
        
        Args:
            expected_concepts: Concepts attendus
            annotations: Annotations avec rôles (pour filtrer validant vs descriptif)
        """
        matches = []
        num_validant_concepts = 0  # Compter seulement les concepts validants
        
        for expected in expected_concepts:
            # Trouver le rôle de l'annotation
            annotation_role = self._get_annotation_role(expected['text'], annotations)
            
            # 🎯 IGNORER les concepts "📝 Description" (ne pas les noter du tout)
            if annotation_role == '📝 Description':
                logger.debug(f"⏭️ Concept descriptif ignoré (non noté): '{expected['text']}'")
                continue  # Passer au concept suivant sans l'ajouter aux matches
            
            # Compter seulement les concepts validants ou sans rôle défini
            num_validant_concepts += 1
            
            # Vérifier si le concept attendu est "normal"
            is_normal_concept = self._is_normal_concept(expected['text'])
            
            if is_normal_concept:
                # Diagnostic validant normal → Validé par "ECG normal"
                matches.append(ConceptMatch(
                    student_concept="ecg normal",
                    expected_concept=expected['text'],
                    match_type=MatchType.PARENT,
                    score=100.0,
                    explanation="✅ Validé par 'ECG normal' (diagnostic global)",
                    category=expected['category']
                ))
            else:
                # Concept pathologique → contradiction
                matches.append(ConceptMatch(
                    student_concept="ecg normal",
                    expected_concept=expected['text'],
                    match_type=MatchType.CONTRADICTION,
                    score=0.0,
                    explanation=f"❌ Contradiction: 'ECG normal' mais '{expected['text']}' attendu",
                    category=expected['category']
                ))
        
        # Calculer le score sur le nombre de concepts VALIDANTS uniquement
        return self._calculate_total_score(matches, num_validant_concepts)
    
    def _get_annotation_role(self, concept_text: str, annotations: Optional[List[Dict]]) -> Optional[str]:
        """
        Récupère le rôle d'annotation pour un concept donné
        
        Args:
            concept_text: Texte du concept (normalisé en lowercase)
            annotations: Liste des annotations avec leurs rôles
            
        Returns:
            Rôle de l'annotation ('🎯 Diagnostic validant', '📝 Description', '❌ Exclusion')
            ou None si pas d'annotation trouvée
        """
        if not annotations:
            return None
        
        # Chercher l'annotation correspondante
        for ann in annotations:
            # Comparer en lowercase pour éviter problèmes de casse
            if ann.get('concept', '').lower().strip() == concept_text.lower().strip():
                return ann.get('annotation_role', '📝 Description')
        
        return None
    
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
        
        # 🆕 1d. Match par synonymes de l'ontologie OWL (DÉTERMINISTE - avant LLM)
        # Ex: Attendu "Syndrome coronarien à la phase aigue avec sus-décalage du segment ST"
        #     Étudiant: "stemi inferieur" → "STEMI" est un synonyme → EQUIVALENT
        if _owl_resolver:
            expected_synonyms = _owl_resolver.get_synonyms(expected_text)
            student_lower = student_text.lower().strip()
            student_no_accent = student_lower
            try:
                from unidecode import unidecode as _unidecode
                student_no_accent = _unidecode(student_lower)
            except ImportError:
                pass
            
            for syn in expected_synonyms:
                syn_lower = syn.lower().strip()
                syn_no_accent = syn_lower
                try:
                    syn_no_accent = _unidecode(syn_lower)
                except Exception:
                    pass
                
                # Synonyme exact ou étudiant contient le synonyme (+ localisation)
                # "stemi inferieur" contient "stemi" → EQUIVALENT
                if syn_lower == student_lower or syn_no_accent == student_no_accent:
                    return ConceptMatch(
                        student_concept=student_text,
                        expected_concept=expected_text,
                        match_type=MatchType.EXACT,
                        score=100.0,
                        explanation=f"✅ Synonyme reconnu (ontologie): '{student_text}' = '{syn}' = '{expected_text}'",
                        category=category
                    )
                if syn_no_accent in student_no_accent or syn_lower in student_lower:
                    # Étudiant a donné synonyme + localisation (ex: "stemi inferieur")
                    return ConceptMatch(
                        student_concept=student_text,
                        expected_concept=expected_text,
                        match_type=MatchType.EXACT,
                        score=100.0,
                        explanation=f"✅ Synonyme + précision: '{student_text}' contient '{syn}' (synonyme de '{expected_text}')",
                        category=category
                    )
            
            # Vérifier aussi les synonymes du concept étudiant → si un synonyme de l'étudiant matche l'attendu
            student_synonyms = _owl_resolver.get_synonyms(student_text)
            expected_lower = expected_text.lower().strip()
            expected_no_accent = expected_lower
            try:
                expected_no_accent = _unidecode(expected_lower)
            except Exception:
                pass
            
            for syn in student_synonyms:
                syn_lower = syn.lower().strip()
                syn_no_accent = syn_lower
                try:
                    syn_no_accent = _unidecode(syn_lower)
                except Exception:
                    pass
                
                if syn_lower == expected_lower or syn_no_accent == expected_no_accent:
                    return ConceptMatch(
                        student_concept=student_text,
                        expected_concept=expected_text,
                        match_type=MatchType.EXACT,
                        score=100.0,
                        explanation=f"✅ Synonyme reconnu (ontologie): '{student_text}' ↔ '{syn}' = '{expected_text}'",
                        category=category
                    )
        
        # 2. Vérifier si l'étudiant a donné un DIAGNOSTIC pour un SIGNE attendu
        # Ex: Attendu "PR allongé", Étudiant "BAV 1er degré"
        # → "BAV 1" implique "PR allongé" mais ce n'est PAS ce qui est demandé
        # → On veut "PR allongé" explicitement, pas un diagnostic parent
        if self._check_medical_implication(student_text, expected_text):
            # L'étudiant a donné un diagnostic qui IMPLIQUE le signe attendu
            # Mais on veut le signe, pas le diagnostic → MISSING
            # Le diagnostic sera marqué EXTRA par ailleurs
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.MISSING,
                score=0.0,
                explanation=f"❌ Attendu '{expected_text}' mais reçu '{student_text}' (diagnostic parent non demandé)",
                category=category
            )
        
        # 3. Vérifier si l'étudiant a donné un SIGNE pour un DIAGNOSTIC attendu
        # Ex: Attendu "BAV 1er degré", Étudiant "PR allongé"
        # → L'étudiant a identifié un signe mais pas le diagnostic complet
        if self._check_medical_implication(expected_text, student_text):
            # L'étudiant a donné un signe d'un diagnostic attendu
            return ConceptMatch(
                student_concept=student_text,
                expected_concept=expected_text,
                match_type=MatchType.PARTIAL,
                score=85.0,  # Note dégradée (signe correct mais diagnostic incomplet)
                explanation=f"⚠️ Signe identifié mais diagnostic incomplet: '{student_text}' est un signe de '{expected_text}'",
                category=category
            )
        
        # 4. Matching sémantique avec GPT-4o-mini
        try:
            prompt = f"""Tu es un expert cardiologue. Compare ces deux concepts ECG:

Concept étudiant: "{student_text}"
Concept attendu: "{expected_text}"

Détermine leur relation sémantique MÉDICALE avec RÈGLES STRICTES:

- EQUIVALENT: Synonymes, abréviations, acronymes, ou équivalents
  * "BAV 1" = "BAV de type 1" = "BAV du 1er degré"
  * "QRS fins" = "QRS normaux"
  * "Péricardite" = "Péricardite sus-décalage" (même diagnostic avec précision)
  * "STEMI" = "Syndrome coronarien à la phase aigue avec sus-décalage du segment ST" (acronyme)
  * "NSTEMI" = "Syndrome coronarien à la phase aigue sans élévation du segment ST" (acronyme)
  * "FA" = "Fibrillation auriculaire" (acronyme)
  * "BBG" = "Bloc de branche gauche" (acronyme)
  * Si le concept étudiant est un ACRONYME du concept attendu → EQUIVALENT
  * Si le concept étudiant CONTIENT le concept attendu + détails (localisation, précision) → EQUIVALENT
  * Si le concept étudiant = concept attendu + localisation (ex: "STEMI inférieur") → EQUIVALENT

- PARENT: L'étudiant a donné un SIGNE pour un DIAGNOSTIC attendu
  * Étudiant dit "PR allongé" pour "BAV 1" attendu
  * Étudiant dit "QRS larges" pour "BBG complet" attendu
  * L'étudiant identifie un signe mais PAS le diagnostic complet
  * ⚠️ SCORING: 85% (note dégradée)

- CHILD: L'étudiant a donné un DIAGNOSTIC pour un SIGNE attendu
  * Étudiant dit "BAV 1" pour "PR allongé" attendu
  * Étudiant dit "BBG complet" pour "QRS larges" attendu
  * ⚠️ SCORING: 0% (MISSING - on veut le signe, pas le diagnostic)

- SIBLING: Concepts reliés mais différents (ex: "QRS larges" vs "QRS fins")

- DIFFERENT: Concepts totalement différents

⚠️ RÈGLES CRITIQUES:
1. Si attendu = SIGNE et étudiant = DIAGNOSTIC qui implique ce signe → CHILD (0%)
2. Si attendu = DIAGNOSTIC et étudiant = SIGNE de ce diagnostic → PARENT (85%)
3. Si étudiant utilise un ACRONYME du concept attendu (STEMI, NSTEMI, FA, BBG, BBD, BAV, etc.) → EQUIVALENT (100%)
4. Si étudiant = concept attendu + localisation/précision → EQUIVALENT (100%)
5. On note EXACTEMENT ce qui est demandé, pas plus, pas moins

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
            
            elif relationship == 'PARENT' and confidence > 0.6:
                # PARENT = Étudiant a donné SIGNE pour DIAGNOSTIC attendu
                # Ex: "PR allongé" pour "BAV 1" attendu
                return ConceptMatch(
                    student_concept=student_text,
                    expected_concept=expected_text,
                    match_type=MatchType.PARTIAL,
                    score=85.0,  # Note dégradée
                    explanation=f"⚠️ Signe identifié mais diagnostic incomplet: {explanation}",
                    category=category
                )
            
            elif relationship == 'CHILD' and confidence > 0.6:
                # CHILD = Étudiant a donné DIAGNOSTIC pour SIGNE attendu
                # Ex: "BAV 1" pour "PR allongé" attendu
                # → On veut le SIGNE, pas le diagnostic parent
                return ConceptMatch(
                    student_concept=student_text,
                    expected_concept=expected_text,
                    match_type=MatchType.MISSING,
                    score=0.0,
                    explanation=f"❌ Diagnostic parent donné mais signe attendu: {explanation}",
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
