"""
🗺️ Territory Resolver - Résolution des territoires pour sélection contextuelle
Résout les territoires possibles pour un concept donné de manière générique

Auteur: Grégoire + BMAD
Date: 2026-01-13
"""

from typing import Dict, List, Optional, Tuple


def get_children_of_concept(concept_id: str, ontology: Dict) -> List[str]:
    """
    Récupère tous les enfants directs d'un concept dans la hiérarchie
    
    Args:
        concept_id: ID du concept parent (ex: "LOCALISATION_IDM")
        ontology: Ontologie complète chargée depuis JSON
        
    Returns:
        Liste des noms des concepts enfants directs
    """
    hierarchy = ontology.get('concept_hierarchy', {})
    concept_mappings = ontology.get('concept_mappings', {})
    
    children_names = []
    
    # Parcourir la hiérarchie pour trouver les enfants directs
    for child_id, parent_id in hierarchy.items():
        if parent_id == concept_id:
            child_data = concept_mappings.get(child_id, {})
            child_name = child_data.get('concept_name')
            if child_name:
                children_names.append(child_name)
    
    return sorted(children_names)


def get_all_descendants_recursive(concept_id: str, ontology: Dict, visited: Optional[set] = None) -> List[str]:
    """
    Récupère TOUS les descendants d'un concept de manière récursive
    
    Descend dans toute la hiérarchie pour trouver les concepts "feuilles"
    (ceux sans enfants) afin d'afficher uniquement les territoires finaux.
    
    Args:
        concept_id: ID du concept parent (ex: "LOCALISATION_IDM")
        ontology: Ontologie complète chargée depuis JSON
        visited: Ensemble des IDs déjà visités (évite boucles infinies)
        
    Returns:
        Liste des noms de tous les descendants (concepts feuilles uniquement)
        
    Exemple:
        LOCALISATION_ESV
          └─ VENTRICULE_DROIT
              ├─ PAROI_LIBRE_DU_VENTRICULE_DROIT  ← feuille
              └─ PAROI_INFÉRIEURE_DU_VENTRICULE_DROIT  ← feuille
        
        Retourne: ["Paroi inférieure du ventricule droit", "Paroi libre du ventricule droit"]
        (sans "Ventricule droit" car c'est un parent intermédiaire)
    """
    if visited is None:
        visited = set()
    
    # Éviter boucles infinies
    if concept_id in visited:
        return []
    visited.add(concept_id)
    
    hierarchy = ontology.get('concept_hierarchy', {})
    concept_mappings = ontology.get('concept_mappings', {})
    
    all_descendants = []
    
    # Trouver les enfants directs
    direct_children_ids = [child_id for child_id, parent_id in hierarchy.items() if parent_id == concept_id]
    
    if not direct_children_ids:
        # Pas d'enfants → c'est une feuille, ajouter son nom
        concept_data = concept_mappings.get(concept_id, {})
        concept_name = concept_data.get('concept_name')
        if concept_name:
            all_descendants.append(concept_name)
    else:
        # A des enfants → descendre récursivement dans chaque enfant
        for child_id in direct_children_ids:
            child_descendants = get_all_descendants_recursive(child_id, ontology, visited.copy())
            all_descendants.extend(child_descendants)
    
    return sorted(list(set(all_descendants)))


