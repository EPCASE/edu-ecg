"""
🛡️ Annotation Validator - Détection de Contradictions Ontologiques
Valide les annotations ECG contre les contradictions médicales

Auteur: Grégoire + BMAD Method
Date: 2026-01-13
Version: 1.0 - POC Phase 1
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ContradictionLevel(Enum):
    """Niveau de gravité de la contradiction"""
    CRITICAL = "critical"      # Impossible médicalement (ex: ECG normal + STEMI)
    WARNING = "warning"        # Inhabituel mais possible (ex: diag différentiel)
    INFO = "info"             # Information contextuelle


@dataclass
class Contradiction:
    """Représente une contradiction détectée entre concepts"""
    concept_a: str
    concept_b: str
    level: ContradictionLevel
    rule_name: str
    medical_reason: str
    suggestion: str
    
    def __repr__(self):
        return f"⚠️ {self.concept_a} ⊥ {self.concept_b}"


class AnnotationValidator:
    """
    Validateur intelligent basé sur l'ontologie
    
    Stratégie:
    1. Règles catégorielles (ECG normal vs pathologies)
    2. Exclusivité dans catégories (un seul rythme de base)
    3. Relations explicites (BBG ⊥ BBD)
    4. Contradictions quantitatives (brady vs tachy)
    """
    
    def __init__(self, ontology_mapping: Dict):
        """
        Args:
            ontology_mapping: Ontologie JSON chargée depuis ontology_from_owl.json
        """
        self.ontology = ontology_mapping
        self.concept_mappings = ontology_mapping.get('concept_mappings', {})
        self.categories = ontology_mapping.get('concept_categories', {})
        self.hierarchy = ontology_mapping.get('concept_hierarchy', {})  # 🆕 Hiérarchie enfant → parent
        
        # Index inverse: concept_name -> ontology_id
        self.concept_to_id = {}
        for ont_id, mapping in self.concept_mappings.items():
            concept_name = mapping.get('concept_name', '').lower()
            self.concept_to_id[concept_name] = ont_id
            
            # Ajouter aussi les synonymes
            for syn in mapping.get('synonymes', []):
                self.concept_to_id[syn.lower()] = ont_id
        
        logger.info(f"✅ AnnotationValidator initialisé avec {len(self.concept_mappings)} concepts")
    
    def validate(self, annotations: List[str]) -> List[Contradiction]:
        """
        Valide une liste d'annotations et retourne les contradictions
        
        Args:
            annotations: Liste de noms de concepts (ex: ["ECG normal", "Bloc de branche gauche"])
            
        Returns:
            Liste des contradictions détectées
        """
        if not annotations or len(annotations) < 2:
            return []  # Pas de contradiction possible avec 0 ou 1 concept
        
        contradictions = []
        
        # Convertir les annotations en IDs ontologiques
        concept_ids = self._resolve_concept_ids(annotations)
        
        # 🆕 Règle 0: Vérifier les exclusions depuis l'ontologie (PRIORITAIRE - source de vérité)
        contradictions.extend(self._check_ontology_excludes(concept_ids, annotations))
        
        # Règle 1: ECG normal exclut toute pathologie
        contradictions.extend(self._check_normal_ecg_rule(concept_ids, annotations))
        
        # Règle 2: Un seul rythme de base autorisé
        contradictions.extend(self._check_exclusive_rhythm_rule(concept_ids, annotations))
        
        # Règle 3: Blocs de branche mutuellement exclusifs
        contradictions.extend(self._check_branch_blocks_rule(concept_ids, annotations))
        
        # Règle 4: Contradictions quantitatives (brady/tachy, hypo/hyper)
        contradictions.extend(self._check_quantitative_contradictions(concept_ids, annotations))
        
        # Règle 5: Asystolie exclut tout autre rythme
        contradictions.extend(self._check_asystole_rule(concept_ids, annotations))
        
        # Règle 6: BAV complet exclut PR normal/court/long
        contradictions.extend(self._check_bav_complet_rule(concept_ids, annotations))
        
        logger.info(f"🔍 Validation: {len(annotations)} concepts → {len(contradictions)} contradictions")
        
        return contradictions
    
    def get_all_parents(self, ontology_id: str) -> List[str]:
        """
        Récupère tous les parents d'un concept (récursif)
        
        Args:
            ontology_id: L'ID du concept dans l'ontologie
            
        Returns:
            Liste des IDs parents (du plus proche au plus éloigné)
        """
        parents = []
        current = ontology_id
        
        # Remonter la hiérarchie (max 10 niveaux pour éviter boucles infinies)
        for _ in range(10):
            if current not in self.hierarchy:
                break
            parent = self.hierarchy[current]
            parents.append(parent)
            current = parent
        
        return parents
    
    def _resolve_concept_ids(self, annotations: List[str]) -> Dict[str, str]:
        """
        Convertit les noms de concepts en IDs ontologiques
        
        Returns:
            Dict {concept_name: ontology_id}
        """
        concept_ids = {}
        for annotation in annotations:
            ann_lower = annotation.lower().strip()
            ont_id = self.concept_to_id.get(ann_lower)
            if ont_id:
                concept_ids[annotation] = ont_id
            else:
                logger.warning(f"⚠️ Concept non trouvé dans l'ontologie: {annotation}")
        
        return concept_ids
    
    def _check_ontology_excludes(self, concept_ids: Dict[str, str], annotations: List[str]) -> List[Contradiction]:
        """
        🆕 Règle 0: Vérifier les exclusions explicites depuis l'ontologie OWL
        
        Cette méthode utilise le champ "excludes" de chaque concept dans l'ontologie.
        C'est la source de vérité médicale définie dans WebProtégé.
        
        Exemples:
        - Hypokaliémie exclut Hyperkaliémie
        - Absence d'onde P exclut Onde P normale
        - BBG exclut BBD (défini dans ontologie)
        
        Returns:
            Liste des contradictions basées sur les exclusions ontologiques
        """
        contradictions = []
        
        # Pour chaque paire de concepts annotés
        for name_a, id_a in concept_ids.items():
            # Récupérer la définition du concept dans l'ontologie
            concept_a_def = self.concept_mappings.get(id_a)
            if not concept_a_def:
                continue
            
            # Récupérer la liste des concepts exclus
            excludes = concept_a_def.get('excludes', [])
            if not excludes:
                continue  # Pas d'exclusions définies pour ce concept
            
            # Vérifier si un concept exclu est présent dans les annotations
            for name_b, id_b in concept_ids.items():
                if name_a == name_b:
                    continue  # Ne pas comparer avec soi-même
                
                concept_b_def = self.concept_mappings.get(id_b)
                if not concept_b_def:
                    continue
                
                concept_b_name = concept_b_def.get('concept_name', '')
                
                # Vérifier si concept_b est dans la liste des exclus de concept_a
                if concept_b_name in excludes:
                    # Déterminer le niveau de gravité basé sur la catégorie
                    category_a = concept_a_def.get('categorie', '')
                    category_b = concept_b_def.get('categorie', '')
                    
                    # CRITICAL si au moins un est URGENT ou MAJEUR
                    if 'URGENT' in category_a or 'URGENT' in category_b or \
                       'MAJEUR' in category_a or 'MAJEUR' in category_b:
                        level = ContradictionLevel.CRITICAL
                    else:
                        level = ContradictionLevel.WARNING
                    
                    contradictions.append(Contradiction(
                        concept_a=name_a,
                        concept_b=name_b,
                        level=level,
                        rule_name="ontology_explicit_exclusion",
                        medical_reason=f"Ces deux concepts s'excluent mutuellement selon l'ontologie médicale. "
                                      f"La présence simultanée de \"{name_a}\" et \"{name_b}\" est médicalement contradictoire.",
                        suggestion=f"Vérifiez le tracé ECG et choisissez soit \"{name_a}\" soit \"{name_b}\", "
                                  f"mais pas les deux. Consultez les définitions si nécessaire."
                    ))
                    
                    logger.debug(f"🚫 Exclusion détectée: {name_a} ⊥ {name_b} (depuis ontologie)")
        
        return contradictions
    
    def _check_normal_ecg_rule(self, concept_ids: Dict[str, str], annotations: List[str]) -> List[Contradiction]:
        """
        Règle 1: ECG normal exclut toute pathologie
        
        Si "ECG normal" est présent, aucune pathologie ne devrait être annotée
        """
        contradictions = []
        
        # Chercher "ECG normal"
        ecg_normal_id = None
        ecg_normal_name = None
        
        for name, ont_id in concept_ids.items():
            if ont_id == "ECG_NORMAL" or "ecg normal" in name.lower():
                ecg_normal_id = ont_id
                ecg_normal_name = name
                break
        
        if not ecg_normal_id:
            return []  # Pas d'ECG normal, règle non applicable
        
        # ECG normal exclut tous les autres concepts sauf concepts "normaux"
        normal_concepts = ['ECG_NORMAL', 'ONDE_T_NORMALES', 'PR_NORMAL', 'ONDE_P_NORMALE', 
                          'VOLTAGE_DU_QRS_NORMAL', 'QRS_FIN', 'RYTHME_SINUSAL']
        
        for name, ont_id in concept_ids.items():
            if name == ecg_normal_name:
                continue  # Skip ECG normal lui-même
            
            # Si le concept n'est pas dans la liste des concepts normaux
            if ont_id not in normal_concepts:
                contradictions.append(Contradiction(
                    concept_a=ecg_normal_name,
                    concept_b=name,
                    level=ContradictionLevel.CRITICAL,
                    rule_name="normal_ecg_excludes_pathology",
                    medical_reason=f"Un ECG normal ne peut pas présenter de pathologie. La présence de \"{name}\" indique une anomalie.",
                    suggestion=f"Choisissez soit \"ECG normal\" (tracé sans anomalie), soit \"{name}\" (pathologie détectée), mais pas les deux."
                ))
        
        return contradictions
    
    def _check_exclusive_rhythm_rule(self, concept_ids: Dict[str, str], annotations: List[str]) -> List[Contradiction]:
        """
        Règle 2: Un seul rythme de base autorisé
        
        Exemples: Rythme sinusal ⊥ Fibrillation atriale
        """
        contradictions = []
        
        # Liste des rythmes de base mutuellement exclusifs
        base_rhythms = {
            "RYTHME_SINUSAL": "Rythme sinusal",
            "FIBRILLATION_ATRIALE": "Fibrillation atriale",
            "FLUTTER_AURICULAIRE": "Flutter auriculaire",
            "TACHYCARDIE_JONCTIONNELLE": "Tachycardie jonctionnelle",
            "RYTHME_JONCTIONNEL": "Rythme jonctionnel",
            "RYTHME_IDIOVENTRICULAIRE": "Rythme idioventriculaire",
            "RYTHME_D'ÉCHAPPEMENT_VENTRICULAIRE": "Rythme d'échappement ventriculaire",
            "RYTHME_AURICULAIRE_ECTOPIQUE": "Rythme auriculaire ectopique"
        }
        
        # Trouver tous les rythmes de base présents
        detected_rhythms = []
        for name, ont_id in concept_ids.items():
            if ont_id in base_rhythms:
                detected_rhythms.append((name, ont_id))
        
        # Si plus d'un rythme de base → contradiction
        if len(detected_rhythms) > 1:
            for i, (name_a, id_a) in enumerate(detected_rhythms):
                for name_b, id_b in detected_rhythms[i+1:]:
                    contradictions.append(Contradiction(
                        concept_a=name_a,
                        concept_b=name_b,
                        level=ContradictionLevel.CRITICAL,
                        rule_name="exclusive_base_rhythm",
                        medical_reason=f"Un ECG ne peut avoir qu'un seul rythme de base. \"{name_a}\" et \"{name_b}\" sont mutuellement exclusifs.",
                        suggestion=f"Choisissez le rythme dominant: soit \"{name_a}\", soit \"{name_b}\"."
                    ))
        
        return contradictions
    
    def _check_branch_blocks_rule(self, concept_ids: Dict[str, str], annotations: List[str]) -> List[Contradiction]:
        """
        Règle 3: Blocs de branche mutuellement exclusifs
        
        BBG complet ⊥ BBD complet
        """
        contradictions = []
        
        # Détecter BBG et BBD
        bbg_present = None
        bbd_present = None
        
        for name, ont_id in concept_ids.items():
            name_lower = name.lower()
            
            # BBG
            if ont_id == "BLOC_DE_BRANCHE_GAUCHE" or "bloc de branche gauche" in name_lower or "bbg" in name_lower:
                bbg_present = name
            
            # BBD
            if ont_id == "BLOC_DE_BRANCHE_DROIT" or "bloc de branche droit" in name_lower or "bbd" in name_lower:
                bbd_present = name
        
        if bbg_present and bbd_present:
            contradictions.append(Contradiction(
                concept_a=bbg_present,
                concept_b=bbd_present,
                level=ContradictionLevel.CRITICAL,
                rule_name="branch_blocks_exclusive",
                medical_reason="Un bloc de branche gauche complet et un bloc de branche droit complet ne peuvent pas coexister (ce serait un bloc bi-fasciculaire ou AV complet).",
                suggestion=f"Vérifiez le tracé: s'agit-il vraiment d'un BBG et BBD simultanés, ou d'un bloc AV complet avec QRS larges ?"
            ))
        
        return contradictions
    
    def _check_quantitative_contradictions(self, concept_ids: Dict[str, str], annotations: List[str]) -> List[Contradiction]:
        """
        Règle 4: Contradictions de valeurs opposées
        
        Exemples:
        - Bradycardie ⊥ Tachycardie
        - Hypokaliémie ⊥ Hyperkaliémie
        - QT long ⊥ QT court
        """
        contradictions = []
        
        # Paires de concepts contradictoires
        opposite_pairs = [
            ("BRADYCARDIE", "TACHYCARDIE", "fréquence cardiaque"),
            ("HYPOKALIÉMIE", "HYPERKALIÉMIE", "kaliémie"),
            ("HYPOCALCÉMIE", "HYPERCALCÉMIE", "calcémie"),
            ("SYNDROME_DU_QT_LONG", "SYNDROME_DU_QT_COURT", "intervalle QT")
        ]
        
        for concept_a_id, concept_b_id, parameter in opposite_pairs:
            name_a = None
            name_b = None
            
            for name, ont_id in concept_ids.items():
                if ont_id == concept_a_id or concept_a_id.lower().replace('_', ' ') in name.lower():
                    name_a = name
                if ont_id == concept_b_id or concept_b_id.lower().replace('_', ' ') in name.lower():
                    name_b = name
            
            if name_a and name_b:
                contradictions.append(Contradiction(
                    concept_a=name_a,
                    concept_b=name_b,
                    level=ContradictionLevel.CRITICAL,
                    rule_name="quantitative_opposite",
                    medical_reason=f"Les valeurs de {parameter} ne peuvent être simultanément basses et élevées.",
                    suggestion=f"Vérifiez les mesures: la {parameter} est-elle diminuée (\"{name_a}\") ou augmentée (\"{name_b}\") ?"
                ))
        
        return contradictions
    
    def _check_asystole_rule(self, concept_ids: Dict[str, str], annotations: List[str]) -> List[Contradiction]:
        """
        Règle 5: Asystolie exclut tout autre rythme ou activité électrique
        """
        contradictions = []
        
        # Chercher asystolie
        asystole_name = None
        for name, ont_id in concept_ids.items():
            if ont_id == "ASYSTOLIE" or "asystolie" in name.lower():
                asystole_name = name
                break
        
        if not asystole_name:
            return []
        
        # Si asystolie présente, tout autre concept est contradictoire
        for name, ont_id in concept_ids.items():
            if name != asystole_name:
                contradictions.append(Contradiction(
                    concept_a=asystole_name,
                    concept_b=name,
                    level=ContradictionLevel.CRITICAL,
                    rule_name="asystole_excludes_all",
                    medical_reason=f"L'asystolie est l'absence totale d'activité électrique cardiaque. Aucun autre élément ECG ne peut être présent.",
                    suggestion=f"En cas d'asystolie, seul ce diagnostic doit être retenu. Retirez \"{name}\"."
                ))
        
        return contradictions
    
    def _check_bav_complet_rule(self, concept_ids: Dict[str, str], annotations: List[str]) -> List[Contradiction]:
        """
        Règle 6: BAV complet exclut tout intervalle PR
        
        En cas de BAV complet (3ème degré), il n'y a pas de conduction AV,
        donc pas d'intervalle PR mesurable
        """
        contradictions = []
        
        # Chercher BAV complet
        bav_complet_name = None
        for name, ont_id in concept_ids.items():
            if ont_id == "BAV_COMPLET" or "bav complet" in name.lower():
                bav_complet_name = name
                break
        
        if not bav_complet_name:
            return []
        
        # Concepts incompatibles avec BAV complet
        pr_concepts = {
            "PR_NORMAL": "PR normal",
            "PR_COURT": "PR court",
            "PR_LONG": "PR long",
            "INTERVALLE_PR_ALLONGÉ": "Intervalle PR allongé"
        }
        
        for name, ont_id in concept_ids.items():
            if ont_id in pr_concepts or any(pr_kw in name.lower() for pr_kw in ["pr normal", "pr court", "pr long", "intervalle pr"]):
                contradictions.append(Contradiction(
                    concept_a=bav_complet_name,
                    concept_b=name,
                    level=ContradictionLevel.CRITICAL,
                    rule_name="bav_complet_no_pr",
                    medical_reason=f"En cas de BAV complet (bloc AV du 3ème degré), il n'y a pas de conduction auriculo-ventriculaire, donc pas d'intervalle PR mesurable. La présence de \"{name}\" est incompatible.",
                    suggestion=f"Vérifiez le degré du BAV. Si le diagnostic est bien un BAV complet, retirez \"{name}\". Si un intervalle PR est mesurable, il ne s'agit probablement pas d'un BAV complet mais d'un BAV de 1er ou 2ème degré."
                ))
        
        return contradictions
    
    def get_validation_summary(self, contradictions: List[Contradiction]) -> str:
        """
        Génère un résumé textuel des contradictions
        
        Returns:
            Texte formaté pour affichage
        """
        if not contradictions:
            return "✅ Aucune contradiction détectée"
        
        critical = [c for c in contradictions if c.level == ContradictionLevel.CRITICAL]
        warnings = [c for c in contradictions if c.level == ContradictionLevel.WARNING]
        
        summary = f"🔴 {len(critical)} contradiction(s) critique(s)\n"
        if warnings:
            summary += f"⚠️ {len(warnings)} avertissement(s)\n"
        
        return summary.strip()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_annotations(annotations: List[str], ontology_mapping: Dict) -> List[Contradiction]:
    """
    Fonction helper pour validation rapide
    
    Args:
        annotations: Liste de concepts à valider
        ontology_mapping: Ontologie chargée
        
    Returns:
        Liste des contradictions
    """
    validator = AnnotationValidator(ontology_mapping)
    return validator.validate(annotations)


def format_contradiction_for_ui(contradiction: Contradiction) -> str:
    """
    Formate une contradiction pour l'affichage UI
    
    Returns:
        Texte HTML/Markdown formaté
    """
    icon = "🔴" if contradiction.level == ContradictionLevel.CRITICAL else "⚠️"
    
    return f"""
{icon} **Contradiction détectée**

**{contradiction.concept_a}** ⊥ **{contradiction.concept_b}**

**Raison:** {contradiction.medical_reason}

💡 **Suggestion:** {contradiction.suggestion}
"""
