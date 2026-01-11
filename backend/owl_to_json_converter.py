"""
Convertisseur OWL → JSON pour l'ontologie ECG
Extrait territoires, électrodes, poids et catégories depuis ontologie.owx

Auteur: Dr. Grégoire + GitHub Copilot BMAD
Date: 2026-01-10
"""

import json
from pathlib import Path
from typing import Dict, List, Any

try:
    from owlready2 import get_ontology, Thing
    OWLREADY_AVAILABLE = True
except ImportError:
    OWLREADY_AVAILABLE = False
    print("⚠️ owlready2 non installé. Utilisez: pip install owlready2")


class OWLToJSONConverter:
    """Convertit ontologie OWL en JSON pour scoring pondéré"""
    
    def __init__(self, owl_path: str):
        """
        Args:
            owl_path: Chemin vers fichier .owl ou .owx
        """
        self.owl_path = Path(owl_path)
        self.onto = None
        self.output = {
            "ontology_version": "2.0-weighted-owl",
            "source_owl": str(self.owl_path),
            "description": "Ontologie ECG extraite depuis OWL - Source de vérité médicale",
            "conversion_date": None,
            "concept_categories": {},
            "territoires_ecg": {},
            "concept_mappings": {},
            "implication_rules": {},
            "scoring_rules": {},
            "metadata": {}
        }
    
    def load_ontology(self):
        """Charge l'ontologie OWL"""
        if not OWLREADY_AVAILABLE:
            raise ImportError("owlready2 requis: pip install owlready2")
        
        if not self.owl_path.exists():
            raise FileNotFoundError(f"Ontologie introuvable: {self.owl_path}")
        
        print(f"📖 Chargement ontologie: {self.owl_path}")
        self.onto = get_ontology(f"file://{self.owl_path.absolute()}").load()
        print(f"✅ Ontologie chargée: {len(list(self.onto.classes()))} classes")
    
    def extract_categories(self):
        """Extrait les catégories de concepts (URGENT, MAJEUR, SIGNE, DESCRIPTEUR)"""
        print("\n🏷️ Extraction catégories...")
        
        # Chercher classes: Diagnostic_Urgent, Diagnostic_Majeur, Signe_ECG, Descripteur_ECG
        categories_mapping = {
            "Diagnostic_Urgent": {"poids": 4, "urgence": "immediate", "couleur": "#D32F2F"},
            "Diagnostic_Majeur": {"poids": 3, "urgence": "differee", "couleur": "#F57C00"},
            "Signe_ECG_Pathologique": {"poids": 2, "urgence": "surveillance", "couleur": "#FFA726"},
            "Descripteur_ECG": {"poids": 1, "urgence": "contexte", "couleur": "#66BB6A"}
        }
        
        for class_name, properties in categories_mapping.items():
            try:
                owl_class = self.onto[class_name]
                if owl_class:
                    self.output["concept_categories"][class_name] = {
                        "poids": properties["poids"],
                        "urgence": properties["urgence"],
                        "couleur_ui": properties["couleur"],
                        "concepts": [c.name for c in owl_class.descendants() if c != owl_class]
                    }
                    print(f"  ✅ {class_name}: {len(self.output['concept_categories'][class_name]['concepts'])} concepts")
            except:
                print(f"  ⚠️ Classe {class_name} non trouvée dans OWL")
    
    def extract_territoires(self):
        """Extrait territoires ECG et leurs électrodes"""
        print("\n🗺️ Extraction territoires ECG...")
        
        # Chercher classe Territoire_ECG
        try:
            territoire_class = self.onto["Territoire_ECG"]
            
            for territoire in territoire_class.descendants():
                if territoire == territoire_class:
                    continue
                
                territoire_data = {
                    "electrodes": [],
                    "artere_principale": None,
                    "synonymes": [],
                    "paroi_vg": None
                }
                
                # Extraire propriétés
                if hasattr(territoire, "hasElectrode"):
                    territoire_data["electrodes"] = [e.name for e in territoire.hasElectrode]
                
                if hasattr(territoire, "hasArtery"):
                    territoire_data["artere_principale"] = str(territoire.hasArtery[0]) if territoire.hasArtery else None
                
                if hasattr(territoire, "synonymes"):
                    territoire_data["synonymes"] = territoire.synonymes
                
                if hasattr(territoire, "paroi"):
                    territoire_data["paroi_vg"] = str(territoire.paroi[0]) if territoire.paroi else None
                
                self.output["territoires_ecg"][territoire.name] = territoire_data
                print(f"  ✅ {territoire.name}: {len(territoire_data['electrodes'])} électrodes")
        
        except:
            print("  ⚠️ Classe Territoire_ECG non trouvée - à créer dans Protégé")
    
    def extract_concepts(self):
        """Extrait tous les concepts ECG avec leurs métadonnées"""
        print("\n📋 Extraction concepts ECG...")
        
        try:
            concept_class = self.onto["Concept_ECG"]
            
            for concept in concept_class.descendants():
                if concept == concept_class:
                    continue
                
                concept_data = {
                    "ontology_id": concept.name,
                    "categorie": self._get_category(concept),
                    "poids": self._get_weight(concept),
                    "territoire": None,
                    "synonymes": [],
                    "implications": [],
                    "urgence_clinique": None,
                    "note_pedagogique": None,
                    # NOUVEAUX CHAMPS (backward compatible)
                    "requires_findings": [],  # 🆕 ecg:requiresFindings
                    "electrodes": None        # 🆕 ecg:hasElectrode
                }
                
                # Extraire propriétés OWL
                if hasattr(concept, "hasTerritory"):
                    concept_data["territoire"] = concept.hasTerritory[0].name if concept.hasTerritory else None
                
                # NOUVEAU: Extraire requiresFindings (implications diagnostiques)
                if hasattr(concept, "requiresFindings"):
                    concept_data["requires_findings"] = [f.name for f in concept.requiresFindings]
                
                # NOUVEAU: Extraire électrodes directement depuis concept (si applicable)
                if hasattr(concept, "hasElectrode"):
                    concept_data["electrodes"] = [e.name for e in concept.hasElectrode]
                
                # Extraire synonymes depuis hasSynonym (propriété custom)
                if hasattr(concept, "hasSynonym"):
                    concept_data["synonymes"] = list(concept.hasSynonym)
                
                # NOUVEAU: Extraire synonymes depuis skos:altLabel (SKOS standard)
                if hasattr(concept, "altLabel"):
                    skos_synonyms = [str(label) for label in concept.altLabel]
                    # Fusionner sans doublons
                    concept_data["synonymes"] = list(set(concept_data["synonymes"] + skos_synonyms))
                
                # Extraire implications (propriété custom impliesSign)
                if hasattr(concept, "impliesSign"):
                    concept_data["implications"] = [s.name for s in concept.impliesSign]
                
                if hasattr(concept, "urgence"):
                    concept_data["urgence_clinique"] = str(concept.urgence[0]) if concept.urgence else None
                
                if hasattr(concept, "note"):
                    concept_data["note_pedagogique"] = str(concept.note[0]) if concept.note else None
                
                # Utiliser label comme clé si disponible
                concept_key = concept.label[0] if hasattr(concept, "label") and concept.label else concept.name
                self.output["concept_mappings"][concept_key] = concept_data
            
            print(f"  ✅ {len(self.output['concept_mappings'])} concepts extraits")
        
        except Exception as e:
            print(f"  ⚠️ Erreur extraction concepts: {e}")
    
    def _get_category(self, concept) -> str:
        """Détermine la catégorie d'un concept"""
        for ancestor in concept.ancestors():
            if ancestor.name in ["Diagnostic_Urgent", "Diagnostic_Majeur", "Signe_ECG_Pathologique", "Descripteur_ECG"]:
                return ancestor.name
        return "Descripteur_ECG"
    
    def _get_weight(self, concept) -> int:
        """Extrait le poids d'un concept"""
        if hasattr(concept, "hasWeight"):
            return int(concept.hasWeight[0]) if concept.hasWeight else 1
        
        # Poids par défaut selon catégorie
        category = self._get_category(concept)
        weights = {
            "Diagnostic_Urgent": 4,
            "Diagnostic_Majeur": 3,
            "Signe_ECG_Pathologique": 2,
            "Descripteur_ECG": 1
        }
        return weights.get(category, 1)
    
    def extract_implication_rules(self):
        """Extrait règles d'implication (diagnostic → signes auto-validés)"""
        print("\n🔗 Extraction règles d'implication...")
        
        for concept_key, concept_data in self.output["concept_mappings"].items():
            if concept_data["implications"]:
                self.output["implication_rules"][concept_data["ontology_id"]] = {
                    "auto_validate": concept_data["implications"],
                    "description": f"{concept_key} implique {', '.join(concept_data['implications'])}"
                }
        
        print(f"  ✅ {len(self.output['implication_rules'])} règles extraites")
    
    def add_scoring_rules(self):
        """Ajoute règles de scoring pondéré"""
        self.output["scoring_rules"] = {
            "version": "2.0-weighted-owl",
            "formule": "(Σ poids concepts validés) / (Σ poids concepts attendus) × 100",
            "bonus_diagnostic_principal": {
                "actif": True,
                "condition": "Au moins 1 concept poids ≥3 identifié",
                "bonus_pourcentage": 15,
                "description": "Bonus +15% si diagnostic urgent/majeur identifié"
            },
            "seuils_validation": {
                "excellent": 90,
                "tres_bien": 80,
                "bien": 70,
                "passable": 60,
                "insuffisant": 50
            }
        }
    
    def add_metadata(self):
        """Ajoute métadonnées de conversion"""
        from datetime import datetime
        
        self.output["conversion_date"] = datetime.now().isoformat()
        self.output["metadata"] = {
            "total_concepts": len(self.output["concept_mappings"]),
            "total_territoires": len(self.output["territoires_ecg"]),
            "total_categories": len(self.output["concept_categories"]),
            "total_regles_implications": len(self.output["implication_rules"]),
            "source": "OWL ontology (Protégé validated)",
            "robustesse": "Médicale - Source unique de vérité"
        }
    
    def convert(self, output_path: str = None) -> Dict[str, Any]:
        """
        Convertit OWL → JSON
        
        Args:
            output_path: Chemin de sortie JSON (optionnel)
        
        Returns:
            dict: Ontologie en format JSON
        """
        print("🔄 CONVERSION OWL → JSON")
        print("=" * 60)
        
        self.load_ontology()
        self.extract_categories()
        self.extract_territoires()
        self.extract_concepts()
        self.extract_implication_rules()
        self.add_scoring_rules()
        self.add_metadata()
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.output, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ CONVERSION TERMINÉE")
            print(f"📄 Fichier JSON: {output_file}")
            print(f"📊 Statistiques:")
            print(f"   - {self.output['metadata']['total_concepts']} concepts")
            print(f"   - {self.output['metadata']['total_territoires']} territoires")
            print(f"   - {self.output['metadata']['total_regles_implications']} règles d'implication")
        
        return self.output


def main():
    """Fonction principale - Exemple d'utilisation"""
    import sys
    
    # Chemin par défaut
    owl_path = Path(__file__).parent.parent / "data" / "ontologie.owx"
    output_path = Path(__file__).parent.parent / "data" / "ontology_from_owl.json"
    
    # Permet de passer chemin en argument
    if len(sys.argv) > 1:
        owl_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    
    print(f"📂 Input OWL: {owl_path}")
    print(f"📂 Output JSON: {output_path}")
    print()
    
    try:
        converter = OWLToJSONConverter(str(owl_path))
        result = converter.convert(str(output_path))
        
        print("\n🎉 SUCCÈS - Ontologie convertie et prête pour l'application")
        return 0
    
    except FileNotFoundError as e:
        print(f"\n❌ ERREUR: {e}")
        print("\n💡 INSTRUCTIONS:")
        print("1. Éditez data/ontologie.owx dans Protégé")
        print("2. Ajoutez classes Territoire_ECG, Diagnostic_Urgent, etc.")
        print("3. Exportez et relancez ce script")
        return 1
    
    except ImportError:
        print("\n❌ ERREUR: owlready2 non installé")
        print("\n💡 Installation:")
        print("   pip install owlready2")
        return 1
    
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
