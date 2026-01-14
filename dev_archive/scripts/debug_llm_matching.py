"""
🔍 Debug LLM Matching
Vérifie ce que le LLM extrait et pourquoi le matching échoue
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import json
from unidecode import unidecode
from backend.services.llm_service import LLMService

# Charger l'ontologie
ONTOLOGY_PATH = Path("data/ontology_from_owl.json")

def normalize_search(text):
    """Normalise le texte pour la recherche"""
    return unidecode(text.lower())

def load_ontology_concepts():
    """Charge les concepts de l'ontologie"""
    with open(ONTOLOGY_PATH, 'r', encoding='utf-8') as f:
        ontology = json.load(f)
    
    concepts = []
    if 'concept_mappings' in ontology:
        for concept_id, concept_data in ontology['concept_mappings'].items():
            if isinstance(concept_data, dict):
                concept_name = concept_data.get('concept_name', '')
                if concept_name and not concept_name.startswith('Localisation') and not concept_name.startswith('localisation'):
                    concepts.append({
                        'name': concept_name,
                        'category': concept_data.get('categorie', concept_data.get('category', 'AUTRE')),
                        'ontology_id': concept_id,
                        'synonyms': concept_data.get('synonymes', concept_data.get('synonyms', [])),
                        'territoires_possibles': concept_data.get('territoires_possibles', [])
                    })
    
    return concepts

def main():
    # Phrase de test
    user_description = "Tracé ECG montrant un STEMI antérieur avec sus-décalage ST en V1-V3"
    
    print("="*80)
    print("🔍 DEBUG LLM MATCHING")
    print("="*80)
    print(f"\n📝 Phrase: {user_description}\n")
    
    # ÉTAPE 1: Extraction LLM
    print("ÉTAPE 1: Extraction par le LLM")
    print("-" * 80)
    
    llm_service = LLMService(use_structured_output=True)
    extraction_result = llm_service.extract_concepts(user_description)
    
    extracted_concepts = extraction_result.get('concepts', [])
    
    print(f"✅ {len(extracted_concepts)} concepts extraits:\n")
    
    for i, concept in enumerate(extracted_concepts, 1):
        print(f"{i}. Text: '{concept['text']}'")
        print(f"   Category: {concept.get('category', 'N/A')}")
        print(f"   Confidence: {int(concept.get('confidence', 0) * 100)}%")
        print()
    
    # ÉTAPE 2: Charger l'ontologie
    print("\nÉTAPE 2: Chargement de l'ontologie")
    print("-" * 80)
    
    ontology_concepts = load_ontology_concepts()
    print(f"✅ {len(ontology_concepts)} concepts chargés\n")
    
    # ÉTAPE 3: Matching
    print("\nÉTAPE 3: Matching avec l'ontologie")
    print("-" * 80)
    
    for extracted in extracted_concepts:
        concept_text = extracted['text']
        print(f"\n🔍 Recherche pour: '{concept_text}'")
        print(f"   Normalisé: '{normalize_search(concept_text)}'")
        
        # Normaliser le texte extrait
        search_words = [normalize_search(word) for word in concept_text.split() if len(word) >= 2]
        print(f"   Mots de recherche: {search_words}")
        
        # Chercher le meilleur match
        best_match = None
        best_score = 0
        all_matches = []
        
        for onto_concept in ontology_concepts:
            # Construire le texte de recherche
            onto_text = normalize_search(onto_concept['name'])
            for syn in onto_concept.get('synonyms', []):
                onto_text += " " + normalize_search(syn)
            
            # 1. Matching exact (100%)
            if normalize_search(concept_text) == normalize_search(onto_concept['name']):
                all_matches.append((onto_concept, 100, "exact name"))
                if 100 > best_score:
                    best_match = onto_concept
                    best_score = 100
            
            # 2. Matching exact avec synonyme (95%)
            for syn in onto_concept.get('synonyms', []):
                if normalize_search(concept_text) == normalize_search(syn):
                    all_matches.append((onto_concept, 95, f"exact synonym: {syn}"))
                    if 95 > best_score:
                        best_match = onto_concept
                        best_score = 95
            
            if best_score >= 95:
                continue
            
            # 3. Matching multi-termes (tous les mots présents) (85%)
            if search_words and all(word in onto_text for word in search_words):
                score = 85
                onto_words = onto_concept['name'].split()
                if len(search_words) == len(onto_words):
                    score = 90
                
                all_matches.append((onto_concept, score, "multi-word match"))
                if score > best_score:
                    best_match = onto_concept
                    best_score = score
            
            # 4. Matching partiel multi-mots (au moins 1 mot significatif) (75%)
            elif search_words:
                # Filtrer les mots courts et non significatifs
                significant_words = [w for w in search_words if len(w) >= 3]
                if significant_words:
                    # Compter combien de mots significatifs matchent
                    matched_words = sum(1 for word in significant_words if word in onto_text)
                    match_ratio = matched_words / len(significant_words)
                    
                    # Si au moins 50% des mots significatifs matchent
                    if match_ratio >= 0.5:
                        score = int(60 + (match_ratio * 20))  # 60-80% selon ratio
                        
                        # 🆕 BONUS: Si le mot matché est un synonyme exact (+10%)
                        for syn in onto_concept.get('synonyms', []):
                            if any(normalize_search(word) == normalize_search(syn) for word in significant_words):
                                score += 10
                                break
                        
                        all_matches.append((onto_concept, score, f"partial multi-word ({matched_words}/{len(significant_words)} words)"))
                        if score > best_score:
                            best_match = onto_concept
                            best_score = score
            
            # 5. Matching partiel simple (70%)
            if normalize_search(concept_text) in onto_text:
                all_matches.append((onto_concept, 70, "partial match"))
                if 70 > best_score:
                    best_match = onto_concept
                    best_score = 70
        
        print(f"\n   📊 Résultats:")
        print(f"   - {len(all_matches)} matches trouvés")
        
        if all_matches:
            # Trier par score
            all_matches.sort(key=lambda x: x[1], reverse=True)
            
            print(f"\n   🏆 Top 5 matches:")
            for concept, score, match_type in all_matches[:5]:
                print(f"      {score}% - {concept['name']} ({match_type})")
                if concept.get('synonyms'):
                    print(f"           Synonymes: {concept['synonyms']}")
        
        if best_match and best_score >= 60:
            print(f"\n   ✅ BEST MATCH (score={best_score}%): {best_match['name']}")
            print(f"      Catégorie: {best_match['category']}")
            if best_match.get('territoires_possibles'):
                print(f"      Territoires: {best_match['territoires_possibles']}")
        else:
            print(f"\n   ❌ AUCUN MATCH (meilleur score: {best_score}% < 60%)")
    
    print("\n" + "="*80)
    print("🏁 FIN DEBUG")
    print("="*80)

if __name__ == "__main__":
    main()
