# Documentation des Métriques BWT

## Vue d'ensemble

Cet add-on expose deux catégories de métriques :

1. **Métriques principales** : Paramètres de configuration et état de l'appareil (mise à jour lente)
2. **Métriques de consommation** : Données en temps quasi-réel sur l'utilisation (mise à jour rapide)

## Métriques Principales

### Connectivité et État

#### `binary_sensor.bwt_XXXXX_online`
- **Type** : Binary Sensor
- **Description** : Indique si l'adoucisseur est en ligne et répond aux requêtes
- **Valeurs** : `on` (en ligne) / `off` (hors ligne)
- **Utilisation** : Surveillance de la disponibilité de l'appareil

#### `binary_sensor.bwt_XXXXX_standby`
- **Type** : Binary Sensor
- **Description** : Mode vacances activé ou non
- **Valeurs** : `on` (mode vacances) / `off` (mode normal)
- **Note** : Quand activé, l'adoucisseur ne peut être désactivé qu'en local sur l'appareil

### Configuration de l'Appareil

#### `sensor.bwt_XXXXX_resin_vol`
- **Type** : Sensor
- **Unité** : Litres (L)
- **Description** : Volume de résine échangeuse d'ions dans l'adoucisseur
- **Exemple** : 13 L
- **Utilisation** : Information technique sur la capacité de l'appareil

#### `sensor.bwt_XXXXX_in_hardness`
- **Type** : Sensor
- **Unité** : Degrés français (°f)
- **Description** : Dureté de l'eau en entrée de l'adoucisseur
- **Exemple** : 30 °f
- **Utilisation** : Mesure de la qualité de l'eau du réseau
- **Note** : Plus la valeur est élevée, plus l'eau est dure (calcaire)

#### `sensor.bwt_XXXXX_out_hardness`
- **Type** : Sensor
- **Unité** : Degrés français (°f)
- **Description** : Dureté de l'eau en sortie de l'adoucisseur (cible)
- **Exemple** : 10 °f
- **Utilisation** : Dureté souhaitée après traitement
- **Note** : Valeur configurée, pas mesurée en temps réel

#### `sensor.bwt_XXXXX_pressure`
- **Type** : Sensor
- **Unité** : Bar
- **Description** : Pression du réseau d'eau
- **Exemple** : 3 bar
- **Utilisation** : Surveillance de la pression hydraulique

#### `sensor.bwt_XXXXX_salt`
- **Type** : Sensor
- **Unité** : Grammes (g)
- **Description** : Quantité de sel utilisée par cycle de régénération
- **Exemple** : 1800 g
- **Utilisation** : Calcul de la consommation totale de sel et prévision des besoins

#### `sensor.bwt_XXXXX_vol_ok`
- **Type** : Sensor
- **Unité** : Litres (L)
- **Description** : Volume d'eau adoucie depuis la dernière régénération
- **Exemple** : 2340 L
- **Utilisation** : Suivi de l'efficacité et du cycle de régénération

### Connectivité WiFi

#### `sensor.bwt_XXXXX_wifi_signal`
- **Type** : Sensor
- **Unité** : dBm
- **Description** : Force du signal WiFi
- **Exemple** : -63 dBm
- **Interprétation** :
  - -30 à -50 dBm : Excellent
  - -50 à -60 dBm : Très bon
  - -60 à -70 dBm : Bon
  - -70 à -80 dBm : Faible
  - < -80 dBm : Très faible
- **Utilisation** : Diagnostic de problèmes de connectivité

## Métriques de Consommation

### Alarmes et Événements

#### `binary_sensor.bwt_XXXXX_salt_alarm`
- **Type** : Binary Sensor
- **Description** : Alarme de niveau de sel bas
- **Valeurs** : `on` (alarme active) / `off` (niveau OK)
- **Action recommandée** : Recharger le bac à sel
- **Note** : L'alarme disparaît automatiquement à la prochaine régénération si le sel a été ajouté

#### `binary_sensor.bwt_XXXXX_power_outage`
- **Type** : Binary Sensor
- **Description** : Coupure de courant détectée pendant la journée
- **Valeurs** : `on` (coupure détectée) / `off` (pas de coupure)
- **Utilisation** : Surveillance de l'alimentation électrique
- **Note** : Se remet à zéro chaque jour

### Consommation d'Eau

#### `sensor.bwt_XXXXX_water_consumption`
- **Type** : Sensor
- **Unité** : Litres (L)
- **State Class** : total_increasing
- **Description** : Consommation d'eau totale de la journée en cours
- **Exemple** : 290 L
- **Comportement** : Se remet à zéro automatiquement à minuit
- **Utilisation** : 
  - Suivi quotidien de la consommation
  - Création de statistiques avec Home Assistant Energy Dashboard
  - Détection de fuites (consommation anormalement élevée)

#### `sensor.bwt_XXXXX_water_increment`
- **Type** : Sensor
- **Unité** : Litres (L)
- **Description** : Quantité d'eau consommée depuis la dernière mesure
- **Exemple** : 12 L
- **Utilisation** : 
  - Mesure précise de la consommation entre deux mises à jour
  - Calcul de débit moyen
  - Détection d'utilisation en temps quasi-réel

