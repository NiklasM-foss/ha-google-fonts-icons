"""Diagnosedaten des Icon-Sets."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Konfiguration und Zustand des Stores ausgeben."""
    return {
        "options": {**entry.data, **entry.options},
        "store": entry.runtime_data.status(),
    }
