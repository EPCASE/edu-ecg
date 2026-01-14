# 🚀 Guide Configuration Rapide - Sprint 1

**Durée estimée:** 10 minutes

---

## ✅ Étape 1: Configurer les Variables d'Environnement

Éditez le fichier `.env` (créé automatiquement depuis `.env.example`):

```bash
# Ouvrir .env dans votre éditeur
notepad .env
# ou
code .env
```

### Variables à Configurer:

#### 1. DB_PASSWORD (Base de données)
```bash
# Générer un mot de passe sécurisé
# Option 1: PowerShell
$password = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host "DB_PASSWORD=$password"

# Option 2: Utiliser un générateur en ligne
# https://passwordsgenerator.net/
```

Remplacer dans `.env`:
```properties
DB_PASSWORD=VotreMo tDePasseGeneré1c1
```

#### 2. JWT_SECRET_KEY (Authentification)
```bash
# PowerShell
$jwt = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
Write-Host "JWT_SECRET_KEY=$jwt"
```

Remplacer dans `.env`:
```properties
JWT_SECRET_KEY=VotreCléJWTGenerée1c1Très Longue64Caracteres
```

#### 3. OPENAI_API_KEY (LLM - Sprint 3)
```properties
# Obtenir clé sur: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

⚠️ **IMPORTANT:** Ne pas committer ce fichier `.env` dans Git !

---

## ✅ Étape 2: Démarrer Docker Desktop

### Windows
1. Ouvrir **Docker Desktop**
2. Attendre que l'icône devienne verte (Docker running)

### Vérifier Docker
```powershell
docker --version
docker-compose --version
```

---

## ✅ Étape 3: Lancer l'Infrastructure

```powershell
# Depuis le dossier du projet
cd "c:\Users\Administrateur\bmad\ECG lecture"

# Construire et démarrer tous les services
docker-compose up -d --build
```

**Durée:** 3-5 minutes (téléchargement images + build)

---

## ✅ Étape 4: Vérifier les Services

```powershell
# Voir les containers
docker-compose ps

# Devrait afficher:
# NAME                   STATUS
# edu-ecg-db             Up (healthy)
# edu-ecg-redis          Up (healthy)
# edu-ecg-api            Up (healthy)
# edu-ecg-frontend       Up
# edu-ecg-nginx          Up
```

### Voir les Logs

```powershell
# Tous les services
docker-compose logs -f

# Un service spécifique
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## ✅ Étape 5: Tester les Accès

### Frontend (Streamlit)
Ouvrir navigateur: **http://localhost:8501**

Devrait afficher: "🫀 Edu-ECG - Plateforme Pédagogique ECG"

### Backend API
Ouvrir navigateur: **http://localhost:8000/docs**

Devrait afficher: Documentation Swagger FastAPI

### Health Check
```powershell
# PowerShell
Invoke-WebRequest http://localhost:8000/health | Select-Object -ExpandProperty Content

# Devrait retourner:
# {"status":"healthy","service":"edu-ecg-backend"}
```

---

## ✅ Étape 6: Tester Redis Cache

```powershell
# Connexion Redis CLI
docker-compose exec redis redis-cli

# Commandes Redis
redis> PING
# Devrait retourner: PONG

redis> KEYS *
# Devrait retourner: (empty array) ou ontology:graph:v1 si déjà chargé

redis> EXIT
```

---

## ✅ Étape 7: Tester PostgreSQL

```powershell
# Connexion PostgreSQL
docker-compose exec postgres psql -U eduecg_admin edu_ecg

# Commandes SQL
edu_ecg=# \dt
# Liste tables (vide pour l'instant - Sprint 2)

edu_ecg=# SELECT version();
# Devrait afficher: PostgreSQL 15.x

edu_ecg=# \q
```

---

## 🎉 Sprint 1 Complété !

Si tous les tests passent, **Sprint 1 Infrastructure est TERMINÉ** ! ✅

### Prochaine Étape: Sprint 2 (8 jours)

```powershell
# Arrêter les services
docker-compose down

# Redémarrer plus tard
docker-compose up -d
```

---

## 🐛 Troubleshooting

### Erreur: Port 8501 déjà utilisé
```powershell
# Trouver processus
netstat -ano | findstr :8501

# Tuer processus (remplacer PID)
taskkill /F /PID <PID>
```

### Erreur: Docker not running
1. Démarrer Docker Desktop
2. Attendre 1-2 minutes
3. Réessayer `docker-compose up -d`

### Erreur: Permission denied
```powershell
# Exécuter PowerShell en Administrateur
# Puis réessayer commandes
```

### Backend ne démarre pas
```powershell
# Voir logs détaillés
docker-compose logs backend

# Reconstruire image
docker-compose build backend
docker-compose up -d backend
```

---

## 📊 Vérification Finale

**Checklist Sprint 1:**

- [ ] `.env` configuré avec secrets
- [ ] Docker Desktop démarré
- [ ] `docker-compose ps` montre 5 containers UP
- [ ] Frontend accessible sur http://localhost:8501
- [ ] Backend API docs sur http://localhost:8000/docs
- [ ] Health check retourne `{"status":"healthy"}`
- [ ] Redis répond PONG
- [ ] PostgreSQL accessible

**Si tous cochés → Sprint 1 RÉUSSI ! 🎉**

---

**Durée totale:** 10-15 minutes  
**Prochaine étape:** Sprint 2 - Authentication & API (8 jours)
