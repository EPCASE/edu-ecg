# 🎓 Système de Collecte - 100 Étudiants × 50 ECG

**Objectif :** Collecter 5000 réponses d'étudiants pour constituer dataset d'entraînement

**Timeline :** 4 semaines après annotation des 50 ECG

**Participants :** 100 étudiants (40 DFASM2 + 40 DFASM3 + 20 Internes)

---

## 🎯 Stratégie de Collecte

### **Option A : Intégration Session TP Existante** ⭐ **RECOMMANDÉE**

**Avantages :**
- ✅ Participation garantie (obligatoire)
- ✅ Conditions standardisées (même salle, même temps)
- ✅ Supervision possible (questions en direct)
- ✅ Pas de biais de sélection

**Logistique :**
- 4 séances TP de 2h
- 25 étudiants par séance
- 10 ECG par étudiant (choisis aléatoirement parmi 50)
- Total : 100 × 10 = 1000 réponses en 4 semaines

### **Option B : Plateforme en Ligne (Complémentaire)**

**Avantages :**
- ✅ Flexibilité horaire
- ✅ Peut atteindre plus d'étudiants
- ✅ Réponses asynchrones

**Inconvénients :**
- ⚠️ Biais de sélection (étudiants motivés)
- ⚠️ Conditions non standardisées
- ⚠️ Risque de triche (recherches)

**Recommandation :** Option A (TP) + Option B pour compléter

---

## 📋 Protocole de Collecte (TP)

### **Avant le TP (1 semaine avant)**

**Préparation technique :**
1. Déployer POC sur serveur accessible (pas localhost)
2. Créer 100 comptes étudiants anonymisés
3. Assigner aléatoirement 10 ECG/étudiant (stratifié par difficulté)
4. Préparer fichiers Excel tracking

**Communication :**
```
Email aux étudiants:

Objet: TP ECG - Système de Correction Intelligent (Recherche)

Chers étudiants,

Dans le cadre d'un projet de recherche du CHU, vous participerez à un TP 
d'interprétation d'ECG assisté par intelligence artificielle.

📅 Date: [...]
🕒 Durée: 2h
📍 Lieu: Salle informatique [...]

Objectifs:
- Pratiquer l'interprétation d'ECG
- Recevoir feedback IA instantané
- Contribuer à la recherche médicale

Vos réponses seront anonymisées et utilisées pour améliorer le système.

Cordialement,
Dr. Grégoire
```

---

### **Pendant le TP (2h)**

**Timeline :**
```
0:00-0:10  Introduction + démonstration système
0:10-0:15  Login + familiarisation interface
0:15-1:45  Analyse des 10 ECG assignés
1:45-2:00  Questionnaire satisfaction + débriefing
```

**Instructions étudiants :**
```
===========================================
    🩺 TP ECG - Mode d'emploi
===========================================

1. Connectez-vous avec votre ID: ETU_XXX
   Mot de passe: [fourni sur papier]

2. Vous avez 10 ECG à analyser (ordre aléatoire)

3. Pour chaque ECG:
   ✍️  Rédigez votre interprétation en texte libre
   
      Exemple:
      "Rythme sinusal régulier. Fréquence cardiaque 
       normale à 75 bpm. PR normal. QRS fins. Axe normal. 
       Pas d'anomalie de repolarisation."
   
   🚀  Cliquez "Corriger avec IA"
   
   📊  Consultez votre score et feedback
   
   💾  Passez à l'ECG suivant (sauvegarde auto)

4. Temps recommandé: 10 min/ECG
   (mais pas de limite stricte)

5. À la fin: Questionnaire satisfaction (5 min)

⚠️  Important:
- Répondez SANS consulter de références
- Écrivez en langage naturel (pas de codes)
- Soyez honnête (pas de note finale)

Bon TP ! 🎯
===========================================
```

---

### **Après le TP**

**Export données :**
```python
# Script d'export automatique
python scripts/export_student_responses.py --session TP1

# Génère:
# - student_responses_TP1.json (toutes les réponses)
# - student_metadata_TP1.csv (niveau, temps par ECG)
# - performance_summary_TP1.xlsx (stats agrégées)
```

