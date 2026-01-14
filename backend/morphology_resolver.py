"""
Résolveur de morphologie ECG
Calcule automatiquement la morphologie ECG en fonction de l'origine anatomique
et du drapeau d'inversion pour les concepts comme échappement ventriculaire.

Règles:
- Échappement ventriculaire BBD (origine) → BBG (morphologie) [INVERSÉ]
- Bloc de branche BBD (origine) → BBD (morphologie) [CONCORDANT]

Auteur: Dr. Grégoire + GitHub Copilot
Date: 2026-01-14
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class MorphologyResolver:
    """Résout la morphologie ECG en fonction de l'origine et de l'inversion"""
    
    def __init__(self, ontology_path: str = "data/ontology_from_owl.json"):
        """
        Initialise le résolveur avec l'ontologie
        
        Args:
            ontology_path: Chemin vers le JSON d'ontologie
        """
        self.ontology_path = Path(ontology_path)
        self.ontology_data = None
        self.concept_mappings = {}
        
        # Map d'inversion (BBD <-> BBG)
        self.morphology_inversion_map = {
            'Bloc de branche droit': 'Bloc de branche gauche',
            'Bloc de branche gauche': 'Bloc de branche droit',
            'BBD': 'BBG',
            'BBG': 'BBD'
        }
        
        self.load_ontology()
    
    def load_ontology(self):
        """Charge l'ontologie depuis le JSON"""
        if not self.ontology_path.exists():
            raise FileNotFoundError(f"Ontologie non trouvée: {self.ontology_path}")
        
        with open(self.ontology_path, 'r', encoding='utf-8') as f:
            self.ontology_data = json.load(f)
            self.concept_mappings = self.ontology_data.get('concept_mappings', {})
    
    def get_concept_data(self, concept_name: str) -> Optional[Dict]:
        """
        Récupère les données d'un concept par son nom
        
        Args:
            concept_name: Nom du concept (ex: "Echappement ventriculaire")
            
        Returns:
            Dictionnaire de données du concept ou None
        """
        # Normalisation du nom
        concept_id = concept_name.upper().replace(' ', '_').replace('-', '_').replace("'", '_')
        
        return self.concept_mappings.get(concept_id)
    
    def resolve_morphology(self, concept_name: str, selected_origin: str) -> Dict[str, any]:
        """
        Résout la morphologie ECG d'un concept en fonction de l'origine sélectionnée
        
        Args:
            concept_name: Nom du concept (ex: "Echappement ventriculaire")
            selected_origin: Origine anatomique sélectionnée (ex: "Branche droite")
            
        Returns:
            Dictionnaire avec:
            - morphology: Morphologie calculée
            - requires_inversion: Si inversion a été appliquée
            - origin: Origine fournie
            - explanation: Explication textuelle
        """
        concept_data = self.get_concept_data(concept_name)
        
        if not concept_data:
            return {
                'morphology': None,
                'requires_inversion': False,
                'origin': selected_origin,
                'explanation': f"Concept '{concept_name}' non trouvé dans l'ontologie"
            }
        
        # Vérifier si le concept nécessite une inversion
        requires_inversion = concept_data.get('requires_morphology_inversion', False)
        
        # Morphologies possibles depuis l'ontologie
        ecg_morphologies = concept_data.get('ecg_morphologies', [])
        
        if not ecg_morphologies:
            return {
                'morphology': None,
                'requires_inversion': requires_inversion,
                'origin': selected_origin,
                'explanation': f"Aucune morphologie définie pour {concept_name}"
            }
        
        # Si pas d'inversion nécessaire, retourner la morphologie directe
        if not requires_inversion:
            return {
                'morphology': ecg_morphologies[0] if ecg_morphologies else None,
                'requires_inversion': False,
                'origin': selected_origin,
                'explanation': f"Morphologie concordante: {selected_origin} → {ecg_morphologies[0] if ecg_morphologies else 'N/A'}"
            }
        
        # LOGIQUE D'INVERSION
        # Déterminer la morphologie inversée en fonction de l'origine
        morphology_base = ecg_morphologies[0]  # Ex: "Bloc de branche"
        
        # Chercher si l'origine contient "droit" ou "gauche"
        if 'droit' in selected_origin.lower():
            # Origine droite → Morphologie GAUCHE (inversion)
            inverted_morphology = self._invert_morphology_term(morphology_base, 'gauche')
            explanation = f"⚡ INVERSION: {selected_origin} (origine) → {inverted_morphology} (morphologie)"
        elif 'gauche' in selected_origin.lower():
            # Origine gauche → Morphologie DROITE (inversion)
            inverted_morphology = self._invert_morphology_term(morphology_base, 'droit')
            explanation = f"⚡ INVERSION: {selected_origin} (origine) → {inverted_morphology} (morphologie)"
        else:
            # Pas de latéralité détectée, retourner la morphologie de base
            inverted_morphology = morphology_base
            explanation = f"Origine sans latéralité: {selected_origin} → {morphology_base}"
        
        return {
            'morphology': inverted_morphology,
            'requires_inversion': requires_inversion,
            'origin': selected_origin,
            'explanation': explanation
        }
    
    def _invert_morphology_term(self, morphology_base: str, target_side: str) -> str:
        """
        Inverse un terme de morphologie (bloc de branche) vers un côté cible
        
        Args:
            morphology_base: Base morphologique (ex: "Bloc de branche")
            target_side: Côté cible ('droit' ou 'gauche')
            
        Returns:
            Terme morphologique complet (ex: "Bloc de branche gauche")
        """
        if target_side.lower() == 'gauche':
            return f"{morphology_base} gauche"
        elif target_side.lower() == 'droit':
            return f"{morphology_base} droit"
        else:
            return morphology_base
    
    def get_available_origins(self, concept_name: str) -> List[str]:
        """
        Récupère les origines anatomiques possibles pour un concept
        
        Args:
            concept_name: Nom du concept
            
        Returns:
            Liste des origines possibles
        """
        concept_data = self.get_concept_data(concept_name)
        
        if not concept_data:
            return []
        
        return concept_data.get('origin_structures', [])
    
    def get_concept_info(self, concept_name: str) -> Dict:
        """
        Récupère toutes les informations morphologiques d'un concept
        
        Args:
            concept_name: Nom du concept
            
        Returns:
            Dictionnaire complet avec origine, morphologie, inversion
        """
        concept_data = self.get_concept_data(concept_name)
        
        if not concept_data:
            return {}
        
        return {
            'concept_name': concept_data.get('concept_name'),
            'origin_structures': concept_data.get('origin_structures', []),
            'ecg_morphologies': concept_data.get('ecg_morphologies', []),
            'requires_morphology_inversion': concept_data.get('requires_morphology_inversion', False),
            'poids': concept_data.get('poids'),
            'categorie': concept_data.get('categorie')
        }


