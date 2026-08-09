"""Rebuild rag_index/ from current data/ontology_v2.json (outil_ontologie helper)."""
import sys
import logging
from pathlib import Path

sys.path.insert(0, r'c:\Users\Administrateur\bmad\ECG lecture\rag_pipeline')
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Administrateur\bmad\ECG lecture\ecg-online\.env')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from ontology_index import OntologyIndex

ontology_path = r'c:\Users\Administrateur\bmad\ECG lecture\data\ontology_v2.json'
index_dir = r'c:\Users\Administrateur\bmad\ECG lecture\rag_pipeline\rag_index'

print(f"Ontologie : {ontology_path}")
print(f"Index     : {index_dir}")

idx = OntologyIndex(ontology_path=ontology_path)
idx.build(include_implications=False)
print(idx.describe())
idx.save(index_dir)
print("OK - index reconstruit")
