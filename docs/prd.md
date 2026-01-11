# 📋 Product Requirements Document (PRD)
# Edu-ECG - Plateforme Pédagogique ECG avec Correction LLM

**Version:** 1.0  
**Date:** 2026-01-10  
**Auteur:** John (PM) & Grégoire  
**Statut:** ✅ Validé par architecture review

---

## 📊 Executive Summary

### Vision

Créer une **plateforme pédagogique d'entraînement ECG** pour étudiants en médecine au CHU, permettant une **pratique illimitée avec feedback automatisé basé sur IA** (LLM + ontologie médicale).

### Unique Value Proposition

**"Apprendre l'ECG avec un feedback pédagogique instantané, précis et illimité - comme avoir un cardiologue disponible 24/7"**

### Success Metrics (Validées)

#### Métriques Techniques
- ✅ **Precision LLM:** >85% (concepts identifiés corrects / total identifiés)
- ✅ **Recall LLM:** >75% (concepts identifiés / total attendus)
- ✅ **F1-Score global:** >80%
- ✅ **Latence moyenne:** <3s par correction (priorisation qualité > vitesse)
- ✅ **Budget OpenAI:** <$50/mois (production)

#### Métriques Pédagogiques
- ✅ **200 étudiants actifs** en 12 mois
- ✅ **50+ cas ECG** validés par cardiologues
- ✅ **Satisfaction étudiants:** >4/5
- ✅ **Adoption enseignants:** 10+ profs créent des sessions

---

## 🎯 Priorités MVP (B+C Validées)

### ✅ Priorisation Confirmée: Qualité + Volume