def test_resolver():
    """Tests du résolveur de morphologie"""
    print("🧪 Tests du Morphology Resolver\n")
    
    resolver = MorphologyResolver()
    
    # Test 1: Échappement ventriculaire avec origine droite
    print("Test 1: Échappement ventriculaire + Branche droite")
    result = resolver.resolve_morphology("Echappement ventriculaire", "Branche droite")
    print(f"  Morphologie calculée: {result['morphology']}")
    print(f"  Explication: {result['explanation']}")
    print()
    
    # Test 2: Échappement ventriculaire avec origine gauche
    print("Test 2: Échappement ventriculaire + Branche gauche")
    result = resolver.resolve_morphology("Echappement ventriculaire", "Branche gauche")
    print(f"  Morphologie calculée: {result['morphology']}")
    print(f"  Explication: {result['explanation']}")
    print()
    
    # Test 3: Bloc de branche (sans inversion)
    print("Test 3: Bloc de branche droit (concordant)")
    result = resolver.resolve_morphology("Bloc de branche droit", "Branche droite")
    print(f"  Morphologie calculée: {result['morphology']}")
    print(f"  Explication: {result['explanation']}")
    print()
    
    # Test 4: Récupérer info concept
    print("Test 4: Informations complètes échappement ventriculaire")
    info = resolver.get_concept_info("Echappement ventriculaire")
    print(f"  Origines possibles: {info.get('origin_structures', [])}")
    print(f"  Morphologies: {info.get('ecg_morphologies', [])}")
    print(f"  Inversion requise: {info.get('requires_morphology_inversion', False)}")
    print()


if __name__ == "__main__":
    test_resolver()
