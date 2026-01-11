"""
Extracteur simplifié OWL → JSON pour ontologie ECG
Parse le XML OWL directement sans owlready2

Auteur: Dr. Grégoire + GitHub Copilot BMAD
Date: 2026-01-10
"""

import xml.etree.ElementTree as ET
import json
from pathlib import Path
from collections import defaultdict


class SimpleOWLExtractor:
    """Extrait poids et territoires depuis OWL XML"""
    
    def __init__(self, owl_path: str):
        self.owl_path = Path(owl_path)
        self.tree = None
        self.root = None
        self.ns = {}
        
        # Structures de sortie
        self.classes_labels = {}  # IRI → label
        self.classes_weights = {}  # label → weight
        self.territoire_electrodes = defaultdict(list)  # territoire → [electrodes]
        self.concept_categories = defaultdict(list)  # catégorie → [concepts]
        
    def load(self):
        """Charge le fichier OWL"""
        print(f"📖 Chargement: {self.owl_path}")
        self.tree = ET.parse(self.owl_path)
        self.root = self.tree.getroot()
        
        # Namespaces OWL
        self.ns = {
            'owl': 'http://www.w3.org/2002/07/owl#',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'xsd': 'http://www.w3.org/2001/XMLSchema#'
        }
        
        print(f"✅ Ontologie chargée")
    
    def extract_labels(self):
        """Extrait les labels (noms lisibles) des classes"""
        print("\n🏷️ Extraction labels...")
        
        # Chercher toutes les annotations rdfs:label
        for annotation in self.root.findall('.//rdfs:label', self.ns):
            # Trouver la classe parente
            class_elem = annotation.find('..')
            if class_elem is not None and class_elem.get('IRI'):
                iri = class_elem.get('IRI')
                label = annotation.text
                self.classes_labels[iri] = label
        
        # Alternative: chercher AnnotationAssertion
        for annot_assert in self.root.findall('.//owl:AnnotationAssertion', self.ns):
            prop = annot_assert.find('owl:AnnotationProperty', self.ns)
            if prop is not None and 'label' in prop.get('IRI', ''):
                iri_elem = annot_assert.find('.//owl:Class', self.ns)
                if iri_elem is not None:
                    iri = iri_elem.get('IRI')
                    literal = annot_assert.find('owl:Literal', self.ns)
                    if literal is not None and literal.text:
                        self.classes_labels[iri] = literal.text
        
        print(f"  ✅ {len(self.classes_labels)} labels trouvés")
    
    def extract_weights(self):
        """Extrait les poids hasWeight"""
        print("\n⚖️ Extraction poids (hasWeight)...")
        
        # Chercher data property assertions pour hasWeight
        for data_prop in self.root.findall('.//owl:DataPropertyAssertion', self.ns):
            prop = data_prop.find('owl:DataProperty', self.ns)
            
            if prop is not None and 'hasWeight' in prop.get('IRI', '').lower():
                # Trouver la classe cible
                class_elem = data_prop.find('.//owl:NamedIndividual', self.ns)
                if class_elem is None:
                    class_elem = data_prop.find('.//owl:Class', self.ns)
                
                if class_elem is not None:
                    iri = class_elem.get('IRI')
                    label = self.classes_labels.get(iri, iri)
                    
                    # Extraire la valeur du poids
                    literal = data_prop.find('owl:Literal', self.ns)
                    if literal is not None and literal.text:
                        try:
                            weight = int(literal.text)
                            self.classes_weights[label] = weight
                            print(f"    {label}: poids {weight}")
                        except ValueError:
                            pass
        
        print(f"  ✅ {len(self.classes_weights)} poids extraits")
    
    def extract_territoires(self):
        """Extrait territoires et leurs électrodes (hasElectrode)"""
        print("\n🗺️ Extraction territoires (hasElectrode)...")
        
        # Chercher object property assertions pour hasElectrode
        for obj_prop in self.root.findall('.//owl:ObjectPropertyAssertion', self.ns):
            prop = obj_prop.find('owl:ObjectProperty', self.ns)
            
            if prop is not None and 'haselectrode' in prop.get('IRI', '').lower():
                # Territoire source
                source = obj_prop.find('.//owl:NamedIndividual[@rdf:about]', self.ns)
                if source is None:
                    source = obj_prop.find('.//owl:Class', self.ns)
                
                # Électrode cible
                target_elems = obj_prop.findall('.//owl:NamedIndividual', self.ns)
                if len(target_elems) >= 2:
                    target = target_elems[1]
                elif len(target_elems) == 1:
                    target = target_elems[0]
                else:
                    target = None
                
                if source is not None and target is not None:
                    territoire_iri = source.get('IRI') or source.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
                    electrode_iri = target.get('IRI') or target.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
                    
                    territoire_label = self.classes_labels.get(territoire_iri, territoire_iri)
                    electrode_label = self.classes_labels.get(electrode_iri, electrode_iri)
                    
                    if territoire_label and electrode_label:
                        self.territoire_electrodes[territoire_label].append(electrode_label)
                        print(f"    {territoire_label} → {electrode_label}")
        
        print(f"  ✅ {len(self.territoire_electrodes)} territoires avec électrodes")
    
    def categorize_by_weight(self):
        """Catégorise les concepts selon leur poids"""
        print("\n📊 Catégorisation par poids...")
        
        for concept, weight in self.classes_weights.items():
            if weight == 4:
                self.concept_categories["DIAGNOSTIC_URGENT"].append(concept)
            elif weight == 3:
                self.concept_categories["DIAGNOSTIC_MAJEUR"].append(concept)
            elif weight == 2:
                self.concept_categories["SIGNE_ECG_PATHOLOGIQUE"].append(concept)
            elif weight == 1:
                self.concept_categories["DESCRIPTEUR_ECG"].append(concept)
        
        for cat, concepts in self.concept_categories.items():
            print(f"    {cat}: {len(concepts)} concepts")
    
    def generate_json(self, output_path: str):
        """Génère le JSON final"""
        print(f"\n💾 Génération JSON: {output_path}")
        
        from datetime import datetime
        
        # Charger l'ontologie mapping existante pour récupérer synonymes et implications
        existing_mapping = {}
        mapping_path = Path(self.owl_path).parent / "epic1_ontology_mapping.json"
        if mapping_path.exists():
            with open(mapping_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_mapping = existing_data.get("concept_mappings", {})
        
        # Structure de sortie
        output = {
            "ontology_version": "2.0-weighted-owl",
            "source_owl": str(self.owl_path),
            "description": "Ontologie ECG extraite depuis OWL - Validation médicale Dr. Grégoire",
            "conversion_date": datetime.now().isoformat(),
            
            "concept_categories": {
                "DIAGNOSTIC_URGENT": {
                    "poids": 4,
                    "urgence": "immediate",
                    "couleur_ui": "#D32F2F",
                    "concepts": self.concept_categories.get("DIAGNOSTIC_URGENT", [])
                },
                "DIAGNOSTIC_MAJEUR": {
                    "poids": 3,
                    "urgence": "differee",
                    "couleur_ui": "#F57C00",
                    "concepts": self.concept_categories.get("DIAGNOSTIC_MAJEUR", [])
                },
                "SIGNE_ECG_PATHOLOGIQUE": {
                    "poids": 2,
                    "urgence": "surveillance",
                    "couleur_ui": "#FFA726",
                    "concepts": self.concept_categories.get("SIGNE_ECG_PATHOLOGIQUE", [])
                },
                "DESCRIPTEUR_ECG": {
                    "poids": 1,
                    "urgence": "contexte",
                    "couleur_ui": "#66BB6A",
                    "concepts": self.concept_categories.get("DESCRIPTEUR_ECG", [])
                }
            },
            
            "territoires_ecg": {},
            "concept_mappings": {},
            "implication_rules": {},
            
            "scoring_rules": {
                "version": "2.0-weighted-owl",
                "formule": "(Σ poids concepts validés) / (Σ poids concepts attendus) × 100",
                "bonus_diagnostic_principal": {
                    "actif": True,
                    "condition": "Au moins 1 concept poids ≥3 identifié",
                    "bonus_pourcentage": 15
                }
            },
            
            "metadata": {
                "total_concepts": len(self.classes_weights),
                "total_territoires": len(self.territoire_electrodes),
                "total_labels": len(self.classes_labels),
                "source": "OWL ontology (Protégé validated by Dr. Grégoire)",
                "robustesse": "Médicale - Source unique de vérité"
            }
        }
        
        # Ajouter territoires
        for territoire, electrodes in self.territoire_electrodes.items():
            output["territoires_ecg"][territoire] = {
                "electrodes": electrodes,
                "artere_principale": None,  # À compléter manuellement si nécessaire
                "synonymes": [],
                "paroi_vg": None
            }
        
        # Ajouter concepts avec poids
        for concept, weight in self.classes_weights.items():
            concept_lower = concept.lower()
            
            # Récupérer données existantes si disponibles
            existing = existing_mapping.get(concept_lower, {})
            
            output["concept_mappings"][concept_lower] = {
                "ontology_id": existing.get("ontology_id", concept.upper().replace(" ", "_")),
                "categorie": self._get_category_by_weight(weight),
                "poids": weight,
                "territoire": None,
                "synonymes": existing.get("synonymes", []),
                "implications": existing.get("implications", []),
                "note": existing.get("note", "")
            }
            
            # Ajouter règles d'implication si existantes
            if existing.get("implications"):
                ont_id = output["concept_mappings"][concept_lower]["ontology_id"]
                output["implication_rules"][ont_id] = {
                    "auto_validate": existing["implications"],
                    "description": f"{concept} implique {', '.join(existing['implications'])}"
                }
        
        # Sauvegarder
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON généré: {output_path}")
        return output
    
    def _get_category_by_weight(self, weight: int) -> str:
        """Retourne la catégorie selon le poids"""
        if weight == 4:
            return "DIAGNOSTIC_URGENT"
        elif weight == 3:
            return "DIAGNOSTIC_MAJEUR"
        elif weight == 2:
            return "SIGNE_ECG_PATHOLOGIQUE"
        else:
            return "DESCRIPTEUR_ECG"
    
    def convert(self, output_path: str):
        """Pipeline complet de conversion"""
        print("🔄 CONVERSION OWL → JSON (Simple XML Parser)")
        print("=" * 60)
        
        self.load()
        self.extract_labels()
        self.extract_weights()
        self.extract_territoires()
        self.categorize_by_weight()
        result = self.generate_json(output_path)
        
        print("\n" + "=" * 60)
        print("✅ CONVERSION TERMINÉE")
        print(f"📊 Statistiques:")
        print(f"   - {result['metadata']['total_concepts']} concepts avec poids")
        print(f"   - {result['metadata']['total_territoires']} territoires")
        print(f"   - {result['metadata']['total_labels']} labels")
        
        return result


def main():
    """Point d'entrée"""
    import sys
    
    # Chemins par défaut
    owl_path = Path(__file__).parent.parent / "data" / "ontologie.owx"
    output_path = Path(__file__).parent.parent / "data" / "ontology_from_owl.json"
    
    if len(sys.argv) > 1:
        owl_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    
    print(f"📂 Input OWL: {owl_path}")
    print(f"📂 Output JSON: {output_path}")
    print()
    
    try:
        extractor = SimpleOWLExtractor(str(owl_path))
        extractor.convert(str(output_path))
        
        print("\n🎉 SUCCÈS - Ontologie convertie !")
        return 0
    
    except FileNotFoundError as e:
        print(f"\n❌ ERREUR: Fichier non trouvé - {e}")
        return 1
    
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