Choix stratégique: **B (Comprendre erreurs) + C (S'entraîner sans limite)**

**RATIONALE:**
1. **Contexte médical exige qualité** - Les étudiants doivent COMPRENDRE (pas juste avoir une note)
2. **Période révision = volume massif** - Besoin de s'entraîner 500+ fois/an
3. **Vitesse secondaire** - Préférable attendre 3s pour feedback de qualité

**IMPLICATIONS ARCHITECTURE:**
- ✅ LLM peut être "lent" (2-3s acceptable)
- ✅ Investir dans **feedback pédagogique riche** (étape 4 pipeline)
- ✅ Budget LLM: priorité **précision** > rapidité
- ✅ Rate limiting: 10 corrections/minute (évite spam, permet volume)

---

## 👥 User Personas

### Persona 1: Étudiant DFASM2 (Utilisateur Principal)

**Nom:** Sarah, 23 ans, DFASM2 (5e année médecine)  
**Contexte:** Révisions cardio avant ECN, stress examens  
**Job-to-be-Done:**  
*"Quand je révise l'ECG, je veux pratiquer sans limite sur des vrais cas et comprendre mes erreurs, pour être prêt le jour de l'ECN."*

**Pain Points:**
- ❌ Pas assez de retours enseignants (1 prof pour 100 étudiants)
- ❌ Livres statiques, pas d'interaction
- ❌ Peur de poser "bêtes questions" en TD

**Gains Attendus:**
- ✅ Feedback immédiat 24/7
- ✅ Anonymat total (pas de jugement)
- ✅ S'entraîner 500+ fois (période révision)
- ✅ Comprendre **pourquoi** une réponse est fausse

**Fréquence d'usage:**
- Semestre normal: 1-2 ECG/semaine
- Période révision: **5-10 ECG/jour** (×50 volume)

### Persona 2: Enseignant Cardiologue (Créateur de Contenu)

**Nom:** Dr. Martin, 45 ans, Cardiologue CHU  
**Contexte:** 2h/semaine enseignement ECG, 100+ étudiants DFASM2  
**Job-to-be-Done:**  
*"Quand je prépare mes cours ECG, je veux créer des cas réalistes avec correction automatisée, pour libérer du temps en TD et suivre la progression des étudiants."*

**Pain Points:**
- ❌ Pas le temps de corriger 100 copies manuellement
- ❌ Difficulté à identifier étudiants en difficulté
- ❌ Répéter les mêmes explications de base

**Gains Attendus:**
- ✅ Import PDF ECG + texte correction → système automatique
- ✅ Dashboard progression (qui bloque sur quoi ?)
- ✅ Focus TD sur cas complexes (automatisation du basique)

**Besoins Critiques:**
- ⚠️ **Confiance dans feedback LLM** → POC validation avec 5 profs (Sprint 3)
- ⚠️ Possibilité validation manuelle si doute
- ⚠️ Ontologie médicalement exacte

### Persona 3: Administrateur Pédagogique

**Nom:** Marie, Responsable plateforme numérique CHU  
**Job-to-be-Done:**  
*"Gérer les utilisateurs, monitorer l'usage, assurer conformité RGPD"*

**Besoins:**
- Gestion utilisateurs/promotions
- Export données anonymisées (analytics)
- Respect RGPD (7 ans conservation validé)

---

## 🎯 Functional Requirements (FRs)

### FR-001: Import Cas ECG (Enseignant)
**Priority:** 🔴 P0 (Critique MVP)  
**User Story:**  
*En tant qu'enseignant, je veux importer un PDF ECG avec énoncé clinique et ma correction, pour créer un cas d'entraînement automatisé.*

**Acceptance Criteria:**
- [ ] Upload PDF (<10 MB)
- [ ] Formulaire: titre, contexte clinique, difficulté (beginner/intermediate/advanced)
- [ ] Textarea correction texte libre
- [ ] **LLM extrait concepts** de ma correction → affichage pour validation
- [ ] Je peux cocher/décocher concepts détectés
- [ ] Ajout tags manuels (pathologies, thèmes)
- [ ] Statut brouillon → publié

**Dependencies:** Architecture LLM (Sprint 3)

---

### FR-002: Pratique ECG Étudiant (Mode Guidé)
**Priority:** 🔴 P0 (Critique MVP)  
**User Story:**  
*En tant qu'étudiant, je veux analyser un ECG et recevoir un feedback détaillé sur mes erreurs, pour progresser de manière autonome.*

**Acceptance Criteria:**
- [ ] Liste ECG (filtres: difficulté, tags)
- [ ] Affichage PDF + énoncé clinique
- [ ] Textarea réponse texte libre
- [ ] Chronomètre (tracking temps)
- [ ] Bouton "Soumettre" → **Pipeline LLM 4 étapes**
- [ ] Affichage résultats:
  - Score global /100
  - ✅ Concepts corrects (vert)
  - ⚠️ Concepts manqués (orange)
  - ❌ Concepts erronés (rouge)
  - 📝 Feedback pédagogique personnalisé
- [ ] Historique tentatives (multiples essais autorisés)

**Dependencies:** Pipeline LLM complet (Sprint 3)

---

### FR-003: Dashboard Progression Étudiant
**Priority:** 🟡 P1 (Important)  
**User Story:**  
*En tant qu'étudiant, je veux voir ma progression globale, pour identifier mes points faibles.*

**Acceptance Criteria:**
- [ ] Score moyen global
- [ ] Scores par difficulté (beginner/intermediate/advanced)
- [ ] Top 5 concepts maîtrisés
- [ ] Top 5 concepts à réviser
- [ ] Graphique progression dans le temps

**Dependencies:** Table `student_progress` (Sprint 2)

---

### FR-004: Sessions d'Entraînement (Enseignant)
**Priority:** 🟡 P1 (Important)  
**User Story:**  
*En tant qu'enseignant, je veux créer une session d'entraînement ciblée avec 5 ECG, pour préparer mon TD de demain.*

**Acceptance Criteria:**
- [ ] Créer session: titre, description, type (quiz/guidé/examen)
- [ ] Sélectionner 5+ ECG (ordre, pondération)
- [ ] Cibler promotion(s) ou étudiant(s)
- [ ] Définir disponibilité (dates début/fin)
- [ ] Options: temps limité, afficher feedback immédiat ou après
- [ ] Dashboard résultats classe (boxplot scores, top erreurs)

**Dependencies:** Tables `learning_sessions` + `session_cases` (Sprint 2)

---

### FR-005: Pipeline LLM 4 Étapes
**Priority:** 🔴 P0 (Critique MVP - Cœur de Valeur)  
**Technical Requirement:**  
*Le système doit analyser une réponse texte libre et produire un scoring hiérarchique précis.*

**Pipeline Steps:**

#### Étape 1: Extraction NER
- **Input:** Texte réponse étudiant
- **LLM:** GPT-4o structured output (`ExtractedConcept` Pydantic)
- **Fallback:** Regex-based extraction (si API échoue)
- **Output:** Liste concepts [{text, category, confidence}]

#### Étape 2: Mapping Ontologique
- **Input:** Concepts bruts
- **Process:** 
  - Recherche dans ontologie OWL (rdflib)
  - Matching synonymes FR/EN
  - Normalisation URI
- **Cache:** Redis (ontologie chargée 1×/24h)
- **Output:** Concepts mappés [{uri, label, confidence}]

#### Étape 3: Scoring Hiérarchique
- **Input:** Concepts étudiant vs. Concepts attendus (correction prof)
- **Relations ontologiques** (5 types):
  1. **Exact match:** 100%
  2. **Parent-enfant:** 70-85%
  3. **Granularité:** 60-90% (vague ↔ précis)
  4. **Indication:** 60-80% (signe → diagnostic)
  5. **Contradiction:** -20% (RS + FA incompatibles)
- **Output:** Score global + matched/missed/wrong concepts

#### Étape 4: Feedback Pédagogique
- **Input:** Résultats scoring + type session (guidé/quiz/examen)
- **LLM:** GPT-4o avec prompt pédagogique
- **Contraintes:**
  - Mode guidé: Indices sans donner réponse
  - Mode quiz: Feedback immédiat positif
  - Mode examen: Feedback complet détaillé
- **Max tokens:** 300 (contrôle coût)
- **Output:** Texte feedback personnalisé

**Acceptance Criteria:**
- [ ] **Precision:** >85%
- [ ] **Recall:** >75%
- [ ] **F1-Score:** >80%
- [ ] **Latence:** <3s (P99)
- [ ] **Fallback activé** si structured output échoue
- [ ] **Test dataset:** 30 cas validés cardiologues

---

### FR-006: Rate Limiting & Quotas
**Priority:** 🔴 P0 (Protection Budget)  
**Technical Requirement:**  
*Prévenir abus et contrôler coûts OpenAI.*

**Acceptance Criteria:**
- [ ] **Limite individuelle:** 10 corrections/minute par étudiant
- [ ] **Quota mensuel:** 100 corrections/étudiant/mois (configurable)
- [ ] **Circuit breaker:** Si budget mensuel $50 dépassé → mode dégradé (fallback regex only)
- [ ] **Monitoring:** Dashboard admin tracking consommation API
- [ ] **Alertes:** Email si >80% budget mensuel

---

### FR-007: RGPD Compliance
**Priority:** 🔴 P0 (Légal Critique)  
**User Story:**  
*En tant qu'étudiant, je veux que mes données soient protégées conformément au RGPD.*

**Acceptance Criteria:**
- [ ] **Anonymisation auto:** 5 ans après dernière connexion (pg_cron)
- [ ] **Conservation données pédagogiques:** 7 ans après anonymisation (validé DPO)
- [ ] **Droit à l'oubli:** Endpoint `/api/users/{id}/gdpr-delete` (admin)
- [ ] **Logs anonymisation:** Table `anonymization_logs`
- [ ] **Purge finale:** 7 ans après anonymisation → suppression définitive
- [ ] **Consentement:** Checkbox CGU lors inscription

**Legal Validation:**
- [ ] Contact DPO CHU (Sprint 2)
- [ ] Validation durées conservation
- [ ] Template email notification anonymisation

---

## ⚡ Non-Functional Requirements (NFRs)

### NFR-001: Performance
- **Latence API:** <200ms (P50), <500ms (P95) (hors LLM)
- **Latence LLM:** <3s (P99) - acceptable car priorité qualité
- **Disponibilité:** >99.5% (infrastructure CHU)
- **Concurrent users:** 200 simultanés

### NFR-002: Sécurité
- **Authentication:** JWT (access 8h, refresh 30 jours)
- **Passwords:** bcrypt hash (cost=12)
- **RBAC:** 3 rôles (student/teacher/admin)
- **SSL/TLS:** Certificat CHU fourni par DSI
- **Rate limiting:** Nginx 10 req/s + SlowAPI applicatif

### NFR-003: Scalabilité
- **Database:** PostgreSQL 15 (200 connexions max)
- **Cache:** Redis ontologie (×100 gain performance)
- **Volumétrie:** 
  - 200 users
  - 1,000 ECG cases
  - 100,000 réponses/an (100/étudiant/an validé)
  - 3 GB données sur 5 ans

### NFR-004: Maintenabilité
- **Code coverage:** >75% tests (pytest)
- **Documentation:** Docstrings Google style
- **Logging:** JSON structuré (ELK-ready)
- **Monitoring:** Health checks `/health`, `/metrics` (Prometheus)

### NFR-005: Déployabilité
- **Infrastructure:** Docker Compose (5 containers)
- **CI/CD:** GitHub Actions (optionnel V2)
- **Backups:** Quotidiens (pg_dump + PDFs)
- **Rollback:** < 15 minutes (docker-compose down/up)

---

## 🚫 Out of Scope (V2)

Les fonctionnalités suivantes sont **hors périmètre MVP** (6 mois):

### V2 Features (12-18 mois)
- ❌ Gamification (badges, leaderboard, achievements)
- ❌ Sondages temps réel en cours (WebSockets)
- ❌ Spaced repetition algorithm (Anki-like)
- ❌ Migration React frontend (Next.js)
- ❌ LLM local (Llama 3) pour réduire coûts
- ❌ Export certificats complétion
- ❌ Mobile app (iOS/Android)
- ❌ Intégration Moodle CHU
- ❌ Reconnaissance vocale (réponse parlée)
- ❌ Génération automatique ECG synthétiques

### Raisons Exclusion MVP
- **Focus:** Valider proposition valeur core (LLM correction)
- **Ressources:** 2-3 devs, 6 mois timeline
- **Risque:** Scope creep fatal

---

## 📊 Success Criteria & KPIs

### Gate Check Sprint 3 (Validation LLM)
- ✅ Dataset 30 cas validés cardiologues
- ✅ F1-Score >80% sur Top 10 pathologies
- ✅ POC testé avec 5 enseignants (feedback >4/5)
- ✅ POC testé avec 10 étudiants (satisfaction >4/5)

### Gate Check Sprint 6 (Beta Private)
- ✅ 50 étudiants beta testeurs
- ✅ 20+ cas ECG publiés
- ✅ Uptime >99% sur 2 semaines
- ✅ Budget OpenAI <$30/mois

### Gate Check Sprint 12 (Go-Live Production)
- ✅ 200 étudiants inscrits
- ✅ 50+ cas ECG validés
- ✅ 10+ enseignants créateurs actifs
- ✅ Satisfaction globale >4/5
- ✅ Validation DSI CHU sécurité
- ✅ Validation DPO RGPD

---

## 🔄 Roadmap Integration

### Sprint 1 (3j) - Infrastructure ✅ EN COURS
- docker-compose.yml avec Redis
- .env.example
- OntologyService cache
- LLMService fallback

### Sprint 2 (8j) - Auth & API
- JWT authentication
- CRUD endpoints
- Rate limiting SlowAPI
- Contact DPO RGPD

### Sprint 3 (11j) - LLM Pipeline 🎯 CRITIQUE
- Pipeline 4 étapes complet
- Dataset 30 cas validation
- Tests Precision/Recall
- **POC 5 profs + 10 étudiants**

### Sprint 4-12 - Voir architecture.md

---

## ✅ Validation & Sign-Off

**Validé par:**
- ✅ Grégoire (Product Owner) - 2026-01-10
- ✅ Winston (Architect) - 2026-01-10
- ✅ John (PM) - 2026-01-10
- ✅ Mary (Analyst) - 2026-01-10

**Prochaines étapes:**
1. Finaliser Sprint 1 (Winston en cours)
2. Créer Epics & Stories (John - prochain)
3. Sprint Planning S1 (Bob Scrum Master)

---

**Document PRD - Version 1.0**  
*Dernière mise à jour : 2026-01-10*  
*Prochaine révision : Après Gate Check Sprint 3*
