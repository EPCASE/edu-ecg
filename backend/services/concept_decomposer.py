"""
🧩 Concept Decomposer - Décomposition intelligente de concepts composites
Gère la décomposition de concepts comme "STEMI antérieur" → ["STEMI", "Antérieur"]
avec validation des relations (territoires, sous-types)

Author: BMad Team - Party Mode
Date: 2026-01-11
"""

from typing import List, Dict, Tuple, Optional
from unidecode import unidecode
import logging

logger = logging.getLogger(__name__)


class ConceptMatch:
    """Représente un concept matché avec son score et sa validation"""
    
    def __init__(self, concept: Dict, score: int, match_type: str, 
                 extracted_text: str = "", validated: bool = False, 
                 relation: Optional[str] = None):
        self.concept = concept
        self.score = score
        self.match_type = match_type
        self.extracted_text = extracted_text
        self.validated = validated  # Validé par relation (territoire, sous-type)
        self.relation = relation  # Type de relation: "territory", "subtype", "main"
    
    def to_dict(self):
        """Convertit en dictionnaire pour l'UI"""
        return {
            'concept': self.concept['name'],
            'category': self.concept['category'],
            'ontology_id': self.concept.get('ontology_id', ''),
            'territoires_possibles': self.concept.get('territoires_possibles', []),
            'confidence': self.score,
            'extracted_text': self.extracted_text,
            'match_score': self.score,
            'validated': self.validated,
            'relation': self.relation
        }


