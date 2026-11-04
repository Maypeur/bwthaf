"""Config flow for BWT integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_DEVICE_NAME,
    CONF_INTERVAL_CONSUMPTION,
    CONF_INTERVAL_MAIN,
    CONF_SERIAL_NUMBER,
    DEFAULT_DEVICE_NAME,
    DEFAULT_INTERVAL_CONSUMPTION,
    DEFAULT_INTERVAL_MAIN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class BWTConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BWT."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_USERNAME):
                errors[CONF_USERNAME] = "required"
            if not user_input.get(CONF_PASSWORD):
                errors[CONF_PASSWORD] = "required"
            if not user_input.get(CONF_SERIAL_NUMBER):
                errors[CONF_SERIAL_NUMBER] = "required"

            if not errors:
                await self.async_set_unique_id(user_input[CONF_SERIAL_NUMBER])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(
                        CONF_DEVICE_NAME, f"{user_input[CONF_SERIAL_NUMBER]}"
                    ),
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_SERIAL_NUMBER): str,
                vol.Optional(CONF_DEVICE_NAME, default=DEFAULT_DEVICE_NAME): str,
                vol.Optional(
                    CONF_INTERVAL_MAIN, default=DEFAULT_INTERVAL_MAIN
                ): vol.All(vol.Coerce(int), vol.Range(min=300, max=86400)),
                vol.Optional(
                    CONF_INTERVAL_CONSUMPTION, default=DEFAULT_INTERVAL_CONSUMPTION
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> BWTOptionsFlow:
        """Get the options flow for this handler."""
        return BWTOptionsFlow()


class BWTOptionsFlow(OptionsFlow):
    """Handle options flow for BWT."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show and update the current BWT parameters."""
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_INTERVAL_MAIN: int(user_input[CONF_INTERVAL_MAIN]),
                    CONF_INTERVAL_CONSUMPTION: int(
                        user_input[CONF_INTERVAL_CONSUMPTION]
                    ),
                }
            )

        interval_main = int(
            self.config_entry.options.get(
                CONF_INTERVAL_MAIN,
                self.config_entry.data.get(CONF_INTERVAL_MAIN, DEFAULT_INTERVAL_MAIN),
            )
        )
        interval_consumption = int(
            self.config_entry.options.get(
                CONF_INTERVAL_CONSUMPTION,
                self.config_entry.data.get(
                    CONF_INTERVAL_CONSUMPTION, DEFAULT_INTERVAL_CONSUMPTION
                ),
            )
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INTERVAL_MAIN, default=interval_main): NumberSelector(
                        NumberSelectorConfig(
                            min=60,
                            max=86400,
                            step=60,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="s",
                        )
                    ),
                    vol.Required(
                        CONF_INTERVAL_CONSUMPTION, default=interval_consumption
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=30,
                            max=3600,
                            step=30,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="s",
                        )
                    ),
                }
            ),
            description_placeholders={
                "username": str(self.config_entry.data.get(CONF_USERNAME) or ""),
                "serial_number": str(
                    self.config_entry.data.get(CONF_SERIAL_NUMBER) or ""
                ),
                "device_name": str(
                    self.config_entry.data.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME)
                ),
                "interval_main": str(interval_main),
                "interval_consumption": str(interval_consumption),
            },
        )
