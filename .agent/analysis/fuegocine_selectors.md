# FuegoCine Website Selector Analysis

**Date:** 2026-04-19  
**Site:** https://www.fuegocine.com  
**Platform:** Blogger (Google)

---

## Executive Summary

The fuegocine.com website uses two different rendering approaches depending on the page type:

1. **Label/Search Pages** (`/search/label/Movie`, `/search/label/Serie`) - Server-side rendered HTML with `.crd` card elements
2. **Main Page** (`/`) - JavaScript template rendering with placeholders (requires Blogger JSON feed API)

---

## Page Structure Analysis

### 1. Label/Search Pages (e.g., `/search/label/Movie`)

These pages return fully rendered HTML. The structure is:

```
div.crd                          (movie card container)
  picture.crd__image             (poster container)
    a[href$=".html"]             (link to movie page)
      img[src="..."]             (poster image)
  div.crd__body                  (card body)
    h3.crd__title                (title container)
      a[href$=".html"]           (title link)
        {title text}
```

### 2. Main Page (`/`)

The main page uses **client-side JavaScript rendering** with template placeholders:

```html
<div class="crd crd-overlap">
  <picture class="crd__image">
    <a href="{url}">                    <!-- Placeholder, not real URL -->
      <img src="{image}" />             <!-- Placeholder -->
    </a>
  </picture>
  <div class="crd__body">
    <h3 class="crd__title">{title}</h3>  <!-- Placeholder text -->
  </div>
</div>
```

**Solution:** Use the Blogger JSON feed API instead of HTML parsing for the main page.

---

## Working Selectors

### For Label/Search Pages (HTML Parsing)

| Element | CSS Selector | Description |
|---------|-------------|-------------|
| **Content Container** | `.crd` | Each movie/series card |
| **Title** | `h3.crd__title a` | Title text in link |
| **URL** | `h3.crd__title a[href]` or `.crd__image a[href]` | Link to content page |
| **Poster Image** | `.crd__image img` or `picture img` | Image element |
| **Pagination** | `#blog-pager a` | "Entradas antiguas" link |

### For Main Page (Blogger JSON Feed)

**Feed URL:**  
```
https://www.fuegocine.com/feeds/posts/default?alt=json&max-results=20
```

**Pagination:**  
```
https://www.fuegocine.com/feeds/posts/default?alt=json&max-results=20&start-index=21
```

**Category Filter:**  
```
https://www.fuegocine.com/feeds/posts/default/-/Movie?alt=json&max-results=20
```

---

## Verified Test Results

### Test 1: Label Page (`/search/label/Movie`)
- **Status:** 200 OK
- **Cards Found:** 20 `.crd` elements
- **Items Extracted:** 20 movies with title, URL, and poster
- **Pagination:** Found `#blog-pager a` with correct URL

### Test 2: Series Label (`/search/label/Serie`)
- **Status:** 200 OK
- **Cards Found:** 20 `.crd` elements
- **Items Extracted:** 20 series entries

### Test 3: Blogger JSON Feed
- **Status:** 200 OK
- **Entries Found:** 20
- **Data Available:** Title, URL, content, categories, thumbnails

---

## Working Python Implementation

