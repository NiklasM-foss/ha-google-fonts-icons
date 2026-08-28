"""Diagnose-Sensor mit dem Zustand des Icon-Sets."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_UPDATED
from .store import IconStore


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensor anlegen."""
    async_add_entities([IconSetSensor(entry, entry.runtime_data)])


class IconSetSensor(SensorEntity):
    """Zeigt, wie viele Icons bereitstehen und woher sie kommen."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "Icons"
    _attr_translation_key = "icon_set"

    def __init__(self, entry: ConfigEntry, store: IconStore) -> None:
        """Sensor an den Store der Konfiguration binden."""
        self._store = store
        self._attr_unique_id = f"{entry.entry_id}_icon_set"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Google Fonts Icons",
            manufacturer="Google",
            model="Material Symbols",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        """Auf Meldungen des Stores horchen."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_UPDATED, self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        """Anzahl der Icons im gewaehlten Stil."""
        return self._store.icon_count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Stil, Strichstaerke, Version und Fehlerlage."""
        return self._store.status()
