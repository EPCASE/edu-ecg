# 🇫🇷 Guide de Déploiement Scalingo (Hébergement Français)

## 🎯 **Pourquoi Scalingo ?**
- ✅ **Hébergement français** (données en France, RGPD natif)
- ✅ **PaaS spécialisé** pour applications web Python
- ✅ **Déploiement Git** automatique
- ✅ **Support Streamlit** natif
- ✅ **Scaling automatique**
- ✅ **SSL inclus** et domaines personnalisés
- ✅ **Prix compétitifs** starting at 7€/mois

---

## 🚀 **Déploiement en 5 Minutes**

### **1. Préparation du Code**
```bash
# Créer un dépôt Git si pas encore fait
git init
git add .
git commit -m "Initial commit pour déploiement Scalingo"

# Pousser sur GitHub/GitLab
git remote add origin https://github.com/votre-username/edu-cg.git
git push -u origin main
```

### **2. Création du Compte Scalingo**
1. Aller sur **https://scalingo.com**
2. Créer un compte (essai gratuit)
3. Installer Scalingo CLI (optionnel)

### **3. Déploiement Automatique**
```bash
# Via l'interface web Scalingo
1. "Créer une nouvelle app"
2. Connecter votre dépôt Git
3. Choisir la branche (main/master)
4. Scalingo détecte automatiquement Python
5. Cliquer "Déployer"
```

### **4. Configuration Variables d'Environnement**
Dans le dashboard Scalingo, ajouter :
```
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
```

### **5. Domaine et SSL**
- **Domaine automatique** : `https://votre-app.osc-fr1.scalingo.io`
- **Domaine personnalisé** : Configuration dans le dashboard
- **SSL automatique** : Inclus gratuitement

---

## 🔧 **Configuration Avancée**

### **Scaling et Performance**
```bash
# Via CLI Scalingo
scalingo -a votre-app scale web:2:M  # 2 conteneurs taille M
```

### **Base de Données (Optionnel)**
Pour persistance avancée :
```bash
# Ajouter PostgreSQL
scalingo -a votre-app addons-add postgresql postgresql-starter-512
```

### **Monitoring et Logs**
```bash
# Voir les logs en temps réel
scalingo -a votre-app logs -f

# Métriques de performance
# Disponibles dans le dashboard web
```

---

## 💰 **Tarification Scalingo**

### **Plan Gratuit** (Parfait pour tests)
- ✅ **1 app gratuite**
- ✅ **512MB RAM**
- ✅ **Sleep après inactivité**
- ✅ **SSL inclus**

### **Plan Starter** (7€/mois)
- ✅ **Pas de sleep**
- ✅ **1GB RAM**
- ✅ **Domaines personnalisés**
- ✅ **Support email**

### **Plan Production** (À partir de 14€/mois)
- ✅ **Scaling automatique**
- ✅ **High availability**
- ✅ **Backup automatique**
- ✅ **Support prioritaire**

---

## 🏢 **Alternatives Françaises**

### **OVHcloud Web Cloud**
```bash
# Pour déploiement sur OVH
# Nécessite configuration Docker ou Node.js wrapper
```

### **Gandi Simple Hosting**
```bash
# Support Python/WSGI
# Configuration via .htaccess et requirements.txt
```

---

## 🔒 **Conformité et Sécurité**

### **RGPD et Données**
- ✅ **Serveurs en France** (Île-de-France)
- ✅ **Certification ISO 27001**
- ✅ **Conformité RGPD native**
- ✅ **Hébergement souverain**

### **Sécurité Application**
- ✅ **HTTPS forcé**
- ✅ **Firewall intégré**
- ✅ **Scanning vulnérabilités**
- ✅ **Backup automatique**

---

## 🎯 **Checklist Déploiement**

### **Avant Déploiement :**
- [ ] Code pushé sur Git (GitHub/GitLab)
- [ ] `Procfile` configuré
- [ ] `requirements_cloud.txt` à jour
- [ ] `app.json` paramétré
- [ ] Variables d'environnement définies

### **Après Déploiement :**
- [ ] Application accessible via URL
- [ ] Interface Admin/Étudiant fonctionnelle
- [ ] Import ECG opérationnel
- [ ] Analytics disponibles
- [ ] Performance satisfaisante

---

## 📞 **Support et Resources**

### **Documentation Scalingo**
- 🔗 **Docs Python** : https://doc.scalingo.com/languages/python
- 🔗 **Streamlit Guide** : https://doc.scalingo.com/tutorials/streamlit
- 🔗 **CLI Tools** : https://doc.scalingo.com/platform/cli/start

### **Communauté**
- 💬 **Slack Scalingo** : Support communautaire
- 📧 **Support Email** : support@scalingo.com
- 🐛 **Issues GitHub** : Pour bugs spécifiques

---

**🇫🇷 Déployez Edu-CG sur une infrastructure française souveraine !**
**🚀 RGPD natif + Performance européenne garantie !**
