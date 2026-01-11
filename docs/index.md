# 📚 Edu-ECG - Documentation Projet

**Date :** 2026-01-10  
**Type :** Projet Brownfield - Plateforme éducative ECG  
**Statut :** Phase Planning (Post-Brainstorming)  
**Timeline MVP :** 6 mois (24 semaines / 12 sprints)

---

## 🎯 Vision du Projet

**Edu-ECG** est une plateforme web interactive d'enseignement pour la lecture et l'évaluation d'électrocardiogrammes (ECG) 12 dérivations, destinée aux étudiants en médecine du CHU.

### Proposition de Valeur Unique

**Correction automatique intelligente** basée sur :
- 🏷️ **Ontologie médicale ECG** (100+ concepts OWL/Turtle)
- 🤖 **Intelligence artificielle LLM** (OpenAI GPT-4o)
- 📊 **Scoring hiérarchique** (5 relations ontologiques)
- 🎓 **Feedback pédagogique personnalisé**

---

## 📊 État Actuel (Brownfield)

### Prototype Existant

**Stack Actuelle :**
- Frontend : Streamlit (Python)
- Backend : Modules Python
- Données : Fichiers JSON locaux
- Ontologie : WebProtégé (OWL/Turtle) - 100+ concepts bilingues FR/EN

**Fonctionnalités Opérationnelles :**
- ✅ Import ECG (PDF + Images)
- ✅ Visualisation ECG basique
- ✅ Annotation manuelle
- ✅ Gestion utilisateurs locale (JSON)

**Limitations Actuelles :**
- ❌ Pas de base de données robuste
- ❌ Pas d'authentification sécurisée
- ❌ Pas de correction automatique LLM
- ❌ Interface UI basique
- ❌ Pas de déploiement production

---

## 🚀 Objectifs MVP (6 mois)

### Top 5 Solutions Prioritaires

| # | Solution | Score | Phase | Justification |
|---|----------|-------|-------|---------------|
| 1 | 🐳 Docker Déploiement CHU | 10/10 | Foundation | Critère CHU obligatoire |
| 2 | 🗄️ PostgreSQL 8 Tables | 9/10 | Foundation | Fondation technique |
| 3 | 🏷️ Système Annotation LLM | 8.3/10 | Core | Valeur unique |
| 4 | 🔐 Auth JWT + RBAC | 8/10 | Foundation | Sécurité CHU |
| 5 | 🎓 4 Modes Apprentissage | 7.5/10 | UX | Pédagogie |

### Fonctionnalités Clés MVP

**1. Système d'Annotation Ontologique LLM**
- Pipeline 4 étapes : NER → Mapping → Scoring → Feedback
- 5 relations hiérarchiques (granularité, indication, contradiction, critères, localisation)
- Validation enseignant des concepts extraits
- Gestion synonymes multilingue (FR/EN)

**2. Infrastructure Docker CHU**
- 4 conteneurs : PostgreSQL + FastAPI + Streamlit + Nginx
- Déploiement Ubuntu Server 22.04 LTS
- Réseau interne CHU uniquement
- `docker-compose up` one-click

**3. Base de Données PostgreSQL**
- 8 tables : users, promotions, ecg_cases, learning_sessions, session_cases, student_responses, student_progress, audit_logs
- JSONB pour concepts ontologiques flexibles
- UUID + RGPD (anonymisation automatique 5 ans)
- Volumétrie : ~3 GB sur 5 ans

**4. 4 Modes d'Apprentissage**
- **Quiz** : Feedback immédiat
- **Guidé** : Indices progressifs + assistance LLM
- **Examen** : Timer + feedback différé
- **Thématique** : Parcours séquentiels par pathologie

**5. Interface Multi-Rôles**
- 👨‍🎓 **Étudiant** : Consultation + progression personnelle
- 👨‍🏫 **Enseignant** : Animation classe + dashboards groupes
- 👨‍💼 **Admin** : Gestion contenu + promotions + analytics globaux

---

## 📅 Roadmap Détaillée (12 Sprints)

### Phase 0: Foundation (S1-2) - 4 semaines

**Sprint 1 - Infrastructure** (3 jours)
- Setup Git + Docker Compose (PostgreSQL + pgAdmin)
- CI/CD basique
- **Livrable :** `docker-compose up` fonctionnel

**Sprint 2 - Auth & API** (8 jours)
- Auth JWT + RBAC (3 rôles)
- API CRUD FastAPI + SQLAlchemy
- Tests API
- **Livrable :** API complète documentée (OpenAPI)
- **Gate Check S2 :** ✅ BDD + Auth + API opérationnels

---

### Phase 1: Core Features (S3-5) - 6 semaines