**Vérifications :**
- [ ] 250 réponses collectées (25 étudiants × 10 ECG)
- [ ] Aucune réponse vide
- [ ] Temps médian cohérent (8-12 min/ECG)
- [ ] Distribution niveaux équilibrée

---

## 💻 Adaptation POC pour Collecte

### **Modifications nécessaires :**

**1. Système d'authentification simple**
```python
# frontend/auth_collecte.py
STUDENT_IDS = {
    "ETU_001": {"level": "DFASM2", "assigned_ecgs": [1,5,12,18,...]},
    "ETU_002": {"level": "DFASM3", "assigned_ecgs": [3,7,14,22,...]},
    # ... 100 étudiants
}
```

**2. Interface simplifiée (mode collecte)**
```python
# Masquer:
- Concepts attendus (pas de triche)
- Guide d'annotation
- Onglet diagnostic

# Afficher uniquement:
- ECG en cours
- Zone texte réponse
- Bouton "Corriger"
- Score + feedback (après soumission)
- Bouton "ECG Suivant"
```

**3. Logging exhaustif**
```python
{
  "student_id": "ETU_042",
  "ecg_id": "ECG_018",
  "timestamp": "2026-02-15T10:23:45",
  "response_text": "Rythme sinusal avec BAV 1...",
  "time_spent_seconds": 547,
  "score": 85.5,
  "concepts_extracted": [...],
  "feedback_shown": "...",
  "student_level": "DFASM3",
  "ecg_difficulty": "intermediaire"
}
```

---

## 📊 Dashboard Temps Réel (Pour Superviseur)

**Pendant le TP, affichage admin :**
```
===========================================
    📊 TP ECG - Tableau de Bord Live
===========================================

Étudiants connectés:  23 / 25
ECG complétés:        127 / 250  (51%)
Temps moyen/ECG:      9.4 min

Performance moyenne:
  - Faciles:          78.5%  (42 réponses)
  - Intermédiaires:   63.2%  (58 réponses)
  - Avancés:          41.8%  (27 réponses)

Alertes:
  ⚠️  ETU_015: Temps excessif ECG_032 (23 min)
  ⚠️  ETU_041: 3 ECG consécutifs <30% (difficulté?)

Reste estimé: 48 minutes
```

---

## 📝 Questionnaire Post-TP

**Objectif :** Évaluer utilité pédagogique + identifier bugs UX

```markdown
# Questionnaire Satisfaction - Système ECG IA

**Durée :** 3 minutes | **Anonyme**

---

## 1. Utilité Pédagogique

**Le feedback IA vous a-t-il aidé à comprendre vos erreurs ?**
☐ Pas du tout  ☐ Un peu  ☐ Modérément  ☐ Beaucoup  ☐ Énormément

**Comparé à une correction traditionnelle, le feedback IA est :**
☐ Bien moins utile  ☐ Moins utile  ☐ Équivalent  ☐ Plus utile  ☐ Bien plus utile

**Avez-vous appris de nouvelles choses grâce aux corrections ?**
☐ Non  ☐ Un peu  ☐ Oui, plusieurs concepts

---

## 2. Qualité du Feedback

**Le ton du feedback était :**
☐ Trop sévère  ☐ Un peu sévère  ☐ Bienveillant  ☐ Encourageant

**La longueur du feedback était :**
☐ Trop court  ☐ Correct  ☐ Trop long

**Les explications étaient :**
☐ Trop simples  ☐ Adaptées  ☐ Trop complexes

---

## 3. Interface

**L'interface était :**
☐ Difficile  ☐ Un peu confuse  ☐ Intuitive  ☐ Très claire

**Temps de réponse du système :**
☐ Trop lent  ☐ Acceptable  ☐ Rapide

**Bugs rencontrés ?**
☐ Non  ☐ Oui, lesquels : _______________________

---

## 4. Intérêt pour Utilisation Future

**Utiliseriez-vous ce système pour réviser vos ECG ?**
☐ Non  ☐ Peut-être  ☐ Oui  ☐ Absolument

**Recommanderiez-vous ce système à d'autres étudiants ?**
☐ Non  ☐ Peut-être  ☐ Oui  ☐ Certainement

---

## 5. Commentaires Libres

**Points forts du système :**
_______________________________________________
_______________________________________________

**Points à améliorer :**
_______________________________________________
_______________________________________________

**Autres remarques :**
_______________________________________________
_______________________________________________

---

Merci pour votre participation ! 🙏
Vos retours sont précieux pour améliorer le système.
```

