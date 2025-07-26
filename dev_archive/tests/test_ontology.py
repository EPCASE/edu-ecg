from owlready2 import get_ontology

print("Loading ontology...")
try:
    onto = get_ontology("ontologie.owx").load()
    print(f"Ontology loaded successfully: {onto}")
    print(f"Number of classes: {len(list(onto.classes()))}")
    print(f"Number of individuals: {len(list(onto.individuals()))}")
    print(f"Number of properties: {len(list(onto.properties()))}")
    
    print("\nAll classes:")
    for cls in onto.classes():
        print(f"  - {cls.name}")
        
    print("\nAll individuals:")
    for ind in onto.individuals():
        print(f"  - {ind.name}")
        
    print("\nAll properties:")
    for prop in onto.properties():
        print(f"  - {prop.name}")
        
except Exception as e:
    print(f"Error loading ontology: {e}")
