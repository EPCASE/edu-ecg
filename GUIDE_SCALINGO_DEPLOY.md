# Guide de Déploiement Scalingo - Edu-ECG

## 🚀 Déploiement sur Scalingo

### 📋 Prérequis
- Compte Scalingo créé
- CLI Scalingo installé
- Git configuré

### 🔧 Étape 1 : Préparation du Repository

```bash
# Initialiser le repository git si pas encore fait
git init
git add .
git commit -m "Version prête pour déploiement Scalingo"

# Ajouter le remote Scalingo (remplacer YOUR_APP_NAME)
git remote add scalingo git@ssh.osc-fr1.scalingo.com:YOUR_APP_NAME.git
```

### 🌐 Étape 2 : Création de l'Application

#### Option A : Via l'interface web Scalingo
1. Se connecter à https://dashboard.scalingo.com
2. Cliquer "Create new app"
3. Choisir le nom de votre application
4. Sélectionner la région (osc-fr1 recommandé)

#### Option B : Via CLI
```bash
# Installer la CLI Scalingo
# https://doc.scalingo.com/platform/cli/start

# Créer l'application
scalingo create YOUR_APP_NAME --region osc-fr1
```

### 📦 Étape 3 : Configuration des Variables d'Environnement

```bash
# Via CLI Scalingo
scalingo --app YOUR_APP_NAME env-set STREAMLIT_SERVER_HEADLESS=true
scalingo --app YOUR_APP_NAME env-set STREAMLIT_SERVER_ENABLE_CORS=false
scalingo --app YOUR_APP_NAME env-set STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Optionnel : Configuration du port (automatique sur Scalingo)
# scalingo --app YOUR_APP_NAME env-set PORT=8080
```

### 🚀 Étape 4 : Déploiement

```bash
# Pousser le code vers Scalingo
git push scalingo main

# Suivre les logs de déploiement
scalingo --app YOUR_APP_NAME logs -f
```

### 🔍 Étape 5 : Vérification

```bash
# Ouvrir l'application
scalingo --app YOUR_APP_NAME open

# Vérifier les logs
scalingo --app YOUR_APP_NAME logs

# Vérifier le statut
scalingo --app YOUR_APP_NAME ps
```

## 📋 Fichiers de Configuration Inclus

### ✅ Procfile
- Commande de démarrage Streamlit optimisée pour Scalingo
- Configuration du port dynamique avec $PORT
- Paramètres de sécurité appropriés

### ✅ runtime.txt
- Version Python 3.11.9 (compatible Scalingo)
- Version stable et testée

### ✅ requirements.txt
- Dépendances minimales optimisées
- Versions fixées pour stabilité

### ✅ app.json
- Configuration complète pour déploiement automatique
- Variables d'environnement prédéfinies
- Métadonnées de l'application

## 🎯 Configuration Optimisée

### 🔧 Paramètres Streamlit pour Production
- `--server.headless=true` : Mode sans interface graphique
- `--server.address=0.0.0.0` : Écoute sur toutes les interfaces
- `--server.port=$PORT` : Port dynamique Scalingo
- `--server.enableCORS=false` : Sécurité optimisée
- `--server.enableXsrfProtection=false` : Compatible reverse proxy

### 📊 Ressources Recommandées
- **Container Size** : S (suffisant pour début)
- **Region** : osc-fr1 (Europe, faible latence)
- **Scaling** : 1 instance pour commencer

## 🛠️ Maintenance et Monitoring

### 📈 Commandes Utiles
```bash
# Redémarrer l'application
scalingo --app YOUR_APP_NAME restart

# Scaler l'application
scalingo --app YOUR_APP_NAME scale web:2

# Voir les métriques
scalingo --app YOUR_APP_NAME stats

# Accéder aux logs en temps réel
scalingo --app YOUR_APP_NAME logs -f
```

### 🔧 Debug et Dépannage
```bash
# Se connecter au container
scalingo --app YOUR_APP_NAME run bash

# Vérifier les variables d'environnement
scalingo --app YOUR_APP_NAME env

# Voir les processus
scalingo --app YOUR_APP_NAME ps
```

## 🎯 URL d'Accès

Une fois déployé, votre application sera accessible à :
- **URL principale** : https://YOUR_APP_NAME.osc-fr1.scalingo.io
- **URL custom** : Configurable via dashboard Scalingo

## 💡 Conseils de Production

### 🔒 Sécurité
- ✅ HTTPS automatique avec certificats SSL
- ✅ Variables d'environnement sécurisées
- ✅ Logs centralisés et monitoring

### 📊 Performance
- ✅ CDN automatique pour ressources statiques
- ✅ Auto-scaling disponible
- ✅ Monitoring intégré

### 🗄️ Données
- ✅ Persistence des fichiers dans `/app`
- ✅ Sauvegarde manuelle recommandée pour `data/` et `users/`
- ✅ Base de données externe recommandée pour production

## 🚀 Prêt pour le Déploiement !

Votre application Edu-ECG est maintenant prête pour Scalingo avec :
- ✅ Structure optimisée et nettoyée
- ✅ Configuration de déploiement complète
- ✅ Dépendances minimales et stables
- ✅ Interface moderne et responsive
- ✅ Fonctionnalités expertes et étudiants opérationnelles

**Commande de déploiement :**
```bash
git push scalingo main
```
