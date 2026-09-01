# Google Fonts Icons for Home Assistant

*Deutsche Version: [README.de.md](README.de.md)*

Adds the [Material Symbols](https://fonts.google.com/icons) from Google Fonts as an
extra icon set to Home Assistant. That gives you about **3,900 icons per style** (each
with a filled variant, so roughly 7,800 names) everywhere only `mdi:` used to work:
entities, dashboard cards, helpers, areas, scripts.

```yaml
type: tile
entity: light.living_room
icon: gfi:floor_lamp
```

The icons are plain SVG path data taken from the npm package
`@material-symbols/svg-<weight>` and cached on the server. No web font is loaded, and
rendering an icon never sends a request to Google.

## Prefixes

| Prefix | Style |
| --- | --- |
| `gfi:` | the style chosen in the options (default *outlined*), the one that shows up in the icon picker |
| `gfio:` | outlined |
| `gfir:` | rounded |
| `gfis:` | sharp |

The filled variant uses the suffix `-fill`. The name itself is the name from the Google
Fonts catalogue with underscores:

| Example | Result |
| --- | --- |
| `gfi:home` | house, default style |
| `gfi:home-fill` | house, filled |
| `gfir:wb_sunny` | sun, rounded |
| `gfis:water_drop-fill` | droplet, sharp, filled |

Only `gfi:` populates the icon picker in the UI, otherwise the same names would be
listed four times. The other prefixes work just as well when typed in by hand.

## Requirements

- Home Assistant **2024.11.0** or newer
- Internet access on first use, to download the icon package or single icons
- HACS, if you want to install and update it the comfortable way

## Installation

### HACS

1. HACS → menu at the top right → *Custom repositories*
2. Repository `https://github.com/NiklasM-foss/ha-google-fonts-icons`, category *Integration*
3. Install "Google Fonts Icons", then restart Home Assistant
4. Settings → Devices & services → *Add integration* → "Google Fonts Icons"

### Manual

Copy the folder `custom_components/google_fonts_icons` to
`<config>/custom_components/google_fonts_icons` and restart Home Assistant.

The integration registers its own frontend module, so there is **no** need to add a
resource under *Settings → Dashboards → Resources*. After setup, reload the browser page
once (Ctrl+F5) and the icons will render.

## Options

| Option | Meaning |
| --- | --- |
| **Style** | The style behind `gfi:` — outlined, rounded or sharp. |
| **Stroke weight** | 100 to 700, the *weight* axis in Google Fonts. 400 is the default. |
| **Keep all icons locally** | Downloads the complete package once (about 2 MB of download, about 11 MB afterwards in `.storage/google_fonts_icons`). Icons then work without internet. |

With that option turned off, the integration fetches each icon you actually use from the
CDN (jsDelivr) one by one and remembers it permanently. That saves disk space but needs
an internet connection the first time an icon is used.

Option changes take effect after the integration reloads itself and the browser page is
refreshed.

## Service and sensor

- **`google_fonts_icons.refresh`** downloads the package again, for example to pick up
  newly published icons.
- The diagnostic sensor **Icons** shows how many icons are available and exposes style,
  stroke weight, package version, source (`pack` or `cdn`), the number of icons cached
  on demand and the last error as attributes.

## Endpoints

For your own cards or templates the integration serves the path data directly:

| Endpoint | Response |
| --- | --- |
| `/api/google_fonts_icons/status` | style, stroke weight, version, counts |
| `/api/google_fonts_icons/list` | all icon names of the selected style |
| `/api/google_fonts_icons/icon/<style>/<name>` | `{"path": "...", "viewBox": "0 -960 960 960"}` |

`default` is accepted as a style and resolves to the setting from the options. The
endpoints return icon geometry only and therefore need no authentication; they accept
only names built from the character set used by the package.

## Troubleshooting

**Icons stay blank or show as a placeholder.** Reload the browser page with Ctrl+F5. The
frontend module is added with a version query string, but a cached page from before the
setup does not know about the icon sets yet.

**Nothing works after a Home Assistant update.** Check that the integration is still
loaded under Settings → Devices & services. The icon sets are registered by the frontend
module, which is only served while the config entry is set up.

**A single icon is missing.** Check the exact name in the
[Google Fonts catalogue](https://fonts.google.com/icons) — names are lowercase with
underscores (`wb_sunny`, not `wb-sunny` or `WbSunny`). Names that do not match
`[a-z0-9_]` plus an optional `-fill` are rejected on purpose.

**The sensor shows 0 icons or `source: cdn` although the offline pack is enabled.** The
download runs in the background and can fail without internet or npm access. The
attribute `last_error` on the sensor names the reason; call
`google_fonts_icons.refresh` to try again.

**Icons should work without internet.** Enable *Keep all icons locally* in the options.
Only then is the complete package on disk; in on-demand mode every icon that has not
been used yet still needs the CDN.

**Reporting a problem.** Settings → Devices & services → Google Fonts Icons → three-dot
menu → *Download diagnostics* collects the options and the store status without any
personal data.

## License

The code is MIT licensed. The Material Symbols themselves come from Google and are
published under the [Apache License 2.0](https://github.com/google/material-design-icons/blob/master/LICENSE);
they are not part of this repository but downloaded at runtime.
