"""
💬 Service de Génération de Feedback Pédagogique
Utilise GPT-4o pour créer feedback personnalisé et bienveillant

Auteur: Edu-ECG Team
Date: 2026-01-10
"""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from openai import OpenAI
import json


@dataclass
class Feedback:
    """Feedback pédagogique structuré"""
    summary: str                    # Résumé général (1-2 phrases)
    strengths: List[str]            # Points forts (concepts corrects)
    missing_concepts: List[str]     # Concepts manquants avec explications
    errors: List[str]               # Erreurs avec corrections
    advice: str                     # Conseil pour progresser
    score_interpretation: str       # Interprétation du score
    next_steps: str                 # Prochaines étapes recommandées


class FeedbackService:
    """
    Service de génération de feedback pédagogique avec GPT-4o
    
    Principes:
    - Bienveillance: Toujours commencer par le positif
    - Constructif: Expliquer POURQUOI, pas juste dire "faux"
    - Actionnable: Donner pistes concrètes d'amélioration
    - Adaptatif: Niveau de détail selon score (débutant vs avancé)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Clé OpenAI (ou utilise env var OPENAI_API_KEY)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY requis (variable env ou paramètre)")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-2024-08-06"
    
    def generate_feedback(
        self,
        case_title: str,
        student_answer: str,
        scoring_result,  # ScoringResult from scoring_service
        student_level: str = "intermediate"  # beginner, intermediate, advanced
    ) -> Feedback:
        """
        Génère feedback personnalisé
        
        Args:
            case_title: Titre du cas ECG
            student_answer: Réponse brute de l'étudiant
            scoring_result: Résultat du scoring hiérarchique
            student_level: Niveau étudiant pour adapter ton
            
        Returns:
            Feedback structuré
        """
        # Construire contexte pour GPT-4o
        context = self._build_context(case_title, student_answer, scoring_result, student_level)
        
        # Appel GPT-4o avec structured output
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(student_level)
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                temperature=0.7,  # Créativité modérée
                max_tokens=800,
                response_format={
                    "type": "json_object"
                }
            )
            
            feedback_json = json.loads(response.choices[0].message.content)
            
            return Feedback(
                summary=feedback_json.get('summary', ''),
                strengths=feedback_json.get('strengths', []),
                missing_concepts=feedback_json.get('missing_concepts', []),
                errors=feedback_json.get('errors', []),
                advice=feedback_json.get('advice', ''),
                score_interpretation=feedback_json.get('score_interpretation', ''),
                next_steps=feedback_json.get('next_steps', '')
            )
            
        except Exception as e:
            # Fallback si GPT-4o échoue
            return self._generate_fallback_feedback(scoring_result)
    
    def _get_system_prompt(self, student_level: str) -> str:
        """Prompt système adapté au niveau étudiant"""
        
        base_prompt = """Tu es un enseignant en cardiologie, expert en ECG, bienveillant et pédagogue.

Ton rôle est de donner un feedback constructif sur l'interprétation ECG d'un étudiant en médecine.

Principes IMPÉRATIFS:
1. 🟢 TOUJOURS commencer par le POSITIF (ce qui est correct)
2. 📚 EXPLIQUER pourquoi c'est faux (pas juste dire "erreur")
3. 🎯 GUIDER vers la bonne réponse (pas donner directement)
4. 💡 SUGGÉRER méthode d'analyse pour éviter erreur future
5. 🌟 ENCOURAGER progrès, valoriser effort

Ton TON:
- Bienveillant mais rigoureux
- Encourageant mais honnête
- Pédagogique (expliquer le "pourquoi")
- Motivant (donner envie de progresser)

Format de réponse JSON:
{
  "summary": "Résumé général en 1-2 phrases",
  "strengths": ["Point fort 1", "Point fort 2", ...],
  "missing_concepts": ["Concept manquant 1 avec explication", ...],
  "errors": ["Erreur 1 avec correction", ...],
  "advice": "Conseil méthodologique principal",
  "score_interpretation": "Interprétation du score avec encouragement",
  "next_steps": "Prochaines étapes pour progresser"
}
"""
        
        level_adaptations = {
            'beginner': "\n\nNiveau DÉBUTANT (DFASM1-2): Explications très détaillées, rappels fondamentaux, vocabulaire simple.",
            'intermediate': "\n\nNiveau INTERMÉDIAIRE (DFASM2-3): Explications claires, liens physiopathologiques, vocabulaire médical standard.",
            'advanced': "\n\nNiveau AVANCÉ (Interne/Senior): Concis, focus nuances diagnostiques, vocabulaire expert."
        }
        
        return base_prompt + level_adaptations.get(student_level, level_adaptations['intermediate'])
    
    def _build_context(
        self,
        case_title: str,
        student_answer: str,
        scoring_result,
        student_level: str
    ) -> str:
        """Construit contexte pour GPT-4o"""
        
        # Extraire infos du scoring
        exact_matches = []
        partial_matches = []
        missing = []
        errors = []
        extras = []
        
        for match in scoring_result.matches:
            if match.match_type.value == 'exact':
                exact_matches.append(match.student_concept)
            elif match.match_type.value in ['child', 'parent', 'sibling']:
                partial_matches.append({
                    'student': match.student_concept,
                    'expected': match.expected_concept,
                    'type': match.match_type.value
                })
            elif match.match_type.value == 'missing':
                missing.append(match.expected_concept)
            elif match.match_type.value == 'contradiction':
                errors.append({
                    'student': match.student_concept,
                    'expected': match.expected_concept
                })
            elif match.match_type.value == 'extra':
                extras.append(match.student_concept)
        
        context = f"""CAS ECG: {case_title}