class ConceptDecomposer:
    """Décompose les concepts composites en concepts atomiques"""
    
    def __init__(self, ontology_concepts: List[Dict]):
        """
        Args:
            ontology_concepts: Liste des concepts de l'ontologie
        """
        self.ontology_concepts = ontology_concepts
        
        # Créer des index pour accélération
        self._build_indexes()
    
    def _build_indexes(self):
        """Construit des index pour accélérer les recherches"""
        # Index nom → concept
        self.name_index = {}
        # Index synonyme → concept
        self.synonym_index = {}
        # Index territoire → concepts qui l'utilisent
        self.territory_index = {}
        
        for concept in self.ontology_concepts:
            # Index par nom
            normalized_name = self._normalize(concept['name'])
            self.name_index[normalized_name] = concept
            
            # Index par synonymes
            for syn in concept.get('synonyms', []):
                normalized_syn = self._normalize(syn)
                self.synonym_index[normalized_syn] = concept
            
            # Index par territoires
            for territory in concept.get('territoires_possibles', []):
                if territory not in self.territory_index:
                    self.territory_index[territory] = []
                self.territory_index[territory].append(concept)
    
    def _normalize(self, text: str) -> str:
        """Normalise le texte pour la recherche"""
        return unidecode(text.lower())
    
    def decompose(self, llm_concept_text: str, llm_confidence: float = 1.0) -> List[ConceptMatch]:
        """
        Décompose un concept composite en concepts atomiques
        
        Args:
            llm_concept_text: Texte extrait par le LLM (ex: "STEMI antérieur")
            llm_confidence: Confiance du LLM (0-1)
            
        Returns:
            Liste de ConceptMatch validés et scorés
        """
        logger.info(f"Décomposition de '{llm_concept_text}'")
        
        # Étape 1: Essayer un match direct (concept atomique)
        direct_match = self._match_direct(llm_concept_text, llm_confidence)
        if direct_match and direct_match.score >= 95:
            logger.info(f"  → Match direct: {direct_match.concept['name']} ({direct_match.score}%)")
            return [direct_match]
        
        # Étape 2: Décomposer en mots et matcher
        words = [w.strip() for w in llm_concept_text.split() if len(w.strip()) >= 2]
        
        if len(words) <= 1:
            # Concept simple, retourner le match direct ou vide
            return [direct_match] if direct_match and direct_match.score >= 60 else []
        
        # Étape 3: Matcher chaque sous-séquence de mots
        matches = self._match_subsequences(words, llm_confidence)
        
        # Étape 4: Valider les relations entre matches
        validated_matches = self._validate_relations(matches)
        
        # Étape 5: Si aucun match validé, retourner le match direct
        if not validated_matches and direct_match and direct_match.score >= 60:
            logger.info(f"  → Fallback sur match direct: {direct_match.concept['name']}")
            return [direct_match]
        
        logger.info(f"  → {len(validated_matches)} concepts décomposés")
        return validated_matches
    
    def _match_direct(self, text: str, confidence: float) -> Optional[ConceptMatch]:
        """Match direct du texte complet"""
        normalized = self._normalize(text)
        
        # Match exact par nom
        if normalized in self.name_index:
            concept = self.name_index[normalized]
            return ConceptMatch(
                concept=concept,
                score=int(min(100, confidence * 100)),
                match_type="exact_name",
                extracted_text=text,
                validated=True,
                relation="main"
            )
        
        # Match exact par synonyme
        if normalized in self.synonym_index:
            concept = self.synonym_index[normalized]
            return ConceptMatch(
                concept=concept,
                score=int(min(95, confidence * 100)),
                match_type="exact_synonym",
                extracted_text=text,
                validated=True,
                relation="main"
            )
        
        # Match partiel (au moins 1 mot significatif)
        return self._match_partial(text, confidence)
    
    def _match_partial(self, text: str, confidence: float) -> Optional[ConceptMatch]:
        """Match partiel multi-mots avec bonus synonyme"""
        normalized = self._normalize(text)
        words = [w for w in normalized.split() if len(w) >= 3]
        
        if not words:
            return None
        
        best_match = None
        best_score = 0
        
        for concept in self.ontology_concepts:
            # Construire texte de recherche (nom + synonymes)
            onto_text = self._normalize(concept['name'])
            for syn in concept.get('synonyms', []):
                onto_text += " " + self._normalize(syn)
            
            # Compter mots matchés
            matched_words = sum(1 for word in words if word in onto_text)
            if matched_words == 0:
                continue
            
            match_ratio = matched_words / len(words)
            
            if match_ratio >= 0.5:  # Au moins 50% des mots
                score = int(60 + (match_ratio * 20))  # 60-80%
                
                # Bonus si synonyme exact
                for syn in concept.get('synonyms', []):
                    if any(self._normalize(word) == self._normalize(syn) for word in words):
                        score += 10
                        break
                
                if score > best_score:
                    best_match = concept
                    best_score = score
        
        if best_match:
            return ConceptMatch(
                concept=best_match,
                score=int(min(best_score, confidence * 100)),
                match_type="partial_multiword",
                extracted_text=text,
                validated=False,
                relation="main"
            )
        
        return None
    
    def _match_subsequences(self, words: List[str], confidence: float) -> List[ConceptMatch]:
        """
        Match toutes les sous-séquences possibles de mots
        Ex: ["STEMI", "antérieur"] → essayer "STEMI", "antérieur", "STEMI antérieur"
        
        Stratégie: essayer TOUTES les combinaisons, pas seulement les séquences continues
        """
        matches = []
        
        # D'abord essayer la séquence complète
        full_text = " ".join(words)
        full_match = self._match_direct(full_text, confidence)
        if full_match and full_match.score >= 95:
            # Match exact du tout, pas besoin de décomposer
            return [full_match]
        
        # Ensuite essayer chaque mot individuellement
        for word in words:
            match = self._match_direct(word, confidence)
            if match and match.score >= 60:
                matches.append(match)
        
        # Si plusieurs matches trouvés, retourner
        if len(matches) > 1:
            return matches
        
        # Si un seul match ou aucun, essayer des combinaisons de 2 mots
        if len(words) >= 2:
            for i in range(len(words)):
                for j in range(i + 1, len(words)):
                    combined = f"{words[i]} {words[j]}"
                    match = self._match_direct(combined, confidence)
                    if match and match.score >= 70:
                        # Vérifier si ce n'est pas déjà dans matches
                        if not any(m.concept['name'] == match.concept['name'] for m in matches):
                            matches.append(match)
        
        # Si toujours rien, retourner le match complet si score acceptable
        if not matches and full_match and full_match.score >= 60:
            matches.append(full_match)
        
        return matches
    
    def _validate_relations(self, matches: List[ConceptMatch]) -> List[ConceptMatch]:
        """
        Valide les relations entre concepts matchés
        Ex: Si "STEMI" + "Antérieur", vérifier que "Antérieur" ∈ territoires_possibles(STEMI)
        """
        if len(matches) <= 1:
            return matches
        
        validated = []
        
        # Identifier le concept principal (score le plus élevé, ou DIAGNOSTIC_URGENT/MAJEUR)
        main_concept = max(matches, key=lambda m: (
            m.concept['category'] in ['DIAGNOSTIC_URGENT', 'DIAGNOSTIC_MAJEUR'],
            m.score
        ))
        
        main_concept.relation = "main"
        main_concept.validated = True
        validated.append(main_concept)
        
        # Valider les autres concepts par rapport au principal
        for match in matches:
            if match == main_concept:
                continue
            
            # Vérifier relation territoriale
            if self._is_territory_of(match.concept, main_concept.concept):
                match.relation = "territory"
                match.validated = True
                match.score = min(match.score + 5, 100)  # Bonus validation
                validated.append(match)
                logger.info(f"  ✅ Territoire validé: {match.concept['name']} pour {main_concept.concept['name']}")
            
            # Vérifier sous-type (même catégorie, score similaire)
            elif match.concept['category'] == main_concept.concept['category']:
                match.relation = "subtype"
                match.validated = True
                validated.append(match)
                logger.info(f"  ✅ Sous-type détecté: {match.concept['name']}")
            
            # Sinon, concept indépendant mais pertinent
            elif match.score >= 70:
                match.relation = "related"
                match.validated = True
                validated.append(match)
                logger.info(f"  ℹ️ Concept lié: {match.concept['name']}")
        
        return validated
    
    def _is_territory_of(self, territory_concept: Dict, main_concept: Dict) -> bool:
        """
        Vérifie si territory_concept est un territoire valide pour main_concept
        """
        # Vérifier dans territoires_possibles du concept principal
        territoires = main_concept.get('territoires_possibles', [])
        
        # Le territoire peut être:
        # 1. Le nom du concept territoire lui-même
        if territory_concept['name'] in territoires:
            return True
        
        # 2. Un concept enfant d'une Localisation référencée
        # Ex: "Antérieur" est enfant de "Localisation IDM"
        for territoire_name in territoires:
            # Chercher si le territoire_concept est lié à cette localisation
            # (Dans notre cas, "Antérieur" aura category="DESCRIPTEUR_ECG" et sera dans la liste des territoires ECG)
            if territory_concept['category'] == 'DESCRIPTEUR_ECG':
                # C'est probablement un territoire valide
                return True
        
        return False


def create_decomposer(ontology_concepts: List[Dict]) -> ConceptDecomposer:
    """Factory function pour créer un décomposeur"""
    return ConceptDecomposer(ontology_concepts)
