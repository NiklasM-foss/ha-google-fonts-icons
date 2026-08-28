"""Beschafft und verwaltet die Icon-Pfade der Material Symbols."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import re
import tarfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import STORAGE_DIR, Store

from .const import (
    DOMAIN,
    ICON_NAME_RE,
    SIGNAL_UPDATED,
    SOURCE_CDN,
    SOURCE_PACK,
    STYLES,
    URL_FILELIST,
    URL_ICON,
    URL_REGISTRY,
    URL_TARBALL,
    VIEWBOX,
)

_LOGGER = logging.getLogger(__name__)

_SVG_RE = re.compile(r'<path[^>]*\bd="([^"]+)"')
_DOWNLOAD_TIMEOUT = 180
_ICON_TIMEOUT = 20


def _extract_pack(raw: bytes) -> dict[str, dict[str, str]]:
    """Tarball auspacken und je Stil ein Verzeichnis Name zu Pfad bauen."""
    icons: dict[str, dict[str, str]] = {style: {} for style in STYLES}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith(".svg"):
                continue
            parts = member.name.split("/")
            if len(parts) < 2:
                continue
            style, name = parts[-2], parts[-1][:-4]
            if style not in icons:
                continue
            handle = tar.extractfile(member)
            if handle is None:
                continue
            match = _SVG_RE.search(handle.read().decode("utf-8", "replace"))
            if match:
                icons[style][name] = match.group(1)
    return icons


class IconStore:
    """Haelt die Icon-Pfade, laedt sie bei Bedarf nach und legt sie auf Platte ab."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        style: str,
        weight: str,
        version: str,
        offline_pack: bool,
    ) -> None:
        """Store fuer eine Kombination aus Stil, Strichstaerke und Paketversion."""
        self.hass = hass
        self.style = style
        self.weight = weight
        self.requested_version = version or "latest"
        self.offline_pack = offline_pack
        self.last_error: str | None = None

        self._dir = Path(hass.config.path(STORAGE_DIR, DOMAIN))
        self._meta: dict[str, Any] = {}
        self._loaded: dict[str, dict[str, str]] = {}
        self._names: list[str] = []
        self._ondemand_store: Store[dict[str, str]] = Store(
            hass, 1, f"{DOMAIN}.ondemand"
        )
        self._ondemand: dict[str, str] = {}
        self._pack_lock = asyncio.Lock()
        self._style_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._names_lock = asyncio.Lock()

    # ---------------------------------------------------------------- Zustand

    @property
    def version(self) -> str | None:
        """Version des zuletzt heruntergeladenen Pakets."""
        return self._meta.get("version")

    @property
    def has_pack(self) -> bool:
        """Liegt ein vollstaendiges Paket passend zur Konfiguration auf Platte?"""
        return bool(self._meta) and self._meta.get("weight") == self.weight

    @property
    def icon_count(self) -> int:
        """Anzahl verfuegbarer Icons im gewaehlten Stil."""
        if self.has_pack:
            return int(self._meta.get("counts", {}).get(self.style, 0))
        return len(self._ondemand)

    def status(self) -> dict[str, Any]:
        """Zusammenfassung fuer Sensor, Diagnose und Frontend."""
        return {
            "style": self.style,
            "weight": self.weight,
            "version": self.version or self.requested_version,
            "source": SOURCE_PACK if self.has_pack else SOURCE_CDN,
            "offline_pack": self.offline_pack,
            "icon_count": self.icon_count,
            "cached_on_demand": len(self._ondemand),
            "view_box": VIEWBOX,
            "last_error": self.last_error,
        }

    # ------------------------------------------------------------------ Laden

    async def async_load(self) -> None:
        """Metadaten und den Zwischenspeicher einzeln geladener Icons einlesen."""
        self._meta = await self.hass.async_add_executor_job(self._read_meta)
        self._ondemand = await self._ondemand_store.async_load() or {}

    def _read_meta(self) -> dict[str, Any]:
        path = self._dir / "meta.json"
        if not path.is_file():
            return {}
        try:
            meta = json.loads(path.read_text("utf-8"))
        except (OSError, ValueError):
            return {}
        counts = meta.get("counts", {})
        if not counts or not all(
            (self._dir / f"{style}.json").is_file() for style in counts
        ):
            return {}
        return meta

    # ------------------------------------------------------------------ Paket

    async def async_ensure_pack(self, force: bool = False) -> bool:
        """Paket herunterladen, falls es fehlt oder nicht mehr zur Konfig passt."""
        async with self._pack_lock:
            version = await self._async_resolve_version()
            if (
                not force
                and self.has_pack
                and (version is None or self._meta.get("version") == version)
            ):
                return True
            if version is None:
                return self.has_pack

            url = URL_TARBALL.format(weight=self.weight, version=version)
            _LOGGER.debug("Lade Icon-Paket %s", url)
            try:
                session = async_get_clientsession(self.hass)
                async with session.get(url, timeout=_DOWNLOAD_TIMEOUT) as resp:
                    resp.raise_for_status()
                    raw = await resp.read()
                icons = await self.hass.async_add_executor_job(_extract_pack, raw)
                meta = await self.hass.async_add_executor_job(
                    self._write_pack, icons, version
                )
            except Exception as err:  # noqa: BLE001
                self.last_error = f"Paket {version} nicht ladbar: {err}"
                _LOGGER.warning("Icon-Paket konnte nicht geladen werden: %s", err)
                self._notify()
                return self.has_pack

            self._meta = meta
            self._loaded.clear()
            self._names = []
            self.last_error = None
            _LOGGER.info(
                "Material Symbols %s (Strichstaerke %s) bereit: %s Icons je Stil",
                version,
                self.weight,
                meta.get("counts", {}).get(self.style, 0),
            )
            self._notify()
            return True

    def _write_pack(
        self, icons: dict[str, dict[str, str]], version: str
    ) -> dict[str, Any]:
        self._dir.mkdir(parents=True, exist_ok=True)
        counts: dict[str, int] = {}
        for style, entries in icons.items():
            (self._dir / f"{style}.json").write_text(
                json.dumps(entries, separators=(",", ":")), "utf-8"
            )
            counts[style] = len(entries)
        meta = {"version": version, "weight": self.weight, "counts": counts}
        (self._dir / "meta.json").write_text(json.dumps(meta), "utf-8")
        return meta

    async def _async_resolve_version(self) -> str | None:
        """Gewuenschte Version bestimmen, latest fragt die npm-Registry."""
        if self.requested_version != "latest":
            return self.requested_version
        try:
            session = async_get_clientsession(self.hass)
            url = URL_REGISTRY.format(weight=self.weight)
            async with session.get(url, timeout=_ICON_TIMEOUT) as resp:
                resp.raise_for_status()
                return str((await resp.json(content_type=None))["version"])
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Version nicht abfragbar: %s", err)
            self.last_error = f"Version nicht abfragbar: {err}"
            return self._meta.get("version")

    # ------------------------------------------------------------------ Icons

    async def async_get_icon(self, style: str, name: str) -> str | None:
        """Pfaddaten eines Icons liefern, notfalls einzeln vom CDN holen."""
        if style not in STYLES or not ICON_NAME_RE.match(name):
            return None

        entries = await self._async_style_entries(style)
        if path := entries.get(name):
            return path

        key = f"{self.weight}/{style}/{name}"
        if path := self._ondemand.get(key):
            return path
        return await self._async_fetch_icon(style, name, key)

    async def _async_style_entries(self, style: str) -> dict[str, str]:
        if not self.has_pack:
            return {}
        if style in self._loaded:
            return self._loaded[style]
        async with self._style_locks[style]:
            if style not in self._loaded:
                self._loaded[style] = await self.hass.async_add_executor_job(
                    self._read_style, style
                )
        return self._loaded[style]

    def _read_style(self, style: str) -> dict[str, str]:
        path = self._dir / f"{style}.json"
        try:
            return json.loads(path.read_text("utf-8"))
        except (OSError, ValueError) as err:
            _LOGGER.warning("Stil %s nicht lesbar: %s", style, err)
            return {}

    async def _async_fetch_icon(self, style: str, name: str, key: str) -> str | None:
        version = self.version or await self._async_resolve_version() or "latest"
        url = URL_ICON.format(
            weight=self.weight, version=version, style=style, name=name
        )
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(url, timeout=_ICON_TIMEOUT) as resp:
                if resp.status == 404:
                    return None
                resp.raise_for_status()
                svg = await resp.text()
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Icon %s/%s nicht ladbar: %s", style, name, err)
            return None

        match = _SVG_RE.search(svg)
        if not match:
            return None
        self._ondemand[key] = match.group(1)
        self._ondemand_store.async_delay_save(lambda: dict(self._ondemand), 30)
        return match.group(1)

    # ------------------------------------------------------------------ Liste

    async def async_icon_names(self) -> list[str]:
        """Alle Icon-Namen des gewaehlten Stils fuer die Icon-Auswahl."""
        if self._names:
            return self._names
        async with self._names_lock:
            if self._names:
                return self._names
            entries = await self._async_style_entries(self.style)
            self._names = sorted(entries) if entries else await self._async_fetch_names()
        return self._names

    async def _async_fetch_names(self) -> list[str]:
        """Ohne Paket die Namensliste einmalig aus dem CDN-Verzeichnis ziehen."""
        cache = self._dir / f"names-{self.weight}.json"
        if names := await self.hass.async_add_executor_job(self._read_names, cache):
            return names

        version = self.version or await self._async_resolve_version()
        if version is None:
            return []
        try:
            session = async_get_clientsession(self.hass)
            url = URL_FILELIST.format(weight=self.weight, version=version)
            async with session.get(url, timeout=_DOWNLOAD_TIMEOUT) as resp:
                resp.raise_for_status()
                listing = await resp.json(content_type=None)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Namensliste nicht ladbar: %s", err)
            return []

        prefix = f"/{self.style}/"
        names = sorted(
            entry["name"][len(prefix) : -4]
            for entry in listing.get("files", [])
            if entry.get("name", "").startswith(prefix)
            and entry["name"].endswith(".svg")
        )
        await self.hass.async_add_executor_job(self._write_names, cache, names)
        return names

    def _read_names(self, cache: Path) -> list[str]:
        try:
            return json.loads(cache.read_text("utf-8"))
        except (OSError, ValueError):
            return []

    def _write_names(self, cache: Path, names: list[str]) -> None:
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(names, separators=(",", ":")), "utf-8")
        except OSError as err:
            _LOGGER.debug("Namensliste nicht speicherbar: %s", err)

    def _notify(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_UPDATED)
