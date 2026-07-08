---
name: scrapy-streaming
description: Scrapy framework adapted for streaming site crawling. Async crawling, pipelines for Kodi addon data extraction, and middleware for anti-detection. Use for large-scale site catalog extraction.
risk: medium
source: community
date_added: "2026-05-11"
---

# Scrapy for Streaming Sites

> High-performance async crawling framework adapted for streaming site catalog extraction.

## 🎯 When to Use Scrapy

| Scenario | Recommended |
|----------|-------------|
| Extract entire catalog (>100 pages) | ✅ Yes |
| Single page testing | ❌ Use requests/CloudScraper |
| Need async/parallel fetching | ✅ Yes |
| Sequential navigation needed | ❌ Use browser tools |
| Build site database | ✅ Yes |
| Test single resolver | ❌ Use simple tests |

---

## 📁 Project Structure

```plaintext
scrapy_streaming/
├── scrapy.cfg
├── streaming_spider/
│   ├── __init__.py
│   ├── items.py          # Kodi item definitions
│   ├── middlewares.py    # Anti-detection middleware
│   ├── pipelines.py      # Kodi data pipeline
│   ├── settings.py       # Spider settings
│   └ spiders/
│       ├── __init__.py
│       ├── blogger.py    # Blogger JSON spider
│       ├── dooplay.py    # WordPress/DooPlay spider
│       └── php_site.py   # Custom PHP spider
```

---

## 🔧 Items Definition (items.py)

```python
import scrapy

class ContentItem(scrapy.Item):
    """Kodi content item."""
    title = scrapy.Field()
    url = scrapy.Field()
    poster = scrapy.Field()
    is_series = scrapy.Field()
    plot = scrapy.Field()
    year = scrapy.Field()
    provider = scrapy.Field()

class EpisodeItem(scrapy.Item):
    """Series episode item."""
    title = scrapy.Field()
    url = scrapy.Field()
    season = scrapy.Field()
    episode = scrapy.Field()
    poster = scrapy.Field()
    series_title = scrapy.Field()

class SourceItem(scrapy.Item):
    """Video source item."""
    name = scrapy.Field()
    embed_url = scrapy.Field()
    quality = scrapy.Field()
    language = scrapy.Field()
    content_url = scrapy.Field()
```

---

## 🔧 Spider: DooPlay (dooplay.py)

