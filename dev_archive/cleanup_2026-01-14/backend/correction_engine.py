# correction_engine.py

from owlready2 import get_ontology

class OntologyCorrector:
    def __init__(self, owl_path):
        self.onto = get_ontology(owl_path).load()
        
        # Dictionnaire des concepts avec leurs labels lisibles
        self.concepts = {}
        self.concept_labels = {}
        
        for cls in self.onto.classes():
            # Utiliser le label si disponible, sinon le nom
            label = cls.label.first() if cls.label else cls.name
            
            # Nettoyer le label (enlever préfixes, etc.)
            if label and isinstance(label, str):
                clean_label = label.replace('ECG_', '').replace('_', ' ')
                self.concepts[clean_label] = cls
                self.concept_labels[cls.name] = clean_label
            else:
                # Fallback sur le nom de classe
                clean_name = cls.name.replace('ECG_', '').replace('_', ' ')
                self.concepts[clean_name] = cls
                self.concept_labels[cls.name] = clean_name
    
    def get_concept_names(self):
        """Retourne la liste des noms de concepts lisibles pour l'interface"""
        return list(self.concepts.keys())

    def get_score(self, expected, user_input):
        """
        expected: str (nom du concept attendu)
        user_input: str (nom du concept proposé)
        return: int (score en %)
        """
        expected_cls = self.concepts.get(expected)
        user_cls = self.concepts.get(user_input)

        if not expected_cls or not user_cls:
            return 0

        if user_cls == expected_cls:
            return 100
        elif user_cls in expected_cls.ancestors():
            return 50
        elif expected_cls in user_cls.ancestors():
            return 25
        else:
            return 0

    def explain(self, expected, user_input):
        score = self.get_score(expected, user_input)
        reason = {
            100: "Exact match",
            50: "User input is a parent of expected concept",
            25: "User input is a child of expected concept",
            0: "Unrelated concept"
        }
        return f"Score: {score}% – {reason[score]}"

if __name__ == "__main__":
    corr = OntologyCorrector("data/ontology.owl")

    print(corr.explain("BlocDeBrancheDroit", "BlocDeBranche"))  # → 50%
    print(corr.explain("BlocDeBrancheDroit", "BlocDeBrancheGauche"))  # → 0%
    print(corr.explain("BlocDeBrancheDroit", "BlocDeBrancheDroit"))  # → 100%