**Sprint 3 - LLM Pipeline** (11 jours)
- OpenAI integration + Pydantic models
- Parser ontologie OWL
- Scoring hiérarchique (3 premières relations)
- **Livrable :** Extraction concepts >80% accuracy

**Sprint 4 - Import ECG** (9 jours)
- Upload PDF + formulaire Streamlit
- Validation enseignant (draft → validated → published)
- **Livrable :** Import 1 ECG end-to-end

**Sprint 5 - Correction Étudiant** (9 jours)
- Interface réponse + auto-save
- Pipeline correction complet
- Update progression
- **Livrable :** Correction automatique fonctionnelle
- **Gate Check S10 :** ✅ Import + Correction end-to-end

---

### Phase 2: User Experience (S6-8) - 6 semaines

**Sprint 6 - Visualisation** (6 jours)
- Mode Vignette + Mode Structuré
- Filtres avancés (difficulté, tags, statut)
- **Livrable :** Base ECG navigable

**Sprint 7 - Modes Apprentissage** (9 jours)
- Implémentation 4 modes
- **Livrable :** Quiz + Guidé + Examen + Thématique opérationnels

**Sprint 8 - Dashboards** (9 jours)
- Dashboard étudiant (progression, concepts maîtrisés)
- Dashboard admin/enseignant (analytics promotion)
- **Livrable :** Interface complète
- **Gate Check S16 :** ✅ UX complète + Tests utilisateurs >4/5

---

### Phase 3: Production (S9-12) - 8 semaines

**Sprint 9 - Optimisations** (9 jours)
- Import batch (50 ECGs <10min)
- Performance (Redis cache + indexes BDD)
- **Livrable :** Performance optimisée

**Sprint 10 - Tests & QA** (10 jours)
- Tests automatisés >75% coverage
- Tests beta (10 étudiants + 2 enseignants)
- **Livrable :** Validation utilisateurs

**Sprint 11 - Déploiement CHU** (7 jours)
- docker-compose.prod.yml + Nginx + SSL
- Coordination DSI + installation VM
- **Livrable :** https://edu-ecg.chu-local opérationnel

**Sprint 12 - Formation** (9 jours)
- Documentation (guides + FAQ)
- Sessions formation (3 rôles)
- **Livrable :** Formation complète + support actif
- **Gate Check Final S24 :** 🎉 PRODUCTION

---

## 🏗️ Architecture Technique

### Stack Technologique

**Frontend :**
- Streamlit (MVP) - Rapid development
- Plotly - Graphiques analytics
- Future V2 : React (si besoin UX avancée)

**Backend :**
- FastAPI - API REST moderne Python
- SQLAlchemy + Alembic - ORM + migrations
- Pydantic - Validation données
- OpenAI API - LLM extraction concepts

**Base de Données :**
- PostgreSQL 15 - BDD principale
- JSONB - Concepts ontologiques flexibles
- pg_cron - Tâches automatiques (RGPD)

**Infrastructure :**
- Docker + Docker Compose
- Nginx - Reverse proxy + SSL
- Ubuntu Server 22.04 LTS

**Sécurité :**
- JWT tokens (8h expiration)
- bcrypt - Hash passwords
- RBAC - 3 rôles (student/teacher/admin)

### Schéma Architecture

```
┌─────────────────────────────────────────────┐
│           Réseau Interne CHU                │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │  Nginx (80/443)                   │    │
│  │  - Reverse Proxy                   │    │
│  │  - SSL CHU                         │    │
│  └──────────┬─────────────────────────┘    │
│             │                               │
│  ┌──────────┴──────────┐  ┌──────────────┐ │
│  │  Streamlit Frontend │  │ FastAPI API  │ │
│  │  (8501)             │←─┤ (8000)       │ │
│  └─────────────────────┘  └──────┬───────┘ │
│                                   │         │
│                        ┌──────────┴───────┐ │
│                        │ PostgreSQL 15    │ │
│                        │ (5432)           │ │
│                        └──────────────────┘ │
│                                             │
│  Volumes: postgres_data/ ecg_pdfs/ backups/ │
└─────────────────────────────────────────────┘
```

---

## 🤖 Pipeline LLM - Correction Automatique

### Workflow Complet

**A. IMPORT CAS ECG (Enseignant)**
```
Upload PDF + Énoncé
    ↓
Enseignant rédige correction manuscrite
    ↓
LLM extrait concepts → ConceptsAttendu[]
    ↓
Validation enseignant (approve/edit/reject)
    ↓
Stockage BDD (JSONB)
```

**B. PRATIQUE ÉTUDIANT**
```
Étudiant lit ECG + rédige réponse texte libre
    ↓
Soumission
```

**C. CORRECTION AUTOMATIQUE (4 étapes)**

**Étape 1 : Extraction NER**
- LLM identifie entités médicales
- Ex: ["tachycardie", "FA", "sus-décalage ST"]

