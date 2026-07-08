---
name: nuvio-providers-best-practices
description: "Master handbook for auditing streaming sites, de-obfuscating CMS decoys, fuzzy season matching, decrypting embeds, and packaging Nuvio providers."
---

# Nuvio Providers Master Handbook

This handbook outlines the comprehensive development pipeline, architectural patterns, WAF-bypass techniques, and de-obfuscation strategies for building, porting, and verifying premium JS-based streaming providers inside the Nuvio/Luvio ecosystem.

---

## 🧭 1. Site Feasibility & WAF Stealth Audit

Before writing a single line of scraper code, you must evaluate the target site's web-application firewall (WAF) and bot protection.

### Step 1: Clean HTTP Header Mimicry Check
Many websites appear to require heavy headless browsers or external bypass APIs, but actually accept standard HTTP `fetch` calls when presented with high-fidelity browser headers.
*   **Action**: Test standard `fetch` with realistic headers (including Accept-Language, Connection, and Upgrade-Insecure-Requests).
*   **Evaluation Metrics**:

| Status Code | Body Condition | Ingestion Verdict | Strategy |
| :--- | :--- | :--- | :--- |
| `200 OK` | Clean HTML | **Highly Feasible** | Fetch directly with clean headers. |
| `200 OK` | Decoy Blog Pages | **Feasible** | Inspect scripts and iframes for hidden redirects. |
| `403 / 503` | Cloudflare/DDOS-Guard | **Blocked** | Check for API endpoints, try TLS/HTTP2 fingerprints. |
| `403 / 503` | Complete Challenge Wall | **Impenetrable** | Skip provider to avoid costly headless/solver overhead. |

```javascript
const USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
const HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
};
```

---

## 🔍 2. Decoy Analysis & Player De-obfuscation

Streaming sites frequently hide their players from automated copyright crawlers and ad networks. You must identify and peel back these decoy layers structurally.

### Decoy Archetype A: Base64 Dropdown Encoded Options
Some themes pack the entire `<iframe>` player HTML into base64 encoded strings within standard `<option>` selector tags to prevent automated link scrapers from seeing them.
*   **Detection**: Look for option tags whose value starts with `PG` (the Base64 signature of `<iframe`).
*   **Resolution**: Decode from Base64 and run regex to extract the `src` attribute.

```javascript
const optionRegex = /<option\s+[^>]*value=["'](PG[a-zA-Z0-9+/=]+)["'][^>]*>([\s\S]*?)<\/option>/gi;
let match;
while ((match = optionRegex.exec(pageHtml)) !== null) {
    const decoded = Buffer.from(match[1], 'base64').toString('utf8');
    const iframeMatch = decoded.match(/src=["']([^"']+)["']/i);
    if (iframeMatch) {
        const embedUrl = iframeMatch[1].startsWith("//") ? "https:" + iframeMatch[1] : iframeMatch[1];
        // ... push stream
    }
}
```

### Decoy Archetype B: Server Subpages & Local Fake Articles
Some platforms load players inside localized sub-pages (e.g. `/v/1/`, `/v/2/`) and load invisible decoy ads/crypto blogs to spoof spiders.
*   **Detection**: Scan the play page for option values matching `/v/\d+/`.
*   **Resolution**: 구조적으로 fetch all server sub-pages, extract all iframes, and strictly filter out known decoy domains.

```javascript
// Strict decoy and ad network filters
const lowerUrl = embedUrl.toLowerCase();
if (lowerUrl.includes("youtube.com") || 
    lowerUrl.includes("doubleclick") || 
    lowerUrl.includes("ads") || 
    lowerUrl.includes("saroadexchange") || 
    lowerUrl.includes("cashzilla") ||
    lowerUrl.includes("t.co") ||
    lowerUrl.includes("blogspot.com") ||
    lowerUrl.includes("luciferdonghua.in") || // Filters local fake pages
    lowerUrl.includes("cryptojobss.com") ||
    lowerUrl.includes("nextbitcoins.com") ||
    lowerUrl.includes("coinprediction.ai")) {
    continue; // Prune decoy
}
```

---

## 🧬 3. Season-Aware Fuzzy Title Matching

Fuzzy matching is required to match TMDB search items with provider index databases without blindly picking the first search result (which leads to mismatch bugs, e.g., *Ladies First* mapping to *Lady and the Tramp 2*).