---

## 📊 Métriques de Succès Collecte

**Objectifs quantitatifs :**
- [ ] ≥1000 réponses collectées
- [ ] ≥80% taux complétion (étudiants finissent 10 ECG)
- [ ] Temps médian 8-12 min/ECG
- [ ] <5% réponses vides/invalides

**Objectifs qualitatifs :**
- [ ] ≥70% étudiants satisfaits (note ≥4/5)
- [ ] ≥60% trouve feedback utile
- [ ] <10% bugs critiques reportés

---

## 🔄 Stratégie d'Assignation ECG

**Assignation stratifiée (chaque étudiant voit 10 ECG) :**

```python
# Exemple assignation pour garantir couverture équilibrée
def assign_ecgs_to_students(students, ecgs):
    assignments = {}
    
    for student in students:
        level = student.level  # DFASM2, DFASM3, Interne
        
        # Chaque étudiant reçoit:
        easy = random.sample(ecgs_faciles, 3)        # 3 faciles
        medium = random.sample(ecgs_intermediaires, 4)  # 4 intermédiaires
        hard = random.sample(ecgs_avances, 2)        # 2 avancés
        trap = random.sample(ecgs_pieges, 1)         # 1 piège
        
        assignments[student.id] = easy + medium + hard + trap
        random.shuffle(assignments[student.id])  # Ordre aléatoire
    
    # Vérifier: chaque ECG vu ~20 fois (100 étudiants × 10 ECG / 50 ECG)
    return assignments
```

**Résultat attendu :**
- Chaque ECG analysé par ~20 étudiants
- Distribution niveaux équilibrée par ECG
- Variabilité suffisante pour mining synonymes

---

## 📁 Structure Données Collectées

```json
{
  "collection_metadata": {
    "session_id": "TP1_2026-02-15",
    "date": "2026-02-15",
    "location": "CHU Salle Info A",
    "supervisor": "Dr. Grégoire",
    "total_students": 25,
    "total_responses": 247
  },
  "responses": [
    {
      "response_id": "RESP_00001",
      "student_id": "ETU_042",
      "student_level": "DFASM3",
      "ecg_id": "ECG_018",
      "ecg_difficulty": "intermediaire",
      "timestamp_start": "2026-02-15T10:15:23",
      "timestamp_submit": "2026-02-15T10:24:10",
      "time_spent_seconds": 527,
      "response_text": "Fibrillation auriculaire rapide...",
      "concepts_extracted": [...],
      "concepts_expected": [...],
      "score": 82.5,
      "feedback_generated": "...",
      "llm_calls": 8,
      "cost_usd": 0.0042
    }
  ]
}
```

---

## ✅ Checklist Lancement Collecte

**2 semaines avant :**
- [ ] 50 ECG annotés et validés
- [ ] POC adapté mode "collecte"
- [ ] Serveur déployé et testé
- [ ] 100 comptes étudiants créés
- [ ] Assignations ECG générées

**1 semaine avant :**
- [ ] Email d'invitation envoyé
- [ ] Salle informatique réservée
- [ ] Test charge serveur (25 connexions simultanées)
- [ ] Dashboard admin fonctionnel

**Jour J :**
- [ ] Présence superviseur (Dr. Grégoire)
- [ ] Support technique disponible
- [ ] Backup serveur configuré
- [ ] Recording démonstration préparée

**Après TP :**
- [ ] Export données immédiat
- [ ] Backup sécurisé (3 copies)
- [ ] Analyse préliminaire (stats descriptives)
- [ ] Email remerciement + résultats agrégés

---

**Version :** 1.0  
**Auteur :** Dr. Grégoire + GitHub Copilot  
**Date :** 2026-01-10  
**Prochaine mise à jour :** Après validation POC
