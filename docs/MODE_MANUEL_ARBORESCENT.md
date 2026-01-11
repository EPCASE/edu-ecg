# 🌳 MODE ANNOTATION MANUEL - VUE ARBORESCENTE

## 📊 Vue d'ensemble

Le nouveau mode manuel offre une **navigation hiérarchique** inspirée de WebProtégé avec :
- ✅ **3 niveaux de hiérarchie** (Catégories → Sous-groupes → Concepts)
- ✅ **Recherche filtrante** en temps réel
- ✅ **Cartes détaillées** pour chaque concept
- ✅ **Ajout rapide** en 1 clic
- ✅ **278 concepts** organisés intelligemment

---

## 🌲 Structure Hiérarchique

### Niveau 1 : Catégories Principales (4)

```
🚨 DIAGNOSTICS URGENTS (24 concepts)
⚕️ DIAGNOSTICS MAJEURS (70 concepts)
📊 SIGNES ECG PATHOLOGIQUES (48 concepts)
📏 DESCRIPTEURS ECG (136 concepts)
```

### Niveau 2 : Sous-groupes Sémantiques

**⚕️ DIAGNOSTICS MAJEURS :**
- 📁 Blocs de conduction (2)
- 📁 Troubles du rythme (17)
- 📁 Syndromes (5)
- 📁 Hypertrophies (2)
- 📁 Autres (44)

**📏 DESCRIPTEURS ECG :**
- 📁 Ondes (14)
- 📁 Segments & Intervalles (5)
- 📁 Territoires (19)
- 📁 ESV & Arythmies (4)
- 📁 Autres (94)

### Niveau 3 : Concepts Individuels

Chaque concept affiche :
- 📝 **Nom complet**
- 📁 **Catégorie**
- 🔤 **Synonymes** (jusqu'à 3, +compteur)
- 🗺️ **Territoires possibles**
- ➕ **Bouton ajout rapide**

---

## 🔍 Recherche Filtrante

**Fonctionnalités :**
- ✅ Recherche insensible à la casse
- ✅ Recherche dans noms ET synonymes
- ✅ Normalisation accents (hémi = hemi)
- ✅ Compteurs dynamiques (X/Y concepts)
- ✅ Affichage uniquement des catégories avec résultats

**Exemples :**
```
"bloc"        → 13 concepts (blocs de conduction)
"tachycardie" → 25 concepts (tous types)
"onde"        → 20 concepts (ondes P, T, U, Q...)
"antérieur"   → Territoires + localisations
```

---

## 🎯 Workflow Utilisateur

### Parcours Hiérarchique
```
1. Ouvrir catégorie (ex: ⚕️ DIAGNOSTICS MAJEURS)
   ↓
2. Parcourir sous-groupes (ex: 📁 Troubles du rythme)
   ↓
3. Voir concept avec détails
   ↓
4. Clic ➕ → Ajouté instantanément
```

### Parcours Recherche
```
1. Taper "BAV" dans filtre
   ↓
2. Voir uniquement 6 concepts BAV
   ↓
3. Choisir (ex: "BAV 2 Mobitz 1")
   ↓
4. Clic ➕ → Ajouté
```

---

## 🎨 Améliorations Visuelles

### Icônes par Niveau
- 🚨 Urgences (rouge)
- ⚕️ Diagnostics majeurs (bleu)
- 📊 Signes ECG (vert)
- 📏 Descripteurs (gris)

### Icônes par Type
- 📁 Sous-groupe
- 🔤 Synonyme
- 🗺️ Territoire
- ➕ Ajouter

### Expanders Streamlit
- ✅ Expand/collapse natif
- ✅ Compteurs dynamiques
- ✅ État conservé entre recherches

---

## 📊 Statistiques

**Organisation :**
- 4 catégories principales
- 9 sous-groupes sémantiques
- 278 concepts au total
- 57 concepts avec synonymes
- 22 concepts avec territoires

**Performance :**
- ⚡ Recherche instantanée (< 50ms)
- ⚡ Filtrage en temps réel
- ⚡ Ajout en 1 clic

---

## 🆚 Comparaison Ancien vs Nouveau

| Feature | Ancien Mode | Nouveau Mode |
|---------|-------------|--------------|
| Navigation | 2 dropdowns séquentiels | Arborescence expand/collapse |
| Recherche | ❌ Non | ✅ Filtre temps réel |
| Détails | ❌ Nom uniquement | ✅ Nom + synonymes + territoires |
| Hiérarchie | ❌ 1 niveau (catégories) | ✅ 3 niveaux |
| Visuels | ❌ Basique | ✅ Icônes + cartes |
| Rapidité | ⚠️ 3 clics minimum | ✅ 1-2 clics |
| Inspiration | Selectbox standard | ✅ Style WebProtégé |

---

## 💡 Cas d'Usage

### Cas 1 : Annoter un STEMI
```
Utilisateur cherche "STEMI"
→ Filtre trouve "Syndrome coronarien à la phase aigue..."
→ Voit territoires: "Localisation IDM"
→ Clic ➕
→ Peut ensuite chercher "antérieur" pour ajouter territoire
```

### Cas 2 : Explorer les BAV
```
Utilisateur ouvre ⚕️ DIAGNOSTICS MAJEURS
→ Voit sous-groupe organisé
→ Trouve "BAV 2 Mobitz 1", "BAV de haut grade"...
→ Ajoute ceux nécessaires
```

### Cas 3 : Perdu dans les modes précédents
```
Utilisateur ne trouve pas avec LLM/Rapide
→ Passe en Manuel
→ Parcourt arborescence méthodiquement
→ Découvre concepts liés dans sous-groupes
→ Vision complète de l'ontologie
```

---

## 🚀 Avantages

**Pour l'Annotation :**
- ✅ Annotation rapide à la volée
- ✅ Découverte de concepts connexes
- ✅ Validation visuelle (synonymes, territoires)
- ✅ Pas besoin de connaître nom exact

**Pour l'Apprentissage :**
- ✅ Vue pédagogique de l'ontologie
- ✅ Relations entre concepts visibles
- ✅ Hiérarchie médicale respectée
- ✅ Peut remplacer recherche rapide

**Pour le Workflow :**
- ✅ Fallback fiable si LLM/Rapide échoue
- ✅ Exploration complète possible
- ✅ Aucun concept ne peut être "perdu"
- ✅ Vision globale toujours accessible

---

## 🔮 Évolutions Futures Possibles

**Phase 2 :**
- ⭐ Favoris/Récents (concepts fréquemment utilisés)
- 📊 Statistiques d'utilisation par concept
- 🔗 Liens entre concepts (relations OWL)
- 📱 Vue mobile optimisée

**Phase 3 :**
- 🎨 Vue graphique (graph network)
- 🔄 Sync temps réel avec WebProtégé
- 🎯 Suggestions basées sur annotations existantes
- 📚 Templates de sessions pré-remplies

---

## ✅ Validation

**Tests Effectués :**
- ✅ Chargement 278 concepts
- ✅ Groupement hiérarchique correct
- ✅ Recherche fonctionnelle
- ✅ Ajout instantané
- ✅ Compteurs dynamiques
- ✅ Performance < 50ms

**Prêt pour Production POC** 🎉

---

*Créé par BMad Team - Party Mode*
*Date: 2026-01-11*