### Step 1: Multi-Locale TMDB Data Harvesting
Always harvest Spanish and English titles to maximize hits on cross-language streaming catalogs:
```javascript
const TMDB_API_KEY = "439c478a771f35c05022f9feabcca01c";

async function getTMDBInfo(id, type) {
    const titles = new Set();
    let year = "";
    const languages = ["es-MX", "es-ES", "en-US"];
    for (const lang of languages) {
        try {
            const url = `https://api.themoviedb.org/3/${type}/${id}?api_key=${TMDB_API_KEY}&language=${lang}`;
            const res = await fetch(url, { headers: { "User-Agent": USER_AGENT } }).then(r => r.json());
            const title = type === "movie" ? res.title : res.name;
            const original = type === "movie" ? res.original_title : res.original_name;
            if (title) titles.add(title);
            if (original) titles.add(original);
            if (!year) year = (res.release_date || res.first_air_date || "").substring(0, 4);
        } catch (e) {}
    }
    return titles.size > 0 ? { titles: Array.from(titles), year } : null;
}
```

### Step 2: Title Normalization
Strip special chars, subtitles, parentheticals, and casing to prevent mismatching due to minor punctuation variance:
```javascript
function cleanTitle(title) {
    if (!title) return "";
    return title.toLowerCase()
        .replace(/\(.*?\)/g, "") // strip parentheticals
        .replace(/\[.*?\]/g, "") // strip brackets
        .replace(/:\s*.*?$/g, "") // strip colon subtitles
        .replace(/[-_]/g, " ")
        .replace(/[^a-z0-9\s]/g, "") // strip special characters
        .replace(/\s+/g, " ")
        .trim();
}
```

### Step 3: Digit De-duplication (Set Mapping)
WordPress themes often duplicate the title inside hover tags, desktop/mobile selectors, or thumbnails within the same candidate link. Standard digit extraction returns `"22"` instead of `"2"`.
*   **Solution**: Feed all extracted digits into a `Set` to de-duplicate them.

```javascript
const queryNumbers = [...new Set(cleanedQuery.match(/\d/g) || [])].sort().join("");
const titleNumbers = [...new Set(cleanedTitle.match(/\d/g) || [])].sort().join("");
```

### Step 4: Strict Penalty & Boost Weights
Apply a heavy penalty on digit mismatch and boost exact matches, while keeping character length penalty minimal to accommodate descriptive tags (like `Ongoing`, `Sub`, `4K`).

```javascript
let score = 0;
if (cleanedTitle === cleanedQuery) {
    score += 100;
} else if (cleanedTitle.includes(cleanedQuery) || cleanedQuery.includes(cleanedTitle)) {
    score += 40;
}

// Strict season check
if (queryNumbers !== titleNumbers) {
    score -= 80; // Large penalty for mismatched season numbers
} else if (queryNumbers.length > 0) {
    score += 30; // Boost for exact season number matches
}