def resolve_territories(concept_data: Dict, ontology: Dict) -> Tuple[List[str], List[str]]:
    """
    Résout les territoires possibles pour un concept de manière récursive
    
    Args:
        concept_data: Données du concept (depuis concept_mappings)
        ontology: Ontologie complète
        
    Returns:
        Tuple (territoires_principaux, territoires_miroir)
        
    Exemple:
        Pour STEMI:
        - territoires_possibles: ["Localisation IDM", "Miroir"]
        - Résout en: ([Antérieur, Inférieur, ...], [Antérieur, Inférieur, ...])
    """
    concept_mappings = ontology.get('concept_mappings', {})
    territoires_possibles = concept_data.get('territoires_possibles', [])
    
    territoires_principaux = []
    territoires_miroir = []
    
    for territoire_name in territoires_possibles:
        # Trouver l'ID du territoire dans l'ontologie
        territoire_id = None
        for tid, tdata in concept_mappings.items():
            if tdata.get('concept_name') == territoire_name:
                territoire_id = tid
                break
        
        if not territoire_id:
            continue
        
        # Si c'est "Miroir", résoudre ses territoires (qui pointent vers Localisation IDM)
        if territoire_name == "Miroir":
            miroir_data = concept_mappings.get(territoire_id, {})
            miroir_territories = miroir_data.get('territoires_possibles', [])
            
            # Résoudre récursivement les territoires du miroir
            for miroir_terr_name in miroir_territories:
                miroir_terr_id = None
                for tid, tdata in concept_mappings.items():
                    if tdata.get('concept_name') == miroir_terr_name:
                        miroir_terr_id = tid
                        break
                
                if miroir_terr_id:
                    # Récupérer TOUS les descendants (récursif) au lieu des enfants directs
                    descendants = get_all_descendants_recursive(miroir_terr_id, ontology)
                    territoires_miroir.extend(descendants)
        
        else:
            # Pour les autres territoires (Localisation IDM, Localisation ESV, etc.)
            # Récupérer TOUS les descendants récursifs au lieu des enfants directs
            descendants = get_all_descendants_recursive(territoire_id, ontology)
            territoires_principaux.extend(descendants)
    
    # Dédupliquer et trier
    territoires_principaux = sorted(list(set(territoires_principaux)))
    territoires_miroir = sorted(list(set(territoires_miroir)))
    
    return territoires_principaux, territoires_miroir


def should_show_territory_selector(concept_data: Dict) -> Tuple[bool, bool, str]:
    """
    Détermine si on doit afficher le sélecteur de territoire pour un concept
    
    Args:
        concept_data: Données du concept
        
    Returns:
        Tuple (show_selector, is_required, importance_level)
        - show_selector: True si sélecteur doit être affiché
        - is_required: True si territoire obligatoire
        - importance_level: "critique", "importante", "optionnelle", ou None
    """
    metadata = concept_data.get('territory_metadata')
    
    if not metadata:
        return False, False, None
    
    may_have_territory = metadata.get('may_have_territory', False)
    importance = metadata.get('importance')
    is_required = metadata.get('required_territory', False)
    
    # Afficher sélecteur si le concept peut avoir un territoire
    show_selector = may_have_territory
    
    return show_selector, is_required, importance


def should_show_mirror_selector(concept_data: Dict) -> bool:
    """
    Détermine si on doit afficher le sélecteur de miroir
    
    Args:
        concept_data: Données du concept
        
    Returns:
        True si sélecteur de miroir doit être affiché
    """
    metadata = concept_data.get('territory_metadata')
    
    if not metadata:
        return False
    
    return metadata.get('may_have_mirror', False)


def get_territory_config(concept_name: str, ontology: Dict) -> Optional[Dict]:
    """
    Récupère la configuration complète des territoires pour un concept
    
    Args:
        concept_name: Nom du concept (ex: "STEMI", "Syndrome coronarien...")
        ontology: Ontologie complète
        
    Returns:
        Dict avec la configuration ou None si concept non trouvé
        {
            'concept_name': str,
            'show_territory_selector': bool,
            'show_mirror_selector': bool,
            'is_required': bool,
            'importance': str,
            'territories': List[str],
            'mirrors': List[str]
        }
    """
    concept_mappings = ontology.get('concept_mappings', {})
    
    # Chercher le concept par nom ou synonyme
    concept_data = None
    for cid, cdata in concept_mappings.items():
        if cdata.get('concept_name', '').lower() == concept_name.lower():
            concept_data = cdata
            break
        # Chercher aussi dans les synonymes
        synonyms = [s.lower() for s in cdata.get('synonymes', [])]
        if concept_name.lower() in synonyms:
            concept_data = cdata
            break
    
    if not concept_data:
        return None
    
    # Vérifier si sélecteur nécessaire
    show_territory, is_required, importance = should_show_territory_selector(concept_data)
    show_mirror = should_show_mirror_selector(concept_data)
    
    if not show_territory:
        return None
    
    # Résoudre les territoires
    territories, mirrors = resolve_territories(concept_data, ontology)
    
    return {
        'concept_name': concept_data.get('concept_name'),
        'show_territory_selector': show_territory,
        'show_mirror_selector': show_mirror,
        'is_required': is_required,
        'importance': importance,
        'territories': territories,
        'mirrors': mirrors
    }
