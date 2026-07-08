# -*- coding: utf-8 -*-
"""
{ADDON_NAME} - Router with deferred imports
"""

import sys
from urllib.parse import parse_qsl

ADDON_ID = "plugin.video.{addon_id}"

# Navigation actions
_NAV_ACTIONS = frozenset({
    "root",
    "search",
    "provider_content",
    "content_detail",
    "seasons",
    "episodes",
    "play",
})


def router(param_string):
    """Main router function."""
    from xbmcplugin import endOfDirectory
    from resources.lib.utils.kodi import ADDON_HANDLE

    if param_string:
        params = dict(parse_qsl(param_string[1:]))  # Remove leading '?'
        action = params.get("action", "")

        if action in _NAV_ACTIONS:
            _route_navigation(action, params)
        else:
            from resources.lib.modules.navigation import root_menu
            root_menu()
    else:
        from resources.lib.modules.navigation import root_menu
        root_menu()


def _route_navigation(action, params):
    """Route to navigation function based on action."""
    # Deferred imports (avoid startup errors)
    from resources.lib.modules.navigation import (
        root_menu,
        search_menu,
        provider_content,
        content_detail,
        seasons_menu,
        episodes_menu,
        play_content,
    )

    actions = {
        "root": root_menu,
        "search": search_menu,
        "provider_content": provider_content,
        "content_detail": content_detail,
        "seasons": seasons_menu,
        "episodes": episodes_menu,
        "play": play_content,
    }

    action_func = actions.get(action)
    if action_func:
        action_func(params)


# Alias for entry point
route = router