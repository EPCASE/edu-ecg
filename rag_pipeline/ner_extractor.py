"""
🧱 Brique 2 — Extracteur d'Entités Cliniques (NER)
====================================================
Prend le texte libre d'un étudiant et utilise GPT-4o (Structured Outputs)
pour extraire une liste structurée de concepts médicaux bruts.

Principes :
  - Extraction "bête et qualifiée" : ZÉRO normalisation / correction
  - Périmètre ECG strict : ignorer la clinique annexe (âge, douleur…)
  - Chaque entité porte un statut clinique : present / absent / hypothese

L'output est un objet Pydantic `NERExtraction` garanti par l'API OpenAI
via la méthode `.parse()` (Structured Outputs).

Auteur : BMad Team
Date   : 2026-02-25
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Literal, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schémas Pydantic — strictement respectés par GPT-4o (Structured Outputs)
# ---------------------------------------------------------------------------

class ClinicalEntity(BaseModel):
    """Une entité clinique extraite du texte étudiant."""
    terme_brut: str = Field(
        description="Le concept exact extrait du texte, sans aucune correction orthographique."
    )
    statut: Literal["present", "absent", "hypothese"] = Field(
        description="Le statut clinique du concept."
    )
    contexte_phrase: str = Field(
        description="La phrase complète d'où le terme a été extrait."
    )


class NERExtraction(BaseModel):
    """Résultat complet de l'extraction NER sur un texte étudiant."""
    entites: List[ClinicalEntity]


# ---------------------------------------------------------------------------
# Prompt système — cœur de la Brique 2
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
Tu es un expert en lecture d'ECG. Ton rôle est d'extraire toutes les entités cliniques, rythmiques et morphologiques du texte rédigé par un étudiant en médecine.

RÈGLES STRICTES :
1. EXTRACTION PURE : N'essaie JAMAIS de corriger ou normaliser le terme. Garde les fautes orthographiques et les abréviations telles quelles (ex: si l'étudiant écrit "tachi supra", extrais "tachi supra").

2. PÉRIMÈTRE ECG — LARGE : Extrais TOUS les termes liés à l'interprétation du tracé ECG. Cela inclut :
   a. Les descriptions morphologiques et rythmiques (ex: "ondes T", "BBD", "tachycardie", "microvoltage", "sous-décalage ST").
   b. Les diagnostics et syndromes affirmés ou suspectés à partir du tracé (ex: "syndrome coronarien", "péricardite", "Brugada").
   c. Les diagnostics ÉTIOLOGIQUES déduits de l'ECG : ce sont les pathologies que l'étudiant conclut en lisant le tracé, même si ce ne sont pas des signes ECG au sens strict. Exemples :
      - "hyperkaliémie", "hypokaliémie", "hypercalcémie" (troubles ioniques)
      - "amylose", "hypothermie", "embolie pulmonaire"
      - "intoxication digitalique", "tamponnade"
      - "dysplasie arythmogène du ventricule droit"
   d. Les concepts de stimulation cardiaque (ex: "pacemaker", "stimulation", "pace", "AAI", "DDD").
   IGNORE UNIQUEMENT le contexte clinique purement anamnestique du patient (âge, poids, "adressé pour douleur thoracique") qui n'est PAS une conclusion tirée de l'ECG.

3. STATUT CLINIQUE : Pour chaque terme, détermine son statut :
   - "present" : le concept est affirmé par l'étudiant.
   - "absent" : le concept est explicitement nié ou écarté (ex: "pas de BBD", "sans FA").
   - "hypothese" : le concept est suspecté ou incertain (ex: "suspi d'infarctus", "peut-être une amylose").
""".strip()

# Modèle OpenAI compatible Structured Outputs
MODEL = "gpt-4o-2024-08-06"


# ---------------------------------------------------------------------------
# Client OpenAI (singleton module-level, initialisé à la demande)
# ---------------------------------------------------------------------------

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Retourne le client OpenAI, en le créant si nécessaire."""
    global _client
    if _client is None:
        # Chercher le .env dans plusieurs emplacements possibles
        env_candidates = [
            Path(".env"),
            Path(__file__).parent / ".env",
            Path(__file__).parent.parent / "ECG lecture" / ".env",
        ]
        for env_path in env_candidates:
            if env_path.exists():
                load_dotenv(env_path)
                break
        else:
            load_dotenv()  # fallback

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY non trouvée. "
                "Ajoutez-la dans un fichier .env ou en variable d'environnement."
            )
        _client = OpenAI(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Fonction principale — Brique 2
# ---------------------------------------------------------------------------

def extract_clinical_terms(texte_etudiant: str) -> NERExtraction:
    """
    Extrait les entités cliniques ECG d'un texte étudiant via GPT-4o.

    Args:
        texte_etudiant: Le texte libre rédigé par l'étudiant.

    Returns:
        NERExtraction: Objet Pydantic contenant la liste des entités extraites,
                       chacune avec terme_brut, statut et contexte_phrase.

    Raises:
        RuntimeError: Si la clé API est manquante.
        openai.APIError: Si l'appel API échoue.
    """
    client = _get_client()

    logger.info(f"🔬 NER Extraction — texte de {len(texte_etudiant)} caractères")

    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Texte de l'étudiant : {texte_etudiant}"},
        ],
        response_format=NERExtraction,
    )

    result = response.choices[0].message.parsed

    logger.info(f"✅ {len(result.entites)} entités extraites")
    for ent in result.entites:
        logger.debug(f"   [{ent.statut:>10}] {ent.terme_brut}")

    return result


# ---------------------------------------------------------------------------
# Point d'entrée CLI pour test rapide
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Texte de test (spécification)
    texte_test = (
        "Patient de 54 ans avec douleur thoracique. "
        "Rythme sinusal. Pas de BBD visible. "
        "On suspecte une amylose devant le microvoltage."
    )

    print(f"\n📝 Texte étudiant :\n   {texte_test}\n")
    print("=" * 60)

    result = extract_clinical_terms(texte_test)

    print(f"\n🔬 {len(result.entites)} entités extraites :\n")
    for i, ent in enumerate(result.entites, 1):
        print(f"  {i}. [{ent.statut:>10}] \"{ent.terme_brut}\"")
        print(f"     └─ Contexte : \"{ent.contexte_phrase}\"\n")

    print("✅ Brique 2 — Extraction NER terminée.")
