"""
Extracteur RDF/XML → JSON pour ontologie ECG WebProtégé
Parse le format RDF/XML de WebProtégé

Auteur: Dr. Grégoire + GitHub Copilot BMAD
Date: 2026-01-10
"""

import xml.etree.ElementTree as ET
import json
from pathlib import Path
from collections import defaultdict


class RDFOWLExtractor:
    """Extrait poids et territoires depuis RDF/XML"""
    
    def __init__(self, owl_path: str):
        self.owl_path = Path(owl_path)
        self.tree = None
        self.root = None
        
        # Namespaces RDF/XML
        self.ns = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'owl': 'http://www.w3.org/2002/07/owl#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'skos': 'http://www.w3.org/2004/02/skos/core#'
        }
        
        # Structures de sortie
        self.classes_labels = {}  # IRI → {'fr': label, 'en': label}
        self.classes_altlabels = defaultdict(list)  # IRI → [altLabel1, altLabel2, ...]
        self.classes_hierarchy = {}  # IRI enfant → IRI parent
        self.weight_iris = {}  # IRI des 4 classes de poids
        self.classe_weights = {}  # IRI classe → IRI weight
        self.territoire_electrodes = defaultdict(list)
        self.classe_territoires = defaultdict(list)  # IRI classe → [IRI territoire1, IRI territoire2, ...]
        self.classe_findings = defaultdict(list)  # 🆕 IRI classe → [IRI finding1, finding2, ...] (requiresFinding)
        self.classe_excludes = defaultdict(list)  # 🆕 IRI classe → [ID exclus1, exclus2, ...] (annotation "exclut")
        self.territory_metadata = {}  # 🆕 IRI classe → {importance, may_have_territory, may_have_mirror}
        self.classe_voisins = defaultdict(list)  # 🆕 IRI classe → [IRI voisin1, voisin2, ...] (relation voisin)
        self.classe_origin_structure = defaultdict(list)  # 🆕 IRI classe → [IRI structure1, structure2, ...] (hasOriginStructure)
        self.classe_ecg_morphology = defaultdict(list)  # 🆕 IRI classe → [IRI morphology1, morphology2, ...] (hasECGMorphology)
        self.classe_morphology_inversion = {}  # 🆕 IRI classe → bool (requires_morphology_inversion)
        
        # IRIs des propriétés (trouvées dans le fichier)
        self.hasweight_iri = "http://webprotege.stanford.edu/R91SX26q028zwTknzSKDZUj"
        self.haselectrode_iri = "http://webprotege.stanford.edu/RBNXrhQkzAvi9hGX9yqhyRF"
        self.hasterritory_iri = "http://webprotege.stanford.edu/R86MFl68gsSAS3kHPEgghC3"
        self.requiresfinding_iri = "http://webprotege.stanford.edu/R7w5XngTituGN8Nt6R834WB"  # 🆕 ecg:requiresFinding
        self.excludes_iri = "http://webprotege.stanford.edu/Rgkbf3QYLEo9sJtKMJFyFW"  # 🆕 ecg:exclut (ObjectProperty)
        self.voisin_iri = "http://webprotege.stanford.edu/RixvaKPBrDKpuR4W2Z7ppX"  # 🆕 ecg:voisin (ObjectProperty)
        self.origin_structure_iri = "http://webprotege.stanford.edu/R8EpeA2cxOPJQ7nwwuht2D2"  # 🆕 hasOriginStructure
        self.ecg_morphology_iri = "http://webprotege.stanford.edu/RBAc9OvdrWdtL7GDUKcc90J"  # 🆕 hasECGMorphology
        self.morphology_inversion_iri = "http://webprotege.stanford.edu/RDHNwOilqvHGM16VJLMkaOh"  # 🆕 requires_morphology_inversion
        
        # 🆕 IRIs des annotation properties pour métadonnées territoire
        self.importance_territoire_iri = "http://webprotege.stanford.edu/RBiXCmVuqDW3Kzzg8N1v6i3"  # importanceTerritoire
        self.mayhave_territory_iri = "http://webprotege.stanford.edu/RvQtNXH9Cp7Ss5k9ocYaZD"  # mayHaveTerritory
        self.mayhave_mirror_iri = "http://webprotege.stanford.edu/R81WX84pmfiju3JOXA5ub0A"  # mayHaveMirror
        
    def load(self):
        """Charge le fichier OWL"""
        print(f"📖 Chargement: {self.owl_path}")
        ET.register_namespace('rdf', self.ns['rdf'])
        ET.register_namespace('owl', self.ns['owl'])
        ET.register_namespace('rdfs', self.ns['rdfs'])
        
        self.tree = ET.parse(self.owl_path)
        self.root = self.tree.getroot()
        print("✅ Ontologie chargée")
        
    def extract_labels(self):
        """Extrait tous les labels rdfs:label et skos:altLabel"""
        print("\n🏷️ Extraction labels et synonymes...")
        
        # Parcourir toutes les classes OWL
        for owl_class in self.root.findall('.//owl:Class', self.ns):
            iri = owl_class.get('{%s}about' % self.ns['rdf'])
            if not iri:
                continue
                
            # Labels principaux (rdfs:label)
            labels = {}
            for label_elem in owl_class.findall('rdfs:label', self.ns):
                lang = label_elem.get('{http://www.w3.org/XML/1998/namespace}lang', 'fr')
                label_text = label_elem.text
                if label_text:
                    labels[lang] = label_text
                
            if labels:
                self.classes_labels[iri] = labels
            
            # Labels alternatifs (skos:altLabel) - SYNONYMES
            for altlabel_elem in owl_class.findall('skos:altLabel', self.ns):
                lang = altlabel_elem.get('{http://www.w3.org/XML/1998/namespace}lang', 'fr')
                altlabel_text = altlabel_elem.text
                if altlabel_text:  # Accepter toutes les langues (fr, en, etc.)
                    self.classes_altlabels[iri].append(altlabel_text)
            
            # Hiérarchie (rdfs:subClassOf direct - pas restriction)
            for subclass_elem in owl_class.findall('rdfs:subClassOf', self.ns):
                parent_iri = subclass_elem.get('{%s}resource' % self.ns['rdf'])
                if parent_iri:  # subClassOf direct (pas une restriction)
                    self.classes_hierarchy[iri] = parent_iri
                
        print(f"  ✅ {len(self.classes_labels)} classes avec labels")
        print(f"  ✅ {len(self.classes_altlabels)} classes avec synonymes (skos:altLabel)")
        print(f"  ✅ {len(self.classes_hierarchy)} relations parent-enfant")
        
    def extract_weight_classes(self):
        """Identifie les 4 classes de poids (Urgent, Majeur, Moyen, Descriptif)"""
        print("\n⚖️ Identification classes de poids...")
        
        weight_keywords = {
            'urgent': 4,
            'majeur': 3,
            'moyen': 2,
            'descriptif': 1
        }
        
        for iri, labels in self.classes_labels.items():
            label_fr = labels.get('fr', '').lower()
            for keyword, weight in weight_keywords.items():
                if label_fr == keyword:
                    self.weight_iris[iri] = weight
                    print(f"    {label_fr.capitalize()} (poids {weight}): {iri[-20:]}")
                    
        print(f"  ✅ {len(self.weight_iris)} classes de poids trouvées")
        
    def extract_weights(self):
        """Extrait les relations hasWeight via restrictions OWL"""
        print("\n⚖️ Extraction poids (hasWeight via restrictions)...")
        
        count = 0
        # Parcourir toutes les classes
        for owl_class in self.root.findall('.//owl:Class', self.ns):
            class_iri = owl_class.get('{%s}about' % self.ns['rdf'])
            if not class_iri:
                continue
                
            # Chercher les restrictions rdfs:subClassOf > owl:Restriction
            for subclass in owl_class.findall('rdfs:subClassOf', self.ns):
                restriction = subclass.find('owl:Restriction', self.ns)
                if restriction is None:
                    continue
                    
                # Vérifier si c'est une restriction hasWeight
                on_property = restriction.find('owl:onProperty', self.ns)
                if on_property is None:
                    continue
                    
                property_iri = on_property.get('{%s}resource' % self.ns['rdf'])
                if property_iri != self.hasweight_iri:
                    continue
                    
                # Récupérer la valeur (someValuesFrom)
                some_values = restriction.find('owl:someValuesFrom', self.ns)
                if some_values is None:
                    continue
                    
                weight_iri = some_values.get('{%s}resource' % self.ns['rdf'])
                if weight_iri in self.weight_iris:
                    self.classe_weights[class_iri] = weight_iri
                    count += 1
                    
        print(f"  ✅ {count} classes avec poids extraits")
    
    def inherit_weights(self):
        """Hérite les poids des parents pour classes sans hasWeight explicite"""
        print("\n🧬 Héritage poids depuis parents...")
        
        inherited_count = 0
        max_depth = 10  # Protection contre boucles infinies
        
        # Pour chaque classe qui n'a pas de poids
        for class_iri in self.classes_labels.keys():
            if class_iri in self.classe_weights:
                continue  # A déjà un poids explicite
                
            # Remonter la hiérarchie pour trouver un parent avec poids
            current_iri = class_iri
            depth = 0
            
            while depth < max_depth:
                parent_iri = self.classes_hierarchy.get(current_iri)
                if not parent_iri:
                    break  # Pas de parent
                    
                if parent_iri in self.classe_weights:
                    # Parent a un poids, on l'hérite
                    self.classe_weights[class_iri] = self.classe_weights[parent_iri]
                    inherited_count += 1
                    break
                    
                # Continuer à remonter
                current_iri = parent_iri
                depth += 1
        
        print(f"  ✅ {inherited_count} classes ont hérité du poids de leur parent")
        print(f"  ✅ Total classes avec poids: {len(self.classe_weights)}")
    
    def build_parent_children_map(self):
        """Construit la map parent → [enfants] pour les implications"""
        print("\n👨‍👧‍👦 Construction map parent → enfants...")
        
        parent_children = {}
        
        # Inverser la hiérarchie : enfant→parent devient parent→[enfants]
        for child_iri, parent_iri in self.classes_hierarchy.items():
            if parent_iri not in parent_children:
                parent_children[parent_iri] = []
            parent_children[parent_iri].append(child_iri)
        
        print(f"  ✅ {len(parent_children)} concepts ont des enfants")
        
        return parent_children
        
    def extract_territoires(self):
        """Extrait les relations hasElectrode"""
        print("\n🗺️ Extraction territoires (hasElectrode)...")
        
        count = 0
        # Parcourir toutes les classes
        for owl_class in self.root.findall('.//owl:Class', self.ns):
            class_iri = owl_class.get('{%s}about' % self.ns['rdf'])
            if not class_iri:
                continue
                
            # Chercher les restrictions rdfs:subClassOf > owl:Restriction
            for subclass in owl_class.findall('rdfs:subClassOf', self.ns):
                restriction = subclass.find('owl:Restriction', self.ns)
                if restriction is None:
                    continue
                    
                # Vérifier si c'est une restriction hasElectrode
                on_property = restriction.find('owl:onProperty', self.ns)
                if on_property is None:
                    continue
                    
                property_iri = on_property.get('{%s}resource' % self.ns['rdf'])
                if property_iri != self.haselectrode_iri:
                    continue
                    
                # Récupérer la valeur (someValuesFrom)
                some_values = restriction.find('owl:someValuesFrom', self.ns)
                if some_values is None:
                    continue
                    
                electrode_iri = some_values.get('{%s}resource' % self.ns['rdf'])
                
                # Récupérer le nom du territoire
                territoire_label = self.classes_labels.get(class_iri, {}).get('fr', '')
                electrode_label = self.classes_labels.get(electrode_iri, {}).get('fr', '')
                
                if territoire_label and electrode_label:
                    self.territoire_electrodes[territoire_label].append(electrode_label)
                    count += 1
                    
        print(f"  ✅ {count} relations territoire-électrode extraites")
        
    def extract_concept_territoires(self):
        """Extrait les relations hasTerritory (concepts → territoires)"""
        print("\n🗺️ Extraction relations hasTerritory (concepts → territoires)...")
        
        count = 0
        # Parcourir toutes les classes
        for owl_class in self.root.findall('.//owl:Class', self.ns):
            class_iri = owl_class.get('{%s}about' % self.ns['rdf'])
            if not class_iri:
                continue
                
            # Chercher les restrictions rdfs:subClassOf > owl:Restriction
            for subclass in owl_class.findall('rdfs:subClassOf', self.ns):
                restriction = subclass.find('owl:Restriction', self.ns)
                if restriction is None:
                    continue
                    
                # Vérifier si c'est une restriction hasTerritory
                on_property = restriction.find('owl:onProperty', self.ns)
                if on_property is None:
                    continue
                    
                property_iri = on_property.get('{%s}resource' % self.ns['rdf'])
                if property_iri != self.hasterritory_iri:
                    continue
                    
                # Récupérer la valeur (someValuesFrom)
                some_values = restriction.find('owl:someValuesFrom', self.ns)
                if some_values is None:
                    continue
                    
                territoire_iri = some_values.get('{%s}resource' % self.ns['rdf'])
                
                # Stocker la relation
                if territoire_iri:
                    self.classe_territoires[class_iri].append(territoire_iri)
                    count += 1
                    
        print(f"  ✅ {count} relations hasTerritory extraites")
        
    def extract_requires_findings(self):
        """Extrait les relations ecg:requiresFinding (concepts → findings descripteurs)"""
        print("\n🎯 Extraction relations requiresFinding (concepts → descripteurs)...")
        
        count = 0
        # Parcourir toutes les classes
        for owl_class in self.root.findall('.//owl:Class', self.ns):
            class_iri = owl_class.get('{%s}about' % self.ns['rdf'])
            if not class_iri:
                continue
                
            # Chercher les restrictions rdfs:subClassOf > owl:Restriction
            for subclass in owl_class.findall('rdfs:subClassOf', self.ns):
                restriction = subclass.find('owl:Restriction', self.ns)
                if restriction is None:
                    continue
                    
                # Vérifier si c'est une restriction requiresFinding
                on_property = restriction.find('owl:onProperty', self.ns)
                if on_property is None:
                    continue
                    
                property_iri = on_property.get('{%s}resource' % self.ns['rdf'])
                if property_iri != self.requiresfinding_iri:
                    continue
                    
                # Récupérer la valeur (someValuesFrom)
                some_values = restriction.find('owl:someValuesFrom', self.ns)
                if some_values is None:
                    continue
                    
                finding_iri = some_values.get('{%s}resource' % self.ns['rdf'])
                
                # Stocker la relation
                if finding_iri:
                    self.classe_findings[class_iri].append(finding_iri)
                    count += 1
                    
        print(f"  ✅ {count} relations requiresFinding extraites")
    
    def extract_excludes(self):
        """Extrait les relations ecg:exclut (ObjectProperty restrictions)"""
        print("\n🚫 Extraction relations d'exclusion (ecg:exclut ObjectProperty)...")
        
        count = 0
        # Parcourir toutes les classes
        for owl_class in self.root.findall('.//owl:Class', self.ns):
            class_iri = owl_class.get('{%s}about' % self.ns['rdf'])
            if not class_iri:
                continue
                
            # Chercher les restrictions rdfs:subClassOf > owl:Restriction
            for subclass in owl_class.findall('rdfs:subClassOf', self.ns):
                restriction = subclass.find('owl:Restriction', self.ns)
                if restriction is None:
                    continue
                    
                # Vérifier si c'est une restriction exclut
                on_property = restriction.find('owl:onProperty', self.ns)
                if on_property is None:
                    continue
                    
                property_iri = on_property.get('{%s}resource' % self.ns['rdf'])
                if property_iri != self.excludes_iri:
                    continue
                    
                # Récupérer la valeur (someValuesFrom)
                some_values = restriction.find('owl:someValuesFrom', self.ns)
                if some_values is None:
                    continue
                    
                excluded_iri = some_values.get('{%s}resource' % self.ns['rdf'])
                
                # Stocker la relation
                if excluded_iri:
                    self.classe_excludes[class_iri].append(excluded_iri)
                    count += 1
                    
        print(f"  ✅ {count} relations d'exclusion extraites")
        
        # Afficher quelques exemples
        if self.classe_excludes:
            print("\n  📋 Exemples d'exclusions trouvées:")
            for class_iri, excludes_iris in list(self.classe_excludes.items())[:3]:
                class_label = self.classes_labels.get(class_iri, {}).get('fr', 'Sans nom')
                excluded_labels = []
                for excluded_iri in excludes_iris:
                    excluded_label = self.classes_labels.get(excluded_iri, {}).get('fr', 'Sans nom')
                    excluded_labels.append(excluded_label)
                print(f"     • {class_label}: exclut {', '.join(excluded_labels)}")
    
    def extract_neighbor_relations(self):
        """
        🆕 Extrait les relations de voisinage (ecg:voisin ObjectProperty)
        Utilisé uniquement pour le scoring (bonus si territoire voisin mentionné)
        """
        print("\n🔗 Extraction relations de voisinage (ecg:voisin)...")
        
        count = 0
        # Parcourir toutes les classes
        for owl_class in self.root.findall('.//owl:Class', self.ns):
            class_iri = owl_class.get('{%s}about' % self.ns['rdf'])
            if not class_iri:
                continue
                
            # Chercher les restrictions rdfs:subClassOf > owl:Restriction
            for subclass in owl_class.findall('rdfs:subClassOf', self.ns):
                restriction = subclass.find('owl:Restriction', self.ns)
                if restriction is None:
                    continue
                    
                # Vérifier si c'est une restriction voisin
                on_property = restriction.find('owl:onProperty', self.ns)
                if on_property is None:
                    continue
                    
                property_iri = on_property.get('{%s}resource' % self.ns['rdf'])
                if property_iri != self.voisin_iri:
                    continue
                    
                # Récupérer la valeur (hasValue pour relation directe)
                has_value = restriction.find('owl:hasValue', self.ns)
                if has_value is None:
                    # Essayer someValuesFrom si hasValue n'existe pas
                    some_values = restriction.find('owl:someValuesFrom', self.ns)
                    if some_values is None:
                        continue
                    neighbor_iri = some_values.get('{%s}resource' % self.ns['rdf'])
                else:
                    neighbor_iri = has_value.get('{%s}resource' % self.ns['rdf'])
                
                # Stocker la relation (bidirectionnelle)
                if neighbor_iri:
                    self.classe_voisins[class_iri].append(neighbor_iri)
                    count += 1
                    
        print(f"  ✅ {count} relations de voisinage extraites")
        
        # Afficher quelques exemples
        if self.classe_voisins:
            print("\n  📋 Exemples de voisinages trouvés:")
            for class_iri, neighbor_iris in list(self.classe_voisins.items())[:5]:
                class_label = self.classes_labels.get(class_iri, {}).get('fr', 'Sans nom')
                neighbor_labels = []
                for neighbor_iri in neighbor_iris:
                    neighbor_label = self.classes_labels.get(neighbor_iri, {}).get('fr', 'Sans nom')
                    neighbor_labels.append(neighbor_label)
                if neighbor_labels:
                    print(f"     • {class_label} ↔ {', '.join(neighbor_labels)}")
    
    def extract_origin_structure(self):
        """🆕 Extrait les relations hasOriginStructure (origine anatomique)"""
        print("\n🏗️ Extraction hasOriginStructure (origine anatomique)...")
        
        count = 0
        for owl_class in self.root.findall('.//owl:Class', self.ns):
            class_iri = owl_class.get('{%s}about' % self.ns['rdf'])
            if not class_iri:
                continue
                
            # Chercher les restrictions rdfs:subClassOf > owl:Restriction
            for subclass in owl_class.findall('rdfs:subClassOf', self.ns):
                restriction = subclass.find('owl:Restriction', self.ns)
                if restriction is None:
                    continue
                    
                on_property = restriction.find('owl:onProperty', self.ns)
                if on_property is None:
                    continue
                    
                property_iri = on_property.get('{%s}resource' % self.ns['rdf'])
                if property_iri != self.origin_structure_iri:
                    continue
                    
                # Récupérer la structure d'origine
                some_values = restriction.find('owl:someValuesFrom', self.ns)
                if some_values is None:
                    has_value = restriction.find('owl:hasValue', self.ns)
                    if has_value is None:
                        continue
                    structure_iri = has_value.get('{%s}resource' % self.ns['rdf'])
                else:
                    structure_iri = some_values.get('{%s}resource' % self.ns['rdf'])
                
                if structure_iri:
                    self.classe_origin_structure[class_iri].append(structure_iri)
                    count += 1
                    
        print(f"  ✅ {count} relations hasOriginStructure extraites")
        
        # Afficher exemples
        if self.classe_origin_structure:
            print("\n  📋 Exemples d'origine anatomique:")
            for class_iri, structure_iris in list(self.classe_origin_structure.items())[:5]:
                class_label = self.classes_labels.get(class_iri, {}).get('fr', 'Sans nom')
                structure_labels = [self.classes_labels.get(s, {}).get('fr', 'Sans nom') for s in structure_iris]
                print(f"     • {class_label} → {', '.join(structure_labels)}")
    
    def extract_ecg_morphology(self):
        """🆕 Extrait les relations hasECGMorphology (morphologie ECG)"""
        print("\n📊 Extraction hasECGMorphology (morphologie ECG)...")
        
        count = 0
        for owl_class in self.root.findall('.//owl:Class', self.ns):
            class_iri = owl_class.get('{%s}about' % self.ns['rdf'])
            if not class_iri:
                continue
                
            # Chercher les restrictions rdfs:subClassOf > owl:Restriction
            for subclass in owl_class.findall('rdfs:subClassOf', self.ns):
                restriction = subclass.find('owl:Restriction', self.ns)
                if restriction is None:
                    continue
                    
                on_property = restriction.find('owl:onProperty', self.ns)
                if on_property is None:
                    continue
                    
                property_iri = on_property.get('{%s}resource' % self.ns['rdf'])
                if property_iri != self.ecg_morphology_iri:
                    continue
                    
                # Récupérer la morphologie
                some_values = restriction.find('owl:someValuesFrom', self.ns)
                if some_values is None:
                    has_value = restriction.find('owl:hasValue', self.ns)
                    if has_value is None:
                        continue
                    morphology_iri = has_value.get('{%s}resource' % self.ns['rdf'])
                else:
                    morphology_iri = some_values.get('{%s}resource' % self.ns['rdf'])
                
                if morphology_iri:
                    self.classe_ecg_morphology[class_iri].append(morphology_iri)
                    count += 1
                    
        print(f"  ✅ {count} relations hasECGMorphology extraites")
        
        # Afficher exemples
        if self.classe_ecg_morphology:
            print("\n  📋 Exemples de morphologie ECG:")
            for class_iri, morphology_iris in list(self.classe_ecg_morphology.items())[:5]:
                class_label = self.classes_labels.get(class_iri, {}).get('fr', 'Sans nom')
                morphology_labels = [self.classes_labels.get(m, {}).get('fr', 'Sans nom') for m in morphology_iris]
                print(f"     • {class_label} → {', '.join(morphology_labels)}")
    
    def extract_morphology_inversion(self):
        """🆕 Extrait les annotations requires_morphology_inversion"""
        print("\n🔄 Extraction requires_morphology_inversion...")
        
        count = 0
        for owl_class in self.root.findall('.//owl:Class', self.ns):
            class_iri = owl_class.get('{%s}about' % self.ns['rdf'])
            if not class_iri:
                continue
            
            # Chercher l'annotation requires_morphology_inversion
            for annotation in owl_class.findall(f'{{http://webprotege.stanford.edu/}}RDHNwOilqvHGM16VJLMkaOh'):
                value = annotation.text
                if value and value.lower() in ['true', '1', 'yes']:
                    self.classe_morphology_inversion[class_iri] = True
                    count += 1
                elif value:
                    self.classe_morphology_inversion[class_iri] = False
                    
        print(f"  ✅ {count} annotations d'inversion trouvées")
        
        if self.classe_morphology_inversion:
            print("\n  📋 Concepts avec inversion de morphologie:")
            for class_iri, requires_inversion in self.classe_morphology_inversion.items():
                if requires_inversion:
                    class_label = self.classes_labels.get(class_iri, {}).get('fr', 'Sans nom')
                    print(f"     • {class_label} (nécessite inversion)")
    
    def extract_territory_metadata(self):
        """
        🆕 Extrait les métadonnées de territoire pour concepts (STEMI, ESV, etc.)
        - importanceTerritoire : critique/importante/optionnelle
        - mayHaveTerritory : true/false
        - mayHaveMirror : true/false
        """
        print("\n🗺️ Extraction métadonnées territoire...")
        
        count = 0
        for owl_class in self.root.findall('.//owl:Class', self.ns):
            class_iri = owl_class.get('{%s}about' % self.ns['rdf'])
            if not class_iri:
                continue
            
            # Extraire les 3 annotation properties
            importance = None
            may_have_territory = None
            may_have_mirror = None
            
            # Parcourir les éléments enfants pour trouver les annotations
            for child in owl_class:
                # Vérifier si c'est une de nos annotation properties
                if child.tag.endswith(self.importance_territoire_iri.split('/')[-1]):
                    importance = child.text
                elif child.tag.endswith(self.mayhave_territory_iri.split('/')[-1]):
                    may_have_territory = child.text
                elif child.tag.endswith(self.mayhave_mirror_iri.split('/')[-1]):
                    may_have_mirror = child.text
            
            # Stocker si au moins une métadonnée trouvée
            if importance or may_have_territory or may_have_mirror:
                self.territory_metadata[class_iri] = {
                    'importance': importance,
                    'may_have_territory': may_have_territory == 'true' if may_have_territory else False,
                    'may_have_mirror': may_have_mirror == 'true' if may_have_mirror else False
                }
                count += 1
        
        print(f"  ✅ {count} concepts avec métadonnées territoire")
        
        # Afficher exemples (focus STEMI)
        if self.territory_metadata:
            print("\n  📋 Exemples de métadonnées trouvées:")
            for class_iri, metadata in list(self.territory_metadata.items())[:5]:
                class_label = self.classes_labels.get(class_iri, {}).get('fr', 'Sans nom')
                importance = metadata.get('importance', 'non défini')
                has_territory = "✓" if metadata.get('may_have_territory') else "✗"
                has_mirror = "✓" if metadata.get('may_have_mirror') else "✗"
                print(f"     • {class_label}")
                print(f"       - Importance: {importance}")
                print(f"       - Territoire: {has_territory} | Miroir: {has_mirror}")
    
    def generate_json(self, output_path="data/ontology_from_owl.json"):
        """Génère le fichier JSON final"""
        print(f"\n💾 Génération JSON: {output_path}")
        
        # Construire la map parent → enfants
        parent_children = self.build_parent_children_map()
        
        # Charger ontologie existante pour synonymes
        existing_path = Path("data/epic1_ontology_mapping.json")
        existing_synonymes = {}
        if existing_path.exists():
            with open(existing_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_synonymes = existing_data.get('concept_mappings', {})
                
        # Construire concept_categories
        concept_categories = {
            "DIAGNOSTIC_URGENT": {"poids": 4, "couleur_ui": "#D32F2F", "concepts": []},
            "DIAGNOSTIC_MAJEUR": {"poids": 3, "couleur_ui": "#F57C00", "concepts": []},
            "SIGNE_ECG_PATHOLOGIQUE": {"poids": 2, "couleur_ui": "#FFA726", "concepts": []},
            "DESCRIPTEUR_ECG": {"poids": 1, "couleur_ui": "#66BB6A", "concepts": []}
        }
        
        # Mapping poids → catégorie
        weight_to_category = {
            4: "DIAGNOSTIC_URGENT",
            3: "DIAGNOSTIC_MAJEUR",
            2: "SIGNE_ECG_PATHOLOGIQUE",
            1: "DESCRIPTEUR_ECG"
        }
        
        # Remplir les concepts par catégorie
        concept_mappings = {}
        for class_iri, weight_iri in self.classe_weights.items():
            weight = self.weight_iris.get(weight_iri)
            if not weight:
                continue
                
            category = weight_to_category.get(weight)
            if not category:
                continue
                
            labels = self.classes_labels.get(class_iri, {})
            label_fr = labels.get('fr', '')
            label_en = labels.get('en', '')
            
            if not label_fr:
                continue
                
            # Ajouter à la catégorie
            concept_id = label_fr.upper().replace(' ', '_').replace('-', '_')
            concept_categories[category]["concepts"].append({
                "ontology_id": concept_id,
                "concept_name": label_fr,
                "label_en": label_en if label_en else label_fr,
                "poids": weight
            })
            
            # Ajouter au mapping (fusionner avec synonymes existants + altLabels)
            existing_concept = existing_synonymes.get(concept_id, {})
            
            # Combiner synonymes : existants + altLabels de l'ontologie
            all_synonymes = list(existing_concept.get('synonymes', []))
            altlabels = self.classes_altlabels.get(class_iri, [])
            for altlabel in altlabels:
                if altlabel not in all_synonymes and altlabel != label_fr:
                    all_synonymes.append(altlabel)
            
            # 🆕 CONSTRUIRE IMPLICATIONS depuis requiresFinding (PRIORITAIRE)
            implications = []
            if class_iri in self.classe_findings:
                # Ce concept a des requiresFinding → ajouter leurs noms comme implications
                for finding_iri in self.classe_findings[class_iri]:
                    finding_labels = self.classes_labels.get(finding_iri, {})
                    finding_name = finding_labels.get('fr', '')
                    if finding_name and finding_name != label_fr:
                        implications.append(finding_name)
            
            # Ajouter aussi enfants hiérarchiques (rdfs:subClassOf) comme implications secondaires
            if class_iri in parent_children:
                for child_iri in parent_children[class_iri]:
                    child_labels = self.classes_labels.get(child_iri, {})
                    child_name = child_labels.get('fr', '')
                    if child_name and child_name != label_fr and child_name not in implications:
                        implications.append(child_name)
            
            # Ajouter implications existantes (si pertinentes)
            existing_implications = existing_concept.get('implications', [])
            for impl in existing_implications:
                if impl not in implications:
                    implications.append(impl)
            
            # 🆕 CONSTRUIRE TERRITOIRES depuis hasTerritory
            territoires_possibles = []
            if class_iri in self.classe_territoires:
                for territoire_iri in self.classe_territoires[class_iri]:
                    territoire_labels = self.classes_labels.get(territoire_iri, {})
                    territoire_name = territoire_labels.get('fr', '')
                    if territoire_name:
                        territoires_possibles.append(territoire_name)
            
            # 🆕 CONSTRUIRE EXCLUSIONS depuis ObjectProperty "exclut"
            excludes = []
            if class_iri in self.classe_excludes:
                for excluded_iri in self.classe_excludes[class_iri]:
                    excluded_labels = self.classes_labels.get(excluded_iri, {})
                    excluded_name = excluded_labels.get('fr', '')
                    if excluded_name:
                        excludes.append(excluded_name)
            
            # 🆕 CONSTRUIRE VOISINS depuis ObjectProperty "voisin" (pour scoring seulement)
            voisins = []
            if class_iri in self.classe_voisins:
                for voisin_iri in self.classe_voisins[class_iri]:
                    voisin_labels = self.classes_labels.get(voisin_iri, {})
                    voisin_name = voisin_labels.get('fr', '')
                    if voisin_name:
                        voisins.append(voisin_name)
            
            # 🆕 CONSTRUIRE MÉTADONNÉES TERRITOIRE
            territory_metadata = None
            if class_iri in self.territory_metadata:
                metadata = self.territory_metadata[class_iri]
                territory_metadata = {
                    "importance": metadata.get('importance'),
                    "may_have_territory": metadata.get('may_have_territory', False),
                    "may_have_mirror": metadata.get('may_have_mirror', False),
                    "required_territory": metadata.get('importance') == 'critique'  # Dérivé automatiquement
                }
            
            # 🆕 CONSTRUIRE ORIGINE ANATOMIQUE depuis hasOriginStructure
            origin_structures = []
            if class_iri in self.classe_origin_structure:
                for structure_iri in self.classe_origin_structure[class_iri]:
                    structure_labels = self.classes_labels.get(structure_iri, {})
                    structure_name = structure_labels.get('fr', '')
                    if structure_name:
                        origin_structures.append(structure_name)
            
            # 🆕 CONSTRUIRE MORPHOLOGIE ECG depuis hasECGMorphology
            ecg_morphologies = []
            if class_iri in self.classe_ecg_morphology:
                for morphology_iri in self.classe_ecg_morphology[class_iri]:
                    morphology_labels = self.classes_labels.get(morphology_iri, {})
                    morphology_name = morphology_labels.get('fr', '')
                    if morphology_name:
                        ecg_morphologies.append(morphology_name)
            
            # 🆕 VÉRIFIER INVERSION DE MORPHOLOGIE
            requires_morphology_inversion = self.classe_morphology_inversion.get(class_iri, False)
            
            concept_mappings[concept_id] = {
                "concept_name": label_fr,
                "synonymes": all_synonymes,
                "implications": implications,  # 🆕 Maintenant avec enfants hiérarchiques !
                "territoires_possibles": territoires_possibles,  # 🆕 Territoires liés au concept !
                "excludes": excludes,  # 🆕 Liste des concepts exclus (IDs)
                "voisins": voisins,  # 🆕 Liste des territoires voisins (pour scoring bonus)
                "territory_metadata": territory_metadata,  # 🆕 Métadonnées pour sélection territoire
                "origin_structures": origin_structures,  # 🆕 Origines anatomiques (hasOriginStructure)
                "ecg_morphologies": ecg_morphologies,  # 🆕 Morphologies ECG (hasECGMorphology)
                "requires_morphology_inversion": requires_morphology_inversion,  # 🆕 Drapeau inversion
                "poids": weight,
                "categorie": category
            }
            
        # Construire territoires_ecg
        territoires_ecg = {}
        for territoire, electrodes in self.territoire_electrodes.items():
            territoire_id = territoire.upper().replace(' ', '_')
            territoires_ecg[territoire_id] = {
                "nom": territoire,
                "electrodes": list(set(electrodes))  # Dédupliquer
            }
            
        # 🆕 Construire la hiérarchie pour le JSON
        hierarchy_map = {}
        for child_iri, parent_iri in self.classes_hierarchy.items():
            child_labels = self.classes_labels.get(child_iri, {})
            parent_labels = self.classes_labels.get(parent_iri, {})
            child_id = child_labels.get('fr', '').upper().replace(' ', '_').replace("'", '_').replace('-', '_')
            parent_id = parent_labels.get('fr', '').upper().replace(' ', '_').replace("'", '_').replace('-', '_')
            if child_id and parent_id:
                hierarchy_map[child_id] = parent_id
        
        # Structure finale
        output = {
            "concept_categories": concept_categories,
            "territoires_ecg": territoires_ecg,
            "concept_mappings": concept_mappings,
            "concept_hierarchy": hierarchy_map,  # 🆕 Hiérarchie enfant → parent
            "scoring_rules": {
                "bonus_diagnostic_principal": 0.15,
                "formule": "(Σ poids validés) / (Σ poids attendus) × 100 + bonus"
            },
            "metadata": {
                "source": "WebProtégé OWL Ontology",
                "extraction_date": "2026-01-10",
                "total_concepts": sum(len(cat["concepts"]) for cat in concept_categories.values()),
                "total_territoires": len(territoires_ecg)
            }
        }
        
        # Sauvegarder
        output_path = Path(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            
        print(f"✅ JSON généré: {output_path}")
        
        return output


def main():
    import sys
    
    # Chemin par défaut ou argument
    owl_path = sys.argv[1] if len(sys.argv) > 1 else "data/epi1c_dataset/BrYOzRZIu7jQTwmfcGsi35.owl"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "data/ontology_from_owl.json"
    
    # Affichage
    print(f"📂 Input OWL: {owl_path}")
    print(f"📂 Output JSON: {Path(output_path).absolute()}")
    print("\n🔄 CONVERSION RDF/XML → JSON")
    print("=" * 60)
    
    # Extraction
    extractor = RDFOWLExtractor(owl_path)
    extractor.load()
    extractor.extract_labels()
    extractor.extract_weight_classes()
    extractor.extract_weights()
    extractor.inherit_weights()  # NOUVEAU : Héritage des poids
    extractor.extract_territoires()
    extractor.extract_concept_territoires()  # 🆕 NOUVEAU : Extraction hasTerritory
    extractor.extract_requires_findings()  # 🎯 NOUVEAU : Extraction ecg:requiresFinding
    extractor.extract_origin_structure()  # 🆕 NOUVEAU : Extraction hasOriginStructure
    extractor.extract_ecg_morphology()  # 🆕 NOUVEAU : Extraction hasECGMorphology
    extractor.extract_morphology_inversion()  # 🆕 NOUVEAU : Extraction requires_morphology_inversion
    result = extractor.generate_json(output_path)
    
    # Résumé
    print("\n" + "=" * 60)
    print("✅ CONVERSION TERMINÉE")
    print(f"📊 Statistiques:")
    print(f"   - {result['metadata']['total_concepts']} concepts avec poids")
    print(f"   - {result['metadata']['total_territoires']} territoires")
    print(f"   - {len(result['concept_categories']['DIAGNOSTIC_URGENT']['concepts'])} diagnostics URGENTS")
    print(f"   - {len(result['concept_categories']['DIAGNOSTIC_MAJEUR']['concepts'])} diagnostics MAJEURS")
    print(f"   - {len(result['concept_categories']['SIGNE_ECG_PATHOLOGIQUE']['concepts'])} signes ECG")
    print(f"   - {len(result['concept_categories']['DESCRIPTEUR_ECG']['concepts'])} descripteurs")
    print("\n🎉 SUCCÈS - Ontologie convertie !")
    

if __name__ == "__main__":
    main()
