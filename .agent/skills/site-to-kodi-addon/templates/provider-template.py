# -*- coding: utf-8 -*-
"""
{SITE_NAME} Provider - {SITE_TYPE} streaming site
Site: {SITE_URL}

{DESCRIPTION}
"""

import re
import xbmc
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from resources.lib.providers.base_provider import BaseProvider, ContentItem, Episode, Source


class {PROVIDER_CLASS}(BaseProvider):
    """Provider for {SITE_URL} - {SITE_TYPE} streaming site."""

    name = "{SITE_NAME}"
    host = "{SITE_URL}"
    supported_types = ["movie", "tv"]

    # Categories mapping (Display Name -> filter_type/label)
    # For Blogger: use Blogger labels
    # For PHP: use category paths
    categories = {
        "Películas": "movies",
        "Series": "series",
        # Add more categories as needed
    }

    def __init__(self):
        super().__init__()
        # Add site-specific headers if needed
        self.session.headers.update({
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        })

    def get_main_page(self, page: int = 1, filter_type: str = None) -> List[Dict]:
        """
        Get main page content.

        {IMPLEMENTATION_NOTE}
        """
        xbmc.log(f"{self.name}: get_main_page page={page}, filter_type='{filter_type}'", xbmc.LOGINFO)

        # === IMPLEMENTATION ===
        # Choose based on site type:
        
        # OPTION A: Blogger JSON Feed
        # start_index = ((page - 1) * 20) + 1
        # if filter_type:
        #     feed_url = f"{self.host}/feeds/posts/default/-/{filter_type}?alt=json&max-results=20&start-index={start_index}"
        # else:
        #     feed_url = f"{self.host}/feeds/posts/default?alt=json&max-results=20&start-index={start_index}"
        # resp = self.session.get(feed_url, timeout=15)
        # data = resp.json()
        # entries = data.get('feed', {}).get('entry', [])
        # return [self._parse_entry(e) for e in entries if self._parse_entry(e)]

        # OPTION B: HTML Parsing
        # url = f"{self.host}/{filter_type}/{page}/" if page > 1 else f"{self.host}/{filter_type}/"
        # resp = self.session.get(url, timeout=15)
        # soup = BeautifulSoup(resp.text, 'html.parser')
        # items = []
        # for elem in soup.select('{SELECTOR}'):
        #     item = self._parse_item(elem)
        #     if item:
        #         items.append(item)
        # return items

        # OPTION C: PHP Endpoint
        # url = f"{self.host}/{filter_type}/"
        # resp = self.session.get(url, timeout=15)
        # ... parse response

        return []  # TODO: Implement

    def _parse_item(self, elem) -> Optional[Dict]:
        """Parse a single item from listing."""
        # Extract title
        title_elem = elem.select_one('{TITLE_SELECTOR}')
        title = title_elem.text.strip() if title_elem else ""

        # Extract URL
        href = elem.get('href', '') or elem.select_one('a').get('href', '') if elem.select_one('a') else ""

        if not title or not href:
            return None

        # Extract poster
        poster = ""
        img = elem.select_one('img')
        if img:
            poster = img.get('src') or img.get('data-src') or ''

        # Detect series
        is_series = '/serie/' in href.lower() or '{SERIES_INDICATOR}' in elem.get('class', [])

        return ContentItem(
            title=title,
            url=self.fix_url(href),
            poster=self.fix_url(poster),
            is_series=is_series,
            provider=self.name,
        ).to_dict()

    def search(self, query: str) -> List[Dict]:
        """Search for content."""
        xbmc.log(f"{self.name}: Searching for '{query}'", xbmc.LOGINFO)

        try:
            # Build search URL
            # Blogger: f"{self.host}/search?q={query}"
            # PHP: f"{self.host}/busqueda.php?p={query}"
            # Custom: f"{self.host}/search/{query}/"
            
            search_url = f"{self.host}/search?q={query}"  # TODO: Adjust
            resp = self.session.get(search_url, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            items = []
            for elem in soup.select('{RESULT_SELECTOR}'):
                item = self._parse_item(elem)
                if item:
                    items.append(item)

            xbmc.log(f"{self.name}: Search found {len(items)} items", xbmc.LOGINFO)
            return items

        except Exception as e:
            xbmc.log(f"{self.name} ERROR in search: {str(e)}", xbmc.LOGERROR)
            return []

    def load(self, url: str) -> Optional[Dict]:
        """Load content details."""
        xbmc.log(f"{self.name}: Loading content {url}", xbmc.LOGINFO)

        try:
            resp = self.session.get(url, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Extract title
            title_elem = soup.select_one('h1, h2.title, .post-title')
            title = title_elem.text.strip() if title_elem else ""

            # Extract plot
            plot_elem = soup.select_one('.sinopsis, .description, .plot')
            plot = plot_elem.text.strip() if plot_elem else ""

            # Extract poster
            poster = ""
            img = soup.select_one('.poster img, img.poster')
            if img:
                poster = img.get('src') or img.get('data-src') or ''

            # Extract year
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', title + plot)
            year = year_match.group(1) if year_match else ""

            # Detect if series
            is_series = '/serie/' in url.lower() or self._detect_series(soup)

            result = {
                "title": title,
                "plot": plot,
                "poster": self.fix_url(poster),
                "is_series": is_series,
                "year": year,
            }

            if is_series:
                # Extract episodes
                episodes = self._extract_episodes(soup, url)
                result['episodes'] = episodes

            xbmc.log(f"{self.name}: Loaded '{title}' (series={is_series})", xbmc.LOGINFO)
            return result

        except Exception as e:
            xbmc.log(f"{self.name} ERROR in load: {str(e)}", xbmc.LOGERROR)
            return None

    def _detect_series(self, soup) -> bool:
        """Detect if content is a series."""
        # Check for episode links
        if soup.select('a[href*="/episodio"], a[href*="temporada"]'):
            return True
        
        # Check for series label
        for label in soup.select('.labels a, .category a'):
            if 'serie' in label.text.lower():
                return True
        
        return False

    def _extract_episodes(self, soup, base_url: str) -> List[Dict]:
        """Extract episodes from series page."""
        episodes = []

        # Method 1: Direct episode links
        for link in soup.select('a[href*="/episodio"], .episode a'):
            href = link.get('href', '')
            text = link.text.strip()
            
            ep_info = self._parse_episode_info(text, href)
            if ep_info:
                episodes.append(Episode(
                    url=self.fix_url(href),
                    title=text,
                    episode=ep_info.get('episode', 0),
                    season=ep_info.get('season', 1),
                ).to_dict())

        # Method 2: JavaScript data
        for script in soup.select('script'):
            content = script.string or ''
            if 'episodes' in content or 'data' in content:
                # Try to parse JSON
                match = re.search(r'var\s+episodes\s*=\s*(\[.*?\])', content)
                if match:
                    try:
                        import json
                        data = json.loads(match.group(1))
                        for ep in data:
                            episodes.append({
                                'url': self.fix_url(ep.get('url', '')),
                                'title': ep.get('title', ''),
                                'episode': ep.get('episode', 0),
                                'season': ep.get('season', 1),
                            })
                    except json.JSONDecodeError:
                        pass

        xbmc.log(f"{self.name}: Found {len(episodes)} episodes", xbmc.LOGINFO)
        return episodes

    def _parse_episode_info(self, text: str, url: str) -> Optional[Dict]:
        """Parse season/episode info from text or URL."""
        combined = f"{text} {url}"

        patterns = [
            (r'[Ss](\d+)[Ee](\d+)', 'standard'),
            (r'[Tt](\d+)[Ee](\d+)', 'spanish'),
            (r'(\d+)[xX](\d+)', 'x_format'),
        ]

        for pattern, _ in patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                return {
                    'season': int(match.group(1)),
                    'episode': int(match.group(2)),
                }

        return None

    def load_links(self, url: str) -> List[Dict]:
        """Load streaming links."""
        xbmc.log(f"{self.name}: Loading links from {url}", xbmc.LOGINFO)

        sources = []

        try:
            resp = self.session.get(url, timeout=15)
            html = resp.text
            soup = BeautifulSoup(html, 'html.parser')

            # Method 1: JavaScript _SV_LINKS variable (Blogger sites)
            sv_links = self._extract_sv_links(html)
            for link in sv_links:
                source = self._process_link(link, url)
                if source:
                    sources.append(source)

            # Method 2: PHP endpoints (if applicable)
            # slug = re.search(r'/([^/]+)/?$', url).group(1)
            # for idx in range(3):
            #     resp = self.session.post(f"{self.host}/serv.php", data={'p': slug, 'r': idx})
            #     iframe = resp.text.strip()
            #     if iframe and iframe != 'Error':
            #         resolved = self.resolve_url(iframe)
            #         if resolved:
            #             sources.append(resolved)

            # Method 3: Direct iframes
            for iframe in soup.select('iframe'):
                src = iframe.get('src') or iframe.get('data-src')
                if src:
                    embed_url = self.fix_url(src)
                    resolved = self.resolve_url(embed_url)
                    if resolved:
                        sources.append(Source(
                            name=self._get_server_name(embed_url),
                            url=resolved['url'],
                            headers=resolved.get('headers', {}),
                            quality=resolved.get('quality', 'HD'),
                        ).to_dict())

            xbmc.log(f"{self.name}: Found {len(sources)} sources", xbmc.LOGINFO)

        except Exception as e:
            xbmc.log(f"{self.name} ERROR in load_links: {str(e)}", xbmc.LOGERROR)

        return sources

    def _extract_sv_links(self, html: str) -> List[Dict]:
        """Extract _SV_LINKS JavaScript variable."""
        links = []
        match = re.search(r'_SV_LINKS\s*=\s*\[(.*?)\]', html, re.DOTALL)

        if not match:
            return links

        content = match.group(1)
        entry_pattern = r'\{[^{}]*lang\s*:\s*["\']([^"\']+)["\'][^{}]*name\s*:\s*["\']([^"\']+)["\'][^{}]*quality\s*:\s*["\']([^"\']+)["\'][^{}]*url\s*:\s*["\']([^"\']+)["\'][^{}]*\}'
        matches = re.findall(entry_pattern, content, re.DOTALL)

        for m in matches:
            lang, name, quality, url = m
            links.append({
                'lang': lang,
                'name': name,
                'quality': quality,
                'url': url,
            })

        return links

    def _process_link(self, link: Dict, referer: str) -> Optional[Dict]:
        """Process a link entry and return source."""
        url = link.get('url', '')
        name = link.get('name', 'Server')
        quality = link.get('quality', 'HD')

        if not url:
            return None

        # Handle link= parameter
        if 'link=' in url:
            from urllib.parse import unquote
            link_match = re.search(r'link=([^&]+)', url)
            if link_match:
                direct_url = unquote(link_match.group(1))
                return Source(
                    name=f"{name} ({link.get('lang', '')})",
                    url=direct_url,
                    headers={'Referer': referer},
                    quality=quality,
                ).to_dict()

        # Resolve embed URL
        resolved = self.resolve_url(url)
        if resolved:
            return Source(
                name=f"{name} ({link.get('lang', '')})",
                url=resolved['url'],
                headers=resolved.get('headers', {}),
                quality=quality,
            ).to_dict()

        return None

    def _get_server_name(self, url: str) -> str:
        """Extract server name from URL."""
        url_lower = url.lower()

        server_map = {
            'streamwish': 'StreamWish',
            'streamtape': 'StreamTape',
            'voe': 'VOE',
            'filemoon': 'Filemoon',
            'vidhide': 'VidHide',
            'dood': 'DoodStream',
            'mixdrop': 'MixDrop',
            'uqload': 'UqLoad',
            'fembed': 'Fembed',
            'ok.ru': 'OK.ru',
        }

        for key, name in server_map.items():
            if key in url_lower:
                return name

        if '.m3u8' in url_lower:
            return 'HLS'
        if '.mp4' in url_lower:
            return 'MP4'

        return 'Server'