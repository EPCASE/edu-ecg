# services/llm_service.py
"""
LLM Service with Fallback Strategy
Handles 4-step pipeline: NER → Mapping → Scoring → Feedback
"""

import logging
import os
from typing import List, Optional
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

# 🔧 CHARGER .env AVANT d'initialiser OpenAI
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ExtractedConcept(BaseModel):
    """Pydantic model for a single concept"""
    text: str
    category: str  # rhythm, conduction, morphology, etc.
    confidence: float


class ConceptsList(BaseModel):
    """Pydantic model for structured output - list of concepts"""
    concepts: List[ExtractedConcept]


class LLMService:
    """Service for LLM-based concept extraction with fallback"""
    
    NER_PROMPT = """Tu es un assistant médical expert en ECG. 
Extrais tous les concepts médicaux liés à l'électrocardiogramme de la réponse de l'étudiant.

**CAS SPÉCIAL**: Si l'étudiant dit "ECG normal", "tracé normal", "aucune anomalie" ou équivalent,
extrais-le comme UN concept unique avec catégorie "global".

Catégories possibles:
- global: diagnostic global (ECG normal, ECG pathologique, etc.)
- rhythm: rythme cardiaque (sinusal, FA, flutter, etc.)
- conduction: troubles de conduction (BAV, bloc de branche, etc.)
- morphology: morphologie des ondes (onde P, QRS, onde T, etc.)
- measurement: mesures (fréquence, intervalles PR/QT, etc.)
- pathology: pathologies (STEMI, hypertrophie, etc.)

Retourne chaque concept avec sa catégorie et un score de confiance (0-1)."""

    def __init__(self, use_structured_output: bool = True):
        self.use_structured_output = use_structured_output
    
    def extract_concepts(self, response_text: str) -> dict:
        """
        Extract medical concepts from student response
        
        Args:
            response_text: Student's text answer
        
        Returns:
            Dict with 'concepts' key containing list of dicts
        """
        if self.use_structured_output:
            try:
                concepts = self._extract_structured(response_text)
                # Convert Pydantic objects to dicts for compatibility
                concepts_dicts = [
                    {
                        'text': c.text,
                        'category': c.category,
                        'confidence': c.confidence
                    }
                    for c in concepts
                ]
                return {'concepts': concepts_dicts}
            
            except (OpenAIError, ValidationError, Exception) as e:
                logger.warning(
                    f"⚠️ Structured output failed: {e.__class__.__name__}: {str(e)}"
                )
                logger.info("🔄 Falling back to regex extraction")
                concepts = self._extract_regex_fallback(response_text)
                return {'concepts': concepts}
        else:
            concepts = self._extract_regex_fallback(response_text)
            return {'concepts': concepts}
    
    def _extract_structured(self, text: str) -> List[ExtractedConcept]:
        """
        PRIMARY METHOD: Structured output with GPT-4o
        
        Raises:
            OpenAIError: If API call fails
            ValidationError: If response doesn't match schema
        """
        logger.info("🤖 Extracting concepts with GPT-4o structured output")
        
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": self.NER_PROMPT},
                {"role": "user", "content": text}
            ],
            response_format=ConceptsList,  # Liste de concepts, pas un seul
            timeout=10  # Timeout after 10s
        )
        
        result = completion.choices[0].message.parsed
        concepts = result.concepts if hasattr(result, 'concepts') else []
        logger.info(f"✅ Extracted {len(concepts)} concepts via LLM")
        
        return concepts
    
    def _extract_regex_fallback(self, text: str) -> List[dict]:
        """
        FALLBACK METHOD: Basic regex extraction (no LLM)
        Returns simple dict format
        """
        logger.info("📝 Extracting concepts with regex fallback (no LLM)")
        
        raw_terms = self._basic_regex_extraction(text)
        
        concepts = [
            {
                'text': term,
                'category': 'unknown',
                'confidence': 0.6
            }
            for term in raw_terms
        ]
        
        logger.info(f"✅ Extracted {len(concepts)} concepts via regex")
        return concepts
    
    def _basic_regex_extraction(self, text: str) -> List[str]:
        """
        Basic regex extraction as last resort
        
        Common ECG terms to detect:
        - BAV (1, 2, 3)
        - Rythme sinusal/auriculaire
        - Fibrillation/Flutter
        - Bloc de branche
        - PR/QT intervals
        """
        import re
        
        patterns = [
            r'BAV\s*[123](?:er)?(?:\s+degré)?',
            r'rythme\s+(?:sinusal|auriculaire)',
            r'fibrillation\s+(?:auriculaire|ventriculaire)',
            r'flutter\s+auriculaire',
            r'bloc\s+de\s+branche\s+(?:droit|gauche)',
            r'tachycardie(?:\s+sinusale)?',
            r'bradycardie(?:\s+sinusale)?',
            r'PR\s+(?:allongé|court|normal)',
            r'QT\s+(?:allongé|court|normal)',
            r'STEMI',
            r'onde\s+[PTU]',
            r'QRS\s+(?:large|fin|normal)',
        ]
        
        found_terms = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            found_terms.extend([m.group(0) for m in matches])
        
        return list(set(found_terms))  # Remove duplicates


# Example usage
if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        service = LLMService()
        
        test_text = "Rythme sinusal avec BAV 1er degré. PR allongé à 220ms. Pas de BBD."
        
        concepts = await service.extract_concepts(test_text)
        
        print("\n🔍 Extracted Concepts:")
        for concept in concepts:
            print(f"  - {concept.text} ({concept.category}) [confidence: {concept.confidence}]")
    
    asyncio.run(test())
