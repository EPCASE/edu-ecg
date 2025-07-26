from owlready2 import get_ontology

onto = get_ontology("ontologie.owx").load()

# Extraire tous les concepts et leur hiérarchie
for cls in onto.classes():
    label = cls.name
    parents = []
    for parent in cls.is_a:
        if parent != onto.Thing:
            # Check if parent has a name attribute (to handle restrictions)
            if hasattr(parent, 'name'):
                parents.append(parent.name)
            else:
                parents.append(str(parent))
    print(f"{label} → {parents or ['owl:Thing']}")