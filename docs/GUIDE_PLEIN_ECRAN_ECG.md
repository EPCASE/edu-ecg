# Guide d'utilisation - Mode Plein Écran ECG

## 🖼️ Nouvelle fonctionnalité : Affichage ECG en plein écran

### Fonctionnalités principales

#### 1. **Activation du mode plein écran**
- Dans la liseuse ECG, cliquez sur le bouton **"🖼️ Plein Écran"** (bouton bleu principal)
- L'ECG s'affiche immédiatement en mode plein écran avec une interface dédiée

#### 2. **Contrôles de zoom intégrés**
- **Slider de zoom** : 25% à 500% par pas de 25%
- **Affichage temps réel** du niveau de zoom actuel
- **Informations dynamiques** sur la taille affichée vs originale

#### 3. **Affichage adaptatif**
- **Zoom 100%** : Utilise toute la largeur disponible de l'écran
- **Zoom modéré (25-150%)** : Image centrée dans l'interface
- **Gros zoom (>150%)** : Scroll horizontal automatique pour naviguer dans l'image

#### 4. **Interface utilisateur enrichie**
- **En-tête coloré** avec titre "ECG - Mode Plein Écran"
- **Informations détaillées** : largeur, hauteur, mode couleur, ratio
- **Métriques visuelles** pour un aperçu rapide des caractéristiques
- **Conseils d'utilisation** intégrés dans l'interface

### Utilisation pratique

#### Navigation dans l'ECG
1. **Ouverture** : Depuis la liseuse normale → Bouton "🖼️ Plein Écran"
2. **Zoom** : Ajustez avec le slider selon vos besoins
   - 25-50% : Vue d'ensemble
   - 100% : Taille optimale
   - 200-500% : Analyse détaillée
3. **Fermeture** : Bouton "❌ Fermer" pour revenir au mode normal

#### Cas d'usage recommandés
- **Analyse détaillée** des tracés ECG complexes
- **Annotation précise** avec zoom élevé
- **Présentation** en mode pleine largeur
- **Comparaison** de détails fins

### Avantages techniques

#### Performance
- **Pas de rechargement** d'image lors du zoom
- **Calcul dynamique** de la largeur d'affichage
- **Interface réactive** avec feedback visuel immédiat

#### Ergonomie
- **Une seule fenêtre** : zoom et affichage intégrés
- **Contrôles accessibles** : slider et boutons visibles
- **Retour facile** au mode normal
- **Informations contextuelles** toujours visibles

### Interface utilisateur

#### Mode normal
```
[Image ECG]    [Contrôles]
               🖼️ Plein Écran
               ---
               Taille: 1024x768
               Mode: RGB
               🔍 Zoom: [slider]
```

#### Mode plein écran
```
📊 ECG - Mode Plein Écran
Case ID: xxx | 🔍 Zoom: [slider] | Zoom: 150% | ❌ Fermer
---
[Image ECG zoomée - pleine largeur]
---
📋 Informations détaillées
[Largeur] [Hauteur] [Mode] [Ratio]
💡 Conseils d'utilisation
```

### Notes techniques

#### Compatibilité
- ✅ Fonctionne avec tous les formats d'image supportés (PNG, JPG, etc.)
- ✅ Compatible avec tous les navigateurs modernes
- ✅ Responsive design pour différentes tailles d'écran

#### Limitations
- Le zoom maximum est limité à 500% pour des raisons de performance
- Les très grandes images peuvent nécessiter plus de mémoire à fort zoom

### Dépannage

#### Problèmes courants
1. **Le bouton plein écran ne répond pas**
   - Vérifiez que l'ECG est bien chargé
   - Actualisez la page si nécessaire

2. **L'image ne s'affiche pas en plein écran**
   - Vérifiez la console du navigateur pour d'éventuelles erreurs
   - Assurez-vous que le fichier image existe

3. **Le zoom ne fonctionne pas correctement**
   - Le zoom s'applique en temps réel
   - Pour les gros zooms, utilisez le scroll horizontal

### Évolutions futures possibles
- Zoom avec la molette de la souris
- Pan/glissement pour naviguer dans l'image zoomée
- Presets de zoom prédéfinis
- Mode présentation avec diaporama
- Annotations directement en mode plein écran

---

*Guide créé pour la version avec mode plein écran ECG intégré*
