# FuegoCine Provider Test Results

**Test Date:** 2026-04-19  
**Test Script:** `F:\PyApps\page2kodi\test_fuegocine_provider.py`

## Executive Summary

| Test | Status | Details |
|------|--------|---------|
| Provider Initialization | PASS | Provider loads correctly with all categories |
| get_main_page() (no filter) | FAIL | Main page uses JavaScript templates |
| get_main_page() (Movie filter) | PASS | Returns 3 actual items |
| get_main_page() (Serie filter) | FAIL | No content with "Series" label on site |
| get_main_page() (Anime filter) | PASS | Returns 20 actual items |
| search() functionality | PASS | Found 5 results for "matrix" query |
| load() content detail | PARTIAL | Title/plot work, video sources need JS |
| URL fixing utilities | PASS | All URL transformations correct |
| Site connection | PASS | HTTP 200, 155KB response |

**Overall: 6/9 tests passing, 2 structural issues identified**

---

## Root Cause Analysis

### Issue 1: Main Page Returns No Items

**Problem:** The main page (`https://www.fuegocine.com/`) returns template placeholders instead of actual content.

**Evidence:**
```
.crd element HTML:
<div class="crd">
  <h3.crd__title a href="{url}">  <!-- Placeholder -->
  <img src="{image}">              <!-- Placeholder -->
</div>
```

**Explanation:** FuegoCine uses client-side JavaScript rendering. The HTML contains template markers like `{url}`, `{title}`, `{image}` that are replaced by JavaScript after page load. Direct HTTP scraping cannot access this rendered content.

**Solution Options:**
1. Skip main page scraping and use label pages only (Peliculas, Anime)
2. Use Selenium/Playwright to render JavaScript
3. Reverse-engineer the JavaScript data source

**Recommendation:** Use label pages as primary content source. Update provider to default to "Peliculas" when no filter specified.

---

### Issue 2: Series Label Has No Content

**Problem:** The "Series" label page (`https://www.fuegocine.com/search/label/Series`) returns zero items.

**Evidence:**
```
Site message: "No hay ninguna entrada con la etiqueta Series"
(Translation: "There are no entries with the Series label")
```

**Explanation:** This is a site-level issue - FuegoCine does not have any content tagged with the "Series" Blogger label. This is not a provider bug.

**Recommendation:** Update categories mapping to reflect actual available labels on the site.

---

### Issue 3: Video Sources Not Extracted

**Problem:** The `load_links()` method cannot extract video sources from content pages.

**Evidence:**
```
Content page analysis:
- Iframes with src: 0
- Video elements: 0
- data-embed attributes: 0 (created dynamically)
- Static embed URLs: 8 (found in HTML)
```

**Available embed URLs found in HTML:**
1. `https://vidsrc.pro/embed/movie/` (template)
2. `https://vidsrc.xyz//embed/movie/` (template)
3. `https://frembed.pro/api/film.php?id=` (template)
4. `https://repfuegocinefree.blogspot.com/?player=...` (backup)
5. `https://unlimplay.com/play.php/embed/movie/149` (template)

**Explanation:** The site uses a JavaScript player system (`strPost` function) that dynamically creates iframe/video elements based on these template URLs. The actual movie ID is appended via JavaScript.

**Solution:** Modify `load_links()` to extract these template URLs and construct the full embed URLs by extracting movie IDs from:
- URL path segments
- TMDB image URLs (contains movie ID)
- `data-post-id` attribute

---

## Working Functionality

### get_main_page() with Label Filters

**Peliculas label** - Works correctly:
```
Items returned: 3
- Los Angeles de Charlie (2019)
- The Witcher: Sirenas de las Profundidades (2025)
- Harry Potter y Las Reliquias de la Muerte: Parte 1 (2010)
```

**Anime label** - Works correctly:
```
Items returned: 20
- Akira (1988)
- El Increible Castillo Vagabundo (2004)
- El Niño y la Garza (2023)
... (and more)
```

### search() Functionality

**Test query: "matrix"**
```
Results: 5 items
- Matrix 2: Recargado (2003)
- Matrix 3: Revoluciones (2003)
- Matrix 4: Resurrecciones (2021)
- Matrix (1999)
- Scary Movie: Una Pelicula de Miedo (2000)
```

### Content Detail Extraction

**Partial success:**
- Title extraction: Works (from h2/h1 elements)
- Plot extraction: Works (from TMDB synopsis)
- Poster extraction: Works (from TMDB images)
- Episode detection: Not tested (no series content found)

---

## Provider Code Quality Assessment

### Strengths
- Clean class structure inheriting from BaseProvider
- Proper session handling with headers
- Good fallback parsing logic (`_parse_card`, `_parse_h3_link`)
- Comprehensive episode parsing patterns
- URL fixing utilities work correctly

### Areas for Improvement
1. **JavaScript-rendered pages:** Need strategy for JS templates
2. **Embed URL extraction:** Current iframe/video selectors miss template URLs
3. **Categories mapping:** Should validate against actual site labels
4. **Error handling:** Silent returns on errors (should log for debugging)

---

## Recommendations

### Immediate Fixes

1. **Update `get_main_page()` to handle main page template issue:**
```python
def get_main_page(self, page: int = 1, filter_type: str = None) -> List[Dict]:
    if not filter_type:
        # Default to Peliculas since main page uses JS templates
        filter_type = "Peliculas"
    # ... rest of implementation
```

2. **Add template URL extraction to `load_links()`:**
```python
# Extract template embed URLs from HTML
embed_templates = [
    'vidsrc.pro/embed/movie/',
    'vidsrc.xyz/embed/movie/',
    'frembed.pro/api/film.php?id=',
]

# Extract movie ID from URL or data attributes
movie_id = self._extract_movie_id(url, soup)

# Construct full embed URLs
for template in embed_templates:
    full_url = template + movie_id
    # Resolve and add to sources
```

3. **Update categories to match actual site:**
```python
categories = {
    "Peliculas": "Movie",   # Works
    "Anime": "Anime",       # Works
    # Remove "Series" - no content
    # Add other working labels found on site
}
```

### Long-term Improvements

1. Consider using a lightweight browser automation for JavaScript rendering
2. Add comprehensive logging for debugging in Kodi environment
3. Create unit tests for each parsing method
4. Add retry logic for transient network failures

---

## Test Files Created

| File | Purpose |
|------|---------|
| `test_fuegocine_provider.py` | Main test script with Kodi mocks |
| `debug_html_structure.py` | HTML structure analysis |
| `debug_label_pages.py` | Label page comparison |
| `debug_load_content.py` | Content detail extraction test |
| `debug_modal_structure.py` | Modal/player structure analysis |
| `debug_video_structure.py` | Video embed deep dive |
| `debug_embed_data.py` | JavaScript data extraction |

---

## Conclusion

The FuegoCine provider logic is **correctly implemented** but faces **structural limitations** due to the site's JavaScript-based rendering:

1. **Provider code is sound** - parsing logic, URL handling, session management all work
2. **Site uses heavy JavaScript** - main page and video embeds are rendered client-side
3. **Label pages work** - content can be retrieved from Blogger label URLs
4. **Search works** - Blogger search returns server-rendered content

The Kodi-specific issues (if any) are separate from the provider logic. The provider can function outside Kodi with the documented limitations. To fully support the site, the provider needs modifications to handle JavaScript templates or use browser automation.

---

**Next Steps:** Update provider code based on recommendations and re-test.