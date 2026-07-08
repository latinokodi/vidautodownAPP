# -*- coding: utf-8 -*-
"""
{ADDON_NAME} - Kodi utilities
"""

import os
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from urllib.parse import urlencode

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_PATH = ADDON.getAddonInfo("path")
ADDON_HANDLE = int(sys.argv[1])  # CRITICAL: Capture at import time
ADDON_VERSION = ADDON.getAddonInfo("version")

# Fallback translation dictionary
_STRINGS = {
    30000: "{ADDON_NAME}",
    30001: "Películas",
    30002: "Series",
    30010: "Buscar",
    30300: "Buscar película o serie...",
    30400: "No se encontraron resultados",
    30401: "Error al cargar contenido",
    30402: "Seleccionar fuente",
    30500: "Temporada",
}


def translation(string_id):
    """Get translated string with fallback."""
    result = ADDON.getLocalizedString(string_id)
    return result if result else _STRINGS.get(string_id, str(string_id))


def build_url(action, **kwargs):
    """Build addon URL with parameters."""
    params = {"action": action}
    params.update(kwargs)
    return f"plugin://{ADDON_ID}?{urlencode(params)}"


def get_icon(filename):
    """Get full path to icon asset."""
    icon_path = os.path.join(ADDON_PATH, "resources", "img", filename)
    if os.path.exists(icon_path):
        return icon_path
    # Try jpg if png not found
    jpg_path = os.path.join(ADDON_PATH, "resources", "img", filename.replace(".png", ".jpg"))
    if os.path.exists(jpg_path):
        return jpg_path
    return os.path.join(ADDON_PATH, "resources", "img", "default.png")


def build_list_item(title, icon=None, poster=None, fanart=None, thumb=None):
    """Build a Kodi list item."""
    li = xbmcgui.ListItem(label=title)

    art = {}
    if icon:
        art["icon"] = icon
        art["thumb"] = icon
    if poster:
        art["poster"] = poster
    if fanart:
        art["fanart"] = fanart
    if thumb:
        art["thumb"] = thumb

    # Fallback thumb to poster
    if poster and not art.get("thumb"):
        art["thumb"] = poster

    if art:
        li.setArt(art)

    return li


def add_directory_item(url, li, is_folder=True):
    """Add item to directory."""
    xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=is_folder)


def end_of_directory(cache=True):
    """End directory listing."""
    xbmcplugin.endOfDirectory(ADDON_HANDLE, cacheToDisc=cache)


def set_content_type(content_type):
    """Set content type for directory."""
    xbmcplugin.setContent(ADDON_HANDLE, content_type)


def set_plugin_category(category):
    """Set plugin category for sorting."""
    xbmcplugin.setPluginCategory(ADDON_HANDLE, category)


def notification(message, title=None, icon=None, duration=3000):
    """Show notification."""
    title = title or translation(30000)
    xbmc.executebuiltin(f'Notification("{title}", "{message}", {duration}, "{icon or ""}")')


def input_dialog(title=None):
    """Show input dialog."""
    title = title or translation(30300)
    dialog = xbmcgui.Dialog()
    return dialog.input(title, type=xbmcgui.INPUT_ALPHANUM)


def kodilog(message, level="info"):
    """Log to Kodi debug log."""
    xbmc.log(f"[{ADDON_ID}] {message}", xbmc.LOGDEBUG if level == "debug" else xbmc.LOGINFO)