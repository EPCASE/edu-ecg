"""
Configuration centralisée pour l'application ECG
"""
from pathlib import Path

# Chemins de base
PROJECT_ROOT = Path(__file__).parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
ECG_CASES_DIR = DATA_ROOT / "ecg_cases"
ECG_SESSIONS_DIR = DATA_ROOT / "ecg_sessions"
ONTOLOGY_FILE = DATA_ROOT / "ontologie.owx"

# Configuration de l'application
APP_NAME = "🫀 Edu-CG - Formation ECG"
APP_VERSION = "1.0"

# Configuration des exercices
DEFAULT_TIME_LIMIT = 30  # minutes
MAX_ANNOTATIONS = 15