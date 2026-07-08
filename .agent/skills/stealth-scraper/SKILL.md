---
name: stealth-scraper
description: Advanced web scraping with anti-bot evasion using CloudScraper, Patchright, and Scrapling. Bypasses Cloudflare, PerimeterX, and other bot detection. Use for streaming sites with heavy protection.
risk: high
source: community
date_added: "2026-05-11"
---

# Stealth Scraper - Anti-Bot Evasion Toolkit

> Comprehensive toolkit for scraping protected streaming sites using multiple stealth techniques.

## 🎯 Tool Selection Matrix

| Tool | Best For | Strengths | Weaknesses |
|------|----------|-----------|------------|
| **CloudScraper** | Cloudflare bypass | Simple, no browser | Limited to CF |
| **Patchright** | Heavy JS sites | Full browser, fast | Requires setup |
| **Scrapling** | Adaptive scraping | Auto-adapts, resilient | Newer tool |
| **Fingerprint Suite** | Fingerprint evasion | Realistic profiles | Complexity |
| **Anansi** | High-perf automation | Fast, stealthy | Less common |
| **Camofox** | Specialized stealth | Built-in evasion | Browser-based |
| **CloakBrowser** | Pro-grade stealth | Advanced spoofing | Commercial focus |
| **Scrapy** | Large-scale crawls | Async, pipelines | Not stealth-focused |

---

## 🔧 Tool 1: CloudScraper

**Repository:** https://github.com/jordanpotti/CloudScraper

A Python library to bypass Cloudflare's anti-bot protection.

### Installation
```bash
pip install cloudscraper
```

### Basic Usage
```python
import cloudscraper

# Create scraper instance
scraper = cloudscraper.create_scraper()

# Simple GET request
response = scraper.get('https://protected-site.com')

# With custom headers
response = scraper.get(
    'https://protected-site.com/video',
    headers={
        'Referer': 'https://protected-site.com/',
        'User-Agent': 'Mozilla/5.0 ...'
    }
)

# POST request
response = scraper.post(
    'https://protected-site.com/api/load',
    data={'slug': 'movie-title', 'index': 0}
)
```

### CloudScraper Features
- Bypasses Cloudflare's JavaScript challenge
- Bypasses Cloudflare's CAPTCHA (manual intervention)
- Works with `requests.Session`
- Can be used as drop-in replacement for `requests`

### CloudScraper for VidHide/StreamWish
```python
import cloudscraper
import re

def resolve_with_cloudscraper(embed_url):
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome120',
            'platform': 'windows',
            'desktop': True
        }
    )

    headers = {
        'Referer': 'https://parent-site.com/',
    }

    resp = scraper.get(embed_url, headers=headers, timeout=15)

    # Extract m3u8
    m3u8_match = re.search(r'(https?://[^"\']+\.m3u8[^"\']*)', resp.text, re.I)
    if m3u8_match:
        return m3u8_match.group(1)

    return None
```

---

## 🔧 Tool 2: Patchright

**Repository:** https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python

A patched version of Playwright with anti-detection patches.

### Installation
```bash
# Install patchright
pip install patchright

# Install patched browsers
patchright install chromium
```

### Basic Usage
```python
from patchright.sync_api import sync_playwright

def scrape_with_patchright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        # Navigate with referer
        page.goto(url, referer='https://parent-site.com/', timeout=60000)

        # Wait for content
        page.wait_for_timeout(5000)

        html = page.content()
        browser.close()

        return html
```

### Patchright Stealth Features
- Removes `navigator.webdriver` flag
- Fixes Chrome DevTools detection
- Hides automation markers
- Works with complex JS-heavy sites

