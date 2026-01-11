# 🚀 SPRINT 2 - PRODUCTION HARDENING

**Date début :** 2026-01-10  
**Date fin :** 2026-01-24 (2 semaines)  
**Objectif :** Transformer le POC en MVP Production-Ready  
**Lead :** Amelia (Dev) + Winston (Architecture)

---

## 🎯 OBJECTIFS SPRINT

### Vision
Passer d'un POC fonctionnel à un système production-ready capable de servir 100+ étudiants avec fiabilité, performance et observabilité.

### Success Metrics
- ✅ Cache LLM : Réduction 70% appels API
- ✅ Latence : <2s par correction (actuellement ~3-5s)
- ✅ Disponibilité : 99.5% uptime
- ✅ Coût : <$0.01 par correction (actuellement ~$0.05)
- ✅ Tests : Coverage >80%
- ✅ Monitoring : Dashboard Grafana opérationnel

---

## 📅 PLANNING DÉTAILLÉ

### 🗓️ SEMAINE 1 : Infrastructure & Performance

#### **Jour 1-2 (Lundi-Mardi) : Cache LLM Redis** 🔥

**Ticket #1 : Implémentation Cache Redis**

**Objectif :** Réduire appels API OpenAI de 70% via cache intelligent

**Tasks :**
1. Setup Redis (local + Heroku addon)
2. Créer `backend/services/llm_cache_service.py`
3. Intégrer dans `llm_semantic_matcher.py`
4. Tests unitaires cache (hit/miss/expiration)

**Spec technique :**
```python
# Cache key format
key = f"llm_match:{hash(student_concept)}:{hash(expected_concept)}"

# Cache structure
{
    "match": true,
    "match_type": "abbreviation",
    "confidence": 95,
    "explanation": "...",
    "cached_at": "2026-01-10T10:30:00Z",
    "ttl": 86400  # 24h
}
```

**Acceptance Criteria :**
- [ ] Redis connecté (local + prod)
- [ ] Cache hit rate >60% après 1h utilisation
- [ ] Fallback gracieux si Redis down
- [ ] TTL configurable (env var)
- [ ] Tests unitaires passent

**Estimation :** 12h  
**Priorité :** P0 (Critique)

---

#### **Jour 3 (Mercredi) : Rate Limiting & Retry Logic** ⚡

**Ticket #2 : Rate Limiting OpenAI API**

**Objectif :** Éviter dépassement quota OpenAI (60 req/min tier 1)

**Tasks :**
1. Implémenter `RateLimiter` class (token bucket algorithm)
2. Queue système si dépassement
3. Backoff exponentiel sur erreurs
4. Tests stress (100 req simultanées)

**Spec technique :**
```python
class RateLimiter:
    def __init__(self, max_requests=60, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def acquire(self):
        # Wait if needed, return when allowed
        pass
```

**Acceptance Criteria :**
- [ ] Max 60 req/min respecté
- [ ] Queue FIFO si dépassement
- [ ] Timeout configurable
- [ ] Metrics exposées (requests_queued, requests_throttled)

**Estimation :** 6h  
**Priorité :** P0 (Critique)

---

**Ticket #3 : Retry Logic avec Backoff**

**Objectif :** Resilience face aux timeouts/erreurs API

**Tasks :**
1. Decorator `@retry_with_backoff`
2. 3 tentatives : 5s → 10s → 15s
3. Fallback matching déterministe si 3 échecs
4. Logging détaillé erreurs

**Spec technique :**
```python
@retry_with_backoff(max_retries=3, backoff_factor=2)
def semantic_match(student_concept, expected_concept):
    # ... existing code
    pass
```

**Acceptance Criteria :**
- [ ] 3 tentatives avec backoff exponentiel
- [ ] Fallback déterministe après 3 échecs
- [ ] Logs structurés (JSON)
- [ ] Tests mock API failures

**Estimation :** 4h  
**Priorité :** P1 (Important)

---

#### **Jour 4 (Jeudi) : Logging Structuré** 📝

**Ticket #4 : Migration vers Logging Structuré**

**Objectif :** Logs JSON pour ELK stack (Elasticsearch, Logstash, Kibana)

**Tasks :**
1. Remplacer `print()` par `logger.info()`
2. Format JSON structuré
3. Contexte enrichi (user_id, case_id, session_id)
4. Niveaux : DEBUG, INFO, WARN, ERROR

