# BWTHAF - BWT Home Assistant Fetcher

Custom component Home Assistant pour récupérer et exposer les métriques des adoucisseurs BWT.
Attention, testé uniquement avec My Perla Optimum

## Description

BWTHAF (BWT Home Assistant Fetcher) est un add-on qui se connecte au service BWT Mon Service pour récupérer les données de votre adoucisseur d'eau BWT et les expose dans Home Assistant via MQTT.

## Installation

1. Ajoutez ce repository à vos add-ons Home Assistant
2. Installez l'add-on "BWTHAF - BWT Home Assistant Fetcher"
3. Configurez l'add-on avec vos identifiants BWT
4. Démarrez l'add-on

## Configuration

### Options obligatoires

- **username** : Votre identifiant BWT Mon Service
- **password** : Votre mot de passe BWT Mon Service
- **serial_number** : Le numéro de série de votre adoucisseur (ex: SERIALNO)

### Options facultatives

- **interval_main** : Intervalle de mise à jour des paramètres généraux en secondes (défaut: 3600 = 1 heure, min: 60, max: 86400)
- **interval_consumption** : Intervalle de mise à jour des consommations en secondes (défaut: 300 = 5 minutes, min: 30, max: 3600)
Les mises à jour ne semblent pas être plus rapides que 5 minutes sur le serveur.

### Exemple de configuration

```yaml
username: "votre.email@example.com"
password: "VotreMotDePasse"
serial_number: "SERIALNO"
interval_main: 3600
interval_consumption: 300
```

## Métriques exposées

L'add-on expose les métriques suivantes dans Home Assistant :

### Métriques principales (mise à jour selon `interval_main`)

#### Sensors

| Nom | Entité | Description | Unité |
|-----|--------|-------------|-------|
| En Ligne | `binary_sensor.bwt_XXXXX_online` | État de connexion de l'appareil | - |
| Mode Vacances | `binary_sensor.bwt_XXXXX_standby` | Mode vacances activé/désactivé | - |
| Sel par Régénération | `sensor.bwt_XXXXX_salt` | Quantité de sel utilisée par régénération | g |
| Volume Résine | `sensor.bwt_XXXXX_resin_vol` | Volume de la résine | L |
| Dureté Entrée | `sensor.bwt_XXXXX_in_hardness` | Dureté de l'eau en entrée | °f |
| Dureté Sortie | `sensor.bwt_XXXXX_out_hardness` | Dureté de l'eau en sortie | °f |
| Pression Réseau | `sensor.bwt_XXXXX_pressure` | Pression du réseau d'eau | bar |
| Signal WiFi | `sensor.bwt_XXXXX_wifi_signal` | Force du signal WiFi | dBm |
| Volume Eau Adoucie | `sensor.bwt_XXXXX_vol_ok` | Volume d'eau adoucie depuis la dernière régénération | L |

### Métriques de consommation (mise à jour selon `interval_consumption`)

#### Sensors

| Nom | Entité | Description | Unité |
|-----|--------|-------------|-------|
| Alarme Sel | `binary_sensor.bwt_XXXXX_salt_alarm` | Alarme de niveau de sel bas | - |
| Coupure de Courant | `binary_sensor.bwt_XXXXX_power_outage` | Coupure de courant détectée | - |
| Consommation d'Eau Journalière | `sensor.bwt_XXXXX_water_consumption` | Consommation d'eau du jour | L |
| Incrément Eau | `sensor.bwt_XXXXX_water_increment` | Eau consommée depuis la dernière mesure | L |
| Nombre de Régénérations | `sensor.bwt_XXXXX_regen_count` | Nombre de régénérations effectuées | - |
| Consommation de Sel | `sensor.bwt_XXXXX_salt_consumption` | Quantité totale de sel consommée | g |
| Date Dernière Mise à Jour | `sensor.bwt_XXXXX_last_update` | Horodatage de la dernière mise à jour | - |

*Note : XXXXX représente votre numéro de série*

## Utilisation des métriques

### Compteurs d'eau

Le sensor `sensor.bwt_XXXXX_water_consumption` représente la consommation d'eau du jour en cours. Il se remet à zéro automatiquement chaque jour.

Le sensor `sensor.bwt_XXXXX_water_increment` indique la quantité d'eau consommée depuis la dernière mesure, permettant à Home Assistant de calculer précisément la consommation.

### Consommation de sel

La consommation de sel est calculée automatiquement par la formule :
```
Consommation de sel = Nombre de régénérations × Sel par régénération
```

### Alarmes

Les binary sensors `salt_alarm` et `power_outage` peuvent être utilisés pour créer des automatisations et des notifications :

**Exemple d'automatisation pour l'alarme sel :**

```yaml
automation:
  - alias: "Alerte Sel Adoucisseur"
    trigger:
      - platform: state
        entity_id: binary_sensor.bwt_serialno_salt_alarm
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Adoucisseur BWT"
          message: "⚠️ Niveau de sel bas ! Veuillez recharger l'adoucisseur."
```

**Exemple pour les coupures de courant :**

```yaml
automation:
  - alias: "Alerte Coupure Courant Adoucisseur"
    trigger:
      - platform: state
        entity_id: binary_sensor.bwt_serialno_power_outage
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Adoucisseur BWT"
          message: "⚡ Coupure de courant détectée sur l'adoucisseur"
```

## Dashboard Lovelace

Exemple de carte pour afficher les informations de l'adoucisseur :

```yaml
type: entities
title: Adoucisseur BWT
entities:
  - entity: binary_sensor.bwt_serialno_online
    name: État
  - entity: sensor.bwt_serialno_water_consumption
    name: Eau consommée aujourd'hui
  - entity: sensor.bwt_serialno_regen_count
    name: Régénérations
  - entity: sensor.bwt_serialno_salt_consumption
    name: Sel consommé
  - entity: binary_sensor.bwt_serialno_salt_alarm
    name: Alarme sel
  - entity: sensor.bwt_serialno_wifi_signal
    name: Signal WiFi
  - entity: sensor.bwt_serialno_in_hardness
    name: Dureté entrée
  - entity: sensor.bwt_serialno_out_hardness
    name: Dureté sortie
```

## Gestion des erreurs

### Erreurs d'authentification

Si les identifiants sont incorrects, l'add-on retente automatiquement toutes les 5 minutes.

Si vous modifiez vos identifiants dans la configuration, l'add-on détecte le changement et retente immédiatement l'authentification.

### Erreurs de connexion

En cas de problème réseau ou d'indisponibilité du service BWT, l'add-on retente automatiquement toutes les minutes.

## Logs

Les logs de l'add-on sont accessibles via l'interface Home Assistant. Ils incluent :

- Les tentatives de connexion
- Les mises à jour réussies
- Les erreurs éventuelles
- Les changements de configuration détectés

## Support

Pour signaler un problème ou demander une fonctionnalité, créez une issue sur le repository GitHub.

## Licence

MIT License

## Auteur

BWTHAF - BWT Home Assistant Fetcher - Maypeur