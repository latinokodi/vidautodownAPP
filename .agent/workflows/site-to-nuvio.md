---
description: Transform any streaming website (movies/TV/anime) into a high-performance Nuvio provider. Handles WAF-stealth audits, decoy player de-obfuscation (Base64/Subpages), season-aware fuzzy title matching, and clean packaging.
---

# Site-to-Nuvio Workflow

You are in **SITE TO NUVIO MODE**. Your task is to analyze a target streaming website and convert it into a functional Nuvio provider module, packaged within a dedicated Nuvio providers repository, strictly adhering to the `nuvio-providers-best-practices` skill guidelines.

## Task to Execute
$ARGUMENTS

---

## 🧭 5-Phase Scraper & Repository Development Process

### ⚡ PHASE 1: STEALTH & FEASIBILITY AUDIT

Verify if standard HTTP `fetch` requests can ingest pages without WAF blocks:
*   **Step 1**: Run standard HTTP queries with realistic browser headers mimicking chrome user-agents.
*   **Step 2**: Inspect response status and body. Detect if there is a Cloudflare, DDOS-Guard, or Sucuri challenge page.
*   **Step 3**: If impenetrable challenge walls block standard fetch, skip integration immediately to avoid Puppeteer/Playwright resource overhead.

---

### 🔍 PHASE 2: CMS & DECOY DE-OBFUSCATION

Examine how the streaming CMS represents video player mirrors and iframes:
*   **Decoy Type A (Base64 Option Tags)**: Look for `<option>` dropdown values starting with `PG`. Retrieve the string, decode from base64, and extract the `src` attribute.
*   **Decoy Type B (Server Subpages)**: Check if server selections resolve to `/v/\d+/` subpages. Ingest all subpage endpoints, fetch them, extract player iframes, and apply strict decoy domain filters to block advertisement trackers and mock pages.
*   **Decoy Type C (Crypto/Blogger Redirects)**: Trace nested redirect routes (e.g. `t.co` shortlinks or Blogspot containers) to locate final media CDNs.

---

### 🧬 PHASE 3: FUZZY SEARCH & SEASON MATCHING

Write fuzzy search algorithms to map TMDB metadata to CMS post listings:
*   **Digit De-duplication**: Feed all title numbers into a `Set` to prevent duplicate digits (such as `"22"` instead of `"2"`) caused by hover/mobile desktop duplicate HTML nodes.
*   **Strict Season Check**: Compare extracted unique digit strings. If season digits mismatch, apply a heavy penalty (`-80` points). If they match exactly, apply a boost (`+30` points).
*   **Low Length Penalty**: Apply a minimal character length penalty (`-0.05` per char difference) to prefer shorter, more precise titles while accommodating descriptive suffixes (`Sub`, `Ongoing`, `4K`).

---

### 🛠️ PHASE 4: MODULE IMPLEMENTATION

Write the provider module in standard Nuvio CommonJS syntax:
*   **No Headless dependencies**: The script must use only global `fetch` API.
*   **Interface**: Export a clean `getStreams(id, type, season, episode)` async function returning structured streams arrays `{ name, title, url, quality, headers }`.
*   **Header Forwarding**: Support piping headers to player streams (`url|Referer=...&User-Agent=...`) to prevent CDNs from returning `403 Forbidden` bad status blocks.

---

### 📦 PHASE 5: REPOSITORY PACKAGING & DEPLOYMENT

Compile the provider scraper inside a dedicated workspace:
*   **manifest.json**: Register provider IDs, languages, logos, and target scraper JS file paths.
*   **package.json**: Set up project specifications and metadata.
*   **README.md**: Keep it clean and simple. Include only a short description and a copyable manifest URL (using raw GitHub templates). Do **not** disclose technical details or source sites in the README.

---

## 📂 Verification Checklist

- [ ] Search fuzzy matching filters season number mismatches strictly (Set-based de-duplication).
- [ ] Base64 option decoders or subpage crawlers successfully resolve player links.
- [ ] Ad network filters prune and discard crypto banners, blogs, and short decoy links.
- [ ] Scraper exports a CommonJS `getStreams()` method.
- [ ] Streams array contains Referer and User-Agent headers if required by hotlink-protected CDNs.
- [ ] Providers are declared in `manifest.json`.
- [ ] Repository `README.md` contains only the copyable raw manifest URL template.