RÉPONSE ÉTUDIANT:
{student_answer}

RÉSULTATS D'ANALYSE:

Score global: {scoring_result.percentage}% ({scoring_result.total_score}/{scoring_result.max_score} points)

Concepts EXACTS ({len(exact_matches)}):
{chr(10).join('- ' + c for c in exact_matches) if exact_matches else '(aucun)'}

Concepts PARTIELS ({len(partial_matches)}):
{chr(10).join(f"- Étudiant: '{p['student']}' → Attendu: '{p['expected']}' (relation: {p['type']})" for p in partial_matches) if partial_matches else '(aucun)'}

Concepts MANQUANTS ({len(missing)}):
{chr(10).join('- ' + c for c in missing) if missing else '(aucun)'}

Concepts NON ATTENDUS ({len(extras)}):
{chr(10).join('- ' + c for c in extras) if extras else '(aucun)'}

Erreurs/Contradictions ({len(errors)}):
{chr(10).join(f"- Étudiant dit '{e['student']}' mais c'est '{e['expected']}'" for e in errors) if errors else '(aucun)'}

NIVEAU ÉTUDIANT: {student_level}

Génère un feedback pédagogique structuré en JSON selon le format spécifié.
"""
        
        return context
    
    def _generate_fallback_feedback(self, scoring_result) -> Feedback:
        """Feedback de secours si GPT-4o échoue"""
        
        score_pct = scoring_result.percentage
        
        # Interprétation score
        if score_pct >= 90:
            interpretation = "Excellent travail ! Votre analyse est très complète."
        elif score_pct >= 75:
            interpretation = "Bonne analyse globale, quelques points à affiner."
        elif score_pct >= 60:
            interpretation = "Analyse correcte mais incomplète, continuez vos efforts."
        elif score_pct >= 40:
            interpretation = "Analyse partielle, revoyez les concepts fondamentaux."
        else:
            interpretation = "Analyse insuffisante, reprenez la méthodologie de lecture ECG."
        
        # Construire feedback basique
        strengths = []
        missing = []
        
        for match in scoring_result.matches:
            if match.match_type.value == 'exact':
                strengths.append(f"✅ {match.student_concept}")
            elif match.match_type.value == 'missing':
                missing.append(f"❌ Concept manquant: {match.expected_concept}")
        
        return Feedback(
            summary=f"Score: {score_pct}%. {interpretation}",
            strengths=strengths if strengths else ["Continuez vos efforts"],
            missing_concepts=missing if missing else [],
            errors=[],
            advice="Revoir la méthodologie systématique de lecture ECG.",
            score_interpretation=interpretation,
            next_steps="Pratiquez avec d'autres cas similaires pour renforcer vos connaissances."
        )


# Exemple d'utilisation
if __name__ == "__main__":
    from scoring_service import HierarchicalScorer, MatchType, ConceptMatch, ScoringResult
    
    # Simuler résultat scoring
    matches = [
        ConceptMatch("Rythme sinusal", "Rythme sinusal", MatchType.EXACT, 100, "✅ Parfait", "rhythm"),
        ConceptMatch("BAV 1er degré", "BAV 1er degré", MatchType.EXACT, 100, "✅ Parfait", "conduction"),
        ConceptMatch(None, "Axe normal", MatchType.MISSING, 0, "Manquant", "morphology")
    ]
    
    scoring_result = ScoringResult(
        total_score=200,
        max_score=300,
        percentage=66.7,
        matches=matches,
        exact_matches=2,
        partial_matches=0,
        missing_concepts=1,
        extra_concepts=0,
        contradictions=0,
        category_scores={'rhythm': 100, 'conduction': 100, 'morphology': 0}
    )
    
    # Générer feedback
    service = FeedbackService()
    
    feedback = service.generate_feedback(
        case_title="BAV 1er degré simple",
        student_answer="Je vois un rythme sinusal avec BAV 1er degré",
        scoring_result=scoring_result,
        student_level="intermediate"
    )
    
    print("=== FEEDBACK ===")
    print(f"\n{feedback.summary}\n")
    print("Points forts:")
    for s in feedback.strengths:
        print(f"  {s}")
    print("\nÀ améliorer:")
    for m in feedback.missing_concepts:
        print(f"  {m}")
    print(f"\nConseil: {feedback.advice}")
    print(f"\nProchaines étapes: {feedback.next_steps}")
