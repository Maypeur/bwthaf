"""Data coordinator for BWT integration."""
from __future__ import annotations

import html
import json
import logging
import re
from datetime import date, datetime, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup

from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    BWT_AJAX_CHART_URL,
    BWT_BASE_URL,
    BWT_DASHBOARD_URL,
    BWT_LOAD_CONSO_URL,
    BWT_LOGIN_URL,
    BWT_SUMMARY_URL,
    CONF_INTERVAL_CONSUMPTION,
    CONF_INTERVAL_MAIN,
    CONF_SERIAL_NUMBER,
    DEFAULT_INTERVAL_CONSUMPTION,
    DEFAULT_INTERVAL_MAIN,
    DOMAIN,
    MQTT_TOPIC_PREFIX,
    quantity_mass,
    quantity_volume,
)

_LOGGER = logging.getLogger(__name__)


def _statistic_slug(serial: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (serial or "").lower()).strip("_") or "bwt"


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return int(value)
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return default if number < 0 else number


def _parse_timestamp(value: str | datetime | None):
    if not value:
        return None
    if isinstance(value, datetime):
        return dt_util.as_utc(value)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt_util.as_utc(parsed)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return dt_util.as_utc(datetime.strptime(value, fmt))
        except ValueError:
            continue
    _LOGGER.warning("Failed to parse BWT timestamp '%s'", value)
    return None


def _history_from_lines(lines: list, salt_per_regen: int) -> list[dict[str, Any]]:
    days: list[dict[str, Any]] = []
    for row in lines or []:
        if not isinstance(row, (list, tuple)) or len(row) < 4:
            continue
        day = str(row[0] or "").split("T")[0]
        if not re.match(r"\d{4}-\d{2}-\d{2}$", day):
            continue
        regen = _as_int(row[1])
        water = _as_int(row[3])
        days.append(
            {
                "date": day,
                "regen": regen,
                "power_outage": bool(row[2]) if len(row) > 2 else False,
                "water_l": water,
                "salt_alarm": bool(row[4]) if len(row) > 4 else False,
                "salt_g": regen * salt_per_regen,
            }
        )
    days.sort(key=lambda item: item["date"])
    return days


class BWTDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching BWT data."""

    def __init__(self, hass: HomeAssistant, entry):
        """Initialize."""
        self.entry = entry
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 HomeAssistant/bwthaf",
            }
        )
        self.receipt_line_key = None
        self._last_main_update = 0
        self._last_water_consumption = 0
        self._last_history_signature = None
        self._last_mqtt_signature = None
        self._last_mqtt_history_signature = None

        interval = entry.options.get(
            CONF_INTERVAL_CONSUMPTION,
            entry.data.get(CONF_INTERVAL_CONSUMPTION, DEFAULT_INTERVAL_CONSUMPTION),
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
            if not self.receipt_line_key:
                await self.hass.async_add_executor_job(self._authenticate)

            data = dict(self.data) if self.data else {}

            interval_main = self.entry.options.get(
                CONF_INTERVAL_MAIN,
                self.entry.data.get(CONF_INTERVAL_MAIN, DEFAULT_INTERVAL_MAIN),
            )

            if (self.hass.loop.time() - self._last_main_update) > interval_main:
                try:
                    main_data = await self.hass.async_add_executor_job(
                        self._get_main_data
                    )
                    data.update(main_data)
                    self._last_main_update = self.hass.loop.time()
                    _LOGGER.debug("Main data updated")
                except Exception as err:  # noqa: BLE001
                    _LOGGER.warning("Failed to update main data: %s", err)

            try:
                consumption_data = await self.hass.async_add_executor_job(
                    self._get_consumption_data, data
                )
                data.update(consumption_data)
                _LOGGER.debug("Consumption data updated")
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Failed to update consumption data: %s", err)

            if "water_consumption" in data:
                current = data["water_consumption"]
                if self._last_water_consumption > 0:
                    if current < self._last_water_consumption:
                        data["water_increment"] = current
                    else:
                        data["water_increment"] = current - self._last_water_consumption
                else:
                    data["water_increment"] = 0
                self._last_water_consumption = current

            if not data or len(data) < 3:
                raise UpdateFailed("Insufficient data received")

            self._import_statistics(data)
            await self._async_publish_mqtt(data)
            return data

        except Exception as err:
            _LOGGER.error("Error fetching BWT data: %s", err)
            if "401" in str(err) or "403" in str(err):
                self.receipt_line_key = None
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _authenticate(self):
        """Authenticate with BWT service."""
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]
        serial_number = self.entry.data[CONF_SERIAL_NUMBER]

        _LOGGER.info("Authenticating with BWT service...")

        response = self.session.post(
            BWT_LOGIN_URL,
            data={"_username": username, "_password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code != 200:
            raise UpdateFailed("Authentication failed")

        _LOGGER.info("Authentication successful")

        dashboard = self.session.get(BWT_DASHBOARD_URL)
        page = dashboard.text
        if serial_number not in page:
            raise UpdateFailed("Configured serial number not found in dashboard")

        soup = BeautifulSoup(dashboard.content, "html.parser")
        links = soup.find_all("a", href=re.compile(r"/device\?receiptLineKey="))
        for link in links:
            info_div = link.find("div", class_="informations")
            if info_div and info_div.find("span", string=re.compile(serial_number)):
                href = link.get("href") or ""
                match = re.search(r"receiptLineKey=([^&]+)", href)
                if match:
                    self.receipt_line_key = html.unescape(match.group(1))
                    _LOGGER.info("Receipt line key found")
                    return

        idx = page.find(serial_number)
        window = page[max(0, idx - 3000) : idx + 800]
        match = re.search(r"receiptLineKey=([^\"'&\s>]+)", window) or re.search(
            r"receiptLineKey=([^\"'&\s>]+)", page
        )
        if match:
            self.receipt_line_key = html.unescape(match.group(1))
            _LOGGER.info("Receipt line key found")
            return

        raise UpdateFailed("Configured serial number not found in dashboard")

    def _get_main_data(self):
        """Get main device data."""
        url = f"{BWT_SUMMARY_URL}/{self.receipt_line_key}"
        response = self.session.get(url)
        if response.status_code != 200:
            raise UpdateFailed("Failed to fetch main data")

        data = response.json()
        if not isinstance(data, dict):
            raise UpdateFailed("Unexpected product summary")

        details = data.get("data")
        if not isinstance(details, dict):
            details = {}

        result = {
            "online": bool(data.get("online", False)),
            "standby": bool(details.get("standBy", False)),
            "salt": details.get("salt"),
        }
        if "saltAlarm" in details:
            result["salt_alarm"] = bool(details["saltAlarm"])

        code_mapping = {
            "resinVol": "resin_vol",
            "inHardness": "in_hardness",
            "outHardness": "out_hardness",
            "pressure": "pressure",
            "salt": "salt",
            "volOK": "vol_ok",
            "rssiLevel": "wifi_signal",
        }

        categories = data.get("dataCategories") or {}
        if not isinstance(categories, dict):
            categories = {}
        for _name, category_data in categories.items():
            if not isinstance(category_data, list):
                continue
            for item in category_data:
                code = item.get("code")
                value = item.get("value")
                if code in code_mapping and value is not None:
                    result[code_mapping[code]] = value
                    _LOGGER.debug("Mapped '%s' → '%s': %s", code, code_mapping[code], value)

        _LOGGER.debug("Main data retrieved: %s", result)
        return result

    def _get_consumption_data(self, current: dict | None = None):
        """Get daily consumption history from BWT Mon Service."""
        salt_per_regen = _as_int((current or {}).get("salt"), 0)
        parts: list[dict[str, Any]] = []
        try:
            parts.append(self._get_consumption_from_chart(salt_per_regen))
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("ajaxChart failed: %s", err)
        try:
            parts.append(self._get_consumption_from_live(salt_per_regen))
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("loadConso failed: %s", err)

        merged: dict[str, dict[str, Any]] = {}
        refresh = None
        for part in parts:
            if not part or not part.get("history"):
                continue
            if part.get("salt_per_regen"):
                salt_per_regen = part["salt_per_regen"]
            if part.get("refresh_date"):
                refresh = part["refresh_date"]
            for day in part["history"]:
                existing = merged.get(day["date"])
                if existing is None:
                    merged[day["date"]] = dict(day)
                    continue
                existing["regen"] = max(existing["regen"], day["regen"])
                existing["water_l"] = max(existing["water_l"], day["water_l"])
                existing["power_outage"] = existing["power_outage"] or day["power_outage"]
                existing["salt_alarm"] = existing["salt_alarm"] or day["salt_alarm"]

        if not merged:
            _LOGGER.warning("BWT history empty (salt_per_regen=%s)", salt_per_regen)
            return {}

        lines = [
            [
                day["date"],
                day["regen"],
                day["power_outage"],
                day["water_l"],
                day["salt_alarm"],
            ]
            for day in (merged[key] for key in sorted(merged))
        ]
        result = self._result_from_lines(lines, salt_per_regen, refresh)
        _LOGGER.debug(
            "BWT history: %s days from %s to %s, %s L / %s g salt",
            result.get("history_days"),
            result.get("history_start"),
            result.get("history_end"),
            result.get("water_total"),
            result.get("salt_total"),
        )
        return result

    def _get_consumption_from_chart(self, salt_per_regen: int) -> dict[str, Any]:
        url = f"{BWT_AJAX_CHART_URL}?receiptLineKey={self.receipt_line_key}"
        response = self.session.post(
            url,
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{BWT_BASE_URL}/device?receiptLineKey={self.receipt_line_key}",
            },
            timeout=40,
        )
        if self._session_expired(response):
            self.receipt_line_key = None
            raise UpdateFailed("BWT session expired")
        if response.status_code != 200:
            _LOGGER.warning("ajaxChart returned %s", response.status_code)
            return {}
        try:
            payload = response.json()
        except ValueError:
            _LOGGER.warning(
                "ajaxChart is not JSON (%s)",
                response.headers.get("Content-Type"),
            )
            return {}
        dataset = payload.get("dataset") or {}
        history = dataset.get("deviceDataHistory") or {}
        lines = history.get("lines") or []
        refresh = history.get("refreshDate") or payload.get("refreshDate")
        parsed = self._result_from_lines(lines, salt_per_regen, refresh)
        if not parsed:
            _LOGGER.warning("ajaxChart has no history lines (%s keys)", list(payload)[:8])
        return parsed

    def _session_expired(self, response) -> bool:
        url = str(getattr(response, "url", "") or "")
        return "/login" in url and "/device" not in url

    def _find_live_div(self, soup: BeautifulSoup):
        live_div = soup.find(attrs={"data-live-name-value": "DeviceTabs"})
        if live_div:
            return live_div
        for element in soup.find_all(attrs={"data-live-props-value": True}):
            name = element.get("data-live-name-value") or ""
            if "DeviceTabs" in name:
                return element
        for element in soup.find_all(attrs={"data-controller": True}):
            controllers = (element.get("data-controller") or "").split()
            if "live" in controllers:
                return element
        return soup.find(attrs={"data-live-props-value": True})

    def _diagnose_missing_live(self, soup: BeautifulSoup) -> None:
        controllers = sorted(
            {
                token
                for element in soup.find_all(attrs={"data-controller": True})
                for token in (element.get("data-controller") or "").split()
                if token
            }
        )
        live_names = sorted(
            {
                name
                for element in soup.find_all(attrs={"data-live-name-value": True})
                if (name := (element.get("data-live-name-value") or "").strip())
            }
        )
        _LOGGER.warning(
            "Live component not found (controllers=%s live_names=%s)",
            ",".join(controllers)[:200],
            ",".join(live_names)[:200],
        )

    def _get_consumption_from_live(self, salt_per_regen: int) -> dict[str, Any]:
        device_url = f"{BWT_BASE_URL}/device?receiptLineKey={self.receipt_line_key}"
        response = self.session.get(device_url, timeout=40)
        if self._session_expired(response):
            self.receipt_line_key = None
            raise UpdateFailed("BWT session expired")
        soup = BeautifulSoup(response.content, "html.parser")
        live_div = self._find_live_div(soup)
        if not live_div:
            self._diagnose_missing_live(soup)
            raise UpdateFailed("Live div not found")

        props_value = live_div.get("data-live-props-value", "")
        props = json.loads(html.unescape(props_value))
        if not salt_per_regen:
            salt_per_regen = _as_int(props.get("consoSalt"))

        component = (live_div.get("data-live-name-value") or "").strip()
        load_url = (
            f"{BWT_BASE_URL}/_components/{component}/loadConso"
            if component
            else BWT_LOAD_CONSO_URL
        )
        headers = {
            "Accept": "application/vnd.live-component+html",
            "X-Requested-With": "XMLHttpRequest",
        }
        csrf = live_div.get("data-live-csrf-value")
        if csrf:
            headers["X-CSRF-TOKEN"] = csrf

        response = self.session.post(
            load_url,
            data={"data": json.dumps({"props": props, "updated": {}, "args": {}})},
            headers=headers,
            timeout=40,
        )
        soup = BeautifulSoup(response.content, "html.parser")
        graph_div = soup.find("div", id="graph_device")
        if not graph_div:
            return {}

        dataset = json.loads(html.unescape(graph_div.get("data-chart-dataset-value", "{}")))
        salt_attr = graph_div.get("data-chart-salt-value")
        if salt_attr not in (None, ""):
            salt_per_regen = _as_int(salt_attr, salt_per_regen)
        return self._result_from_lines(
            dataset.get("lines") or [],
            salt_per_regen,
            dataset.get("refreshDate"),
        )

    def _result_from_lines(
        self, lines: list, salt_per_regen: int, refresh_date_str: str | None
    ) -> dict[str, Any]:
        history = _history_from_lines(lines, salt_per_regen)
        if not history:
            return {}
        latest = history[-1]
        result: dict[str, Any] = {
            "salt_per_regen": salt_per_regen,
            "last_date": latest["date"],
            "regen_count": latest["regen"],
            "power_outage": latest["power_outage"],
            "water_consumption": latest["water_l"],
            "salt_alarm": latest["salt_alarm"],
            "salt_consumption": sum(day["salt_g"] for day in history),
            "refresh_date": _parse_timestamp(refresh_date_str),
            "last_update": _parse_timestamp(latest["date"]),
            "history": history,
            "history_days": len(history),
            "history_start": history[0]["date"],
            "history_end": latest["date"],
            "water_total": sum(day["water_l"] for day in history),
            "salt_total": sum(day["salt_g"] for day in history),
        }
        if salt_per_regen:
            result["salt"] = salt_per_regen
        return result

    def _import_statistics(self, data: dict[str, Any]) -> None:
        """Import daily water and salt into the Home Assistant recorder."""
        history = data.get("history") or []
        if not history:
            return
        signature = (
            history[0]["date"],
            history[-1]["date"],
            len(history),
            history[-1]["water_l"],
            history[-1]["regen"],
            data.get("water_total"),
            data.get("salt_total"),
        )
        if signature == self._last_history_signature:
            return

        try:
            from homeassistant.components.recorder.models import StatisticMeanType
            from homeassistant.components.recorder.statistics import (
                async_add_external_statistics,
            )
        except ImportError:
            _LOGGER.debug("Recorder unavailable, BWT history not imported")
            return

        slug = _statistic_slug(self.entry.data[CONF_SERIAL_NUMBER])
        timezone = dt_util.get_default_time_zone()
        water_points: list[dict[str, Any]] = []
        salt_points: list[dict[str, Any]] = []
        cum_water = 0.0
        cum_salt = 0.0
        for day in history:
            try:
                day_date = date.fromisoformat(day["date"])
            except ValueError:
                continue
            start_at = datetime.combine(day_date, datetime.min.time(), tzinfo=timezone)
            cum_water += day["water_l"]
            cum_salt += day["salt_g"]
            water_points.append({"start": start_at, "state": cum_water, "sum": cum_water})
            salt_points.append({"start": start_at, "state": cum_salt, "sum": cum_salt})

        series = (
            (
                f"{DOMAIN}:water_{slug}",
                "BWT eau adoucie",
                "L",
                water_points,
            ),
            (
                f"{DOMAIN}:salt_{slug}",
                "BWT sel consommé",
                "g",
                salt_points,
            ),
        )
        for statistic_id, name, unit, points in series:
            if not points:
                continue
            metadata = {
                "has_mean": False,
                "has_sum": True,
                "mean_type": StatisticMeanType.NONE,
                "name": name,
                "source": DOMAIN,
                "statistic_id": statistic_id,
                "unit_of_measurement": unit,
            }
            try:
                async_add_external_statistics(self.hass, metadata, points)
            except Exception:  # noqa: BLE001
                _LOGGER.warning("Impossible d'importer %s", statistic_id, exc_info=True)
                return
        self._last_history_signature = signature
        _LOGGER.info("BWT statistics imported: %s days", len(history))

    async def _async_publish_mqtt(self, data: dict[str, Any]) -> None:
        """Publish BWT Mon Service data on the bwt MQTT topic tree."""
        if "mqtt" not in self.hass.config.components:
            return
        from homeassistant.components.mqtt import async_publish

        serial = self.entry.data[CONF_SERIAL_NUMBER]
        slug = _statistic_slug(serial)
        history = data.get("history") or []
        latest = history[-1] if history else {}
        snapshot = {
            "serial": serial,
            "online": data.get("online"),
            "standby": data.get("standby"),
            "salt_alarm": data.get("salt_alarm"),
            "power_outage": data.get("power_outage"),
            "pressure_bar": data.get("pressure"),
            "in_hardness_f": data.get("in_hardness"),
            "out_hardness_f": data.get("out_hardness"),
            "wifi_signal_dbm": data.get("wifi_signal"),
            "resin_vol": quantity_volume(data.get("resin_vol")),
            "vol_ok": quantity_volume(data.get("vol_ok")),
            "water_today": quantity_volume(data.get("water_consumption")),
            "water_increment": quantity_volume(data.get("water_increment")),
            "water_total": quantity_volume(data.get("water_total")),
            "salt_per_regen": quantity_mass(
                data.get("salt_per_regen") or data.get("salt")
            ),
            "salt_today": quantity_mass(latest.get("salt_g")),
            "salt_total": quantity_mass(
                data.get("salt_total") or data.get("salt_consumption")
            ),
            "regen_today": data.get("regen_count"),
            "history_days": data.get("history_days"),
            "history_start": data.get("history_start"),
            "history_end": data.get("history_end"),
            "last_update": _iso(data.get("last_update")),
            "refresh_date": _iso(data.get("refresh_date")),
        }
        snapshot_signature = json.dumps(snapshot, sort_keys=True, ensure_ascii=False)
        history_signature = (
            data.get("history_start"),
            data.get("history_end"),
            data.get("history_days"),
            data.get("water_total"),
            data.get("salt_total"),
            latest.get("water_l"),
            latest.get("regen"),
        )
        try:
            if snapshot_signature != self._last_mqtt_signature:
                await async_publish(
                    self.hass,
                    f"{MQTT_TOPIC_PREFIX}/{slug}",
                    snapshot_signature,
                    qos=0,
                    retain=True,
                )
                self._last_mqtt_signature = snapshot_signature
            if history and history_signature != self._last_mqtt_history_signature:
                history_payload = {
                    "serial": serial,
                    "history_days": data.get("history_days"),
                    "history_start": data.get("history_start"),
                    "history_end": data.get("history_end"),
                    "water_total": quantity_volume(data.get("water_total")),
                    "salt_total": quantity_mass(data.get("salt_total")),
                    "days": [
                        {
                            "date": day["date"],
                            "water": quantity_volume(day["water_l"]),
                            "salt": quantity_mass(day["salt_g"]),
                            "regen": day["regen"],
                            "power_outage": day["power_outage"],
                            "salt_alarm": day["salt_alarm"],
                        }
                        for day in history
                    ],
                }
                await async_publish(
                    self.hass,
                    f"{MQTT_TOPIC_PREFIX}/{slug}/history",
                    json.dumps(history_payload, ensure_ascii=False),
                    qos=0,
                    retain=True,
                )
                self._last_mqtt_history_signature = history_signature
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Publication MQTT BWT impossible", exc_info=True)


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