### Patchright for Streaming Sites
```python
from patchright.sync_api import sync_playwright
import re

def resolve_embed_with_patchright(embed_url, parent_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Use realistic context
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720},
            locale='es-MX',
            timezone_id='America/Mexico_City'
        )
        page = context.new_page()

        # Navigate with referer
        page.goto(embed_url, referer=parent_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(7000)  # Wait for JS to execute

        content = page.content()

        # Extract packer payload
        if 'eval(function(p,a,c,k,e,' in content:
            # Use packer unpacker
            from resources.lib.modules.packer import unpack_v2
            unpacked = unpack_v2(content)
            m3u8_match = re.search(r'(https?://[^"\']+\.m3u8[^"\']*)', unpacked, re.I)
            if m3u8_match:
                return m3u8_match.group(1)

        # Direct m3u8
        m3u8_match = re.search(r'(https?://[^"\']+\.m3u8[^"\']*)', content, re.I)
        if m3u8_match:
            return m3u8_match.group(1)

        browser.close()
    return None
```

---

## 🔧 Tool 3: Scrapling

**Repository:** https://github.com/D4Vinci/Scrapling

An adaptive scraping library that automatically adapts to website changes.

### Installation
```bash
pip install scrapling
### Basic Usage
```python
from scrapling import FetchAdaptor

# Fetch page with auto-adaptation
page = FetchAdaptor(url='https://protected-site.com')

# Select elements
title = page.css_first('h1.title').text()
items = page.css('.movie-item')

# Get attributes
poster = page.css_first('img.poster').attr('src')
```

### Scrapling Features
- Auto-adapts to website structure changes
- Handles dynamic content
- Built-in resilience for failed selectors
- Works with Cloudflare-protected sites

---

## 🔧 Tool 4: Fingerprint Suite

**Repository:** https://github.com/apify/fingerprint-suite

Comprehensive browser fingerprint generation and management for stealth automation.

### Features
- Generates realistic browser fingerprints (User-Agent, Canvas, WebGL, etc.)
- Supports Playwright and Puppeteer integration
- Built-in header generator for realistic network traffic
- Prevents detection by advanced bot managers (Akamai, DataDome)

---

## 🔧 Tool 5: Anansi

**Repository:** https://github.com/mdowis/anansi

High-performance, stealthy browser automation designed for speed and reliability.

### Features
- Optimized for scraping large volumes of data
- Built-in evasion techniques for common bot detectors
- Lightweight alternative to full browser suites when performance matters

---

## 🔧 Tool 6: Camofox

**Repository:** https://github.com/jo-inc/camofox-browser

A browser designed from the ground up for stealth and anti-bot evasion.

### Features
- Hardened browser engine to resist fingerprinting
- Automatic header and device profile rotation
- Seamless integration with existing scraping workflows

---

## 🔧 Tool 7: CloakBrowser

**Repository:** https://github.com/CloakHQ/CloakBrowser

Professional-grade stealth browser with advanced fingerprinting and spoofing capabilities.

### Features
- Advanced canvas and WebGL noise injection
- Realistic hardware profile simulation (GPU, Audio, Battery)
- High success rate against top-tier bot protection systems

---

## 🔧 Tool 8: Scrapy

**Repository:** https://github.com/scrapy/scrapy

A fast high-level web crawling and scraping framework.

### Installation
```bash
pip install scrapy
```

### Scrapy Spider for Streaming Sites
```python
import scrapy
from scrapy.crawler import CrawlerProcess
from typing import List, Dict

class StreamingSiteSpider(scrapy.Spider):
    name = 'streaming_site'
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 2,
        'COOKIES_ENABLED': True,
    }

    def __init__(self, base_url=None, max_pages=10):
        self.base_url = base_url
        self.max_pages = max_pages
        self.results = []

    def start_requests(self):
        for page in range(1, self.max_pages + 1):
            url = f"{self.base_url}/page/{page}/"
            yield scrapy.Request(url, callback=self.parse_main_page)

    def parse_main_page(self, response):
        for article in response.css('article.post'):
            title = article.css('h2.entry-title::text').get()
            href = article.css('a::attr(href)').get()
            poster = article.css('img::attr(src)').get()

            self.results.append({
                'title': title,
                'url': href,
                'poster': poster,
            })

            # Follow to detail page
            if href:
                yield scrapy.Request(href, callback=self.parse_detail)

    def parse_detail(self, response):
        # Extract embed URLs
        embeds = response.css('iframe::attr(src)').getall()

        self.logger.info(f'Found {len(embeds)} embeds for {response.url}')

