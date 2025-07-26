import unittest
import sys
import os

# Ajouter le chemin du backend pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))

from correction_engine import OntologyCorrector

class TestOntologyCorrector(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Initialiser le correcteur une seule fois pour tous les tests"""
        ontology_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ontologie.owx')
        cls.corrector = OntologyCorrector(ontology_path)
        print(f"✅ Ontologie chargée avec {len(cls.corrector.concepts)} concepts")
    
    def test_ontology_loading(self):
        """Test que l'ontologie se charge correctement"""
        self.assertIsNotNone(self.corrector.onto)
        self.assertGreater(len(self.corrector.concepts), 0)
        print(f"📊 Nombre de concepts : {len(self.corrector.concepts)}")
    
    def test_exact_match(self):
        """Test correspondance exacte entre concepts"""
        # Prendre les premiers concepts disponibles pour le test
        concepts = list(self.corrector.concepts.keys())
        if len(concepts) >= 2:
            concept1 = concepts[0]
            # Test exact match
            score = self.corrector.get_score(concept1, concept1)
            self.assertEqual(score, 100)
            print(f"✅ Test exact match: {concept1} = 100%")
    
    def test_hierarchy_relationships(self):
        """Test des relations hiérarchiques"""
        concepts = list(self.corrector.concepts.keys())
        
        # Trouver des concepts avec des relations parent-enfant
        parent_child_pairs = []
        for concept_name, concept_cls in self.corrector.concepts.items():
            for parent in concept_cls.is_a:
                if hasattr(parent, 'name') and parent.name in self.corrector.concepts:
                    parent_child_pairs.append((parent.name, concept_name))
        
        if parent_child_pairs:
            parent, child = parent_child_pairs[0]
            
            # Test: enfant vers parent (devrait donner 50%)
            score_child_to_parent = self.corrector.get_score(parent, child)
            print(f"🔼 {child} → {parent} : {score_child_to_parent}%")
            
            # Test: parent vers enfant (devrait donner 25%)
            score_parent_to_child = self.corrector.get_score(child, parent)
            print(f"🔽 {parent} → {child} : {score_parent_to_child}%")
            
            # Au moins un des deux devrait avoir un score > 0
            self.assertTrue(score_child_to_parent > 0 or score_parent_to_child > 0)
    
    def test_unrelated_concepts(self):
        """Test concepts non reliés"""
        concepts = list(self.corrector.concepts.keys())
        if len(concepts) >= 2:
            # Prendre deux concepts au hasard et espérer qu'ils ne soient pas reliés
            concept1, concept2 = concepts[0], concepts[-1]
            if concept1 != concept2:
                score = self.corrector.get_score(concept1, concept2)
                print(f"🔀 {concept1} vs {concept2} : {score}%")
                # Le score peut être 0, 25, 50 ou 100 selon la relation
                self.assertIn(score, [0, 25, 50, 100])
    
    def test_nonexistent_concepts(self):
        """Test avec concepts inexistants"""
        score = self.corrector.get_score("CONCEPT_INEXISTANT", "AUTRE_INEXISTANT")
        self.assertEqual(score, 0)
        print("✅ Concepts inexistants = 0%")
    
    def test_explain_functionality(self):
        """Test de la fonction d'explication"""
        concepts = list(self.corrector.concepts.keys())
        if concepts:
            concept = concepts[0]
            explanation = self.corrector.explain(concept, concept)
            self.assertIn("Score: 100%", explanation)
            self.assertIn("Exact match", explanation)
            print(f"💬 Explication: {explanation}")

if __name__ == '__main__':
    print("🧪 === TESTS DU MOTEUR DE CORRECTION ECG ===")
    unittest.main(verbosity=2)
