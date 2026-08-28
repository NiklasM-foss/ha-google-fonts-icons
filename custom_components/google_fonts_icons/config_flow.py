"""Einrichtung ueber die Oberflaeche."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_OFFLINE_PACK,
    CONF_STYLE,
    CONF_WEIGHT,
    DEFAULT_OFFLINE_PACK,
    DEFAULT_STYLE,
    DEFAULT_WEIGHT,
    DOMAIN,
    STYLES,
    WEIGHTS,
)

TITLE = "Google Fonts Icons"


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    """Formular fuer Einrichtung und Optionen."""
    return vol.Schema(
        {
            vol.Required(
                CONF_STYLE, default=defaults.get(CONF_STYLE, DEFAULT_STYLE)
            ): SelectSelector(
                SelectSelectorConfig(
                    options=STYLES,
                    translation_key="style",
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_WEIGHT, default=defaults.get(CONF_WEIGHT, DEFAULT_WEIGHT)
            ): SelectSelector(
                SelectSelectorConfig(options=WEIGHTS, mode=SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(
                CONF_OFFLINE_PACK,
                default=defaults.get(CONF_OFFLINE_PACK, DEFAULT_OFFLINE_PACK),
            ): BooleanSelector(),
        }
    )


class GoogleFontsIconsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Einmalige Einrichtung des Icon-Sets."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Stil, Strichstaerke und Offline-Paket abfragen."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title=TITLE, data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Optionen nachtraeglich aendern."""
        return GoogleFontsIconsOptionsFlow()


class GoogleFontsIconsOptionsFlow(OptionsFlow):
    """Stil, Strichstaerke und Offline-Paket nachtraeglich anpassen."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Formular mit den aktuellen Werten anzeigen."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(defaults))