// Low character length penalty
const lengthDiff = Math.abs(cleanedTitle.length - cleanedQuery.length);
score -= lengthDiff * 0.05;
```

---

## 🛠️ 4. High-Tier Embed Stream Resolvers

The following reference implementations resolve protected player URLs to direct `.m3u8` or `.mp4` video streams.

### A. OkRu (Odnoklassniki) — 100% Reliable
*   **Stealth Advantage**: Does **not** require headers during playback (plays flawlessly in any ExoPlayer/VLC instance without 403 Forbidden blocks).
*   **Resolution Strategy**: Extracts the HTML, decodes `data-options` JSON, and parses `flashvars.metadata` for the HLS manifest or high-quality video variants:
```javascript
async function resolveOkru(embedUrl) {
    try {
        const html = await fetch(embedUrl, { headers: { "User-Agent": USER_AGENT } }).then(r => r.text());
        const m = html.match(/data-options="([^"]+)"/i);
        if (!m) return null;
        const decoded = m[1].replace(/&quot;/g, '"').replace(/&amp;/g, '&');
        const data = JSON.parse(decoded);
        const metadataStr = data?.flashvars?.metadata;
        if (!metadataStr) return null;
        const meta = JSON.parse(metadataStr);
        
        if (meta.hlsManifestUrl) {
            let hls = meta.hlsManifestUrl;
            if (hls.startsWith("//")) hls = "https:" + hls;
            return { url: hls, server: "OkRu", quality: "1080p", headers: { "User-Agent": USER_AGENT, "Referer": "https://ok.ru/" } };
        }
        const videos = meta.videos || [];
        const qualityOrder = ["full", "hd", "sd", "low"];
        for (const q of qualityOrder) {
            const match = videos.find(v => v.name === q);
            if (match?.url) {
                let streamUrl = match.url;
                if (streamUrl.startsWith("//")) streamUrl = "https:" + streamUrl;
                return { url: streamUrl, server: "OkRu", quality: q === "full" ? "1080p" : q === "hd" ? "720p" : "480p" };
            }
        }
    } catch (e) {}
    return null;
}
```

### B. StreamWish (HLSWish / Hanerix / EmbedWish)
*   **Resolution Strategy**: Race requests across multiple mirrors in parallel, extract MD5 challenge hash → trigger dynamic XML HTTP request `/dl?op=view&hash=...` API or decode packers.

### C. VidHide (MinoChinos Vip/Pro)
*   **Resolution Strategy**: Execute packer decoding using Dean Edwards packer unpacker, search inside the unpacked javascript logic for `"hls4"` or `"hls2"` streaming properties:
```javascript
const packedMatch = html.match(/eval\(function\(p,a,c,k,e,[rd]\)[\s\S]*?\.split\('\|'\)[^\)]*\)\)/);
const unpacked = evalUnpack(packedMatch[0]);
const hlsMatch = unpacked.match(/"hls[24]"\s*:\s*"([^"]+)"/);
```

### D. FileMoon ( ECDSA Challenge Bypass )
*   **Critical Path-Fix**: FileMoon URLs can contain a trailing filename (e.g., `/e/wxiu9ckx6nzk/Hachi_Siempre_a_tu_lado`). Structurally parse pathparts to prevent slicing failures:
```javascript
const pathParts = urlObj.pathname.split("/").filter(Boolean);
let videoId = null;
if (pathParts[0] === "e" || pathParts[0] === "d") {
    videoId = pathParts[1];
} else {
    videoId = pathParts.pop();
}
```

### E. VOE (ROT13 + Base64 Double Decode)
*   **Resolution Strategy**: Follow temporary tokens redirect -> locate dynamic JSON script tags -> apply multi-stage ROT13 and base64 parsing:
```javascript
const jsonMatch = html.match(/<script type="application\/json">([\s\S]*?)<\/script>/);
// Steps: ROT13 Shift -> Strip Noise chars ('@$', '^^', etc.) -> base64 decode -> Shift charCodes -3 -> Reverse String -> base64 decode -> JSON.parse
```

---

## 🚀 5. Playback Header Forwarding (403 Evasion)

The single most common cause of playback failure (`ERROR_CODE_IO_BAD_HTTP_STATUS` / HTTP 403 Forbidden) is the streaming client omitting headers.

> [!IMPORTANT]
> Modern video CDNs (VOE, VidHide, StreamWish, Vimeos) enforce strict hotlink protection. Direct stream URLs **cannot** be loaded without forwarding the headers returned by the provider.

If your player application cannot forward a separate `headers` payload to ExoPlayer/VLC, you must configure the provider to append the headers to the URL using a pipe `|` separator (Kodi/VLC standard):
```javascript
const pipedUrl = `${resolved.url}|Referer=${encodeURIComponent(resolved.headers.Referer)}&User-Agent=${encodeURIComponent(resolved.headers['User-Agent'])}`;
```

---

## 📂 6. Nuvio Provider Repository Blueprint

To distribute scrapers properly, a separate Nuvio repository must be established following this structural blueprint:

```
nuvio-repo-name/
├── manifest.json         # Providers scraper registry
├── package.json          # Node dependencies
├── .gitignore            # Git exclusions
├── README.md             # Clean manifest installer instruction
└── providers/            # Scrapers CommonJS modules
    ├── provider1.js
    └── provider2.js
```

### A. Clean Installer README.md Rule
Do **not** clutter the repository `README.md` with technical implementation secrets, internal scraper variables, or source site names. Keep it extremely clean, containing only a short description and a copyable manifest URL:

```markdown
# Nuvio Custom Providers Collection

A collection of scrapers for Nuvio to stream content.

## 🔗 Nuvio Manifest URL

To install this provider collection, copy and paste the following manifest URL into your Nuvio application:

```text
https://raw.githubusercontent.com/<YOUR_GITHUB_USERNAME>/<REPO_NAME>/main/manifest.json
```
```

### B. CommonJS Scraper Module Template
Always wrap the resolved streams in the Nuvio standard object array:

```javascript
const TMDB_API_KEY = "439c478a771f35c05022f9feabcca01c";

async function getStreams(id, type, season, episode) {
    // 1. Fetch metadata from TMDB
    // 2. Query WordPress search ?s=
    // 3. Score candidates using de-duplicated digit logic
    // 4. Resolve episode subpages or decode base64 dropdowns
    // 5. Extract embed iframes, filter decoys, and return
    return [
        {
            name: "ProviderId",
            title: "[4K] English [Rumble]",
            url: embedUrl,
            quality: "2160p",
            headers: {
                "Referer": "https://referer-base-site.com/"
            }
        }
    ];
}

module.exports = { getStreams };
```

---

## 🛠️ 7. Development & Testing Workflow

1.  **Strict Debug Flag**: Ensure that all scrapers define a silent `DEBUG = false` flag at the top. Use `log()` wrapper instead of `console.log()` to keep test logs quiet in production:
    ```javascript
    const DEBUG = false;
    function log(...args) {
        if (DEBUG) console.log(...args);
    }
    ```
2.  **Verify via Test Runner**: Prior to committing changes, execute the Node test runner against your provider using active, non-expired streams:
    ```bash
    node tests/test_providers.js <provider-id>
    ```
3.  **Active Movie Test Cases**: Use movies with functional, non-expiring hosts (like **OK.ru** on *Todo sobre mi padre / About My Father*, TMDB ID `829051`) as test fixtures to ensure E2E integration remains green.