**Spec technique :**
```json
{
  "timestamp": "2026-01-10T10:30:45.123Z",
  "level": "INFO",
  "service": "llm_semantic_matcher",
  "event": "match_found",
  "context": {
    "user_id": "greg_001",
    "case_id": "EPIC1_002",
    "session_id": "sess_abc123"
  },
  "data": {
    "student_concept": "BAV2M1",
    "expected_concept": "BAV 2 Mobitz 1",
    "match_type": "abbreviation",
    "confidence": 95,
    "cached": true,
    "latency_ms": 45
  }
}
```

**Acceptance Criteria :**
- [ ] Tous `print()` remplacés
- [ ] Format JSON valide
- [ ] Rotation logs (max 100MB)
- [ ] Pas de PII (données personnelles) dans logs

**Estimation :** 4h  
**Priorité :** P1 (Important)

---

#### **Jour 5 (Vendredi) : Configuration Flexible** ⚙️

**Ticket #5 : Externaliser Configuration**

**Objectif :** Paramètres modifiables sans redéploiement

**Tasks :**
1. Créer `config/llm_config.yaml`
2. Variables d'environnement (.env)
3. Validation schéma (pydantic)
4. Hot reload configuration

**Configuration exposée :**
```yaml
llm:
  model: "gpt-4o"
  temperature: 0.1
  max_tokens: 300
  confidence_threshold: 70
  retry_max_attempts: 3
  retry_backoff_factor: 2

cache:
  enabled: true
  ttl_seconds: 86400
  redis_url: "redis://localhost:6379"

rate_limit:
  max_requests: 60
  time_window: 60
```

**Acceptance Criteria :**
- [ ] Config YAML chargée au démarrage
- [ ] Override via env vars (12-factor app)
- [ ] Validation schéma (erreur si invalide)
- [ ] Hot reload sans restart (optionnel)

**Estimation :** 4h  
**Priorité :** P2 (Nice to have)

---

### 🗓️ SEMAINE 2 : Observabilité & Tests

#### **Jour 6-7 (Lundi-Mardi) : Métriques Prometheus** 📊

**Ticket #6 : Instrumentation Prometheus**

**Objectif :** Métriques temps réel pour monitoring

**Tasks :**
1. Setup Prometheus client Python
2. Exposer endpoint `/metrics`
3. Définir métriques clés
4. Intégrer dans tous services

**Métriques exposées :**
```python
# Compteurs
llm_calls_total{status="success|error|cached"}
llm_cache_hits_total
llm_cache_misses_total
corrections_total{case_id, user_level}

# Histogrammes
llm_latency_seconds{percentile="50|95|99"}
llm_confidence_score{match_type}
llm_cost_dollars

# Gauges
llm_cost_daily_dollars
llm_cost_monthly_dollars
active_users
```

**Acceptance Criteria :**
- [ ] Endpoint `/metrics` répond format Prometheus
- [ ] Toutes métriques clés présentes
- [ ] Labels pertinents (case_id, match_type)
- [ ] Pas d'impact performance (<1ms overhead)

**Estimation :** 10h  
**Priorité :** P0 (Critique)

---

#### **Jour 8 (Mercredi) : Dashboard Grafana** 📈

**Ticket #7 : Dashboard Monitoring**

**Objectif :** Visualisation temps réel métriques

**Tasks :**
1. Setup Grafana (local + Grafana Cloud)
2. Créer dashboard "LLM Semantic Matcher"
3. Panels : latence, coût, cache hit rate, erreurs
4. Alertes (coût >$10/jour, latence >3s)

**Panels dashboard :**
```
┌─────────────────────────────────────────────────┐
│ LLM Semantic Matcher - Production Dashboard    │
├─────────────────────────────────────────────────┤
│                                                 │
│  Latency (p95)          Cache Hit Rate         │
│  ┌─────────────┐        ┌──────────────┐       │
│  │   1.2s      │        │    73%       │       │
│  │  ▃▅▇▆▄▃     │        │  ████████░░  │       │
│  └─────────────┘        └──────────────┘       │
│                                                 │
│  Daily Cost             Error Rate             │
│  ┌─────────────┐        ┌──────────────┐       │
│  │   $2.45     │        │    0.3%      │       │
│  │  ▁▂▃▄▅▆     │        │  ▁▁▁▁▁▁▁▁    │       │
│  └─────────────┘        └──────────────┘       │
│                                                 │
│  Requests/min           Confidence Avg         │
│  ┌─────────────┐        ┌──────────────┐       │
│  │   24        │        │    88%       │       │
│  │  ▇▆▅▄▃▂     │        │  ▆▇▇▆▅▄      │       │
│  └─────────────┘        └──────────────┘       │
└─────────────────────────────────────────────────┘
```

