# Google Fonts Icons für Home Assistant

*English version: [README.md](README.md)*

Bindet die [Material Symbols](https://fonts.google.com/icons) von Google Fonts als
zusätzliches Icon-Set in Home Assistant ein. Damit stehen rund **3.900 Icons je Stil**
(jeweils zusätzlich als gefüllte Variante, also etwa 7.800 Namen) überall dort zur
Verfügung, wo sonst nur `mdi:` möglich ist: Entitäten, Dashboard-Karten, Helfer,
Bereiche, Skripte.

```yaml
type: tile
entity: light.wohnzimmer
icon: gfi:floor_lamp
```

Die Icons kommen als reine Pfaddaten aus dem npm-Paket `@material-symbols/svg-<Stärke>`
und werden serverseitig zwischengespeichert. Es wird keine Schriftart geladen und beim
Anzeigen eines Icons geht keine Anfrage an Google.

## Präfixe

| Präfix | Stil |
| --- | --- |
| `gfi:` | Stil aus den Optionen (Voreinstellung *outlined*), erscheint in der Icon-Auswahl |
| `gfio:` | outlined |
| `gfir:` | rounded |
| `gfis:` | sharp |

Die gefüllte Variante hat das Suffix `-fill`, der Name selbst ist der Name aus dem
Google-Fonts-Katalog mit Unterstrichen:

| Beispiel | Ergebnis |
| --- | --- |
| `gfi:home` | Haus, Standardstil |
| `gfi:home-fill` | Haus, gefüllt |
| `gfir:wb_sunny` | Sonne, rounded |
| `gfis:water_drop-fill` | Tropfen, sharp, gefüllt |

Nur `gfi:` füllt die Icon-Auswahl der Oberfläche, sonst stünden dieselben Namen
viermal in der Liste. Die anderen Präfixe funktionieren durch Eintippen genauso.

## Voraussetzungen

- Home Assistant **2024.11.0** oder neuer
- Beim ersten Einsatz eine Internetverbindung, um das Icon-Paket oder einzelne Icons zu laden
- HACS, wenn Installation und Updates bequem laufen sollen

## Installation

### HACS

1. HACS → Menü oben rechts → *Benutzerdefinierte Repositories*
2. Repository `https://github.com/NiklasM-foss/ha-google-fonts-icons`, Kategorie *Integration*
3. „Google Fonts Icons" installieren, Home Assistant neu starten
4. Einstellungen → Geräte & Dienste → *Integration hinzufügen* → „Google Fonts Icons"

### Manuell

Ordner `custom_components/google_fonts_icons` nach `<config>/custom_components/google_fonts_icons`
kopieren und Home Assistant neu starten.

Das benötigte Frontend-Modul registriert die Integration selbst, es muss **keine**
Ressource unter *Einstellungen → Dashboards → Ressourcen* eingetragen werden. Nach der
Einrichtung einmal die Browser-Seite neu laden (Strg+F5), danach werden die Icons
gerendert.

## Optionen

| Option | Bedeutung |
| --- | --- |
| **Stil** | Stil hinter `gfi:` – outlined, rounded oder sharp. |
| **Strichstärke** | 100 bis 700, entspricht der Achse *weight* in Google Fonts. 400 ist der Standard. |
| **Alle Icons lokal vorhalten** | Lädt das komplette Paket einmalig (rund 2 MB Download, danach etwa 11 MB in `.storage/google_fonts_icons`). Icons funktionieren dann ohne Internet. |

Ist die Option ausgeschaltet, holt die Integration jedes benutzte Icon einzeln vom
CDN (jsDelivr) und merkt es sich dauerhaft. Das spart Plattenplatz, braucht aber beim
ersten Aufruf eines Icons eine Internetverbindung.

Änderungen an den Optionen greifen nach dem automatischen Neuladen der Integration und
einem Neuladen der Browser-Seite.

## Dienst und Sensor

- **`google_fonts_icons.refresh`** lädt das Paket erneut herunter, etwa für neu
  veröffentlichte Icons.
- Der Diagnose-Sensor **Icons** zeigt die Anzahl verfügbarer Icons und als Attribute
  Stil, Strichstärke, Paketversion, Quelle (`pack` oder `cdn`), die Zahl der einzeln
  geholten Icons und den letzten Fehler.

## Endpunkte

Für eigene Karten oder Vorlagen liefert die Integration die Pfaddaten direkt:

| Endpunkt | Antwort |
| --- | --- |
| `/api/google_fonts_icons/status` | Stil, Strichstärke, Version, Anzahl |
| `/api/google_fonts_icons/list` | alle Icon-Namen des gewählten Stils |
| `/api/google_fonts_icons/icon/<stil>/<name>` | `{"path": "...", "viewBox": "0 -960 960 960"}` |

Als Stil ist auch `default` erlaubt, das entspricht der Einstellung aus den Optionen.
Die Endpunkte liefern ausschließlich Icon-Geometrie und brauchen daher keine
Anmeldung, akzeptiert werden nur Namen aus dem Zeichenvorrat des Pakets.

## Fehlersuche

**Icons bleiben leer oder erscheinen als Platzhalter.** Browser-Seite mit Strg+F5 neu
laden. Das Frontend-Modul wird mit Versionskennung eingebunden, eine noch aus der Zeit
vor der Einrichtung zwischengespeicherte Seite kennt die Icon-Sets aber schlicht nicht.

**Nach einem Home-Assistant-Update geht nichts mehr.** Prüfen, ob die Integration unter
Einstellungen → Geräte & Dienste noch geladen ist. Die Icon-Sets meldet das
Frontend-Modul an, und das wird nur ausgeliefert, solange der Konfigurationseintrag
eingerichtet ist.

**Ein einzelnes Icon fehlt.** Den genauen Namen im
[Google-Fonts-Katalog](https://fonts.google.com/icons) nachsehen: klein geschrieben und
mit Unterstrichen (`wb_sunny`, nicht `wb-sunny` oder `WbSunny`). Namen, die nicht aus
`[a-z0-9_]` plus optionalem `-fill` bestehen, werden bewusst abgewiesen.

**Der Sensor zeigt 0 Icons oder `source: cdn`, obwohl das Offline-Paket an ist.** Der
Download läuft im Hintergrund und kann ohne Internet oder npm-Zugriff scheitern. Das
Attribut `last_error` am Sensor nennt den Grund, ein Aufruf von
`google_fonts_icons.refresh` versucht es erneut.

**Icons sollen ohne Internet funktionieren.** In den Optionen *Alle Icons lokal
vorhalten* einschalten. Nur dann liegt das komplette Paket auf Platte, im
Bedarfs-Modus braucht jedes noch nicht benutzte Icon weiterhin das CDN.

**Problem melden.** Einstellungen → Geräte & Dienste → Google Fonts Icons →
Drei-Punkte-Menü → *Diagnose herunterladen* sammelt Optionen und Store-Zustand ohne
personenbezogene Daten.

## Lizenz

Der Code steht unter der MIT-Lizenz. Die Material Symbols selbst stammen von Google und
stehen unter der [Apache-Lizenz 2.0](https://github.com/google/material-design-icons/blob/master/LICENSE);
sie sind nicht Teil dieses Repositories, sondern werden zur Laufzeit geladen.
