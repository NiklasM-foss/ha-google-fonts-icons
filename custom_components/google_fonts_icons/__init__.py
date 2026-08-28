"""Material Symbols von Google Fonts als Icon-Set in Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url, remove_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_OFFLINE_PACK,
    CONF_STYLE,
    CONF_VERSION,
    CONF_WEIGHT,
    DATA_STORE,
    DEFAULT_OFFLINE_PACK,
    DEFAULT_STYLE,
    DEFAULT_VERSION,
    DEFAULT_WEIGHT,
    DOMAIN,
    JS_FILENAME,
    JS_URL,
    SERVICE_REFRESH,
)
from .store import IconStore
from .views import async_register_views

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# Wird an die JS-URL gehaengt, damit Browser eine neue Version wirklich holen.
JS_VERSION = "1.0.0"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Icon-Set einrichten: Store, Endpunkte und Frontend-Modul."""
    options = {**entry.data, **entry.options}
    store = IconStore(
        hass,
        style=options.get(CONF_STYLE, DEFAULT_STYLE),
        weight=str(options.get(CONF_WEIGHT, DEFAULT_WEIGHT)),
        version=options.get(CONF_VERSION, DEFAULT_VERSION),
        offline_pack=options.get(CONF_OFFLINE_PACK, DEFAULT_OFFLINE_PACK),
    )
    await store.async_load()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][DATA_STORE] = store
    entry.runtime_data = store

    async_register_views(hass)
    await _async_register_frontend(hass)

    if store.offline_pack:
        entry.async_create_background_task(
            hass, store.async_ensure_pack(), f"{DOMAIN}_pack"
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Icon-Set abmelden."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        data = hass.data.get(DOMAIN, {})
        data.pop(DATA_STORE, None)
        if data.pop("frontend_registered", None):
            remove_extra_js_url(hass, f"{JS_URL}?v={JS_VERSION}")
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
    return unloaded


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Nach Optionsaenderung neu laden, damit Stil und Staerke greifen."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Das Modul ausliefern, das die Icon-Sets im Browser anmeldet."""
    if hass.data[DOMAIN].get("frontend_registered"):
        return
    source = Path(__file__).parent / "frontend" / JS_FILENAME
    await hass.http.async_register_static_paths(
        [StaticPathConfig(JS_URL, str(source), False)]
    )
    add_extra_js_url(hass, f"{JS_URL}?v={JS_VERSION}")
    hass.data[DOMAIN]["frontend_registered"] = True


def _async_register_services(hass: HomeAssistant) -> None:
    """Dienst zum erneuten Laden des Icon-Pakets anbieten."""
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        return

    async def _handle_refresh(call: ServiceCall) -> None:
        store: IconStore | None = hass.data.get(DOMAIN, {}).get(DATA_STORE)
        if store is None:
            _LOGGER.warning("Icon-Set ist nicht geladen, nichts zu aktualisieren")
            return
        await store.async_ensure_pack(force=True)

    hass.services.async_register(DOMAIN, SERVICE_REFRESH, _handle_refresh)