```python
import scrapy
from streaming_spider.items import ContentItem, EpisodeItem, SourceItem
import re

class DooPlaySpider(scrapy.Spider):
    name = 'dooplay'
    allowed_domains = []

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'COOKIES_ENABLED': True,
        'ROBOTSTXT_OBLIGE': False,
    }

    def __init__(self, base_url=None, content_type='movies', max_pages=10):
        self.base_url = base_url
        self.content_type = content_type
        self.max_pages = max_pages

    def start_requests(self):
        """Generate initial requests based on content type."""
        if self.content_type == 'movies':
            path = '/pelicula/'
        elif self.content_type == 'series':
            path = '/serie/'
        else:
            path = '/'

        for page in range(1, self.max_pages + 1):
            url = f"{self.base_url}{path}page/{page}/"
            yield scrapy.Request(url, callback=self.parse_list)

    def parse_list(self, response):
        """Parse content list page."""
        for article in response.css('article.post'):
            item = ContentItem()

            # Title extraction with cleaning
            title_elem = article.css('h2.entry-title, .title-movie')
            raw_title = title_elem.css('::text').get() or ''
            item['title'] = self._clean_title(raw_title)

            # URL extraction
            link = article.css('a[href*="/pelicula/"], a[href*="/serie/"]')
            item['url'] = link.css('::attr(href)').get()

            # Poster
            img = article.css('img')
            item['poster'] = (
                img.css('::attr(src)').get() or
                img.css('::attr(data-src)').get() or ''
            )

            # Is series
            item['is_series'] = '/serie/' in item.get('url', '')
            item['provider'] = self.name

            if item['url']:
                yield scrapy.Request(
                    item['url'],
                    callback=self.parse_detail,
                    meta={'item': item}
                )

        # Follow pagination
        next_page = response.css('a.next::attr(href)').get()
        if next_page and self._get_page_number(next_page) <= self.max_pages:
            yield scrapy.Request(next_page, callback=self.parse_list)

    def parse_detail(self, response):
        """Parse content detail page."""
        item = response.meta['item']

        # Extract plot
        item['plot'] = response.css('.wp-content p::text').get() or ''

        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', item.get('title', ''))
        item['year'] = year_match.group(0) if year_match else ''

        yield item

        # If series, extract episodes
        if item.get('is_series'):
            # Season tabs
            for season_tab in response.css('.se-c'):
                season_num = season_tab.css('.se-q::text').re_first(r'\d+')

                for ep_link in season_tab.css('.episodiotitle a'):
                    ep_item = EpisodeItem()
                    ep_item['season'] = int(season_num) if season_num else 1
                    ep_item['episode'] = ep_link.css('::text').re_first(r'\d+')
                    ep_item['url'] = ep_link.css('::attr(href)').get()
                    ep_item['series_title'] = item.get('title')

                    if ep_item['url']:
                        yield scrapy.Request(
                            ep_item['url'],
                            callback=self.parse_episode,
                            meta={'item': ep_item}
                        )

    def parse_episode(self, response):
        """Parse episode page for embed sources."""
        item = response.meta['item']

        # Extract embed URLs
        for iframe in response.css('#embed-cont iframe, .player iframe'):
            source = SourceItem()
            source['embed_url'] = iframe.css('::attr(src)').get()
            source['content_url'] = item.get('url')
            source['name'] = self._get_host_name(source['embed_url'])

            yield source

    def _clean_title(self, title: str) -> str:
        """Clean DooPlay title suffixes."""
        title = re.sub(r'\s*\|\s*Ver Online\s*$', '', title, flags=re.I)
        title = re.sub(r'\s*\|\s*Descargar\s*$', '', title, flags=re.I)
        title = re.sub(r'\s*Online\s*$', '', title, flags=re.I)
        title = re.sub(r'\s*Gratis\s*$', '', title, flags=re.I)
        return ' '.join(title.split()).strip()

    def _get_host_name(self, url: str) -> str:
        """Extract host name from embed URL."""
        hosts = {
            'streamwish': 'StreamWish',
            'voe': 'VOE',
            'filemoon': 'Filemoon',
            'vidhide': 'VidHide',
            'dood': 'DoodStream',
            'mixdrop': 'MixDrop',
        }
        for key, name in hosts.items():
            if key in url.lower():
                return name
        return 'Unknown'

    def _get_page_number(self, url: str) -> int:
        """Extract page number from URL."""
        match = re.search(r'/page/(\d+)/', url)
        return int(match.group(1)) if match else 1
```

---

## 🔧 Spider: Blogger JSON (blogger.py)

```python
import scrapy
from streaming_spider.items import ContentItem, SourceItem
import json

class BloggerSpider(scrapy.Spider):
    name = 'blogger'

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 3,
    }

    def __init__(self, base_url=None, label=None, max_results=500):
        self.base_url = base_url
        self.label = label
        self.max_results = max_results

    def start_requests(self):
        """Fetch JSON feed."""
        if self.label:
            url = f"{self.base_url}/feeds/posts/default/-/{self.label}?alt=json&max-results={self.max_results}"
        else:
            url = f"{self.base_url}/feeds/posts/default?alt=json&max-results={self.max_results}"

        yield scrapy.Request(url, callback=self.parse_json_feed)

    def parse_json_feed(self, response):
        """Parse Blogger JSON feed."""
        data = json.loads(response.text)

        for entry in data.get('feed', {}).get('entry', []):
            item = ContentItem()

            # Title
            item['title'] = entry.get('title', {}).get('$t', '')

            # URL
            links = entry.get('link', [])
            item['url'] = next(
                (l.get('href') for l in links if l.get('rel') == 'alternate'),
                ''
            )

            # Poster
            thumbnail = entry.get('media$thumbnail', {})
            item['poster'] = thumbnail.get('url', '')

            # Is series (check URL pattern)
            item['is_series'] = '/serie/' in item.get('url', '').lower()
            item['provider'] = self.name

            yield item

        # Pagination
        next_link = next(
            (l.get('href') for l in data.get('feed', {}).get('link', [])
             if l.get('rel') == 'next'),
            None
        )
        if next_link:
            yield scrapy.Request(next_link, callback=self.parse_json_feed)
```

---

## 🔧 Middlewares (middlewares.py)