**Alertes configurées :**
- 🚨 Coût > $10/jour → Email + Slack
- ⚠️ Latence p95 > 3s → Slack
- ⚠️ Error rate > 5% → Email + Slack
- ⚠️ Cache hit rate < 50% → Slack

**Acceptance Criteria :**
- [ ] Dashboard accessible (Grafana Cloud)
- [ ] 6 panels minimum
- [ ] Alertes configurées et testées
- [ ] Documentation accès dashboard

**Estimation :** 6h  
**Priorité :** P1 (Important)

---

#### **Jour 9 (Jeudi) : Tests Intégration** 🧪

**Ticket #8 : Suite Tests Complète**

**Objectif :** Coverage >80%, tests automatisés

**Tasks :**
1. Tests unitaires (pytest)
2. Tests intégration (cache + LLM)
3. Tests E2E (POC flow complet)
4. Mock OpenAI API (vcr.py)

**Structure tests :**
```
tests/
├── unit/
│   ├── test_llm_semantic_matcher.py
│   ├── test_llm_cache_service.py
│   ├── test_rate_limiter.py
│   └── test_retry_logic.py
├── integration/
│   ├── test_cache_llm_integration.py
│   └── test_poc_flow.py
├── e2e/
│   └── test_correction_complete.py
└── fixtures/
    ├── mock_openai_responses.yaml
    └── test_cases.json
```

**Coverage targets :**
- llm_semantic_matcher.py : >90%
- llm_cache_service.py : >85%
- correction_llm_poc.py : >70%
- Overall : >80%

