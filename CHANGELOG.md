# Changelog

## [1.0.0] - 2025-11-27

### Ajouté
- Version initiale de BWTHAF (BWT Home Assistant Fetcher)
- Authentification automatique au service BWT Mon Service
- Récupération automatique du receiptLineKey basé sur le numéro de série
- Exposition de 17 métriques via MQTT Discovery :
  - 9 métriques principales (configuration et état)
  - 8 métriques de consommation (temps réel)
- Gestion automatique des erreurs avec retry :
  - Erreurs d'authentification : retry toutes les 5 minutes
  - Erreurs de connexion : retry toutes les 1 minute
- Intervalles de mise à jour configurables :
  - Métriques principales : 1 heure par défaut
  - Métriques de consommation : 5 minute par défaut
- Support MQTT Discovery pour Home Assistant
- Documentation complète en français
- Logs détaillés pour le debugging

### Métriques exposées
#### Principales
- État en ligne
- Mode vacances
- Sel par régénération
- Volume résine
- Dureté entrée/sortie
- Pression réseau
- Signal WiFi
- Volume eau adoucie

#### Consommation
- Alarme sel
- Coupure de courant
- Consommation d'eau journalière
- Incrément d'eau
- Nombre de régénérations
- Consommation de sel
- Date dernière mise à jour

### Sécurité
- Stockage sécurisé du mot de passe (type password)
- Session HTTPS avec le service BWT
- Gestion automatique des cookies de session

### Documentation
- README.md complet avec exemples
- METRICS.md détaillant chaque métrique
- Exemples d'automatisations
- Exemples de dashboards Lovelace
