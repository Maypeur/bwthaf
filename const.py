"""Constants for BWT integration."""
from datetime import timedelta

DOMAIN = "bwthaf"
MANUFACTURER = "BWT"

# Configuration
CONF_SERIAL_NUMBER = "serial_number"
CONF_DEVICE_NAME = "device_name"
CONF_INTERVAL_MAIN = "interval_main"
CONF_INTERVAL_CONSUMPTION = "interval_consumption"

# Defaults
DEFAULT_DEVICE_NAME = "Adoucisseur BWT"
DEFAULT_INTERVAL_MAIN = 3600  # 1 hour
DEFAULT_INTERVAL_CONSUMPTION = 60  # 1 minute

# Update intervals
UPDATE_INTERVAL_MAIN = timedelta(seconds=3600)
UPDATE_INTERVAL_CONSUMPTION = timedelta(seconds=300)

# API URLs
BWT_BASE_URL = "https://www.bwt-monservice.com"
BWT_LOGIN_URL = f"{BWT_BASE_URL}/login"
BWT_DASHBOARD_URL = f"{BWT_BASE_URL}/dashboard"
BWT_DEVICE_URL = f"{BWT_BASE_URL}/device"
BWT_SUMMARY_URL = f"{BWT_BASE_URL}/ajax/product-summary"
BWT_LOAD_CONSO_URL = f"{BWT_BASE_URL}/_components/DeviceTabs/loadConso"
BWT_AJAX_CHART_URL = f"{BWT_BASE_URL}/device/ajaxChart"

# Sensor types
SENSOR_TYPES = {
    "salt": {
        "name": "Sel par Régénération",
        "unit": "g",
        "icon": "mdi:shaker",
        "device_class": "weight",
        "state_class": "measurement",
    },
    "resin_vol": {
        "name": "Volume Résine",
        "unit": "L",
        "icon": "mdi:water",
        "device_class": None,
        "state_class": "measurement",
    },
    "in_hardness": {
        "name": "Dureté Entrée",
        "unit": "°f",
        "icon": "mdi:water-opacity",
        "device_class": None,
        "state_class": "measurement",
    },
    "out_hardness": {
        "name": "Dureté Sortie",
        "unit": "°f",
        "icon": "mdi:water-check",
        "device_class": None,
        "state_class": "measurement",
    },
    "pressure": {
        "name": "Pression",
        "unit": "bar",
        "icon": "mdi:gauge",
        "device_class": "pressure",
        "state_class": "measurement",
    },
    "wifi_signal": {
        "name": "Signal WiFi",
        "unit": "dBm",
        "icon": "mdi:wifi",
        "device_class": "signal_strength",
        "state_class": "measurement",
    },
    "vol_ok": {
        "name": "Volume Eau Adoucie",
        "unit": "L",
        "icon": "mdi:water-check",
        "device_class": "water",
        "state_class": "total",
    },
    "water_consumption": {
        "name": "Consommation Eau",
        "unit": "L",
        "icon": "mdi:water",
        "device_class": "water",
        "state_class": "total_increasing",
    },
    "water_increment": {
        "name": "Incrément Eau",
        "unit": "L",
        "icon": "mdi:water-plus",
        "device_class": None,
        "state_class": "measurement",
    },
    "regen_count": {
        "name": "Régénérations",
        "unit": "",
        "icon": "mdi:refresh",
        "device_class": None,
        "state_class": "total_increasing",
    },
    "salt_consumption": {
        "name": "Consommation Sel",
        "unit": "g",
        "icon": "mdi:shaker-outline",
        "device_class": "weight",
        "state_class": "total_increasing",
    },
    "last_update": {
        "name": "Date des Mesures",
        "unit": None,
        "icon": "mdi:calendar-clock",
        "device_class": "timestamp",
        "state_class": None,
    },
    "refresh_date": {
        "name": "Dernière MAJ Données",
        "unit": None,
        "icon": "mdi:update",
        "device_class": "timestamp",
        "state_class": None,
    },
}

BINARY_SENSOR_TYPES = {
    "online": {
        "name": "En Ligne",
        "device_class": "connectivity",
        "icon": "mdi:lan-connect",
    },
    "standby": {
        "name": "Mode Vacances",
        "device_class": "running",
        "icon": "mdi:power-sleep",
    },
    "salt_alarm": {
        "name": "Alarme Sel",
        "device_class": "problem",
        "icon": "mdi:alert",
    },
    "power_outage": {
        "name": "Coupure Courant",
        "device_class": "problem",
        "icon": "mdi:power-plug-off",
    },
}

MQTT_TOPIC_PREFIX = "bwt"
UNIT_SCALE_THRESHOLD = 1000
MASS_SENSOR_KEYS = frozenset({"salt", "salt_consumption"})
VOLUME_SENSOR_KEYS = frozenset(
    {"vol_ok", "water_consumption", "water_increment", "resin_vol"}
)


def _as_number(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def scale_mass_g(value):
    """Show kilograms once the mass reaches 1000 g."""
    raw = _as_number(value)
    if raw is None:
        return None, "g"
    if raw >= UNIT_SCALE_THRESHOLD:
        return round(raw / 1000.0, 3), "kg"
    return int(raw) if raw == int(raw) else raw, "g"


def scale_volume_l(value):
    """Show cubic meters once the volume reaches 1000 L."""
    raw = _as_number(value)
    if raw is None:
        return None, "L"
    if raw >= UNIT_SCALE_THRESHOLD:
        return round(raw / 1000.0, 3), "m³"
    return int(raw) if raw == int(raw) else raw, "L"


def quantity_mass(value):
    raw = _as_number(value)
    if raw is None:
        return None
    display, unit = scale_mass_g(raw)
    return {"value": display, "unit": unit, "g": int(round(raw))}


def quantity_volume(value):
    raw = _as_number(value)
    if raw is None:
        return None
    display, unit = scale_volume_l(raw)
    return {"value": display, "unit": unit, "L": int(round(raw))}
