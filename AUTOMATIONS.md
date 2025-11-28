# Exemples d'Automatisations

Ce fichier contient des exemples d'automatisations pour exploiter au mieux les données de votre adoucisseur BWT.

## Alertes

### Alerte Niveau de Sel Bas

```yaml
automation:
  - alias: "BWT - Alerte Sel Bas"
    description: "Notification quand le niveau de sel est bas"
    trigger:
      - platform: state
        entity_id: binary_sensor.bwt_serialno_salt_alarm
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Adoucisseur BWT"
          message: "Niveau de sel bas ! Veuillez recharger le bac à sel."
          data:
            priority: high
            tag: "bwt-salt-alarm"
```

### Alerte Coupure de Courant

```yaml
automation:
  - alias: "BWT - Alerte Coupure Courant"
    description: "Notification en cas de coupure de courant"
    trigger:
      - platform: state
        entity_id: binary_sensor.bwt_serialno_power_outage
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "⚡ Adoucisseur BWT"
          message: "Coupure de courant détectée sur l'adoucisseur"
          data:
            priority: high
            tag: "bwt-power-outage"
```

### Alerte Appareil Hors Ligne

```yaml
automation:
  - alias: "BWT - Alerte Hors Ligne"
    description: "Notification si l'adoucisseur est hors ligne"
    trigger:
      - platform: state
        entity_id: binary_sensor.bwt_serialno_online
        to: "off"
        for:
          minutes: 30
    action:
      - service: notify.mobile_app
        data:
          title: "🔌 Adoucisseur BWT"
          message: "L'adoucisseur est hors ligne depuis 30 minutes"
```

### Alerte Signal WiFi Faible

```yaml
automation:
  - alias: "BWT - Alerte WiFi Faible"
    description: "Notification si le signal WiFi est faible"
    trigger:
      - platform: numeric_state
        entity_id: sensor.bwt_serialno_wifi_signal
        below: -75
        for:
          minutes: 15
    action:
      - service: notify.mobile_app
        data:
          title: "📡 Adoucisseur BWT"
          message: "Signal WiFi faible ({{ states('sensor.bwt_serialno_wifi_signal') }} dBm)"
```

## Suivi de Consommation

### Alerte Consommation Anormalement Élevée

```yaml
automation:
  - alias: "BWT - Consommation Anormale"
    description: "Alerte si la consommation est anormalement élevée (possible fuite)"
    trigger:
      - platform: numeric_state
        entity_id: sensor.bwt_serialno_water_consumption
        above: 500
    condition:
      - condition: time
        after: "20:00:00"
        before: "06:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "💧 Adoucisseur BWT"
          message: "Consommation anormalement élevée la nuit ({{ states('sensor.bwt_serialno_water_consumption') }} L)"
          data:
            priority: high
```

### Rapport Journalier

```yaml
automation:
  - alias: "BWT - Rapport Journalier"
    description: "Envoi un résumé quotidien de la consommation"
    trigger:
      - platform: time
        at: "21:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "📊 Adoucisseur BWT - Résumé du jour"
          message: >
            Eau consommée: {{ states('sensor.bwt_serialno_water_consumption') }} L
            Régénérations: {{ states('sensor.bwt_serialno_regen_count') }}
            Sel consommé: {{ (states('sensor.bwt_serialno_salt_consumption') | float / 1000) | round(1) }} kg
```

### Rapport Hebdomadaire

```yaml
automation:
  - alias: "BWT - Rapport Hebdomadaire"
    description: "Résumé hebdomadaire de la consommation"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: time
        weekday:
          - sun
    action:
      - service: notify.mobile_app
        data:
          title: "📈 Adoucisseur BWT - Résumé de la semaine"
          message: >
            Cette semaine:
            
            Eau totale: {{ (state_attr('sensor.bwt_serialno_water_consumption', 'sum') | float) | round(0) }} L
            
            Régénérations: {{ (state_attr('sensor.bwt_serialno_regen_count', 'sum') | float) | round(0) }}
            
            Sel: {{ (state_attr('sensor.bwt_serialno_salt_consumption', 'sum') | float / 1000) | round(1) }} kg
```

## Maintenance

### Rappel Rechargement Sel

```yaml
automation:
  - alias: "BWT - Rappel Rechargement Sel"
    description: "Rappel pour vérifier le niveau de sel"
    trigger:
      - platform: time
        at: "10:00:00"
    condition:
      - condition: template
        value_template: "{{ (now().day - 1) % 15 == 0 }}"
    action:
      - service: notify.mobile_app
        data:
          title: "🧂 Adoucisseur BWT"
          message: "N'oubliez pas de vérifier le niveau de sel !"
```

### Rappel Nettoyage

```yaml
automation:
  - alias: "BWT - Rappel Nettoyage"
    description: "Rappel pour nettoyer l'adoucisseur"
    trigger:
      - platform: time
        at: "10:00:00"
    condition:
      - condition: template
        value_template: "{{ now().month in [3, 9] and now().day == 1 }}"
    action:
      - service: notify.mobile_app
        data:
          title: "🧼 Adoucisseur BWT"
          message: "Il est temps de nettoyer l'adoucisseur avec des pastilles nettoyantes"
```

## Statistiques

### Création de Sensors de Statistiques Quotidiennes

```yaml
sensor:
  - platform: statistics
    name: "BWT Consommation Moyenne Quotidienne"
    entity_id: sensor.bwt_serialno_water_consumption
    state_characteristic: mean
    max_age:
      days: 30
    sampling_size: 30
    
  - platform: statistics
    name: "BWT Régénérations Moyenne Quotidienne"
    entity_id: sensor.bwt_serialno_regen_count
    state_characteristic: mean
    max_age:
      days: 30
    sampling_size: 30
```

### Template Sensors pour Analyse

```yaml
template:
  - sensor:
      - name: "BWT Coût Sel Journalier"
        unit_of_measurement: "€"
        state: >
          {{ ((states('sensor.bwt_serialno_salt_consumption') | float / 1000) * 0.50) | round(2) }}
        # Hypothèse: 0.50€ par kg de sel
        
      - name: "BWT Consommation par Personne"
        unit_of_measurement: "L"
        state: >
          {{ (states('sensor.bwt_serialno_water_consumption') | float / 4) | round(0) }}
        # À adapter selon le nombre de personnes dans votre foyer
        
      - name: "BWT Qualité Signal WiFi"
        state: >
          {% set rssi = states('sensor.bwt_serialno_wifi_signal') | float %}
          {% if rssi > -50 %}
            Excellent
          {% elif rssi > -60 %}
            Très bon
          {% elif rssi > -70 %}
            Bon
          {% elif rssi > -80 %}
            Faible
          {% else %}
            Très faible
          {% endif %}
```

## Intégration Energy Dashboard

### Configuration pour le Tableau de Bord Énergie

Ajoutez dans votre `configuration.yaml` :

```yaml
sensor:
  - platform: integration
    source: sensor.bwt_serialno_water_increment
    name: "BWT Consommation Eau Totale"
    unit_prefix: k
    round: 2
    method: left
```

Puis ajoutez ce sensor dans le Energy Dashboard de Home Assistant :
1. Paramètres → Tableaux de bord → Énergie
2. Ajoutez la consommation d'eau individuelle
3. Sélectionnez `sensor.bwt_consommation_eau_totale`
