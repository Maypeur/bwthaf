"""Data coordinator for BWT integration."""
import logging
from datetime import timedelta, datetime
import requests
from bs4 import BeautifulSoup
import json
import re
import html
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_SERIAL_NUMBER,
    CONF_INTERVAL_MAIN,
    CONF_INTERVAL_CONSUMPTION,
    DEFAULT_INTERVAL_MAIN,
    DEFAULT_INTERVAL_CONSUMPTION,
    BWT_BASE_URL,
    BWT_LOGIN_URL,
    BWT_DASHBOARD_URL,
    BWT_SUMMARY_URL,
    BWT_LOAD_CONSO_URL,
)

_LOGGER = logging.getLogger(__name__)


class BWTDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching BWT data."""

    def __init__(self, hass: HomeAssistant, entry):
        """Initialize."""
        self.entry = entry
        self.session = requests.Session()
        self.receipt_line_key = None
        self._last_main_update = 0
        self._last_water_consumption = 0
        
        interval = entry.options.get(
            CONF_INTERVAL_CONSUMPTION,
            entry.data.get(CONF_INTERVAL_CONSUMPTION, DEFAULT_INTERVAL_CONSUMPTION)
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )

    async def _async_update_data(self):
        """Fetch data from BWT."""
        try:
            # Authentification si nécessaire
            if not self.receipt_line_key:
                await self.hass.async_add_executor_job(self._authenticate)
            
            # Conserver les données existantes
            data = dict(self.data) if self.data else {}
            
            # Données principales (moins fréquent)
            interval_main = self.entry.options.get(
                CONF_INTERVAL_MAIN,
                self.entry.data.get(CONF_INTERVAL_MAIN, DEFAULT_INTERVAL_MAIN)
            )
            
            if (self.hass.loop.time() - self._last_main_update) > interval_main:
                try:
                    main_data = await self.hass.async_add_executor_job(self._get_main_data)
                    data.update(main_data)
                    self._last_main_update = self.hass.loop.time()
                    _LOGGER.debug("Main data updated")
                except Exception as err:
                    _LOGGER.warning("Failed to update main data: %s", err)
                    # Ne pas bloquer si seules les main data échouent
            
            # Données de consommation (fréquent)
            try:
                consumption_data = await self.hass.async_add_executor_job(self._get_consumption_data)
                data.update(consumption_data)
                _LOGGER.debug("Consumption data updated")
            except Exception as err:
                _LOGGER.warning("Failed to update consumption data: %s", err)
                # Ne pas bloquer si seules les consumption data échouent
            
            # Calculer l'incrément d'eau
            if "water_consumption" in data:
                current = data["water_consumption"]
                if self._last_water_consumption > 0:
                    # Détection du changement de jour (reset)
                    if current < self._last_water_consumption:
                        data["water_increment"] = current
                    else:
                        data["water_increment"] = current - self._last_water_consumption
                else:
                    data["water_increment"] = 0
                self._last_water_consumption = current
            
            # Vérifier qu'on a au moins quelques données
            if not data or len(data) < 3:
                raise UpdateFailed("Insufficient data received")
            
            return data
            
        except Exception as err:
            _LOGGER.error("Error fetching BWT data: %s", err)
            # En cas d'erreur d'auth, réinitialiser le receipt_line_key
            if "401" in str(err) or "403" in str(err):
                self.receipt_line_key = None
            raise UpdateFailed(f"Error communicating with API: {err}")

    def _authenticate(self):
        """Authenticate with BWT service."""
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]
        serial_number = self.entry.data[CONF_SERIAL_NUMBER]
        
        _LOGGER.info("Authenticating with BWT service...")
        
        # Login
        response = self.session.post(
            BWT_LOGIN_URL,
            data={
                "_username": username,
                "_password": password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            raise UpdateFailed("Authentication failed")
        
        _LOGGER.info("Authentication successful")
        
        # Get receipt line key
        dashboard = self.session.get(BWT_DASHBOARD_URL)
        soup = BeautifulSoup(dashboard.content, 'html.parser')
        
        links = soup.find_all('a', href=re.compile(r'/device\?receiptLineKey='))
        for link in links:
            info_div = link.find('div', class_='informations')
            if info_div:
                serial_span = info_div.find('span', string=re.compile(serial_number))
                if serial_span:
                    href = link.get('href')
                    match = re.search(r'receiptLineKey=([^&]+)', href)
                    if match:
                        self.receipt_line_key = match.group(1)
                        _LOGGER.info("Receipt line key found: %s", self.receipt_line_key)
                        return
        
        raise UpdateFailed(f"Serial number {serial_number} not found in dashboard")

    def _get_main_data(self):
        """Get main device data."""
        url = f"{BWT_SUMMARY_URL}/{self.receipt_line_key}"
        response = self.session.get(url)
        
        if response.status_code != 200:
            raise UpdateFailed("Failed to fetch main data")
        
        data = response.json()
        
        result = {
            "online": data.get("online", False),
            "standby": data.get("data", {}).get("standBy", False),
            "salt": data.get("data", {}).get("salt"),
        }
        
        # Mapping des codes API vers nos clés de sensors
        code_mapping = {
            # Configuration de l'appareil
            "resinVol": "resin_vol",           # Volume résine (L)
            "inHardness": "in_hardness",       # Dureté d'entrée (°f)
            "outHardness": "out_hardness",     # Dureté de sortie (°f)
            "pressure": "pressure",            # Pression du réseau d'eau (bar)
            
            # Données de régénération
            "salt": "salt",                    # Consommation de sel par régénération (g)
            
            # Données de télémétrie
            "volOK": "vol_ok",                 # Volume d'eau adoucie (L)
            "rssiLevel": "wifi_signal",        # Signal WiFi (dBm)
        }
        
        # Parse configuration categories
        categories = data.get("dataCategories", {})
        for category_name, category_data in categories.items():
            if isinstance(category_data, list):
                for item in category_data:
                    code = item.get("code")
                    value = item.get("value")
                    
                    if code and value is not None:
                        # Utiliser le mapping si disponible
                        if code in code_mapping:
                            mapped_key = code_mapping[code]
                            result[mapped_key] = value
                            _LOGGER.debug("Mapped '%s' → '%s': %s", code, mapped_key, value)
        
        _LOGGER.debug("Main data retrieved: %s", result)
        return result

    def _get_consumption_data(self):
        """Get consumption data."""
        device_url = f"{BWT_BASE_URL}/device?receiptLineKey={self.receipt_line_key}"
        response = self.session.get(device_url)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        live_div = soup.find('div', {'data-controller': 'live'})
        
        if not live_div:
            raise UpdateFailed("Live div not found")
        
        props_value = live_div.get('data-live-props-value', '')
        props_decoded = html.unescape(props_value)
        
        # Construct payload
        payload_data = {
            "props": json.loads(props_decoded),
            "updated": {},
            "args": {}
        }
        
        # Post to loadConso
        response = self.session.post(
            BWT_LOAD_CONSO_URL,
            data={"data": json.dumps(payload_data)},
            headers={"Accept": "application/vnd.live-component+html"}
        )
        
        soup = BeautifulSoup(response.content, 'html.parser')
        graph_div = soup.find('div', id='graph_device')
        
        if not graph_div:
            return {}
        
        # Extract data
        dataset = graph_div.get('data-chart-dataset-value', '{}')
        salt_value = graph_div.get('data-chart-salt-value', '0')
        
        dataset_json = json.loads(html.unescape(dataset))
        
        result = {
            "salt_per_regen": int(salt_value),
        }
        
        # Parser refreshDate (date/heure de mise à jour des données)
        refresh_date_str = dataset_json.get("refreshDate")
        if refresh_date_str:
            try:
                # Format attendu: "2025-11-27T21:54:39.000" (ISO 8601 avec millisecondes)                
                for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                    try:
                        naive_dt = datetime.strptime(refresh_date_str, fmt)
                        result["refresh_date"] = dt_util.as_utc(naive_dt)
                        break
                    except ValueError:
                        continue
                else:
                    _LOGGER.warning("Failed to parse refreshDate '%s'", refresh_date_str)
                    result["refresh_date"] = None
            except Exception as e:
                _LOGGER.warning("Error parsing refreshDate '%s': %s", refresh_date_str, e)
                result["refresh_date"] = None
        
        # Parse first line of data (données les plus récentes)
        lines = dataset_json.get("lines", [])
        if lines:
            first_line = lines[0]
            if len(first_line) >= 5:
                result["last_date"] = first_line[0]  # "2025-11-27"
                result["regen_count"] = int(first_line[1]) if first_line[1] else 0
                result["power_outage"] = first_line[2] if isinstance(first_line[2], bool) else False
                result["water_consumption"] = int(first_line[3]) if first_line[3] else 0
                result["salt_alarm"] = first_line[4] if isinstance(first_line[4], bool) else False
                result["salt_consumption"] = result["regen_count"] * result["salt_per_regen"]
                
                # Parser last_update (date des mesures, sans heure)
                try:
                    naive_dt = datetime.strptime(result["last_date"], "%Y-%m-%d")
                    result["last_update"] = dt_util.as_utc(naive_dt)
                except Exception as e:
                    _LOGGER.warning("Failed to parse last_date '%s': %s", result.get("last_date"), e)
                    result["last_update"] = None
        
        _LOGGER.debug("Consumption data retrieved: %s", result)
        return result
