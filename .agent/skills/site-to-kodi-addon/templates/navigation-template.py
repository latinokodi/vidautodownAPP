# -*- coding: utf-8 -*-
"""
{ADDON_NAME} - Navigation and menus
"""

import sys
import xbmc
import xbmcgui
import xbmcplugin
from resources.lib.utils.kodi import (
    build_url,
    build_list_item,
    add_directory_item,
    end_of_directory,
    set_content_type,
    get_icon,
    set_plugin_category,
    notification,
    input_dialog,
)


def root_menu(params=None):
    """Root menu - shows provider categories."""
    xbmc.log("{ADDON_NAME} NAV: root_menu called", xbmc.LOGINFO)

    set_plugin_category("{ADDON_NAME}")

    from resources.lib.providers import Provider

    # Show provider categories
    for name, filter_type in Provider.categories.items():
        xbmc.log(f"{ADDON_NAME} NAV: Building URL for '{name}' with filter='{filter_type}'", xbmc.LOGINFO)
        li = build_list_item(name)
        url = build_url("provider_content", provider=Provider.name, label=filter_type, page=1)
        add_directory_item(url, li)

    # Add search
    search_li = build_list_item("Buscar")
    search_url = build_url("search")
    add_directory_item(search_url, search_li)

    end_of_directory(cache=False)


def provider_content(params):
    """Show content from provider."""
    xbmc.log(f"{ADDON_NAME} NAV: provider_content params={params}", xbmc.LOGINFO)

    provider_name = params.get("provider", "{PROVIDER_NAME}")
    category = params.get("category", "movies")
    filter_type = params.get("label") or params.get("filter", "")
    page = int(params.get("page", 1))

    xbmc.log(f"{ADDON_NAME} NAV: provider={provider_name}, filter_type='{filter_type}', page={page}", xbmc.LOGINFO)

    from resources.lib.providers import ALL_PROVIDERS
    provider = next((p for p in ALL_PROVIDERS if p.name == provider_name), None)

    if not provider:
        notification("Error al cargar contenido")
        end_of_directory()
        return

    set_plugin_category(provider_name)

    try:
        items = provider.get_main_page(page, filter_type)
        _display_content_list(items, category, provider_name, page, filter_type)
    except Exception as e:
        notification(f"Error: {str(e)}")
        end_of_directory()


def _display_content_list(items, category, provider_name, page, filter_type):
    """Display content items in directory."""
    set_content_type("movies" if category == "movies" else "tvshows")

    for item in items:
        title = item.get("title", "")
        poster = item.get("poster", "")
        is_series = item.get("is_series", False)

        li = build_list_item(title, poster=poster)
        li.setProperty("IsPlayable", "false" if is_series else "true")

        info_dict = {
            "title": title,
            "plot": item.get("plot", ""),
        }

        # Add optional metadata
        try:
            if item.get("year"):
                info_dict["year"] = int(item.get("year"))
        except ValueError:
            pass

        li.setInfo("video", info_dict)

        if is_series:
            url = build_url("content_detail", url=item.get("url"), provider=provider_name, category=category)
            add_directory_item(url, li, is_folder=True)
        else:
            url = build_url("play", url=item.get("url"), provider=provider_name, category=category)
            add_directory_item(url, li, is_folder=False)

    # Pagination
    if len(items) >= 20:
        next_li = build_list_item("Siguiente >>", get_icon("next.jpg"))
        next_url = build_url("provider_content", provider=provider_name, category=category, page=page + 1, label=filter_type)
        add_directory_item(next_url, next_li)

    end_of_directory()


def content_detail(params):
    """Show content detail - seasons for series, sources for movies."""
    url = params.get("url")
    provider_name = params.get("provider")

    from resources.lib.providers import ALL_PROVIDERS
    provider = next((p for p in ALL_PROVIDERS if p.name == provider_name), None)

    if not provider:
        notification("Error al cargar contenido")
        end_of_directory()
        return

    try:
        detail = provider.load(url)
        if not detail:
            notification("Error al cargar contenido")
            end_of_directory()
            return

        is_series = detail.get("is_series", False)

        if is_series:
            seasons = detail.get("seasons", [])
            if seasons:
                _show_seasons_list(url, provider_name, seasons)
            else:
                # Direct to episodes
                episodes = detail.get("episodes", [])
                _show_episodes_list(url, provider_name, episodes, 1)
        else:
            # Movie - show sources
            _show_sources_list(url, provider_name, detail)

    except Exception as e:
        notification(f"Error: {str(e)}")
        end_of_directory()


def _show_seasons_list(url, provider_name, seasons):
    """Show seasons list."""
    set_plugin_category("Temporadas")
    set_content_type("tvshows")

    for season in seasons:
        season_num = season.get("number", 1)
        name = f"Temporada {season_num}"
        poster = season.get("poster", "")

        li = build_list_item(name, poster=poster)
        li.setInfo("video", {"season": season_num})

        next_url = build_url("episodes", url=url, provider=provider_name, season=season_num)
        add_directory_item(next_url, li)

    end_of_directory()


def seasons_menu(params):
    """Show seasons for a series."""
    url = params.get("url")
    provider_name = params.get("provider")

    from resources.lib.providers import ALL_PROVIDERS
    provider = next((p for p in ALL_PROVIDERS if p.name == provider_name), None)

    if not provider:
        notification("Error al cargar contenido")
        end_of_directory()
        return

    try:
        detail = provider.load(url)
        seasons = detail.get("seasons", [])
        _show_seasons_list(url, provider_name, seasons)
    except Exception as e:
        notification(f"Error: {str(e)}")
        end_of_directory()


