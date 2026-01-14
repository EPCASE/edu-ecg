"""
📋 QUICK START GUIDE - Validation POC
=====================================

🎯 OBJECTIF: Valider que le POC fonctionne avant d'investir 17h dans l'annotation

⏱️ DURÉE: 30 minutes

📍 ÉTAPES:

1. LANCER LE POC
   ✅ URL: http://localhost:8501
   ✅ Vérifier que l'interface charge

2. TEST #1 - ECG NORMAL
   📝 Entrer: "ECG normal"
   ✅ Attendu: Score ~100%
   ✅ Vérifier: Tous concepts normaux validés par "concept parent"
   
3. TEST #2 - ECG PATHOLOGIQUE (BAV1 + BBG)
   📝 Entrer: 
      "Rythme sinusal
       Onde P normale
       BAV 1er degré
       Bloc de branche gauche complet"
   
   ✅ Attendu: Score ~85-90%
   ✅ Vérifier implications:
      - "BAV 1er degré" implique "PR allongé" → 100pts
      - "BBG complet" implique "QRS larges" → 100pts
   
4. TEST #3 - SYNONYMES
   📝 Entrer:
      "Rythme sinusal
       Fréquence normale
       QRS fins
       PR normal
       Repolarisation normale"
   
   ✅ Attendu: Score ~95-100%
   ✅ Vérifier synonymes reconnus:
      - "QRS fins" = "QRS normal"
      - "Fréquence normale" = "Fréquence cardiaque normale"

5. TEST #4 - PERFORMANCE
   ✅ Chronométrer 3 corrections
   ✅ Attendu: < 10 secondes par correction
   
6. TEST #5 - QUALITÉ FEEDBACK
   ✅ Lire le feedback généré
   ✅ Évaluer sur 5:
      - Pédagogique (explique pourquoi c'est bon/mauvais)
      - Bienveillant (encourage sans démoraliser)
      - Précis (mentionne concepts manquants/corrects)
      - Constructif (suggère améliorations)
   ✅ Attendu: Note ≥ 4/5

📊 DÉCISION GO/NO-GO:

✅ GO SI:
   - Tous les tests passent
   - Score ≥95% pour réponses parfaites
   - Implications médicales reconnues
   - Synonymes reconnus
   - Temps < 10s
   - Feedback qualité ≥4/5

❌ NO-GO SI:
   - Un test critique échoue
   - Implications non reconnues
   - Temps > 15s
   - Feedback générique/inutile

🎯 APRÈS VALIDATION:

SI GO → Passer à Phase 2 (Annotation 50 ECG)
   📄 Suivre: docs/GUIDE_ANNOTATION_50_ECG.md
   ⏱️ Budget: 17h sur 4 semaines (4h/semaine)
   🎯 Objectif: 10 easy + 20 intermediate + 15 advanced + 5 trap

SI NO-GO → Améliorer POC
   🔧 Identifier problèmes spécifiques
   🔨 Corriger et re-tester
   ⏱️ Timeline: +1 semaine itération

=====================================
📞 QUESTIONS? Consultez docs/ROADMAP_COMPLETE.md