### Régénération

#### `sensor.bwt_XXXXX_regen_count`
- **Type** : Sensor
- **State Class** : total_increasing
- **Description** : Nombre de cycles de régénération effectués dans la journée
- **Exemple** : 1
- **Valeurs typiques** : 0 à 3 par jour selon l'utilisation
- **Utilisation** : 
  - Suivi de l'activité de l'adoucisseur
  - Calcul de la consommation de sel
  - Détection de régénérations anormales

#### `sensor.bwt_XXXXX_salt_consumption`
- **Type** : Sensor
- **Unité** : Grammes (g)
- **State Class** : total_increasing
- **Description** : Quantité totale de sel consommée (calculée)
- **Formule** : `regen_count × salt_per_regen`
- **Exemple** : Si 1 régénération × 1800 g = 1800 g
- **Utilisation** : 
  - Prévision de rechargement du sel
  - Calcul du coût d'exploitation
  - Statistiques mensuelles/annuelles

### Horodatage

#### `sensor.bwt_XXXXX_last_update`
- **Type** : Sensor
- **Device Class** : timestamp
- **Description** : Date et heure de la dernière mise à jour des données
- **Format** : ISO 8601 (ex: 2025-11-27T14:03:27.000)
- **Utilisation** : 
  - Vérification de la fraîcheur des données
  - Détection de problèmes de communication
  - Création d'automatisations basées sur l'ancienneté des données

## Fréquence de Mise à Jour

### Métriques Principales
- **Fréquence par défaut** : 1 heure (3600 secondes)
- **Configurable** : Oui (60 à 86400 secondes)
- **Recommandation** : Conserver 1 heure, ces données changent peu

**Métriques concernées** :
- En Ligne
- Mode Vacances
- Sel par Régénération
- Volume Résine
- Dureté Entrée/Sortie
- Pression
- Signal WiFi
- Volume Eau Adoucie

### Métriques de Consommation
- **Fréquence par défaut** : 1 minute (60 secondes)
- **Configurable** : Oui (30 à 3600 secondes)
- **Recommandation** : 
  - 30-60 secondes pour un suivi précis
  - 5-10 minutes pour économiser les ressources

**Métriques concernées** :
- Alarme Sel
- Coupure de Courant
- Consommation d'Eau
- Incrément Eau
- Nombre de Régénérations
- Consommation de Sel
- Dernière Mise à Jour

## Cas d'Usage

### 1. Surveillance du Niveau de Sel

Combinez `binary_sensor.bwt_XXXXX_salt_alarm` avec `sensor.bwt_XXXXX_salt_consumption` pour :
- Recevoir une alerte quand le sel est bas
- Estimer combien de temps avant le prochain rechargement
- Planifier l'achat de sel

### 2. Suivi de la Consommation d'Eau

Utilisez `sensor.bwt_XXXXX_water_consumption` et `sensor.bwt_XXXXX_water_increment` pour :
- Détecter les fuites (consommation continue)
- Analyser les habitudes de consommation
- Comparer avec les factures d'eau
- Intégration au Energy Dashboard de Home Assistant

### 3. Maintenance Préventive

Surveillez :
- `sensor.bwt_XXXXX_wifi_signal` : Problèmes de connectivité
- `binary_sensor.bwt_XXXXX_power_outage` : Problèmes électriques
- `sensor.bwt_XXXXX_regen_count` : Fréquence anormale des régénérations

### 4. Optimisation de la Configuration

Analysez :
- `sensor.bwt_XXXXX_in_hardness` vs `sensor.bwt_XXXXX_out_hardness`
- `sensor.bwt_XXXXX_vol_ok` pour comprendre les cycles de régénération
- `sensor.bwt_XXXXX_water_consumption` pour ajuster les paramètres

## Graphiques Recommandés

### Consommation d'Eau (7 derniers jours)
```yaml
type: history-graph
title: Consommation d'Eau
entities:
  - entity: sensor.bwt_serialno_water_consumption
hours_to_show: 168
```

### Régénérations (30 derniers jours)
```yaml
type: statistics-graph
title: Régénérations
entities:
  - sensor.bwt_serialno_regen_count
stat_types:
  - sum
chart_type: bar
period: day
```

### Signal WiFi
```yaml
type: gauge
entity: sensor.bwt_serialno_wifi_signal
min: -90
max: -30
severity:
  green: -60
  yellow: -70
  red: -80
```

## Notes Importantes

1. **Remise à zéro quotidienne** : Les compteurs journaliers (`water_consumption`, `regen_count`, `power_outage`) se remettent à zéro automatiquement chaque jour selon les données du service BWT.

2. **Cumul automatique** : Home Assistant peut cumuler automatiquement les données avec les `state_class: total_increasing` pour créer des statistiques long terme.

3. **Délai de synchronisation** : Les données ne sont pas en temps réel strict. Elles dépendent :
   - De la fréquence de mise à jour configurée
   - Du délai de synchronisation de l'appareil BWT avec le cloud
   - De la stabilité de votre connexion Internet

4. **Précision** : Les valeurs sont celles fournies par le service BWT. L'add-on ne fait aucune modification ou interpolation des données.
