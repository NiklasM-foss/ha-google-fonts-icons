/*
 * Meldet die Material Symbols von Google Fonts als Icon-Sets im Frontend an.
 *
 *   gfi:home        Standardstil aus den Integrationsoptionen
 *   gfio:home       outlined
 *   gfir:home       rounded
 *   gfis:home       sharp
 *   gfi:home-fill   gefuellte Variante (Suffix -fill an jedem Namen)
 *
 * Die Pfaddaten liefert die Integration, dieses Modul haelt sie nur im Speicher.
 */

const VERSION = "1.0.0";
const API = "/api/google_fonts_icons";
const VIEW_BOX = "0 -960 960 960";
const FALLBACK_STYLE = "outlined";

const SETS = {
  gfi: null, // null = Stil aus den Optionen
  gfio: "outlined",
  gfir: "rounded",
  gfis: "sharp",
};

const iconCache = new Map();
let statusPromise;
let listPromise;

const getStatus = () => {
  if (!statusPromise) {
    statusPromise = fetch(`${API}/status`)
      .then((response) => (response.ok ? response.json() : {}))
      .catch(() => ({}));
  }
  return statusPromise;
};

const resolveStyle = async (style) => {
  if (style) return style;
  const status = await getStatus();
  return status.style || FALLBACK_STYLE;
};

const requestIcon = async (style, name) => {
  const response = await fetch(`${API}/icon/${style}/${encodeURIComponent(name)}`);
  if (!response.ok) {
    throw new Error(`Icon ${style}:${name} nicht gefunden (${response.status})`);
  }
  const data = await response.json();
  return { path: data.path, viewBox: data.viewBox || VIEW_BOX };
};

const getIcon = async (setStyle, name) => {
  const style = await resolveStyle(setStyle);
  const key = `${style}/${name}`;
  if (!iconCache.has(key)) {
    // Fehlschlaege nicht dauerhaft merken, sonst bleibt das Icon fuer immer leer.
    iconCache.set(
      key,
      requestIcon(style, name).catch((error) => {
        iconCache.delete(key);
        throw error;
      })
    );
  }
  return iconCache.get(key);
};

const getIconList = () => {
  if (!listPromise) {
    listPromise = fetch(`${API}/list`)
      .then((response) => (response.ok ? response.json() : { icons: [] }))
      .then((data) =>
        (data.icons || []).map((name) => ({
          name,
          keywords: name.split(/[_-]/).filter(Boolean),
        }))
      )
      .catch(() => []);
  }
  return listPromise;
};

window.customIcons = window.customIcons || {};
window.customIconsets = window.customIconsets || {};

for (const [prefix, style] of Object.entries(SETS)) {
  const helpers = { getIcon: (name) => getIcon(style, name) };
  // Nur das Standardset fuellt die Icon-Auswahl, sonst haette sie vier
  // vollstaendige Kopien derselben Namen zu filtern.
  if (style === null) {
    helpers.getIconList = getIconList;
  }
  window.customIcons[prefix] = helpers;
  window.customIconsets[prefix] = helpers.getIcon;
}

console.info(
  `%c GOOGLE-FONTS-ICONS %c ${VERSION} `,
  "color:#fff;background:#4285f4;font-weight:700",
  "color:#4285f4;background:#eee"
);