**Étape 2 : Mapping Ontologique**
- Lien entités → concepts ontologie
- Gestion synonymes FR/EN
- "FA" → "Fibrillation Auriculaire"

**Étape 3 : Scoring Hiérarchique**
- Comparer concepts identifiés vs attendus
- 5 relations ontologiques
- Détection contradictions

**Étape 4 : Feedback Pédagogique**
- Retour personnalisé selon mode
- Concepts trouvés / manquants / erronés
- Suggestions d'amélioration

### Scoring Hiérarchique (5 Relations)

1. **Granularité** : "PR allongé" (60%) → "BAV 1er degré" (100%)
2. **Indication** : Signe + Diagnostic = 100%
3. **Contradiction** : "Rythme sinusal" ⚠️ "FA" = -20%
4. **Critères multiples** : BBD = QRS >120ms + rSR' V1 + Onde S V6
5. **Localisation** : STEMI → Antérieur/Inférieur/Latéral

---

## 📈 Volumétrie & Performance

### Données Projetées (5 ans)

```
Utilisateurs : 1000 (200/an × 5)     ~100 KB
Cas ECG : 1000 × 2 MB                ~2 GB
Réponses : 50 000                    ~500 MB
───────────────────────────────────────────
TOTAL                                ~3 GB
```

### Objectifs Performance

- ✅ API <200ms (95e percentile)
- ✅ Import batch 50 ECGs <10min
- ✅ 100 utilisateurs simultanés
- ✅ Disponibilité >99.5%

---

## 🚨 Risques & Mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Coûts OpenAI élevés | Haute | Monitoring + cache + budget alert |
| Accuracy LLM <75% | Critique | POC Sprint 3 + fallback validation manuelle |
| Retard DSI CHU | Moyenne | Déploiement local + doc anticipée |
| Scope creep | Moyenne | Backlog V2 strict + roadmap claire |

---

## 🔮 Roadmap Post-MVP (V2)

**Priorisation après feedback S24 :**

1. **Gamification** (3 sem) - Badges, points, leaderboards
2. **Sondages Temps Réel** (4 sem) - Mode enseignant interactif
3. **Spaced Repetition** (4 sem) - Algorithme révision espacée
4. **Migration React** (10 sem) - Si Streamlit trop limitant
5. **LLM Local** (6 sem + GPU) - Réduction coûts OpenAI

---

## 📚 Documents de Référence

### Documents BMad

- 📄 [Brainstorming Session (4126 lignes)](./_bmad-output/analysis/brainstorming-session-2026-01-10.md)
- 📄 [Decision Tree Roadmap (328 lignes)](./_bmad-output/analysis/decision-tree-roadmap.md)
- 📄 [Workflow Status](./_bmad-output/planning-artifacts/bmm-workflow-status.yaml)

### Documents Techniques Existants

- ARCHITECTURE_VALIDEE.md
- GUIDE_AUTHENTIFICATION.md
- PROJET_STATUS_FINAL.md
- Projet ECG ontologie et correction automatique.docx

---

## 👥 Équipe & Contexte

**Facilitateur :** Grégoire  
**Équipe Cible :** 2-3 développeurs full-stack  
**Partenaire :** DSI CHU (VM + support déploiement)  
**Utilisateurs :** 200 étudiants + 5 enseignants + 2 admins

---

## ✅ Prochaines Étapes

### Immédiat (Cette semaine)

1. ✅ [DP] Document Project - **FAIT** (ce document)
2. ⏭️ [ARCH] Architecture Document - Design technique complet
3. ⏭️ [EPICS] Créer epics et stories - Décomposition en tickets

### Setup Environnement (Semaine 1-2)

1. Initialiser repository Git
2. Créer docker-compose.yml local
3. Setup PostgreSQL + pgAdmin
4. POC LLM extraction (validation technique)
5. Maquettes UI Streamlit (wireframes)

---

## 📊 Métriques de Succès MVP

**Technique :**
- ✅ 50+ cas ECG en production
- ✅ LLM accuracy >80%
- ✅ Tests coverage >75%
- ✅ Disponibilité >99%

**Pédagogique :**
- ✅ 200 comptes étudiants actifs
- ✅ 1000+ réponses soumises
- ✅ Satisfaction utilisateurs >4/5
- ✅ Temps correction enseignant -60%

---

**État du Projet :** 🟢 **Prêt pour Architecture & Développement**

**Confiance Réussite :** 🟢 **Haute (85%)**
- Scope réaliste et bien défini
- Stack technique éprouvée
- Timeline raisonnable (6 mois)
- Risques identifiés et mitigés

---

*Document généré le 2026-01-10*  
*Version : 1.0 - Project Documentation (Phase 0 complete)*  
*Prochaine étape : Architecture Document*
