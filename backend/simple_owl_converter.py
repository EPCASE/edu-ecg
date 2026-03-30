"""
Convertisseur OWL → JSON MINIMALISTE avec rdflib
Version robuste, sans owlready2, basée sur conventions SKOS standard

Auteur: BMad Team
Date: 2026-01-11
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

try:
    from rdflib import Graph, Namespace, RDF, RDFS, OWL
    from rdflib.namespace import SKOS
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False
    print("⚠️ rdflib non installé. Installation: pip install rdflib")


# Namespaces
ECG = Namespace("http://www.example.org/ecg#")


class SimpleOWLConverter:
    """
    Convertisseur minimaliste OWL→JSON basé sur CONVENTIONS, pas sur code
    
    Conventions attendues dans WebProtégé :
    - rdfs:label = nom officiel
    - skos:altLabel = synonymes (standard SKOS!)
    - rdfs:subClassOf = hiérarchie (catégorie)
    - ecg:hasWeight = poids (optionnel, déduit si absent)
    """
    
    def __init__(self, owl_path: str):
        self.owl_path = Path(owl_path)
        self.g = Graph()
        self.output = {
            "ontology_version": "3.0-skos-standard",
            "source_owl": str(self.owl_path),
            "conversion_date": None,
            "concept_categories": {},
            "metadata": {}
        }
        
        # Catégories avec propriétés par défaut
        self.categories = {
            "Diagnostic_Urgent": {"poids": 4, "urgence": "immediate", "couleur": "#D32F2F"},
            "Diagnostic_Majeur": {"poids": 3, "urgence": "differee", "couleur": "#F57C00"},
            "Signe_ECG_Pathologique": {"poids": 2, "urgence": "surveillance", "couleur": "#FFA726"},
            "Descripteur_ECG": {"poids": 1, "urgence": "contexte", "couleur": "#66BB6A"}
        }
    
    def load(self):
        """Charge le graphe RDF depuis OWL"""
        if not RDFLIB_AVAILABLE:
            raise ImportError("rdflib requis: pip install rdflib")
        
        if not self.owl_path.exists():
            raise FileNotFoundError(f"Fichier introuvable: {self.owl_path}")
        
        print(f"📖 Chargement: {self.owl_path}")
        self.g.parse(self.owl_path, format="xml")
        print(f"✅ {len(self.g)} triplets RDF chargés")
    
    def extract_all(self):
        """Extraction complète par catégorie"""
        print("\n🔍 Extraction des concepts par catégorie...")
        
        for category_name, props in self.categories.items():
            category_uri = ECG[category_name]
            
            # Trouver tous les concepts de cette catégorie
            concepts = []
            
            for concept in self.g.subjects(RDFS.subClassOf, category_uri):
                concept_data = self._extract_concept(concept, category_name, props["poids"])
                if concept_data:
                    concepts.append(concept_data)
            
            # Stocker dans output
            if concepts:
                self.output["concept_categories"][category_name] = {
                    "poids": props["poids"],
                    "urgence": props["urgence"],
                    "couleur_ui": props["couleur"],
                    "concepts": concepts
                }
                print(f"  ✅ {category_name}: {len(concepts)} concepts")
    
    def _extract_concept(self, uri, category: str, default_weight: int) -> Dict:
        """Extrait un concept individuel avec TOUTES ses métadonnées SKOS"""
        
        # Label officiel (obligatoire)
        label = self._get_label(uri)
        if not label:
            return None  # Ignorer concepts sans label
        
        # Synonymes via skos:altLabel (STANDARD !)
        synonyms = [str(syn) for syn in self.g.objects(uri, SKOS.altLabel)]
        
        # Poids (déduit si absent)
        weight = self._get_weight(uri, default_weight)
        
        # Définition SKOS
        definition = self._get_value(uri, SKOS.definition)
        
        # Note pédagogique
        note = self._get_value(uri, RDFS.comment)
        
        # Territoire (custom property)
        territoire = self._get_value(uri, ECG.hasTerritory)
        
        return {
            "concept_name": label,
            "ontology_id": str(uri).split("#")[-1],  # Dernier segment de l'URI
            "category": category,
            "weight": weight,
            "synonyms": synonyms,
            "definition": definition,
            "note_pedagogique": note,
            "territoire": territoire
        }
    
    def _get_label(self, uri) -> str:
        """Récupère rdfs:label (priorité: @fr > @en > sans langue)"""
        # Essayer label français
        for label in self.g.objects(uri, RDFS.label):
            if label.language == 'fr':
                return str(label)
        
        # Fallback: premier label trouvé
        for label in self.g.objects(uri, RDFS.label):
            return str(label)
        
        return None
    
    def _get_value(self, uri, predicate) -> str:
        """Récupère une valeur simple (premier objet trouvé)"""
        for obj in self.g.objects(uri, predicate):
            return str(obj)
        return None
    
    def _get_weight(self, uri, default: int) -> int:
        """Récupère poids ou utilise valeur par défaut"""
        weight_str = self._get_value(uri, ECG.hasWeight)
        if weight_str:
            try:
                return int(weight_str)
            except ValueError:
                pass
        return default
    
    def add_metadata(self):
        """Ajoute métadonnées de conversion"""
        total_concepts = sum(
            len(cat["concepts"]) 
            for cat in self.output["concept_categories"].values()
        )
        
        total_synonyms = sum(
            sum(len(c["synonyms"]) for c in cat["concepts"])
            for cat in self.output["concept_categories"].values()
        )
        
        self.output["conversion_date"] = datetime.now().isoformat()
        self.output["metadata"] = {
            "total_concepts": total_concepts,
            "total_categories": len(self.output["concept_categories"]),
            "total_synonyms": total_synonyms,
            "source": "WebProtégé (Stanford) - SKOS standard",
            "parser": "rdflib (lightweight)",
            "conventions": "SKOS altLabel pour synonymes"
        }
        
        print(f"\n📊 Statistiques:")
        print(f"   • {total_concepts} concepts")
        print(f"   • {total_synonyms} synonymes (skos:altLabel)")
    
    def convert(self, output_path: str = None) -> Dict:
        """Conversion complète"""
        print("🔄 CONVERSION OWL → JSON (rdflib + SKOS)")
        print("=" * 60)
        
        self.load()
        self.extract_all()
        self.add_metadata()
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.output, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ TERMINÉ: {output_file}")
        
        return self.output


def main():
    """Point d'entrée"""
    import sys
    
    owl_path = r"C:\Users\Administrateur\bmad\BrYOzRZIu7jQTwmfcGsi35.owl"
    json_path = "data/ontology_from_owl.json"
    
    if len(sys.argv) > 1:
        owl_path = sys.argv[1]
    if len(sys.argv) > 2:
        json_path = sys.argv[2]
    
    try:
        converter = SimpleOWLConverter(owl_path)
        result = converter.convert(json_path)
        
        print("\n🎉 SUCCÈS - Ontologie prête!")
        print(f"\n💡 Prochaine étape:")
        print(f"   streamlit run frontend/ecg_session_builder.py --server.port 8502")
        return 0
    
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
