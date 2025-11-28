"""Binary sensor platform for BWT integration."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, BINARY_SENSOR_TYPES, CONF_SERIAL_NUMBER, CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME
from .coordinator import BWTDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BWT binary sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for sensor_type in BINARY_SENSOR_TYPES:
        entities.append(BWTBinarySensor(coordinator, entry, sensor_type))
    
    async_add_entities(entities)


class BWTBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a BWT binary sensor."""

    def __init__(
        self,
        coordinator: BWTDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._serial_number = entry.data[CONF_SERIAL_NUMBER]
        self._device_name = entry.data.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME)
        self._attr_unique_id = f"{self._serial_number}_{sensor_type}"
        
        sensor_info = BINARY_SENSOR_TYPES[sensor_type]
        self._attr_name = f"{self._device_name} {sensor_info['name']}"
        self._attr_device_class = sensor_info.get("device_class")
        self._attr_icon = sensor_info.get("icon")
        
        # Device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._serial_number)},
            "name": self._device_name,
            "manufacturer": MANUFACTURER,
            "model": "Adoucisseur BWT",
        }

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None:
            return None
        
        return self.coordinator.data.get(self._sensor_type, False)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
