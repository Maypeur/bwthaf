# Changelog

## [1.1.0] - 2026-11-04

### Corrigé
- Consommation bloquée sur `unknown` avec l'erreur `Live div not found` (#4) : le site BWT n'expose plus un `data-controller="live"` exact. La récupération passe d'abord par `/device/ajaxChart`, puis par le composant Live `DeviceTabs` / `loadConso`.
- Écran d'options en erreur 500 sur Home Assistant récent (#4, commentaires) : `OptionsFlow` n'assigne plus `config_entry`.
- Authentification plus tolérante si le numéro de série n'est plus dans le même bloc HTML du dashboard.
- Fusion de l'historique ajaxChart et loadConso pour conserver toute la période disponible.

### Ajouté
- Import de l'historique quotidien dans les statistiques Home Assistant (`bwthaf:water_*`, `bwthaf:salt_*`) pour les graphiques jour par jour.
- Publication MQTT optionnelle (si le broker HA est configuré) :
  - `bwt/<serial>/` état courant
  - `bwt/<serial>/history` historique quotidien
- Affichage en kg / m³ au-delà de 1000 g / 1000 L (valeurs natives inchangées : g et L).
- Jeton CSRF Live envoyé s'il est présent ; diagnostic sans données personnelles si le composant Live est introuvable.

### Sécurité
- Plus de numéro de série, de receiptLineKey ni d'extrait HTML dans les logs.
- Identifiants toujours lus depuis l'entrée de configuration Home Assistant, jamais en dur.

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