```python
# -*- coding: utf-8 -*-
"""
FuegoCine Provider - Corrected Implementation
Site: https://www.fuegocine.com
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ContentItem:
    title: str
    url: str
    poster: str = ""
    is_series: bool = False
    provider: str = "FuegoCine"

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "url": self.url,
            "poster": self.poster,
            "is_series": self.is_series,
            "provider": self.provider,
        }


class FuegoCineProvider:
    """Provider for fuegocine.com with dual-mode fetching."""
    
    name = "FuegoCine"
    host = "https://www.fuegocine.com"
    
    # Blogger blog ID (discovered from page source)
    BLOG_ID = "4722968919659799364"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        })
    
    def fix_url(self, url: str) -> str:
        """Ensure URL is absolute."""
        if not url:
            return ""
        if url.startswith('//'):
            return f"https:{url}"
        if not url.startswith('http'):
            return f"{self.host}{url}"
        return url
    
    def get_main_page(self, page: int = 1, filter_type: str = None) -> List[Dict]:
        """
        Get main page content.
        
        For label pages (filter_type set): Use HTML parsing
        For main page (no filter): Use Blogger JSON feed
        """
        if filter_type:
            # Use HTML parsing for label pages
            return self._get_label_page(page, filter_type)
        else:
            # Use JSON feed for main page
            return self._get_json_feed(page)
    
    def _get_label_page(self, page: int, label: str) -> List[Dict]:
        """Fetch content from Blogger label page using HTML parsing."""
        url = f"{self.host}/search/label/{label}"
        if page > 1:
            # Blogger pagination uses max-results and start parameters
            url = f"{url}?max-results=20&start={((page - 1) * 20)}"
        
        try:
            resp = self.session.get(url, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            items = []
            # CORRECT SELECTORS:
            # Container: .crd
            # Title: h3.crd__title a
            # Poster: .crd__image img
            for card in soup.select('.crd'):
                item = self._parse_card(card)
                if item:
                    items.append(item)
            
            return items
        except Exception as e:
            print(f"Error fetching label page: {e}")
            return []
    
    def _get_json_feed(self, page: int) -> List[Dict]:
        """Fetch content from Blogger JSON feed API."""
        # Blogger JSON feed URL
        start_index = ((page - 1) * 20) + 1
        feed_url = f"{self.host}/feeds/posts/default?alt=json&max-results=20&start-index={start_index}"
        
        try:
            resp = self.session.get(feed_url, timeout=15)
            data = resp.json()
            
            items = []
            entries = data.get('feed', {}).get('entry', [])
            
            for entry in entries:
                # Extract title
                title = entry.get('title', {}).get('$t', '')
                
                # Extract URL (first alternate link)
                url = ''
                for link in entry.get('link', []):
                    if link.get('rel') == 'alternate' and link.get('type') == 'text/html':
                        url = link.get('href', '')
                        break
                
                # Extract poster from content or media thumbnail
                poster = ''
                
                # Try media$thumbnail first
                if 'media$thumbnail' in entry:
                    poster = entry['media$thumbnail'].get('url', '')
                
                # Try to find image in content
                if not poster:
                    content = entry.get('content', {}).get('$t', '')
                    if not content:
                        content = entry.get('summary', {}).get('$t', '')
                    
                    # Parse HTML to find first image
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        img = soup.find('img')
                        if img:
                            poster = img.get('src') or img.get('data-src', '')
                
                # Detect if series from categories or URL
                is_series = False
                categories = entry.get('category', [])
                for cat in categories:
                    term = cat.get('term', '').lower()
                    if term in ['serie', 'series', 'anime']:
                        is_series = True
                        break
                
                if not is_series and url:
                    is_series = '/serie/' in url.lower()
                
                if title and url:
                    items.append(ContentItem(
                        title=title,
                        url=url,
                        poster=self.fix_url(poster),
                        is_series=is_series,
                    ).to_dict())
            
            return items
        except Exception as e:
            print(f"Error fetching JSON feed: {e}")
            return []
    
    def _parse_card(self, card_elem) -> Optional[Dict]:
        """Parse a .crd card element from HTML."""
        # CORRECT SELECTOR: h3.crd__title a
        title_elem = card_elem.select_one('h3.crd__title a, h3 a[href$=".html"]')
        if not title_elem:
            return None
        
        title = title_elem.text.strip()
        href = title_elem.get('href', '')
        
        if not href or not href.endswith('.html'):
            return None
        
        # Detect series from URL
        is_series = '/serie/' in href.lower()
        
        # CORRECT SELECTOR: .crd__image img
        poster = ""
        img_elem = card_elem.select_one('.crd__image img, picture img')
        if img_elem:
            poster = img_elem.get('src') or img_elem.get('data-src') or ''
            # Skip placeholder images
            if poster.startswith('data:') or '{image}' in poster:
                poster = ""
        
        return ContentItem(
            title=title,
            url=self.fix_url(href),
            poster=self.fix_url(poster),
            is_series=is_series,
        ).to_dict()
    
    def get_pagination_url(self, page: int, label: str = None) -> Optional[str]:
        """Get pagination URL for next page."""
        if label:
            url = f"{self.host}/search/label/{label}"
            feed_url = f"{self.host}/feeds/posts/default/-/{label}?alt=json&max-results=20&start-index={((page - 1) * 20) + 1}"
        else:
            feed_url = f"{self.host}/feeds/posts/default?alt=json&max-results=20&start-index={((page - 1) * 20) + 1}"
        
        return feed_url


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == '__main__':
    provider = FuegoCineProvider()
    
    # Test 1: Get movies from label page
    print("=== Movies from Label Page ===")
    movies = provider.get_main_page(filter_type="Movie")
    for item in movies[:5]:
        print(f"  {item['title']}: {item['url'][:50]}...")
    
    # Test 2: Get main page content via JSON feed
    print("\n=== Main Page via JSON Feed ===")
    main = provider.get_main_page()
    for item in main[:5]:
        print(f"  {item['title']}: {item['url'][:50]}...")
    
    # Test 3: Get series
    print("\n=== Series ===")
    series = provider.get_main_page(filter_type="Serie")
    for item in series[:5]:
        print(f"  {item['title']}: {item['url'][:50]}...")
```

---

## Summary of CSS Selectors

### Primary Selectors (Label Pages)

```css
/* Movie card container */
.crd

/* Title element */
h3.crd__title a

/* Poster image */
.crd__image img

/* Pagination link */
#blog-pager a
```

### Fallback for JSON Feed

Use the Blogger JSON feed when HTML parsing returns empty results:

```
https://www.fuegocine.com/feeds/posts/default?alt=json&max-results=20
```

---

## Key Findings

1. **The `.crd` selector is CORRECT** - it returns 20 items on label pages
2. **The `h3.crd__title a` selector is CORRECT** - returns title and URL
3. **The `.crd__image img` selector is CORRECT** - returns poster URL
4. **Main page requires JSON feed** - HTML has template placeholders
5. **Blogger JSON feed is reliable** - Returns full data for all pages

---

## Recommendations

1. **Dual-mode implementation:**
   - Use HTML parsing for label pages (faster, less data)
   - Use JSON feed for main page (reliable data)

2. **Handle both methods in `get_main_page()`:**
   - If `filter_type` is set, use HTML parsing
   - If `filter_type` is None, use JSON feed

3. **Pagination:**
   - HTML pages: Extract URL from `#blog-pager a`
   - JSON feed: Use `start-index` parameter

4. **Series detection:**
   - Check URL path for `/serie/`
   - Check categories in JSON feed for 'Serie' or 'Series'