---
description: Set up Python virtual environment with all required dependencies for Kodi addon development. Includes CloudScraper, Patchright, Scrapling, and testing tools.
---

# Virtual Environment Setup Workflow

You are in **VENV SETUP MODE**. Your task: configure a Python virtual environment with all dependencies for Kodi addon development and testing.

## Task to Execute
$ARGUMENTS

---

## 🔴 CRITICAL: 4-Phase Setup Process

### PHASE 1: Environment Creation

| Step | Action | Command |
|------|--------|---------|
| 1 | Create venv | `python -m venv .venv` |
| 2 | Activate venv | `.venv\Scripts\activate` (Windows) |
| 3 | Verify Python | `python --version` |
| 4 | Upgrade pip | `pip install --upgrade pip` |

### PHASE 2: Core Dependencies

| Package | Purpose | Command |
|---------|---------|---------|
| requests | HTTP requests | `pip install requests>=2.31.0` |
| beautifulsoup4 | HTML parsing | `pip install beautifulsoup4>=4.12.0` |
| lxml | Fast parsing | `pip install lxml>=5.0.0` |
| cloudscraper | Cloudflare bypass | `pip install cloudscraper>=1.2.71` |

### PHASE 3: Browser Automation Tools

| Package | Purpose | Command |
|---------|---------|---------|
| patchright | Stealth browser | `pip install patchright>=0.1.0` |
| scrapling | Adaptive scraping | `pip install scrapling>=0.2.0` |
| playwright | Standard browser | `pip install playwright>=1.40.0` |

**Post-Install:**
```bash
# Install Patchright browsers
patchright install chromium

# Install Playwright browsers (optional)
playwright install chromium
```

### PHASE 4: Testing & Utilities

| Package | Purpose | Command |
|---------|---------|---------|
| pytest | Test runner | `pip install pytest>=8.0.0` |
| scrapy | Large-scale crawling | `pip install scrapy>=2.11.0` |

---

## 📁 Required Files

### requirements.txt
```txt
# Core HTTP & Parsing
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0

# Anti-Bot & Stealth
cloudscraper>=1.2.71
patchright>=0.1.0
scrapling>=0.2.0

# Browser Automation (Optional)
playwright>=1.40.0

# Large-Scale Crawling
scrapy>=2.11.0

# Testing
pytest>=8.0.0

# Code Quality (Optional)
ruff>=0.1.0
```

### pyproject.toml (Alternative)
```toml
[project]
name = "kodi-addon-dev"
version = "0.1.0"
description = "Kodi addon development environment"
requires-python = ">=3.11"

dependencies = [
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
    "cloudscraper>=1.2.71",
    "patchright>=0.1.0",
    "scrapling>=0.2.0",
    "scrapy>=2.11.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.1.0",
]
```

---

## 🔧 Setup Commands (Windows)

```powershell
# Phase 1: Create venv
python -m venv .venv

# Activate
.venv\Scripts\activate

# Phase 2: Install core
pip install requests beautifulsoup4 lxml

# Phase 3: Install stealth tools
pip install cloudscraper patchright scrapling

# Install Patchright browsers
patchright install chromium

# Phase 4: Install testing
pip install pytest scrapy

# Alternative: Install all from requirements.txt
pip install -r requirements.txt
```

---

## 🔧 Setup Commands (Linux/Mac)

```bash
# Phase 1: Create venv
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Phase 2-4: Install all
pip install -r requirements.txt

# Install browsers
patchright install chromium
```

---

## 🛠️ Verification Script

```python
"""
verify_env.py - Verify venv setup is complete
"""

import sys

def verify_environment():
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")
    print(f"In venv: { hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)}")

    packages = [
        'requests',
        'bs4',
        'lxml',
        'cloudscraper',
        'patchright',
        'scrapling',
        'pytest',
        'scrapy',
    ]

    print("\n=== Package Status ===")
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} - MISSING")

    # Test Patchright browser
    print("\n=== Browser Status ===")
    try:
        from patchright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            print("  ✓ Patchright Chromium")
            browser.close()
    except Exception as e:
        print(f"  ✗ Patchright browser: {e}")

    # Test CloudScraper
    print("\n=== CloudScraper Test ===")
    try:
        import cloudscraper
        scraper = cloudscraper.create_scraper()
        resp = scraper.get('https://www.google.com', timeout=5)
        print(f"  ✓ CloudScraper working (status: {resp.status_code})")
    except Exception as e:
        print(f"  ✗ CloudScraper: {e}")

    print("\n=== Setup Complete ===")

if __name__ == '__main__':
    verify_environment()
```

---

## 📊 Environment Checklist

| Item | Command | Expected |
|------|---------|----------|
| Python 3.11+ | `python --version` | `Python 3.11.x` |
| In venv | `sys.prefix != sys.base_prefix` | True |
| requests | `import requests` | No error |
| cloudscraper | `import cloudscraper` | No error |
| patchright | `import patchright.sync_api` | No error |
| scrapling | `import scrapling` | No error |
| Chromium | `patchright install` | Already installed |

---

## 🔴 EXIT GATE

Before proceeding to addon development:

1. ✅ **Venv Active**: `sys.prefix != sys.base_prefix`
2. ✅ **Core Packages**: requests, bs4, lxml installed
3. ✅ **Stealth Tools**: cloudscraper, patchright, scrapling installed
4. ✅ **Browser Ready**: Patchright Chromium installed
5. ✅ **Testing Ready**: pytest installed
6. ✅ **Verify Passed**: `python verify_env.py` shows all ✓

---

## 🎯 Next Steps After Setup

1. Create addon structure using `/site-to-kodi` workflow
2. Write resolver tests using `resolver-testing` skill
3. Test provider using venv environment
4. Package addon using zipper script

---

## Output Format

```markdown
## 🐍 Venv Setup Report

### 1. Environment
- **Python**: {version}
- **Venv Path**: {path}
- **Active**: ✅ Yes

### 2. Packages Installed
| Package | Version | Status |
|---------|---------|--------|
| requests | {version} | ✅ |
| cloudscraper | {version} | ✅ |
| patchright | {version} | ✅ |
| scrapling | {version} | ✅ |
| pytest | {version} | ✅ |

### 3. Browser Status
- **Patchright Chromium**: ✅ Installed

### 4. Verification
- **CloudScraper**: ✅ Working
- **Patchright**: ✅ Browser launched

### 5. Ready for Development
Run `/site-to-kodi {site_url}` to create addon.
```