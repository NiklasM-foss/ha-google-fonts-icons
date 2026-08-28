"""HTTP-Endpunkte, aus denen das Frontend die Icon-Pfade zieht."""

from __future__ import annotations

from typing import Any

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant, callback

from .const import API_BASE, DATA_STORE, DOMAIN, STYLES, VIEWBOX
from .store import IconStore

# Icons aendern sich nur mit der Paketversion, der Browser darf sie behalten.
_CACHE_ICON = "public, max-age=86400"
_CACHE_LIST = "public, max-age=3600"
_CACHE_STATUS = "no-cache"


class _BaseView(HomeAssistantView):
    """Gemeinsame Basis: oeffentlich lesbar, liefert nur Icon-Geometrie."""

    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """View an die laufende Instanz binden."""
        self.hass = hass

    @property
    def store(self) -> IconStore | None:
        """Aktueller Store, solange die Integration geladen ist."""
        return self.hass.data.get(DOMAIN, {}).get(DATA_STORE)

    @staticmethod
    def _json(data: Any, cache: str) -> web.Response:
        return web.json_response(data, headers={"Cache-Control": cache})

    @staticmethod
    def _error(reason: str, status: int) -> web.Response:
        return web.json_response({"error": reason}, status=status)


class IconView(_BaseView):
    """Einzelnes Icon als Pfaddaten."""

    url = f"{API_BASE}/icon/{{style}}/{{name}}"
    name = "api:google_fonts_icons:icon"

    async def get(self, request: web.Request, style: str, name: str) -> web.Response:
        """Pfad und viewBox eines Icons liefern."""
        if (store := self.store) is None:
            return self._error("not_loaded", 503)

        if style == "default":
            style = store.style
        if style not in STYLES:
            return self._error("unknown_style", 404)

        path = await store.async_get_icon(style, name)
        if path is None:
            return self._error("unknown_icon", 404)
        return self._json(
            {"path": path, "viewBox": VIEWBOX, "style": style, "name": name},
            _CACHE_ICON,
        )


class ListView(_BaseView):
    """Namensliste fuer die Icon-Auswahl im Frontend."""

    url = f"{API_BASE}/list"
    name = "api:google_fonts_icons:list"

    async def get(self, request: web.Request) -> web.Response:
        """Alle bekannten Icon-Namen liefern."""
        if (store := self.store) is None:
            return self._error("not_loaded", 503)
        return self._json({"icons": await store.async_icon_names()}, _CACHE_LIST)


class StatusView(_BaseView):
    """Aktuelle Konfiguration, damit das Frontend den Standardstil kennt."""

    url = f"{API_BASE}/status"
    name = "api:google_fonts_icons:status"

    async def get(self, request: web.Request) -> web.Response:
        """Stil, Strichstaerke, Version und Anzahl der Icons liefern."""
        if (store := self.store) is None:
            return self._error("not_loaded", 503)
        return self._json(store.status(), _CACHE_STATUS)


@callback
def async_register_views(hass: HomeAssistant) -> None:
    """Views einmalig registrieren, aiohttp kennt kein Abmelden."""
    if hass.data[DOMAIN].get("views_registered"):
        return
    for view in (IconView(hass), ListView(hass), StatusView(hass)):
        hass.http.register_view(view)
    hass.data[DOMAIN]["views_registered"] = True
