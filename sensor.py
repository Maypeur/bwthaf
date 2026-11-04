"""Sensor platform for BWT integration."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_NAME,
    CONF_SERIAL_NUMBER,
    DEFAULT_DEVICE_NAME,
    DOMAIN,
    MANUFACTURER,
    MASS_SENSOR_KEYS,
    SENSOR_TYPES,
    VOLUME_SENSOR_KEYS,
    quantity_mass,
    quantity_volume,
    scale_mass_g,
    scale_volume_l,
)
from .coordinator import BWTDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BWT sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(BWTSensor(coordinator, entry, sensor_type))
    
    async_add_entities(entities)


class BWTSensor(CoordinatorEntity, SensorEntity):
    """Representation of a BWT sensor."""

    def __init__(
        self,
        coordinator: BWTDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._serial_number = entry.data[CONF_SERIAL_NUMBER]
        self._device_name = entry.data.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME)
        self._attr_unique_id = f"{self._serial_number}_{sensor_type}"
        
        sensor_info = SENSOR_TYPES[sensor_type]
        self._attr_name = f"{self._device_name} {sensor_info['name']}"
        self._attr_icon = sensor_info["icon"]
        self._attr_device_class = sensor_info.get("device_class")
        self._attr_state_class = sensor_info.get("state_class")
        
        # Device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._serial_number)},
            "name": self._device_name,
            "manufacturer": MANUFACTURER,
            "model": "Adoucisseur BWT",
        }

    def _raw_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._sensor_type)

    def _display_unit(self):
        raw = self._raw_value()
        if self._sensor_type in MASS_SENSOR_KEYS:
            _value, unit = scale_mass_g(raw)
            return unit
        if self._sensor_type in VOLUME_SENSOR_KEYS:
            _value, unit = scale_volume_l(raw)
            return unit
        return SENSOR_TYPES[self._sensor_type]["unit"]

    @property
    def native_value(self):
        """Return the state of the sensor in the native unit (g / L)."""
        return self._raw_value()

    @property
    def native_unit_of_measurement(self):
        return SENSOR_TYPES[self._sensor_type]["unit"]

    @property
    def suggested_unit_of_measurement(self):
        """Ask the frontend for kg / m³ once the value crosses 1000."""
        unit = self._display_unit()
        native = SENSOR_TYPES[self._sensor_type]["unit"]
        return unit if unit and unit != native else None

    @property
    def suggested_display_precision(self):
        if self._display_unit() in ("kg", "m³"):
            return 3
        return None

    @property
    def extra_state_attributes(self):
        """Expose history bounds on the daily counters."""
        data = self.coordinator.data or {}
        if self._sensor_type == "water_consumption":
            total = quantity_volume(data.get("water_total")) or {}
            return {
                "jours": data.get("history_days"),
                "debut": data.get("history_start"),
                "fin": data.get("history_end"),
                "total": total.get("value"),
                "total_unit": total.get("unit"),
                "total_litres": data.get("water_total"),
            }
        if self._sensor_type == "salt_consumption":
            total = quantity_mass(data.get("salt_total")) or {}
            dose = quantity_mass(data.get("salt_per_regen") or data.get("salt")) or {}
            return {
                "jours": data.get("history_days"),
                "debut": data.get("history_start"),
                "fin": data.get("history_end"),
                "total": total.get("value"),
                "total_unit": total.get("unit"),
                "total_grammes": data.get("salt_total"),
                "sel_par_regeneration": dose.get("value"),
                "sel_par_regeneration_unit": dose.get("unit"),
            }
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