```python
import random
import time

class AntiDetectionMiddleware:
    """Middleware for anti-detection measures."""

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    def process_request(self, request, spider):
        # Random User-Agent
        request.headers['User-Agent'] = random.choice(self.USER_AGENTS)

        # Add common headers
        request.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        request.headers['Accept-Language'] = 'es-MX,es;q=0.9,en;q=0.8'

        # Random delay
        if spider.custom_settings.get('DOWNLOAD_DELAY'):
            time.sleep(random.uniform(0.5, 2.0))


class CloudflareMiddleware:
    """Middleware to handle Cloudflare challenges."""

    def process_response(self, request, response, spider):
        # Check for Cloudflare challenge
        if any(x in response.text for x in ['__CF$cv$params', 'cf-browser-verification', 'Just a moment...']):
            spider.logger.warning(f'Cloudflare detected on {request.url}')
            # Return retry request
            return request.replace(dont_filter=True)

        return response
```

---

## 🔧 Pipelines (pipelines.py)

```python
import json
from pathlib import Path

class KodiDataPipeline:
    """Pipeline to save data for Kodi addon."""

    def __init__(self, output_dir='output'):
        self.output_dir = Path(output_dir)
        self.items = []

    def open_spider(self, spider):
        self.output_dir.mkdir(exist_ok=True)

    def process_item(self, item, spider):
        # De-duplicate
        if item not in self.items:
            self.items.append(dict(item))
        return item

    def close_spider(self, spider):
        # Save to JSON
        output_file = self.output_dir / f'{spider.name}_catalog.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)

        spider.logger.info(f'Saved {len(self.items)} items to {output_file}')


class DeDuplicationPipeline:
    """Pipeline to de-duplicate items."""

    def __init__(self):
        self.seen_urls = set()
        self.seen_titles = set()

    def process_item(self, item, spider):
        url = item.get('url', '')
        title = item.get('title', '').lower().replace(' ', '')

        if url in self.seen_urls or title in self.seen_titles:
            spider.logger.debug(f'Dropped duplicate: {title}')
            return None  # Drop item

        self.seen_urls.add(url)
        self.seen_titles.add(title)
        return item
```

---

## 🔧 Settings (settings.py)

```python
BOT_NAME = 'streaming_spider'
SPIDER_MODULES = ['streaming_spider.spiders']
NEWSPIDER_MODULE = 'streaming_spider.spiders'

# Anti-detection
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
ROBOTSTXT_OBLIGE = False
COOKIES_ENABLED = True

# Rate limiting
DOWNLOAD_DELAY = 2
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Middlewares
DOWNLOADER_MIDDLEWARES = {
    'streaming_spider.middlewares.AntiDetectionMiddleware': 543,
    'streaming_spider.middlewares.CloudflareMiddleware': 544,
}

# Pipelines
ITEM_PIPELINES = {
    'streaming_spider.pipelines.DeDuplicationPipeline': 100,
    'streaming_spider.pipelines.KodiDataPipeline': 200,
}

# Logging
LOG_LEVEL = 'INFO'
```

---

## 🚀 Running Spiders

### Command Line
```bash
# Run DooPlay spider
scrapy crawl dooplay -a base_url=https://site.com -a max_pages=20

# Run Blogger spider
scrapy crawl blogger -a base_url=https://site.blogspot.com

# Output to JSON
scrapy crawl dooplay -o output.json
```

### Python Script
```python
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def run_spider(spider_name, **kwargs):
    process = CrawlerProcess(get_project_settings())
    process.crawl(spider_name, **kwargs)
    process.start()

# Usage
run_spider('dooplay', base_url='https://site.com', max_pages=10)
```

---

## 📊 Comparison: Scrapy vs Other Tools

| Feature | Scrapy | CloudScraper | Patchright | Scrapling | Stealth Browsers* |
|---------|---------|--------------|------------|-----------|------------------|
| Async | ✅ | ❌ | ✅ (browser) | ❌ | ✅/❌ (varies) |
| Cloudflare | ❌ Manual | ✅ Auto | ✅ Auto | ✅ Auto | ✅ Auto |
| JS Support | ❌ | ❌ | ✅ Full | ✅ Some | ✅ Full |
| Scale | ✅ 1000+ | ❌ | ❌ Heavy | ❌ | ❌ Heavy |
| Fingerprinting| ❌ | ❌ | ✅ Patched | ❌ | ✅ Advanced |

*\*Stealth Browsers include Camofox, CloakBrowser, and Anansi.*

---

## ✅ Verification Checklist

- [ ] Spider class defined with `name` attribute
- [ ] `start_requests()` generates initial URLs
- [ ] `parse_*` methods extract items
- [ ] Items use scrapy.Field definitions
- [ ] De-duplication pipeline enabled
- [ ] Rate limiting settings configured
- [ ] User-Agent rotation middleware active
- [ ] Output pipeline saves to JSON
- [ ] Custom settings override defaults
- [ ] `max_pages` parameter limits scope