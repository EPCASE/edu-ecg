"""
⚔️ BENCHMARK: LLM vs Classic NLP
Compare les deux approches de scoring sur les mêmes cas

Métriques:
- Précision extraction
- Score final
- Temps d'exécution
- Coût (LLM seulement)

Auteur: Edu-ECG Team
Date: 2026-01-10
"""

import time
import json
from pathlib import Path
from typing import Dict, List
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scoring_service import SemanticScorer
from backend.scoring_service_classic import ClassicNLPScorer
from backend.services.llm_service import LLMService


def load_test_case(case_id: str = "RYTHME_SINUSAL_001") -> Dict:
    """Charge un cas de test"""
    test_cases_path = Path(__file__).parent.parent / "data" / "test_cases.json"
    
    with open(test_cases_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    return cases['cases'][0]  # Premier cas


def benchmark_llm_approach(text: str, expected_concepts: List[Dict]) -> Dict:
    """Teste l'approche LLM"""
    
    print("\n" + "="*60)
    print("🤖 APPROACH 1: LLM (GPT-4o)")
    print("="*60)
    
    # 1. Extraction
    start_extract = time.time()
    llm_service = LLMService()
    extraction_result = llm_service.extract_concepts(text)
    student_concepts = extraction_result['concepts']
    extract_time = time.time() - start_extract
    
    print(f"\n📊 Extraction:")
    print(f"  - Temps: {extract_time:.2f}s")
    print(f"  - Concepts trouvés: {len(student_concepts)}")
    for c in student_concepts:
        print(f"    • {c['text']} ({c['category']}) [{c['confidence']:.2f}]")
    
    # 2. Scoring
    start_score = time.time()
    scorer = SemanticScorer()
    result = scorer.score(student_concepts, expected_concepts)
    score_time = time.time() - start_score
    
    print(f"\n🎯 Scoring:")
    print(f"  - Temps: {score_time:.2f}s")
    print(f"  - Score final: {result.percentage:.1f}%")
    print(f"  - Matches exacts: {result.exact_matches}/{len(expected_concepts)}")
    print(f"  - Concepts manquants: {result.missing_concepts}")
    
    # Estimation coût (approximatif)
    # GPT-4o: ~$0.005/1K tokens input, ~$0.015/1K tokens output
    # Moyenne 200 tokens input + 100 output par extraction
    # GPT-4o-mini: ~$0.0001/1K tokens pour matching (6 calls)
    cost_extract = 0.005 * 0.2 + 0.015 * 0.1  # ~$0.0025
    cost_matching = 0.0001 * 0.3 * len(expected_concepts)  # ~$0.0002
    total_cost = cost_extract + cost_matching
    
    print(f"\n💰 Coût estimé:")
    print(f"  - Extraction: ${cost_extract:.4f}")
    print(f"  - Matching ({len(expected_concepts)} concepts): ${cost_matching:.4f}")
    print(f"  - TOTAL: ${total_cost:.4f}")
    
    return {
        'method': 'LLM (GPT-4o + GPT-4o-mini)',
        'extraction_time': extract_time,
        'scoring_time': score_time,
        'total_time': extract_time + score_time,
        'score': result.percentage,
        'concepts_found': len(student_concepts),
        'exact_matches': result.exact_matches,
        'missing': result.missing_concepts,
        'cost_usd': total_cost
    }


def benchmark_classic_approach(text: str, expected_concepts: List[Dict]) -> Dict:
    """Teste l'approche NLP classique"""
    
    print("\n" + "="*60)
    print("🏛️ APPROACH 2: CLASSIC NLP (Regex + Ontology)")
    print("="*60)
    
    # 1. Extraction
    start_extract = time.time()
    scorer = ClassicNLPScorer()
    student_concepts = scorer.extract_concepts(text)
    extract_time = time.time() - start_extract
    
    print(f"\n📊 Extraction:")
    print(f"  - Temps: {extract_time:.3f}s")
    print(f"  - Concepts trouvés: {len(student_concepts)}")
    for c in student_concepts:
        print(f"    • {c['text']} ({c['category']}) [{c['confidence']:.2f}]")
    
    # 2. Scoring
    start_score = time.time()
    result = scorer.score(student_concepts, expected_concepts)
    score_time = time.time() - start_score
    
    print(f"\n🎯 Scoring:")
    print(f"  - Temps: {score_time:.3f}s")
    print(f"  - Score final: {result.percentage:.1f}%")
    print(f"  - Matches exacts: {result.exact_matches}/{len(expected_concepts)}")
    print(f"  - Concepts manquants: {result.missing_concepts}")
    
    print(f"\n💰 Coût: $0 (gratuit)")
    
    return {
        'method': 'Classic NLP',
        'extraction_time': extract_time,
        'scoring_time': score_time,
        'total_time': extract_time + score_time,
        'score': result.percentage,
        'concepts_found': len(student_concepts),
        'exact_matches': result.exact_matches,
        'missing': result.missing_concepts,
        'cost_usd': 0.0
    }


def compare_results(llm_result: Dict, classic_result: Dict):
    """Affiche tableau comparatif"""
    
    print("\n" + "="*60)
    print("📊 COMPARISON SUMMARY")
    print("="*60)
    
    print(f"\n{'Metric':<25} {'LLM':<20} {'Classic NLP':<20} {'Winner':<10}")
    print("-" * 75)
    
    # Temps total
    llm_time = llm_result['total_time']
    classic_time = classic_result['total_time']
    time_winner = "Classic" if classic_time < llm_time else "LLM"
    print(f"{'⏱️  Total Time':<25} {llm_time:.2f}s{'':<15} {classic_time:.3f}s{'':<15} {time_winner}")
    
    # Score
    llm_score = llm_result['score']
    classic_score = classic_result['score']
    score_winner = "LLM" if llm_score > classic_score else "Classic" if classic_score > llm_score else "Tie"
    print(f"{'🎯 Score Accuracy':<25} {llm_score:.1f}%{'':<15} {classic_score:.1f}%{'':<15} {score_winner}")
    
    # Concepts trouvés
    llm_concepts = llm_result['concepts_found']
    classic_concepts = classic_result['concepts_found']
    concepts_winner = "LLM" if llm_concepts > classic_concepts else "Classic" if classic_concepts > llm_concepts else "Tie"
    print(f"{'🔍 Concepts Found':<25} {llm_concepts}{'':<19} {classic_concepts}{'':<19} {concepts_winner}")
    
    # Matches exacts
    llm_exact = llm_result['exact_matches']
    classic_exact = classic_result['exact_matches']
    exact_winner = "LLM" if llm_exact > classic_exact else "Classic" if classic_exact > llm_exact else "Tie"
    print(f"{'✅ Exact Matches':<25} {llm_exact}{'':<19} {classic_exact}{'':<19} {exact_winner}")
    
    # Coût
    llm_cost = llm_result['cost_usd']
    classic_cost = classic_result['cost_usd']
    print(f"{'💰 Cost per correction':<25} ${llm_cost:.4f}{'':<14} ${classic_cost:.4f}{'':<14} Classic")
    
    # Coût annuel (200 étudiants × 20 cas)
    annual_llm = llm_cost * 200 * 20
    annual_classic = classic_cost * 200 * 20
    print(f"{'💸 Annual cost (4K)':<25} ${annual_llm:.2f}{'':<15} ${annual_classic:.2f}{'':<15} Classic")
    
    print("\n" + "="*60)
    print("🏆 OVERALL WINNER:")
    
    # Score pondéré
    llm_points = 0
    classic_points = 0
    
    if time_winner == "LLM": llm_points += 1
    elif time_winner == "Classic": classic_points += 1
    
    if score_winner == "LLM": llm_points += 3  # Score x3 importance
    elif score_winner == "Classic": classic_points += 3
    
    if concepts_winner == "LLM": llm_points += 2
    elif concepts_winner == "Classic": classic_points += 2
    
    if exact_winner == "LLM": llm_points += 3
    elif exact_winner == "Classic": classic_points += 3
    
    classic_points += 2  # Bonus coût gratuit
    
    print(f"  LLM: {llm_points} points")
    print(f"  Classic NLP: {classic_points} points")
    
    if llm_points > classic_points:
        print("\n  🥇 LLM wins! Better accuracy justifies cost.")
    elif classic_points > llm_points:
        print("\n  🥇 Classic NLP wins! Free and fast enough.")
    else:
        print("\n  🤝 It's a tie! Both approaches viable.")
    
    print("="*60)


def main():
    """Lance le benchmark complet"""
    
    print("\n🔬 BENCHMARKING LLM vs CLASSIC NLP SCORING")
    print("Testing on: RYTHME_SINUSAL_001 case")
    
    # Charger cas de test
    test_case = load_test_case()
    student_text = test_case['student_response_example']
    expected_concepts = test_case['expected_concepts']
    
    print(f"\n📝 Student text to analyze:")
    print(f'  "{student_text}"')
    print(f"\n🎯 Expected concepts: {len(expected_concepts)}")
    
    # Benchmark LLM
    llm_result = benchmark_llm_approach(student_text, expected_concepts)
    
    # Benchmark Classic
    classic_result = benchmark_classic_approach(student_text, expected_concepts)
    
    # Comparer
    compare_results(llm_result, classic_result)


if __name__ == "__main__":
    main()