def run_scrapy_spider(base_url: str, max_pages: int = 10) -> List[Dict]:
    """Run Scrapy spider and return results."""
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'LOG_LEVEL': 'INFO',
    })

    spider = StreamingSiteSpider(base_url=base_url, max_pages=max_pages)
    process.crawl(spider)
    process.start()

    return spider.results
```

---

## 📊 Tool Selection Decision Tree

```
Is site Cloudflare-protected?
├─ Yes → CloudScraper (first attempt)
│       │
│       └─► Failed? → Patchright (browser-based)
│               │
│               └─► Failed? → Scrapling (adaptive)
│
├─ PerimeterX / Advanced Bot Detection?
│       ├─ Yes → Fingerprint Suite + CloakBrowser
│       └─ No → Standard tools
│
├─ JS-heavy content?
│       ├─ Yes → Patchright, Anansi, or Camofox
│       └─ No → Scrapy or requests
│
├─ Need high-performance automation?
│       ├─ Yes → Anansi
│       └─ No → Patchright
│
├─ Multiple pages to scrape?
│       ├─ Yes (>50 pages) → Scrapy
│       └─ No → CloudScraper or Patchright
│
└─ Dynamic selectors likely to change?
        ├─ Yes → Scrapling (adaptive)
        └─ No → Standard BeautifulSoup
```

---

## 🧪 Testing Workflow

### Phase 1: Detection Test
```python
# Test if site needs stealth
import requests

def detect_protection(url):
    resp = requests.get(url, timeout=10)

    indicators = {
        'cloudflare': any(x in resp.text for x in ['__CF$cv$params', 'cf-browser-verification', 'Just a moment...']),
        'perimeterx': '_px' in resp.text or 'PX-' in resp.headers,
        'ddos_guard': 'DDoS protection' in resp.text,
        'js_challenge': 'challenge-platform' in resp.text,
    }

    return indicators
```

### Phase 2: Tool Testing
```bash
# Test each tool in venv
python -c "
import cloudscraper
scraper = cloudscraper.create_scraper()
resp = scraper.get('https://target-site.com')
print(f'CloudScraper: {resp.status_code}')
"

python -c "
from patchright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    print('Patchright: Browser launched successfully')
    browser.close()
"

python -c "
from scrapling import FetchAdaptor
page = FetchAdaptor(url='https://target-site.com', stealth=True)
print(f'Scrapling: {len(page.css(\"a\"))} links found')
"
```

---

## 🛡️ Best Practices

### 1. Rate Limiting
```python
import time
from functools import wraps

def rate_limit(delay=2.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(2.0)
def fetch_page(url):
    return scraper.get(url)
```

### 2. Session Reuse
```python
# Reuse session for multiple requests
session = cloudscraper.create_scraper()

# First request (sets cookies)
session.get(base_url)

# Subsequent requests use saved cookies
session.get(embed_url)
```

### 3. Error Handling
```python
def safe_fetch(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            resp = scraper.get(url, timeout=15)
            if resp.status_code == 200:
                return resp
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2 * (attempt + 1))
    return None
```

---

## 📁 Environment Setup

### requirements.txt
```txt
cloudscraper>=1.2.71
patchright>=0.1.0
scrapling>=0.2.0
scrapy>=2.11.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
```

### venv Setup
```bash
# Create venv
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Patchright browsers
patchright install chromium
```

---

## 🔗 Related Skills

| Skill | Purpose |
|-------|---------|
| `web-scraper` | General scraping patterns |
| `playwright-skill` | Standard Playwright usage |
| `protocol-reverse-engineering` | API discovery |
| `site-to-kodi-addon` | Kodi addon integration |

---

## ✅ Verification Checklist

- [ ] Tool selected based on protection type
- [ ] Rate limiting implemented
- [ ] Session reuse for cookies
- [ ] Error handling with retries
- [ ] Timeout limits set (15-30s)
- [ ] User-Agent header realistic
- [ ] Referer header set for embeds
- [ ] venv environment active
- [ ] Patchright browsers installed