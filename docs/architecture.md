# 🏗️ Edu-ECG - Architecture Document

**Version :** 1.0  
**Date :** 2026-01-10  
**Auteur :** Grégoire  
**Type :** Brownfield - Évolution vers Production

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture Système](#architecture-système)
3. [Schéma Base de Données](#schéma-base-de-données)
4. [API Backend](#api-backend)
5. [Pipeline LLM](#pipeline-llm)
6. [Sécurité](#sécurité)
7. [Infrastructure](#infrastructure)
8. [Flux de Données](#flux-de-données)

---

## 🎯 Vue d'Ensemble

### Objectifs Architecturaux

- ✅ **Robustesse** - Production CHU avec disponibilité >99.5%
- ✅ **Sécurité** - Authentification JWT + RBAC + RGPD
- ✅ **Scalabilité** - Support 200 utilisateurs simultanés
- ✅ **Maintenabilité** - Stack standard + documentation complète
- ✅ **Déployabilité** - Docker Compose one-click

### Contraintes

- 🏥 **Réseau CHU interne uniquement** (pas d'internet public)
- 🐳 **Déploiement Docker obligatoire** (VM Ubuntu Server 22.04)
- 🔐 **RGPD strict** - Anonymisation automatique après 5 ans
- 💰 **Budget API OpenAI limité** (~200-300€/mois)
- 👥 **Équipe réduite** - 2-3 développeurs full-stack

### Principes de Design

1. **KISS** - Keep It Simple, Stupid (MVP avant optimisation)
2. **Convention over Configuration** - Frameworks opinionated
3. **API-First** - Backend découplé du frontend
4. **Database as Source of Truth** - PostgreSQL central
5. **Fail-Safe** - Validation manuelle si LLM échoue

---

## 🏛️ Architecture Système

### Architecture Globale (4 Tiers)

```
┌────────────────────────────────────────────────────────┐
│                    Réseau Interne CHU                   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │          Tier 1: Reverse Proxy (Nginx)          │   │
│  │  - SSL Termination (certificat CHU)             │   │
│  │  - Load Balancing (si scale horizontal)         │   │
│  │  - Static Files Serving                         │   │
│  │  - Rate Limiting (10 req/s par IP)              │   │
│  └────────────────┬────────────────────────────────┘   │
│                   │                                     │
│         ┌─────────┴─────────┐                          │
│         │                   │                          │
│  ┌──────▼─────────┐  ┌──────▼─────────┐               │
│  │ Tier 2: Frontend│  │ Tier 3: Backend │               │
│  │   (Streamlit)   │  │   (FastAPI)     │               │
│  │                 │  │                 │               │
│  │ - UI Components │  │ - REST API      │               │
│  │ - Session State │  │ - Business Logic│               │
│  │ - Visualisation │  │ - LLM Pipeline  │               │
│  │ - Forms         │◄─┤ - Auth/RBAC    │               │
│  └─────────────────┘  └────────┬────────┘               │
│                                │                        │
│                   ┌────────────▼────────────┐           │
│                   │  Tier 4: Database       │           │
│                   │    (PostgreSQL 15)      │           │
│                   │                         │           │
│                   │  - 8 Tables principales │           │
│                   │  - JSONB Concepts       │           │
│                   │  - Views Matérialisées  │           │
│                   │  - pg_cron Jobs         │           │
│                   └─────────────────────────┘           │
│                                                         │
│  Volumes Persistants:                                   │
│  - postgres_data/  (Base de données)                    │
│  - ecg_pdfs/       (Fichiers ECG)                       │
│  - backups/        (Sauvegardes quotidiennes)           │
└────────────────────────────────────────────────────────┘
```

### Composants Détaillés

#### 1. Nginx (Reverse Proxy)

**Image :** `nginx:alpine`  
**Port :** 80 (HTTP) + 443 (HTTPS)  
**Rôle :** Point d'entrée unique

**Configuration :**
```nginx
upstream frontend {
    server frontend:8501;
}

upstream backend {
    server backend:8000;
}

server {
    listen 443 ssl;
    server_name edu-ecg.chu-local;

    ssl_certificate /etc/nginx/ssl/edu-ecg.crt;
    ssl_certificate_key /etc/nginx/ssl/edu-ecg.key;

    # Frontend Streamlit
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
}
```

#### 2. Frontend (Streamlit)

**Image :** `python:3.11-slim` + Streamlit  
**Port :** 8501  
**Rôle :** Interface utilisateur

**Structure :**
```
frontend/
├── app.py                 # Point d'entrée principal
├── pages/
│   ├── 1_base_ecg.py     # Navigation base ECG
│   ├── 2_practice.py     # Interface pratique étudiant
│   ├── 3_admin.py        # Interface admin
│   └── 4_dashboard.py    # Dashboards analytics
├── components/
│   ├── auth.py           # Composants authentification
│   ├── ecg_viewer.py     # Visualiseur ECG
│   └── forms.py          # Formulaires réponses
└── config.py             # Configuration Streamlit
```

**Bibliothèques :**
- `streamlit >= 1.30.0` - Framework UI
- `plotly >= 5.18.0` - Graphiques interactifs
- `pandas >= 2.1.0` - Manipulation données
- `requests >= 2.31.0` - Appels API backend

#### 3. Backend (FastAPI)

**Image :** `python:3.11-slim` + FastAPI  
**Port :** 8000  
**Rôle :** API REST + Business Logic

**Structure :**
```
backend/
├── main.py                    # FastAPI app
├── api/
│   ├── routes/
│   │   ├── auth.py           # POST /api/auth/login, /refresh
│   │   ├── users.py          # CRUD utilisateurs
│   │   ├── ecg_cases.py      # CRUD cas ECG
│   │   ├── sessions.py       # Gestion sessions
│   │   └── responses.py      # Soumission réponses
│   └── dependencies.py       # JWT validation, RBAC
├── models/
│   ├── user.py               # SQLAlchemy models
│   ├── ecg_case.py
│   └── response.py
├── schemas/
│   ├── user.py               # Pydantic schemas
│   └── response.py
├── services/
│   ├── llm_service.py        # Pipeline LLM 4 étapes
│   ├── ontology_service.py   # Parser OWL
│   └── scoring_service.py    # Scoring hiérarchique
└── core/
    ├── config.py             # Settings Pydantic
    ├── security.py           # JWT + bcrypt
    └── database.py           # SQLAlchemy engine
```

**Bibliothèques :**
- `fastapi >= 0.109.0` - Framework API
- `sqlalchemy >= 2.0.0` - ORM
- `alembic >= 1.13.0` - Migrations BDD
- `pydantic >= 2.5.0` - Validation données
- `openai >= 1.10.0` - API OpenAI
- `python-jose >= 3.3.0` - JWT
- `passlib >= 1.7.4` - Hash passwords
- `rdflib >= 7.0.0` - Parser ontologie OWL

#### 4. Database (PostgreSQL)

**Image :** `postgres:15-alpine`  
**Port :** 5432 (interne uniquement)  
**Rôle :** Persistance données

**Configuration :**
- `max_connections = 200`
- `shared_buffers = 256MB`
- `work_mem = 4MB`
- `maintenance_work_mem = 64MB`

**Extensions :**
- `pg_cron` - Tâches planifiées (anonymisation RGPD)
- `uuid-ossp` - Génération UUID

---

## 🗄️ Schéma Base de Données

### Diagramme ERD (Entity Relationship Diagram)

```
┌─────────────────┐
│   promotions    │
│─────────────────│
│ id (UUID) PK    │
│ name            │
│ academic_year   │
│ start_date      │
│ end_date        │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────────────┐
│       users             │
│─────────────────────────│
│ id (UUID) PK            │
│ username (unique)       │
│ email (unique)          │
│ password_hash           │
│ role (enum)             │──────────┐
│ promotion_id FK         │          │
│ first_name              │          │
│ last_name               │          │
│ created_at              │          │
│ last_login              │          │
│ is_active               │          │
│ anonymized_at           │          │
│ deletion_scheduled_at   │          │
└─────────┬───────────────┘          │
          │                          │
          │ 1:N                      │ 1:N (created_by)
          │                          │
┌─────────▼──────────────┐    ┌──────▼─────────────────┐
│ student_progress       │    │     ecg_cases          │
│────────────────────────│    │────────────────────────│
│ id (UUID) PK           │    │ id (UUID) PK           │
│ student_id FK          │    │ title                  │
│ total_cases_attempted  │    │ clinical_context       │
│ total_cases_completed  │    │ pdf_path               │
│ average_score          │    │ difficulty_level       │
│ beginner_score_avg     │    │ correction_text        │
│ intermediate_score_avg │    │ correction_concepts    │──┐
│ advanced_score_avg     │    │   (JSONB)              │  │
│ mastered_concepts      │    │ created_by FK          │  │
│   (JSONB)              │    │ validated_by FK        │  │
│ weak_concepts (JSONB)  │    │ created_at             │  │
│ last_activity          │    │ updated_at             │  │
│ updated_at             │    │ is_published           │  │
└────────────────────────┘    │ tags (array)           │  │
                              │ pathologies (array)    │  │
                              └──────┬─────────────────┘  │
                                     │                    │
                                     │ 1:N                │
                                     │                    │
                      ┌──────────────▼─────────┐          │
                      │   learning_sessions    │          │
                      │────────────────────────│          │
                      │ id (UUID) PK           │          │
                      │ title                  │          │
                      │ description            │          │
                      │ session_type (enum)    │          │
                      │ created_by FK          │          │
                      │ target_promotions      │          │
                      │   (UUID[])             │          │
                      │ target_students        │          │
                      │   (UUID[])             │          │
                      │ time_limit_minutes     │          │
                      │ shuffle_cases          │          │
                      │ show_feedback          │          │
                      │ available_from         │          │
                      │ available_until        │          │
                      │ created_at             │          │
                      │ is_active              │          │
                      └──────┬─────────────────┘          │
                             │                            │
                             │ 1:N                        │
                             │                            │
                  ┌──────────▼──────────┐                 │
                  │   session_cases     │                 │
                  │─────────────────────│                 │
                  │ id (UUID) PK        │                 │
                  │ session_id FK       │                 │
                  │ ecg_case_id FK      │◄────────────────┘
                  │ display_order       │
                  │ weight              │
                  └─────────────────────┘

┌──────────────────────────┐
│  student_responses       │
│──────────────────────────│
│ id (UUID) PK             │
│ student_id FK            │
│ ecg_case_id FK           │
│ session_id FK (nullable) │
│ response_text            │
│ concepts_identified      │──┐ JSONB
│   (JSONB)                │  │ [{"uri": "...", "label": "...", "score": ...}]
│ score_global             │  │
│ concepts_matched (JSONB) │◄─┘
│ concepts_missed (JSONB)  │
│ concepts_wrong (JSONB)   │
│ feedback_text            │
│ submitted_at             │
│ time_spent_seconds       │
│ attempt_number           │
└──────────────────────────┘

┌──────────────────────────┐
│  anonymization_logs      │
│──────────────────────────│
│ id (UUID) PK             │
│ user_id (UUID)           │
│ anonymized_at            │
│ anonymized_by FK         │
│ reason                   │
│ data_deleted (JSONB)     │
└──────────────────────────┘
```

### Tables Détaillées

#### Table: `users`

**Rôle :** Gestion utilisateurs + authentification

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'teacher', 'admin')),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    promotion_id UUID REFERENCES promotions(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    anonymized_at TIMESTAMP,
    deletion_scheduled_at TIMESTAMP,
    
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_promotion ON users(promotion_id);
CREATE INDEX idx_users_deletion ON users(deletion_scheduled_at) WHERE deletion_scheduled_at IS NOT NULL;
```

**RGPD :** Fonction auto-anonymisation

```sql
CREATE OR REPLACE FUNCTION auto_anonymize_old_users()
RETURNS void AS $$
BEGIN
    -- Anonymiser utilisateurs > 5 ans inactifs
    UPDATE users
    SET 
        email = 'deleted_' || id || '@anonymized.local',
        password_hash = 'ANONYMIZED',
        first_name = 'Anonyme',
        last_name = 'Anonyme',
        anonymized_at = NOW(),
        is_active = FALSE
    WHERE 
        deletion_scheduled_at < NOW()
        AND anonymized_at IS NULL;
        
    -- Logger anonymisations
    INSERT INTO anonymization_logs (user_id, reason, data_deleted)
    SELECT id, 'Auto 5 ans inactivité', 
           jsonb_build_object('email', email, 'name', first_name || ' ' || last_name)
    FROM users
    WHERE anonymized_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Tâche quotidienne (pg_cron)
SELECT cron.schedule('anonymize-old-users', '0 2 * * *', 'SELECT auto_anonymize_old_users()');
```

#### Table: `ecg_cases`

**Rôle :** Stockage cas ECG + corrections validées

```sql
CREATE TABLE ecg_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    clinical_context TEXT,
    pdf_path VARCHAR(500) NOT NULL,
    difficulty_level VARCHAR(20) CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    
    -- Correction enseignant
    correction_text TEXT NOT NULL,
    correction_concepts JSONB, -- Format: [{"uri": "...", "label": "BAV1", "weight": 1.0, "context": "..."}]
    
    -- Métadonnées
    created_by UUID REFERENCES users(id),
    validated_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_published BOOLEAN DEFAULT FALSE,
    
    -- Filtres
    tags VARCHAR(100)[],
    pathologies VARCHAR(100)[]
);

CREATE INDEX idx_ecg_difficulty ON ecg_cases(difficulty_level);
CREATE INDEX idx_ecg_published ON ecg_cases(is_published);
CREATE INDEX idx_ecg_tags ON ecg_cases USING GIN(tags);
CREATE INDEX idx_ecg_pathologies ON ecg_cases USING GIN(pathologies);
```

**Exemple JSONB `correction_concepts` :**

```json
[
  {
    "uri": "http://ontology.chu/ecg#BAV1",
    "label": "Bloc auriculo-ventriculaire du 1er degré",
    "label_en": "First-degree atrioventricular block",
    "weight": 1.0,
    "context": "PR à 220ms sur toutes les dérivations",
    "category": "conduction_disorder"
  },
  {
    "uri": "http://ontology.chu/ecg#RythmeSinusal",
    "label": "Rythme sinusal",
    "weight": 0.5,
    "context": "Ondes P régulières",
    "category": "rhythm"
  }
]
```

#### Table: `student_responses`

**Rôle :** Réponses étudiants + résultats scoring LLM

```sql
CREATE TABLE student_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) NOT NULL,
    ecg_case_id UUID REFERENCES ecg_cases(id) NOT NULL,
    session_id UUID REFERENCES learning_sessions(id),
    
    -- Réponse étudiant
    response_text TEXT NOT NULL,
    concepts_identified JSONB,
    
    -- Scoring
    score_global FLOAT CHECK (score_global >= 0 AND score_global <= 100),
    concepts_matched JSONB,   -- Concepts corrects
    concepts_missed JSONB,    -- Concepts manquants
    concepts_wrong JSONB,     -- Concepts erronés
    feedback_text TEXT,
    
    -- Métadonnées
    submitted_at TIMESTAMP DEFAULT NOW(),
    time_spent_seconds INTEGER,
    attempt_number INTEGER DEFAULT 1,
    
    CONSTRAINT unique_student_case_session 
        UNIQUE(student_id, ecg_case_id, session_id, attempt_number)
);

CREATE INDEX idx_responses_student ON student_responses(student_id);
CREATE INDEX idx_responses_ecg ON student_responses(ecg_case_id);
CREATE INDEX idx_responses_session ON student_responses(session_id);
CREATE INDEX idx_responses_submitted ON student_responses(submitted_at);
```

### Vues Matérialisées (Analytics)

```sql
-- Vue performance par promotion
CREATE MATERIALIZED VIEW mv_promotion_stats AS
SELECT 
    p.id as promotion_id,
    p.name as promotion_name,
    p.academic_year,
    COUNT(DISTINCT u.id) as total_students,
    AVG(sp.average_score) as avg_score,
    COUNT(DISTINCT sr.ecg_case_id) as unique_cases_attempted,
    COUNT(sr.id) as total_responses
FROM promotions p
LEFT JOIN users u ON u.promotion_id = p.id AND u.role = 'student'
LEFT JOIN student_progress sp ON sp.student_id = u.id
LEFT JOIN student_responses sr ON sr.student_id = u.id
GROUP BY p.id, p.name, p.academic_year;

CREATE UNIQUE INDEX idx_mv_promotion_stats ON mv_promotion_stats(promotion_id);

-- Refresh quotidien (pg_cron)
SELECT cron.schedule('refresh-promotion-stats', '0 3 * * *', 
    'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_promotion_stats');
```

---

## 🔌 API Backend

### Endpoints Principaux

#### Authentication

```
POST   /api/auth/register        # Inscription (admin only)
POST   /api/auth/login           # Connexion (JWT token)
POST   /api/auth/refresh         # Refresh token
POST   /api/auth/logout          # Déconnexion
GET    /api/auth/me              # Profil utilisateur courant
```

#### Users Management

```
GET    /api/users                # Liste utilisateurs (admin/teacher)
GET    /api/users/{id}           # Détails utilisateur
PUT    /api/users/{id}           # Modifier utilisateur
DELETE /api/users/{id}           # Supprimer utilisateur (admin)
GET    /api/users/{id}/progress  # Progression étudiant (teacher)
```

#### ECG Cases

```
GET    /api/ecg-cases            # Liste cas ECG (filtres: difficulty, tags, published)
GET    /api/ecg-cases/{id}       # Détails cas ECG
POST   /api/ecg-cases            # Créer cas ECG (teacher/admin)
PUT    /api/ecg-cases/{id}       # Modifier cas ECG
DELETE /api/ecg-cases/{id}       # Supprimer cas ECG (admin)
POST   /api/ecg-cases/batch      # Import batch (admin)
```

#### Learning Sessions

```
GET    /api/sessions             # Liste sessions (teacher/admin)
GET    /api/sessions/{id}        # Détails session
POST   /api/sessions             # Créer session (teacher/admin)
PUT    /api/sessions/{id}        # Modifier session
DELETE /api/sessions/{id}        # Supprimer session
GET    /api/sessions/{id}/results # Résultats session (teacher)
```

#### Student Responses

```
POST   /api/responses            # Soumettre réponse étudiant
GET    /api/responses/{id}       # Détails réponse
GET    /api/responses/my         # Mes réponses (student)
GET    /api/responses/ecg/{id}   # Réponses pour un ECG (teacher)
```

### Exemple: POST /api/responses

**Request :**

```json
{
  "ecg_case_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "660e8400-e29b-41d4-a716-446655440000",
  "response_text": "Rythme sinusal avec BAV 1er degré. PR allongé à environ 220ms. Pas d'autre anomalie notable."
}
```

**Response :**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "score_global": 85.5,
  "concepts_identified": [
    {
      "uri": "http://ontology.chu/ecg#RythmeSinusal",
      "label": "Rythme sinusal",
      "confidence": 0.95,
      "matched": true
    },
    {
      "uri": "http://ontology.chu/ecg#BAV1",
      "label": "BAV 1er degré",
      "confidence": 0.92,
      "matched": true
    }
  ],
  "concepts_matched": [
    {"label": "Rythme sinusal", "score": 100},
    {"label": "BAV 1er degré", "score": 100}
  ],
  "concepts_missed": [],
  "concepts_wrong": [],
  "feedback_text": "Excellent ! Vous avez correctement identifié le rythme sinusal et le BAV 1er degré. Votre estimation de l'intervalle PR (220ms) est précise. Continue comme ça !",
  "submitted_at": "2026-01-10T14:30:00Z",
  "time_spent_seconds": 180
}
```

### RBAC (Role-Based Access Control)

**Matrice de permissions :**

| Endpoint | Student | Teacher | Admin |
|----------|---------|---------|-------|
| GET /api/ecg-cases | ✅ (published only) | ✅ (all) | ✅ (all) |
| POST /api/ecg-cases | ❌ | ✅ | ✅ |
| DELETE /api/ecg-cases | ❌ | ❌ | ✅ |
| POST /api/responses | ✅ (own) | ✅ (testing) | ✅ |
| GET /api/responses/ecg/{id} | ❌ | ✅ | ✅ |
| GET /api/users | ❌ | ✅ (promotion only) | ✅ (all) |
| POST /api/users | ❌ | ❌ | ✅ |

**Implémentation FastAPI :**

```python
from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = get_user_by_username(username)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(required_role: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        role_hierarchy = {"student": 1, "teacher": 2, "admin": 3}
        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 99):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Utilisation
@app.post("/api/ecg-cases")
async def create_ecg_case(
    case: ECGCaseCreate,
    current_user: User = Depends(require_role("teacher"))
):
    # ...
```

---

## 🤖 Pipeline LLM

### Architecture Pipeline (4 Étapes)

```
┌─────────────────────────────────────────────────────────────┐
│                 ÉTAPE 1: Extraction NER                     │
│  Input: "Rythme sinusal avec FA rapide à 120 bpm"          │
│  LLM: GPT-4o avec structured output                         │
│  Output: ["Rythme sinusal", "FA", "Fréquence 120 bpm"]     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ÉTAPE 2: Mapping Ontologique                   │
│  Input: ["Rythme sinusal", "FA", "Fréquence 120 bpm"]      │
│  Processus:                                                  │
│    - Parser ontologie OWL (rdflib)                          │
│    - Matching synonymes (FA = Fibrillation Auriculaire)    │
│    - Normalisation FR/EN                                    │
│  Output: [                                                   │
│    {uri: "...#RythmeSinusal", label: "..."},               │
│    {uri: "...#FibrillationAuriculaire", label: "..."},     │
│    {uri: "...#Tachycardie", label: "..."}                  │
│  ]                                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           ÉTAPE 3: Scoring Hiérarchique                     │
│  Input:                                                      │
│    - concepts_identified (étudiant)                         │
│    - concepts_expected (correction validée)                 │
│  Processus: 5 relations ontologiques                        │
│    1. Granularité: "PR allongé" vs "BAV1" → 80%            │
│    2. Indication: Signe + Diagnostic → 100%                │
│    3. Contradiction: "RS" + "FA" → -20%                    │
│    4. Critères: BBD = 3 critères → 33% par critère         │
│    5. Localisation: STEMI + région → bonus                 │
│  Output: score_global (0-100)                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          ÉTAPE 4: Feedback Pédagogique                      │
│  Input:                                                      │
│    - score_global                                            │
│    - concepts_matched / missed / wrong                      │
│    - session_type (quiz / guidé / examen)                   │
│  LLM: GPT-4o avec prompt pédagogique                        │
│  Output selon mode:                                          │
│    - Quiz: "Très bien ! Concept X correct. Concept Y ?"    │
│    - Guidé: "Avez-vous regardé l'intervalle PR ?"          │
│    - Examen: Feedback complet après soumission             │
└─────────────────────────────────────────────────────────────┘
```

### Implémentation Python

**services/llm_service.py**

```python
from openai import OpenAI
from pydantic import BaseModel
from typing import List

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ExtractedConcept(BaseModel):
    text: str
    category: str  # "rhythm", "conduction", "morphology", etc.
    confidence: float

class LLMService:
    
    async def extract_concepts(self, response_text: str) -> List[ExtractedConcept]:
        """Étape 1: Extraction NER"""
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": response_text}
            ],
            response_format=ExtractedConcept
        )
        return completion.choices[0].message.parsed
    
    async def map_to_ontology(
        self, 
        concepts: List[ExtractedConcept],
        ontology: OntologyGraph
    ) -> List[MappedConcept]:
        """Étape 2: Mapping ontologique"""
        mapped = []
        for concept in concepts:
            # Recherche dans ontologie (synonymes, labels FR/EN)
            uri = ontology.find_concept(concept.text)
            if uri:
                mapped.append(MappedConcept(
                    uri=uri,
                    label=ontology.get_label(uri),
                    original_text=concept.text,
                    confidence=concept.confidence
                ))
        return mapped
    
    async def compute_score(
        self,
        identified: List[MappedConcept],
        expected: List[MappedConcept],
        ontology: OntologyGraph
    ) -> ScoringResult:
        """Étape 3: Scoring hiérarchique"""
        scorer = HierarchicalScorer(ontology)
        
        matched = []
        missed = []
        wrong = []
        total_score = 0
        
        for exp in expected:
            # Chercher match exact ou hiérarchique
            match = scorer.find_best_match(exp, identified)
            if match:
                relation_score = scorer.compute_relation_score(exp, match)
                matched.append({
                    "expected": exp.label,
                    "found": match.label,
                    "score": relation_score
                })
                total_score += relation_score * exp.weight
            else:
                missed.append(exp.label)
        
        # Concepts identifiés mais non attendus
        for ident in identified:
            if not any(m["found"] == ident.label for m in matched):
                wrong.append(ident.label)
        
        # Pénalité contradictions
        contradictions = scorer.detect_contradictions(identified)
        total_score -= len(contradictions) * 20
        
        return ScoringResult(
            score_global=max(0, min(100, total_score)),
            concepts_matched=matched,
            concepts_missed=missed,
            concepts_wrong=wrong,
            contradictions=contradictions
        )
    
    async def generate_feedback(
        self,
        scoring_result: ScoringResult,
        session_type: str,
        response_text: str
    ) -> str:
        """Étape 4: Feedback pédagogique"""
        prompt = FEEDBACK_PROMPTS[session_type].format(
            score=scoring_result.score_global,
            matched=scoring_result.concepts_matched,
            missed=scoring_result.concepts_missed,
            wrong=scoring_result.concepts_wrong
        )
        
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": response_text}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return completion.choices[0].message.content
```

### Scoring Hiérarchique Détaillé

**services/scoring_service.py**

```python
class HierarchicalScorer:
    
    def __init__(self, ontology: OntologyGraph):
        self.ontology = ontology
    
    def compute_relation_score(
        self, 
        expected: MappedConcept, 
        found: MappedConcept
    ) -> float:
        """Calcul score selon relation ontologique"""
        
        # 1. Match exact
        if expected.uri == found.uri:
            return 100.0
        
        # 2. Relation granularité (plusPrecisQue)
        if self.ontology.has_relation(found.uri, "plusPrecisQue", expected.uri):
            # Étudiant trop vague
            return 60.0  # "PR allongé" au lieu de "BAV1"
        
        if self.ontology.has_relation(expected.uri, "plusPrecisQue", found.uri):
            # Étudiant trop précis (mais correct)
            return 90.0  # "BAV1" au lieu de "PR allongé"
        
        # 3. Relation indication (indiqueDiagnostic)
        if self.ontology.has_relation(found.uri, "indiqueDiagnostic", expected.uri):
            # Étudiant a donné signe au lieu de diagnostic
            return 60.0  # "Sus-décalage ST" au lieu de "STEMI"
        
        if self.ontology.has_relation(expected.uri, "indiqueDiagnostic", found.uri):
            # Étudiant a donné diagnostic au lieu de signe
            return 80.0  # "STEMI" au lieu de "Sus-décalage ST"
        
        # 4. Relation parent-enfant (rdfs:subClassOf)
        if self.ontology.is_parent(expected.uri, found.uri):
            # Étudiant a donné concept parent
            return 70.0  # "Arythmie" au lieu de "FA"
        
        if self.ontology.is_child(expected.uri, found.uri):
            # Étudiant a donné concept enfant
            return 85.0
        
        # Pas de relation → concept non pertinent
        return 0.0
    
    def detect_contradictions(
        self, 
        concepts: List[MappedConcept]
    ) -> List[tuple]:
        """Détecter concepts incompatibles"""
        contradictions = []
        
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                if self.ontology.has_relation(c1.uri, "incompatibleAvec", c2.uri):
                    contradictions.append((c1.label, c2.label))
        
        return contradictions
```

---

## 🔐 Sécurité

### Authentication (JWT)

**Workflow :**

```
1. Connexion:
   POST /api/auth/login
   {username, password}
   ↓
   Vérification bcrypt
   ↓
   Génération JWT (access + refresh)
   ↓
   Return {access_token, refresh_token}

2. Requêtes API:
   Header: Authorization: Bearer <access_token>
   ↓
   Validation JWT
   ↓
   Extraction user_id + role
   ↓
   RBAC check
   ↓
   Execute endpoint

3. Refresh Token:
   POST /api/auth/refresh
   {refresh_token}
   ↓
   Nouveau access_token
```

**Configuration JWT :**

```python
SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Depuis .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 heures
REFRESH_TOKEN_EXPIRE_DAYS = 30
```

### Password Hashing (bcrypt)

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Création utilisateur
hashed_password = pwd_context.hash("password123")

# Vérification login
if pwd_context.verify(plain_password, hashed_password):
    # OK
```

### RGPD Compliance

**1. Anonymisation automatique (5 ans)**

```sql
-- Fonction pg_cron (déjà définie plus haut)
SELECT cron.schedule('anonymize-old-users', '0 2 * * *', 
    'SELECT auto_anonymize_old_users()');
```

**2. Droit à l'oubli (sur demande)**

```python
@app.delete("/api/users/{user_id}/gdpr-delete")
async def gdpr_delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role("admin"))
):
    """Suppression RGPD (anonymisation immédiate)"""
    user = get_user(user_id)
    
    # Anonymiser données personnelles
    user.email = f"deleted_{user.id}@anonymized.local"
    user.password_hash = "ANONYMIZED"
    user.first_name = "Anonyme"
    user.last_name = "Anonyme"
    user.anonymized_at = datetime.now()
    user.is_active = False
    
    # Logger suppression
    log_anonymization(user_id, "Demande utilisateur RGPD", current_user.id)
    
    # Conserver données pédagogiques anonymisées
    # (student_responses, student_progress gardés avec user_id anonyme)
    
    db.commit()
    return {"message": "Utilisateur anonymisé avec succès"}
```

### Rate Limiting

**Nginx :**

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

location /api/ {
    limit_req zone=api burst=20 nodelay;
}

location /api/auth/login {
    limit_req zone=login burst=3 nodelay;
}
```

### SSL/TLS

**Certificat CHU (fourni par DSI) :**

```yaml
# docker-compose.prod.yml
nginx:
  volumes:
    - ./ssl/edu-ecg.chu-local.crt:/etc/nginx/ssl/cert.crt:ro
    - ./ssl/edu-ecg.chu-local.key:/etc/nginx/ssl/cert.key:ro
```

**Configuration Nginx :**

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512';
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

---

## 🐳 Infrastructure

### Docker Compose Configuration

**docker-compose.yml :**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: edu-ecg-db
    environment:
      POSTGRES_DB: ${DB_NAME:-edu_ecg}
      POSTGRES_USER: ${DB_USER:-eduecg_admin}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-eduecg_admin}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - edu-ecg-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: edu-ecg-api
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ENVIRONMENT: ${ENVIRONMENT:-production}
    volumes:
      - ./data/ecg_pdfs:/app/data/ecg_pdfs
      - ./data/ontology:/app/data/ontology
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - edu-ecg-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: edu-ecg-frontend
    environment:
      BACKEND_URL: http://backend:8000
    ports:
      - "8501:8501"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - edu-ecg-network

  nginx:
    image: nginx:alpine
    container_name: edu-ecg-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
    networks:
      - edu-ecg-network

volumes:
  postgres_data:
    driver: local

networks:
  edu-ecg-network:
    driver: bridge
```

**.env (environnement) :**

```bash
# Database
DB_NAME=edu_ecg
DB_USER=eduecg_admin
DB_PASSWORD=<SECURE_PASSWORD>

# OpenAI
OPENAI_API_KEY=sk-...

# JWT
JWT_SECRET_KEY=<SECURE_RANDOM_KEY>

# Environment
ENVIRONMENT=production
```

### Déploiement CHU (Ubuntu Server 22.04)

**Prérequis DSI CHU :**

```bash
# Installation Docker + Docker Compose
sudo apt update
sudo apt install -y docker.io docker-compose

# Permissions utilisateur
sudo usermod -aG docker $USER

# Firewall (réseau interne uniquement)
sudo ufw allow from 10.0.0.0/8 to any port 80
sudo ufw allow from 10.0.0.0/8 to any port 443
sudo ufw enable
```

**Déploiement :**

```bash
# Cloner repository
git clone <repo_url> /opt/edu-ecg
cd /opt/edu-ecg

# Créer .env
cp .env.example .env
nano .env  # Configurer passwords

# Lancer stack
docker-compose up -d

# Vérifier santé
docker-compose ps
docker-compose logs -f
```

### Backups Automatiques

**Script backup quotidien :**

```bash
#!/bin/bash
# /opt/edu-ecg/scripts/backup.sh

BACKUP_DIR="/opt/edu-ecg/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker-compose exec -T postgres pg_dump \
  -U eduecg_admin edu_ecg \
  > "$BACKUP_DIR/edu_ecg_$DATE.sql"

# Compression
gzip "$BACKUP_DIR/edu_ecg_$DATE.sql"

# Backup PDFs
tar -czf "$BACKUP_DIR/ecg_pdfs_$DATE.tar.gz" ./data/ecg_pdfs

# Rétention 30 jours
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Cron quotidien :**

```bash
# crontab -e
0 2 * * * /opt/edu-ecg/scripts/backup.sh >> /var/log/edu-ecg-backup.log 2>&1
```

---

## 🔄 Flux de Données

### Flux 1: Import Cas ECG (Enseignant)

```
┌─────────────┐
│  Enseignant │
└──────┬──────┘
       │ 1. Upload PDF + Énoncé clinique
       ▼
┌──────────────────┐
│ Frontend         │
│ (Streamlit)      │
└──────┬───────────┘
       │ 2. POST /api/ecg-cases
       │    {title, clinical_context, pdf_file}
       ▼
┌──────────────────┐
│ Backend (FastAPI)│
│ - Valide JWT     │
│ - Check RBAC     │
│ - Save PDF       │
└──────┬───────────┘
       │ 3. INSERT INTO ecg_cases
       │    status='draft'
       ▼
┌──────────────────┐
│ PostgreSQL       │
│ Table: ecg_cases │
└──────────────────┘
       │
       │ 4. Enseignant rédige correction
       ▼
┌──────────────────┐
│ Frontend Form    │
│ Textarea:        │
│ "Rythme sinusal  │
│  avec BAV1..."   │
└──────┬───────────┘
       │ 5. PUT /api/ecg-cases/{id}/validate
       │    {correction_text: "..."}
       ▼
┌──────────────────────┐
│ Backend LLM Service  │
│ - Extract concepts   │
│ - Map to ontology    │
└──────┬───────────────┘
       │ 6. Return concepts for validation
       │    [{uri: "...", label: "BAV1", weight: 1.0}]
       ▼
┌──────────────────┐
│ Frontend Review  │
│ ☑ BAV1           │
│ ☑ Rythme sinusal │
│ ☐ Tachycardie    │
│ [Valider]        │
└──────┬───────────┘
       │ 7. PUT /api/ecg-cases/{id}/publish
       │    {correction_concepts: [...]}
       ▼
┌──────────────────┐
│ PostgreSQL       │
│ UPDATE ecg_cases │
│ SET is_published │
│     = TRUE       │
└──────────────────┘
```

### Flux 2: Pratique Étudiant + Correction

```
┌─────────────┐
│   Étudiant  │
└──────┬──────┘
       │ 1. GET /api/ecg-cases (published only)
       ▼
┌──────────────────┐
│ Frontend         │
│ - Galerie ECG    │
│ - Sélection cas  │
└──────┬───────────┘
       │ 2. Affichage PDF + Énoncé
       ▼
┌──────────────────┐
│ Étudiant rédige  │
│ réponse texte    │
│ libre            │
└──────┬───────────┘
       │ 3. POST /api/responses
       │    {ecg_case_id, response_text}
       ▼
┌──────────────────────────────┐
│ Backend - Pipeline LLM       │
│                              │
│ ÉTAPE 1: Extract concepts    │
│   → ["BAV1", "RS"]           │
│                              │
│ ÉTAPE 2: Map to ontology     │
│   → [{uri: "...", label}]    │
│                              │
│ ÉTAPE 3: Scoring             │
│   Compare vs expected        │
│   → score_global: 85.5       │
│                              │
│ ÉTAPE 4: Generate feedback   │
│   → "Excellent ! ..."        │
└──────┬───────────────────────┘
       │ 4. INSERT student_responses
       │    UPDATE student_progress
       ▼
┌──────────────────┐
│ PostgreSQL       │
│ - Réponse stockée│
│ - Score calculé  │
│ - Progression MAJ│
└──────┬───────────┘
       │ 5. Return à frontend
       ▼
┌──────────────────┐
│ Frontend Feedback│
│ Score: 85.5%     │
│ ✅ BAV1          │
│ ✅ Rythme sinusal│
│ "Excellent ! ..." │
└──────────────────┘
```

### Flux 3: Dashboard Enseignant

```
┌─────────────┐
│  Enseignant │
└──────┬──────┘
       │ 1. GET /api/sessions/{id}/results
       ▼
┌──────────────────┐
│ Backend          │
│ - Query BDD      │
└──────┬───────────┘
       │ 2. SELECT FROM student_responses
       │    JOIN users ON ...
       │    WHERE session_id = ...
       ▼
┌──────────────────────┐
│ PostgreSQL           │
│ - student_responses  │
│ - users              │
│ - student_progress   │
└──────┬───────────────┘
       │ 3. Agrégation données
       │    - Score moyen: 75.2%
       │    - Taux complétion: 85%
       │    - Top 3 difficultés
       ▼
┌──────────────────┐
│ Frontend Plotly  │
│ - Boxplot scores │
│ - Histogramme    │
│ - Top erreurs    │
└──────────────────┘
```

---

## 📊 Métriques & Monitoring

### Métriques Applicatives

**Backend (FastAPI) :**

```python
from prometheus_client import Counter, Histogram

# Requêtes API
api_requests = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])

# Temps réponse
api_response_time = Histogram('api_response_seconds', 'API response time')

# Corrections LLM
llm_corrections = Counter('llm_corrections_total', 'Total LLM corrections', ['status'])
llm_accuracy = Histogram('llm_accuracy_score', 'LLM accuracy scores')
```

**Endpoint métriques :**

```
GET /metrics  # Format Prometheus
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    """Healthcheck pour orchestration"""
    checks = {
        "database": await check_db_connection(),
        "openai_api": await check_openai_api(),
        "disk_space": check_disk_space("/data/ecg_pdfs")
    }
    
    if all(checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail=checks)
```

### Logging

**Format JSON structuré :**

```python
import logging
import json

logger = logging.getLogger("edu-ecg")

logger.info(json.dumps({
    "event": "correction_completed",
    "user_id": str(user.id),
    "ecg_case_id": str(case.id),
    "score": score_global,
    "duration_ms": duration,
    "timestamp": datetime.now().isoformat()
}))
```

---

## 🔮 Évolution & Scalabilité

### Scalabilité Horizontale (V2)

**Si charge augmente (>500 utilisateurs simultanés) :**

```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3  # 3 instances backend
  
  nginx:
    # Load balancing automatique vers replicas
```

### Ajout Cache Redis (V2)

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
```

**Usage :**
- Cache réponses LLM fréquentes
- Sessions utilisateurs
- Rate limiting distribué

### Migration React Frontend (V2)

**Si Streamlit trop limitant :**
- Next.js 14 (SSR + routing)
- TailwindCSS (design system)
- TanStack Query (API calls)
- WebSockets (sondages temps réel)

---

## ✅ Checklist Déploiement Production

### Avant Go-Live

- [ ] Tests automatisés >75% coverage
- [ ] Tests beta (10 étudiants + 2 enseignants) validés
- [ ] Backup/restore testés
- [ ] SSL certificat CHU installé
- [ ] Variables d'environnement sécurisées
- [ ] Logs centralisés configurés
- [ ] Monitoring actif (health checks)
- [ ] Documentation utilisateur complète
- [ ] Formation enseignants effectuée
- [ ] Plan rollback défini
- [ ] Support 2 semaines planifié

### Post Go-Live (Semaine 1)

- [ ] Monitoring quotidien erreurs
- [ ] Vérification backups automatiques
- [ ] Feedback utilisateurs collectés
- [ ] Performance API <200ms validée
- [ ] Budget OpenAI monitored

---

**Document Architecture - Version 1.0**  
*Dernière mise à jour : 2026-01-10*  
*Prochaine révision : Après Sprint 2 (validation infrastructure)*