def episodes_menu(params):
    """Show episodes for a season."""
    url = params.get("url")
    provider_name = params.get("provider")
    season = int(params.get("season", 1))

    from resources.lib.providers import ALL_PROVIDERS
    provider = next((p for p in ALL_PROVIDERS if p.name == provider_name), None)

    if not provider:
        notification("Error al cargar contenido")
        end_of_directory()
        return

    try:
        detail = provider.load(url)
        all_episodes = detail.get("episodes", [])
        # Filter by season
        episodes = [ep for ep in all_episodes if ep.get("season", 1) == season]

        if not episodes:
            # Try to get episodes directly
            episodes = provider.get_episodes(url, season)

        _show_episodes_list(url, provider_name, episodes, season)
    except Exception as e:
        notification(f"Error: {str(e)}")
        end_of_directory()


def _show_episodes_list(url, provider_name, episodes, season):
    """Show episodes list."""
    set_plugin_category(f"Temporada {season}")
    set_content_type("episodes")

    for ep in episodes:
        ep_num = ep.get("episode", 0)
        title = ep.get("title", f"Episodio {ep_num}")
        name = f"{ep_num:02d}. {title}"
        poster = ep.get("poster", "")

        li = build_list_item(name, poster=poster)
        li.setProperty("IsPlayable", "true")
        li.setInfo("video", {
            "title": title,
            "episode": ep_num,
            "season": season,
            "plot": ep.get("plot", ""),
        })

        ep_url = ep.get("url", "")
        play_url = build_url("play", url=ep_url, provider=provider_name, category="series")
        add_directory_item(play_url, li, is_folder=False)

    end_of_directory()


def _show_sources_list(url, provider_name, detail):
    """Show available sources for content."""
    from resources.lib.utils.kodi import notification
    from resources.lib.providers import ALL_PROVIDERS

    provider = next((p for p in ALL_PROVIDERS if p.name == provider_name), None)
    if not provider:
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())
        return

    xbmc.executebuiltin(f'Notification("{provider_name}", "Cargando fuentes...", 3000)')

    try:
        sources = provider.load_links(url)
        if not sources:
            xbmcgui.Dialog().ok(provider_name, "No se encontraron fuentes.")
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())
            return

        if len(sources) == 1:
            _resolve_and_play(sources[0])
            return

        # Show source selection
        labels = [s.get("name", "Fuente") for s in sources]
        idx = xbmcgui.Dialog().select("Seleccionar fuente", labels)

        if idx < 0:
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())
            return

        _resolve_and_play(sources[idx])

    except Exception as e:
        notification(f"Error: {str(e)}")
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())


def play_content(params):
    """Play content - resolve URL and start playback."""
    url = params.get("url")
    provider_name = params.get("provider")

    from resources.lib.providers import ALL_PROVIDERS
    provider = next((p for p in ALL_PROVIDERS if p.name == provider_name), None)

    if not provider:
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())
        return

    xbmc.executebuiltin(f'Notification("{provider_name}", "Cargando fuentes...", 3000)')

    try:
        sources = provider.load_links(url)
        if not sources:
            xbmcgui.Dialog().ok(provider_name, "No se encontraron fuentes.")
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())
            return

        if len(sources) == 1:
            _resolve_and_play(sources[0])
            return

        # Show source selection
        labels = [s.get("name", "Fuente") for s in sources]
        idx = xbmcgui.Dialog().select("Seleccionar fuente", labels)

        if idx < 0:
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())
            return

        _resolve_and_play(sources[idx])

    except Exception as e:
        xbmc.executebuiltin(f'Notification("{provider_name}", "Error: {str(e)}", 5000)')
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())


def _resolve_and_play(source):
    """Resolve source URL and play."""
    import xbmc
    from urllib.parse import quote_plus, urlencode

    url = source.get("url", "")
    headers = source.get("headers", {})

    xbmc.log(f"{ADDON_NAME} PLAY: source url={url}", xbmc.LOGINFO)

    # Build final URL with headers
    if headers:
        headers_parts = [f"{k}={quote_plus(str(v))}" for k, v in headers.items()]
        headers_parts.append("verifypeer=false")
        final_url = f"{url}|{urlencode(headers)}"
    else:
        final_url = f"{url}|verifypeer=false"

    xbmc.log(f"{ADDON_NAME} PLAY: final_url={final_url}", xbmc.LOGINFO)

    li = xbmcgui.ListItem(path=final_url)
    li.setProperty("IsPlayable", "true")
    li.setContentLookup(False)

    # Set mimetype for HLS streams
    if ".m3u8" in final_url.lower():
        li.setMimeType("application/vnd.apple.mpegurl")
    elif ".mp4" in final_url.lower():
        li.setMimeType("video/mp4")

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)


def search_menu(params=None):
    """Search menu."""
    query = input_dialog("Buscar película o serie...")
    if not query:
        end_of_directory()
        return

    from resources.lib.providers import ALL_PROVIDERS

    # Search across all providers
    all_results = []
    for provider in ALL_PROVIDERS:
        try:
            results = provider.search(query)
            all_results.extend(results)
        except:
            continue

    if not all_results:
        notification("No se encontraron resultados")
        end_of_directory()
        return

    set_content_type("videos")

    for item in all_results:
        title = item.get("title", "")
        poster = item.get("poster", "")
        is_series = item.get("is_series", False)
        provider_name = item.get("provider", "")

        li = build_list_item(title, poster=poster)
        li.setProperty("IsPlayable", "false" if is_series else "true")

        li.setInfo("video", {
            "title": title,
            "plot": item.get("plot", ""),
        })

        if is_series:
            url = build_url("content_detail", url=item.get("url"), provider=provider_name)
            add_directory_item(url, li, is_folder=True)
        else:
            url = build_url("play", url=item.get("url"), provider=provider_name)
            add_directory_item(url, li, is_folder=False)

    end_of_directory()