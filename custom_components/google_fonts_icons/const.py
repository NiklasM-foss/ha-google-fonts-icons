"""Konstanten der Material-Symbols-Integration."""

from __future__ import annotations

import re
from typing import Final

DOMAIN: Final = "google_fonts_icons"

STYLES: Final = ["outlined", "rounded", "sharp"]
WEIGHTS: Final = ["100", "200", "300", "400", "500", "600", "700"]

CONF_STYLE: Final = "style"
CONF_WEIGHT: Final = "weight"
CONF_OFFLINE_PACK: Final = "offline_pack"
CONF_VERSION: Final = "version"

DEFAULT_STYLE: Final = "outlined"
DEFAULT_WEIGHT: Final = "400"
DEFAULT_VERSION: Final = "latest"
DEFAULT_OFFLINE_PACK: Final = True

# Alle Material Symbols nutzen dasselbe Koordinatensystem.
VIEWBOX: Final = "0 -960 960 960"

API_BASE: Final = "/api/google_fonts_icons"
JS_URL: Final = "/google_fonts_icons/google-fonts-icons.js"
JS_FILENAME: Final = "google-fonts-icons.js"

PACKAGE: Final = "@material-symbols/svg-{weight}"
URL_REGISTRY: Final = "https://registry.npmjs.org/@material-symbols/svg-{weight}/latest"
URL_TARBALL: Final = (
    "https://registry.npmjs.org/@material-symbols/svg-{weight}"
    "/-/svg-{weight}-{version}.tgz"
)
URL_ICON: Final = (
    "https://cdn.jsdelivr.net/npm/@material-symbols/svg-{weight}@{version}"
    "/{style}/{name}.svg"
)
URL_FILELIST: Final = (
    "https://data.jsdelivr.com/v1/packages/npm/@material-symbols/svg-{weight}"
    "@{version}?structure=flat"
)

# Nur diese Zeichen kommen in Dateinamen des Pakets vor, alles andere wird abgewiesen.
ICON_NAME_RE: Final = re.compile(r"^[a-z0-9_]{1,64}(-fill)?$")

SERVICE_REFRESH: Final = "refresh"
SIGNAL_UPDATED: Final = f"{DOMAIN}_updated"

SOURCE_PACK: Final = "pack"
SOURCE_CDN: Final = "cdn"

DATA_STORE: Final = "store"
DATA_ENTRY: Final = "entry"
