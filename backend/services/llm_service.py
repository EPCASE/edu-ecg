# services/llm_service.py
"""
LLM Service with Fallback Strategy
Handles 4-step pipeline: NER → Mapping → Scoring → Feedback
"""

import logging
import os
from typing import List
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
    concepts: List[ExtractedConcept]  # Use typing.List for Python 3.9 compatibility


class LLMService:
    """Service for LLM-based concept extraction with fallback"""
    
    NER_PROMPT = """Tu es un assistant médical expert en ECG.
Extrais TOUS les concepts médicaux liés à l'électrocardiogramme de la réponse de l'étudiant.

**RÈGLES CRITIQUES** :
1. RESTITUE FIDÈLEMENT ce que l'étudiant a écrit, même si c'est mal orthographié ou incomplet
2. Normalise vers les termes de l'ontologie CI-DESSOUS si tu les reconnais avec certitude
3. Si un terme n'est pas dans l'ontologie mais est un concept ECG valide, GARDE-LE TEL QUEL
4. Ne JAMAIS inventer de concepts qui ne sont pas dans le texte
5. Les abréviations et acronymes doivent être développés : "BBD" → "Bloc de branche droit"
6. Les qualificatifs importants doivent être INCLUS : "complet", "incomplet", "droit", "gauche"

**CAS SPÉCIAL**: Si l'étudiant dit "ECG normal", "tracé normal", "aucune anomalie" ou équivalent,
extrais-le comme UN concept unique avec catégorie "global".

ONTOLOGIE ECG (normalise vers ces termes quand possible) :

Diagnostic urgent (poids 4): STEMI, Embolie pulmonaire, Torsade de pointes, BAV complet,
  Fibrillation ventriculaire, Asystolie, Hyperkaliémie, Hypokaliémie, Tamponnade

Diagnostic majeur (poids 3): Fibrillation atriale, BAV 2 Mobitz 2, Tachycardie ventriculaire,
  Syndrome de Wolf-Parkinson-White, Syndrome du QT long, Syndrome de Brugada,
  Dysfonction sinusale, Intoxication digitalique, Faisceau accessoire à conduction antérograde,
  Bloc de branche gauche complet, Bloc de branche droit complet

Signes ECG (poids 2): BAV 1er degré, BAV 2 Mobitz 1, Bloc de branche droit, Bloc de branche gauche,
  Hypertrophie ventriculaire gauche, Flutter auriculaire, Tachycardie sinusale, Bradycardie sinusale,
  Extrasystole ventriculaire, Extrasystole auriculaire, Stimulation atriale, Stimulation ventriculaire,
  Bloc fasciculaire antérieur gauche, Bloc fasciculaire postérieur gauche,
  Microvoltage, Pré-excitation ventriculaire

Descripteurs ECG (poids 1): Rythme sinusal, QRS fin, QRS large, Axe normal, Axe gauche, Axe droit,
  PR normal, PR allongé, QT normal, QT allongé, Onde P normale, Onde T négative, Onde T positive,
  Sus-décalage du segment ST, Sous-décalage du segment ST, Onde Q, Séquelle de nécrose,
  Fréquence cardiaque normale, Tachycardie, Bradycardie

SYNONYMES & ACRONYMES :
- "FA"/"fibrillation auriculaire" → Fibrillation atriale
- "BBG"/"bloc branche gauche" → Bloc de branche gauche
- "BBD"/"bloc branche droit" → Bloc de branche droit
- "BAV 1"/"PR allongé" → BAV 1er degré
- "BAV 2 M1"/"Wenckebach"/"Luciani-Wenckebach" → BAV 2 Mobitz 1
- "STEMI"/"sus-décalage ST" → Syndrome coronarien à la phase aigue avec sus-décalage du segment ST
- "NSTEMI"/"sous-décalage ST" → Syndrome coronarien à la phase aigue sans élévation du segment ST
- "HVG"/"hypertrophie VG" → Hypertrophie ventriculaire gauche
- "ESV" → Extrasystole ventriculaire
- "ESA" → Extrasystole auriculaire
- "WPW"/"Wolf"/"pré-excitation"/"faisceau accessoire" → Faisceau accessoire à conduction antérograde
- "HBAG" → Bloc fasciculaire antérieur gauche
- "HBPG" → Bloc fasciculaire postérieur gauche
- "microvolté"/"microvoltage" → Microvoltage
- "TV" → Tachycardie ventriculaire
- "péricardite"/"pericardite" → Péricardite

EXEMPLES D'EXTRACTION:
Input: "Rythme sinusal avec BAV 1 et BBG"
Output: [
  {text: "Rythme sinusal", category: "rhythm", confidence: 1.0},
  {text: "BAV 1er degré", category: "conduction", confidence: 1.0},
  {text: "Bloc de branche gauche", category: "conduction", confidence: 1.0}
]

Input: "FA rapide à 150 bpm"
Output: [
  {text: "Fibrillation atriale", category: "rhythm", confidence: 1.0},
  {text: "Fréquence ventriculaire rapide", category: "measurement", confidence: 0.9}
]

Input: "ESV infundibulaire droite"
Output: [
  {text: "Extrasystole ventriculaire", category: "rhythm", confidence: 1.0}
]

Catégories possibles:
- global: diagnostic global (ECG normal, ECG pathologique, etc.)
- rhythm: rythme cardiaque (sinusal, FA, flutter, etc.)
- conduction: troubles de conduction (BAV, bloc de branche, etc.)
- morphology: morphologie des ondes (onde P, QRS, onde T, segment ST, etc.)
- measurement: mesures (fréquence, intervalles PR/QT, etc.)
- pathology: pathologies (STEMI, hypertrophie, péricardite, etc.)

Retourne chaque concept avec sa catégorie et un score de confiance (0-1).
NE JETTE AUCUN concept médical ECG même s'il n'est pas dans la liste ci-dessus."""

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