**Acceptance Criteria :**
- [ ] Coverage >80%
- [ ] Tous tests passent (green)
- [ ] Tests rapides (<30s suite complète)
- [ ] Mock OpenAI (pas d'appels réels)
- [ ] CI/CD intégré (GitHub Actions)

**Estimation :** 8h  
**Priorité :** P0 (Critique)

---

#### **Jour 10 (Vendredi) : CI/CD Pipeline** 🔄

**Ticket #9 : GitHub Actions Pipeline**

**Objectif :** Automatisation tests + déploiement

**Tasks :**
1. Créer `.github/workflows/ci.yml`
2. Pipeline : lint → test → build → deploy
3. Environnements : dev, staging, prod
4. Secrets management (GitHub Secrets)

**Pipeline structure :**
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Lint Python
        run: |
          pip install flake8 black
          flake8 backend/ frontend/
          black --check backend/ frontend/
  
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: |
          pip install -r requirements.txt
          pytest --cov=backend --cov-report=xml
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
  
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Staging
        run: |
          heroku container:push web --app edu-ecg-staging
          heroku container:release web --app edu-ecg-staging
  
  deploy-prod:
    if: github.ref == 'refs/heads/main'
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        run: |
          heroku container:push web --app edu-ecg-prod
          heroku container:release web --app edu-ecg-prod
```

**Acceptance Criteria :**
- [ ] Pipeline s'exécute sur push/PR
- [ ] Lint + Tests passent
- [ ] Deploy auto staging (branch develop)
- [ ] Deploy auto prod (branch main)
- [ ] Notifications Slack (succès/échec)

**Estimation :** 6h  
**Priorité :** P1 (Important)

---

## 📊 SPRINT BACKLOG RÉSUMÉ

| Ticket | Titre | Priorité | Estimation | Jour |
|--------|-------|----------|------------|------|
| #1 | Cache LLM Redis | P0 | 12h | 1-2 |
| #2 | Rate Limiting | P0 | 6h | 3 |
| #3 | Retry Logic | P1 | 4h | 3 |
| #4 | Logging Structuré | P1 | 4h | 4 |
| #5 | Configuration Flexible | P2 | 4h | 5 |
| #6 | Métriques Prometheus | P0 | 10h | 6-7 |
| #7 | Dashboard Grafana | P1 | 6h | 8 |
| #8 | Tests Intégration | P0 | 8h | 9 |
| #9 | CI/CD Pipeline | P1 | 6h | 10 |

**Total effort :** 60h (10 jours × 6h/jour)

---

## 🎯 DEFINITION OF DONE

### Sprint 2 Terminé Quand :

**Infrastructure :**
- [x] Redis cache opérationnel (hit rate >60%)
- [x] Rate limiting actif (60 req/min)
- [x] Retry logic implémenté (3 tentatives)
- [x] Logs JSON structurés

**Observabilité :**
- [x] Prometheus metrics exposées
- [x] Dashboard Grafana accessible
- [x] Alertes configurées (coût, latence, erreurs)

**Qualité :**
- [x] Coverage tests >80%
- [x] CI/CD pipeline opérationnel
- [x] Documentation à jour

**Performance :**
- [x] Latence <2s (p95)
- [x] Coût <$0.01/correction
- [x] Disponibilité >99%

---

## 🚀 QUICK WINS (Optionnels)

Si on termine en avance, features bonus :

**Quick Win #1 : Mode Apprentissage/Examen** (4h)
- Toggle UI simple
- Seuil confiance : 70% (apprentissage) vs 85% (examen)
- Badge visuel mode actif

**Quick Win #2 : Health Check Endpoint** (2h)
- `/health` endpoint
- Status : Redis, OpenAI API, DB
- Uptime monitoring

**Quick Win #3 : Admin Dashboard** (6h)
- Streamlit admin interface
- Stats temps réel
- Configuration hot-reload
- Flush cache manuel

---

## 📈 SUIVI SPRINT

### Daily Standup (9h30 chaque jour)

**Questions :**
1. Qu'est-ce qui a été fait hier ?
2. Qu'est-ce qui sera fait aujourd'hui ?
3. Y a-t-il des blocages ?

### Sprint Review (Vendredi 24/01 - 14h)

**Démo :**
- Cache LLM en action (hit rate dashboard)
- Dashboard Grafana live
- Tests coverage report
- CI/CD pipeline execution

### Sprint Retrospective (Vendredi 24/01 - 15h30)

**Questions :**
1. Qu'est-ce qui a bien fonctionné ?
2. Qu'est-ce qui peut être amélioré ?
3. Actions pour Sprint 3

---

## 🛠️ INFRASTRUCTURE REQUISE

### Développement Local
```bash
# Redis
docker run -d -p 6379:6379 redis:alpine

# Prometheus
docker run -d -p 9090:9090 prom/prometheus

# Grafana
docker run -d -p 3000:3000 grafana/grafana
```

### Production (Heroku)
```bash
# Addons
heroku addons:create heroku-redis:mini       # $3/mois
heroku addons:create papertrail:choklad      # Gratuit (logs)
heroku addons:create newrelic:wayne          # Gratuit (APM)

# Config
heroku config:set REDIS_URL=redis://...
heroku config:set OPENAI_API_KEY=sk-...
heroku config:set LLM_CACHE_ENABLED=true
```

**Coût mensuel estimé :** $3 (Redis) + $5 (dyno) = **$8/mois**

---

## 📚 DOCUMENTATION

### À Créer
- [ ] `docs/CACHE_ARCHITECTURE.md`
- [ ] `docs/MONITORING_GUIDE.md`
- [ ] `docs/DEPLOYMENT_GUIDE.md`
- [ ] `docs/TROUBLESHOOTING.md`

### À Mettre à Jour
- [ ] `README.md` (nouveau setup)
- [ ] `SETUP_GUIDE.md` (Redis, Prometheus)
- [ ] `API_DOCUMENTATION.md` (endpoints metrics)

---

## 🎉 SUCCESS CRITERIA

Sprint 2 réussi si :

1. ✅ **Performance** : Latence moyenne <2s (actuellement ~3-5s)
2. ✅ **Coût** : Réduction 70% appels API via cache
3. ✅ **Qualité** : Coverage tests >80%
4. ✅ **Observabilité** : Dashboard Grafana opérationnel
5. ✅ **Automation** : CI/CD déploie automatiquement

**Metric de succès ultime :** 
Système peut gérer **100 corrections simultanées** sans dégradation performance.

---

## 👥 ÉQUIPE

**Dev Lead :** Amelia  
**Architect :** Winston  
**Product Owner :** Gregoire  
**QA :** Tests automatisés (CI/CD)

---

## 📞 COMMUNICATION

**Daily Standup :** GitHub Discussions  
**Blockers :** Slack #dev-sprint2  
**Questions :** Ce chat ou documentation  

---

**🚀 LET'S GO SPRINT 2 !**

*"Make it fast, make it reliable, make it observable."*

---

**📅 Créé :** 2026-01-10  
**🔄 Dernière MAJ :** 2026-01-10  
**✍️ Auteur :** BMad Master + Amelia + Winston
