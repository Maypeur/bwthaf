# Installation BWTHAF comme Custom Component

## 📦 Méthode 1 : Installation via HACS (Recommandée)

### Prérequis
- HACS installé dans Home Assistant
- Accès à votre repository GitHub

### Étapes

1. **Ajouter le repository dans HACS**
   - Ouvrez Home Assistant
   - Allez dans **HACS** → **Intégrations**
   - Cliquez sur les **⋮** en haut à droite
   - Sélectionnez **Dépôts personnalisés**
   - Ajoutez l'URL : `https://github.com/Maypeur/bwthaf`
   - Catégorie : **Intégration**
   - Cliquez sur **Ajouter**

2. **Installer l'intégration**
   - Recherchez "BWTHAF" dans HACS
   - Cliquez sur **Télécharger**
   - Redémarrez Home Assistant

3. **Configurer l'intégration**
   - Allez dans **Paramètres** → **Appareils et services**
   - Cliquez sur **+ Ajouter une intégration**
   - Recherchez "BWT"
   - Remplissez le formulaire :
     - Identifiant : votre.email@example.com
     - Mot de passe : VotreMotDePasse
     - Numéro de série : SERIALNO
     - Intervalle principal : 3600 (défaut)
     - Intervalle consommation : 60 (défaut)
   - Cliquez sur **Soumettre**

## 📂 Méthode 2 : Installation Manuelle

### Étapes

1. **Copier les fichiers**
   
   Copiez le dossier `bwthaf` dans le dossier `custom_components` de Home Assistant :
   
   ```
   /config/custom_components/bwthaf/
   ├── __init__.py
   ├── manifest.json
   ├── const.py
   ├── config_flow.py
   ├── coordinator.py
   ├── sensor.py
   ├── binary_sensor.py
   ├── strings.json
   └── translations/
       ├── en.json
       └── fr.json
   ```

   **Via SSH/Terminal** :
   ```bash
   mkdir -p /config/custom_components
   cd /config/custom_components
   # Puis copiez les fichiers
   ```

2. **Vérifier la structure**
   
   Assurez-vous que les fichiers sont dans :
   `/config/custom_components/bwthaf/`
   
   Et **PAS** dans :
   - `/config/custom_components/bwthaf/bwthaf/` ❌
   - `/addons/bwthaf/` ❌

3. **Redémarrer Home Assistant**
   
   **Paramètres** → **Système** → **Redémarrer**

4. **Ajouter l'intégration**
   
   - **Paramètres** → **Appareils et services**
   - **+ Ajouter une intégration**
   - Recherchez "BWT" ou "BWTHAF"
   - Suivez le formulaire de configuration

## 🔍 Vérification

### Vérifier que l'intégration est reconnue

1. **Via les logs**
   
   **Paramètres** → **Système** → **Journaux**
   
   Recherchez :
   ```
   [custom_components.bwthaf] 
   ```

2. **Via Developer Tools**
   
   **Outils de développement** → **États**
   
   Recherchez : `sensor.bwt_` ou `binary_sensor.bwt_`

3. **Vérifier les entités créées**
   
   **Paramètres** → **Appareils et services** → **Entités**
   
   Vous devriez voir ~17 entités commençant par `bwt_SERIALNO_`

## ⚙️ Configuration Avancée

### Modifier les intervalles après installation

1. **Paramètres** → **Appareils et services**
2. Cliquez sur **BWTHAF**
3. Cliquez sur **Configurer**
4. Modifiez les intervalles
5. Cliquez sur **Soumettre**

### Plusieurs adoucisseurs

Vous pouvez ajouter plusieurs appareils :
1. **+ Ajouter une intégration**
2. Recherchez "BWT"
3. Entrez les identifiants du 2ème appareil
4. Un nouvel appareil sera créé avec ses propres entités

## 🐛 Dépannage

### L'intégration n'apparaît pas

**Vérifiez les logs** :
```
Configuration invalide pour [bwthaf]
```

**Solution** :
- Vérifiez que `manifest.json` est présent et valide
- Vérifiez les permissions des fichiers
- Redémarrez Home Assistant

### Erreur "Authentication failed"

**Causes possibles** :
- Identifiants incorrects
- Compte BWT bloqué
- Problème de connexion Internet

**Solution** :
- Testez sur https://www.bwt-monservice.com
- Vérifiez les identifiants
- Reconfigurez l'intégration

### Erreur "Serial number not found"

**Causes** :
- Numéro de série incorrect
- Appareil non visible sur le compte BWT

**Solution** :
- Connectez-vous sur BWT Mon Service
- Vérifiez le numéro exact (majuscules/minuscules)
- Assurez-vous que l'appareil est en ligne

### Les entités ne se mettent pas à jour

**Vérifiez** :
- `binary_sensor.bwt_SERIALNO_online` doit être `on`
- Les logs pour des erreurs
- La connexion Internet de Home Assistant

**Solution** :
- Augmentez les intervalles de mise à jour
- Vérifiez que BWT Mon Service est accessible
- Rechargez l'intégration

### Recharger l'intégration

1. **Paramètres** → **Appareils et services**
2. Trouvez **BWTHAF**
3. Cliquez sur **⋮** → **Recharger**

## 📊 Utilisation

Une fois installé, vous pouvez :
- Créer des **dashboards** avec les entités
- Créer des **automatisations** (voir AUTOMATIONS.md)
- Intégrer au **Energy Dashboard**
- Créer des **alertes** et **notifications**

## 🔄 Mise à jour

### Via HACS
1. HACS vous notifiera des mises à jour
2. Cliquez sur **Mettre à jour**
3. Redémarrez Home Assistant

### Manuelle
1. Téléchargez la nouvelle version
2. Remplacez les fichiers dans `/config/custom_components/bwthaf/`
3. Redémarrez Home Assistant

## 🗑️ Désinstallation

1. **Paramètres** → **Appareils et services**
2. Trouvez **BWTHAF**
3. Cliquez sur **⋮** → **Supprimer**
4. Supprimez le dossier `/config/custom_components/bwthaf/`
5. Redémarrez Home Assistant

## 📚 Documentation

- [README.md](README.md) - Vue d'ensemble
- [METRICS.md](METRICS.md) - Documentation des métriques
- [AUTOMATIONS.md](AUTOMATIONS.md) - Exemples d'automatisations
- [PROJECT.md](PROJECT.md) - Architecture technique

## 🆘 Support

En cas de problème :
1. Consultez les logs Home Assistant
2. Vérifiez que BWT Mon Service est accessible
3. Ouvrez une issue sur GitHub avec :
   - Version de Home Assistant
   - Logs (sans identifiants !)
   - Description du problème
