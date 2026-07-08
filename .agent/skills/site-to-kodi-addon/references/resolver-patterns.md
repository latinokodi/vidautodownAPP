# Resolver Patterns

> URL resolution patterns for extracting direct streams from embeds.

---

## 🏗️ Resolver Architecture

### Resolver Router (`resolvers/__init__.py`)

```python
# -*- coding: utf-8 -*-
"""Streaming Resolvers - Route embed URLs to correct resolver"""

import re
import requests
from typing import Dict, Optional, Any

# Import all resolvers
from . import voe, streamwish, goodstream, fastream, filemoon, okru, vidhide, vimeos, uqload, dood, mixdrop, fembed, streamtape


def resolve(embed_url: str, session: requests.Session = None) -> Optional[Dict[str, Any]]:
    """Resolve embed URL using domain matching."""
    if not session:
        session = requests.Session()
    
    # Domain-based resolver routing
    if 'voe.sx' in embed_url:
        return voe.resolve(embed_url, session)
    
    if any(x in embed_url for x in ['streamwish', 'hlswish', 'strwish', 'vibuxer', 'hglink']):
        return streamwish.resolve(embed_url, session)
    
    if 'goodstream' in embed_url:
        return goodstream.resolve(embed_url, session)
    
    if 'fastream.to' in embed_url:
        return fastream.resolve(embed_url, session)
    
    if any(x in embed_url for x in ['filemoon', 'moonembed']):
        return filemoon.resolve(embed_url, session)
    
    if 'ok.ru' in embed_url:
        return okru.resolve(embed_url, session)
    
    if any(x in embed_url for x in ['vidhide', 'vidhidepro']):
        return vidhide.resolve(embed_url, session)
    
    if 'vimeos.net' in embed_url:
        return vimeos.resolve(embed_url, session)
    
    if 'uqload' in embed_url:
        return uqload.resolve(embed_url, session)
    
    if 'dood' in embed_url or 'doodstream' in embed_url:
        return dood.resolve(embed_url, session)
    
    if 'mixdrop' in embed_url:
        return mixdrop.resolve(embed_url, session)
    
    if 'embedsito' in embed_url or 'fembed' in embed_url:
        return fembed.resolve(embed_url, session)
    
    if 'streamtape' in embed_url or 'strtape' in embed_url:
        return streamtape.resolve(embed_url, session)
    
    # Generic HLS/M3U8 detection
    if '.m3u8' in embed_url:
        return {
            "url": embed_url,
            "headers": {"Referer": embed_url.split('/')[2] if '/' in embed_url else ""},
            "quality": "HD",
        }
    
    # Direct MP4/MKV
    if any(ext in embed_url for ext in ['.mp4', '.mkv', '.avi']):
        return {
            "url": embed_url,
            "headers": {},
            "quality": "HD",
        }
    
    return None
```

---

## 🔧 Resolver Implementations

### StreamWish Resolver (Complex)

```python
# streamwish.py
# -*- coding: utf-8 -*-
"""StreamWish resolver with packer unpacker"""

import re
import requests
from typing import Dict, Optional
from resources.lib.modules import packer


def resolve(url: str, session: requests.Session = None) -> Optional[Dict]:
    """Resolve StreamWish embed to direct stream."""
    if not session:
        session = requests.Session()
    
    try:
        # Domain normalization
        if 'hglink.to' in url:
            url = url.replace('hglink.to', 'vibuxer.com')
        
        embed_host = re.search(r'^(https?://[^/]+)', url).group(1) if re.search(r'^(https?://[^/]+)', url) else 'https://hlswish.com'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': url,
        }
        
        resp = session.get(url, headers=headers, timeout=12)
        html = resp.text
        
        # Method 1: Direct m3u8 extraction
        m3u8_match = re.search(r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)', html, re.I)
        if m3u8_match:
            return {
                "url": m3u8_match.group(1).replace('\\/', '/'),
                "headers": {"User-Agent": headers['User-Agent'], "Referer": embed_host + '/'},
                "quality": "HD",
            }
        
        # Method 2: file: "..." pattern
        file_match = re.search(r'file\s*:\s*["\']([^"\']+)["\']', html, re.I)
        if file_match:
            target = file_match.group(1).replace('\\/', '/')
            if target.startswith('/'):
                target = embed_host + target
            return {
                "url": target,
                "headers": {"User-Agent": headers['User-Agent'], "Referer": embed_host + '/'},
                "quality": "HD",
            }
        
        # Method 3: Packer unpacker
        unpacked = packer.unpack_v2(html)
        if unpacked:
            m3u8_match = re.search(r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)', unpacked, re.I)
            if m3u8_match:
                return {
                    "url": m3u8_match.group(1),
                    "headers": {"User-Agent": headers['User-Agent'], "Referer": embed_host + '/'},
                    "quality": "HD",
                }
        
    except Exception:
        pass
    
    return None
```

### VOE Resolver

```python
# voe.py
# -*- coding: utf-8 -*-
"""VOE resolver - simple m3u8 extraction"""

import re
import requests
from typing import Dict, Optional


def resolve(url: str, session: requests.Session = None) -> Optional[Dict]:
    """Resolve VOE embed."""
    if not session:
        session = requests.Session()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': url,
        }
        
        resp = session.get(url, headers=headers, timeout=12)
        html = resp.text
        
        # Look for m3u8 URL
        m3u8_patterns = [
            r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)',
            r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"',
            r'src\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        ]
        
        for pattern in m3u8_patterns:
            match = re.search(pattern, html, re.I)
            if match:
                return {
                    "url": match.group(1).replace('\\/', '/'),
                    "headers": {"Referer": url.split('/')[2]},
                    "quality": "HD",
                }
        
    except Exception:
        pass
    
    return None
```

### OK.ru Resolver

```python
# okru.py
# -*- coding: utf-8 -*-
"""OK.ru resolver - direct MP4 extraction"""

import re
import requests
from typing import Dict, Optional


def resolve(url: str, session: requests.Session = None) -> Optional[Dict]:
    """Resolve OK.ru embed."""
    if not session:
        session = requests.Session()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        resp = session.get(url, headers=headers, timeout=12)
        html = resp.text
        
        # Extract video URL from JSON metadata
        # Pattern: "url":"https://..."
        patterns = [
            r'"url"\s*:\s*"([^"]+\.mp4[^"]*)"',
            r'data-video\s*=\s*"([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                video_url = match.group(1).replace('\\/', '/')
                return {
                    "url": video_url,
                    "headers": {},
                    "quality": "HD",
                }
        
    except Exception:
        pass
    
    return None
```

### DoodStream Resolver

```python
# dood.py
# -*- coding: utf-8 -*-
"""DoodStream resolver - token-based extraction"""

import re
import requests
from typing import Dict, Optional


def resolve(url: str, session: requests.Session = None) -> Optional[Dict]:
    """Resolve DoodStream embed."""
    if not session:
        session = requests.Session()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': url,
        }
        
        # Normalize URL
        if 'dood.' in url and 'dood.la' not in url:
            url = url.replace('dood.', 'dood.la')
        
        resp = session.get(url, headers=headers, timeout=12)
        html = resp.text
        
        # Extract pass_md5 token
        pass_match = re.search(r'pass_md5\s*=\s*["\']([^"\']+)["\']', html)
        if not pass_match:
            return None
        
        pass_token = pass_match.group(1)
        
        # Build video URL
        base_url = url.split('/')[2]
        video_url = f"https://{base_url}/pass_md5/{pass_token}"
        
        # Get final URL (needs redirect)
        resp2 = session.get(video_url, headers=headers, timeout=10, allow_redirects=False)
        if resp2.status_code == 302:
            final_url = resp2.headers.get('Location', '')
            if final_url:
                return {
                    "url": final_url,
                    "headers": {"Referer": url},
                    "quality": "HD",
                }
        
    except Exception:
        pass
    
    return None
```

### MixDrop Resolver

```python
# mixdrop.py
# -*- coding: utf-8 -*-
"""MixDrop resolver"""

import re
import requests
from typing import Dict, Optional


def resolve(url: str, session: requests.Session = None) -> Optional[Dict]:
    """Resolve MixDrop embed."""
    if not session:
        session = requests.Session()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': url,
        }
        
        resp = session.get(url, headers=headers, timeout=12)
        html = resp.text
        
        # Look for video URL in JavaScript
        match = re.search(r'WURL\s*=\s*"([^"]+)"', html)
        if match:
            video_url = match.group(1).replace('\\/', '/')
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            return {
                "url": video_url,
                "headers": {"Referer": url},
                "quality": "HD",
            }
        
        # Alternative: direct source tag
        source_match = re.search(r'<source\s+src\s*=\s*["\']([^"\']+)["\']', html)
        if source_match:
            return {
                "url": source_match.group(1),
                "headers": {"Referer": url},
                "quality": "HD",
            }
        
    except Exception:
        pass
    
    return None
```

### Filemoon Resolver

```python
# filemoon.py
# -*- coding: utf-8 -*-
"""Filemoon resolver"""

import re
import base64
import requests
from typing import Dict, Optional


def resolve(url: str, session: requests.Session = None) -> Optional[Dict]:
    """Resolve Filemoon embed."""
    if not session:
        session = requests.Session()
    
    try:
        # Normalize URL
        if 'filemoon.' in url and 'filemoon.sx' not in url:
            url = re.sub(r'filemoon\.[a-z]+', 'filemoon.sx', url)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': url,
        }
        
        resp = session.get(url, headers=headers, timeout=12)
        html = resp.text
        
        # Look for m3u8 URL
        m3u8_match = re.search(r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)', html, re.I)
        if m3u8_match:
            return {
                "url": m3u8_match.group(1).replace('\\/', '/'),
                "headers": {"Referer": url},
                "quality": "HD",
            }
        
        # Look for base64 encoded URL
        b64_match = re.search(r'atob\s*\(\s*["\']([A-Za-z0-9+/=]+)["\']\s*\)', html)
        if b64_match:
            decoded = base64.b64decode(b64_match.group(1)).decode('utf-8')
            if '.m3u8' in decoded or '.mp4' in decoded:
                return {
                    "url": decoded,
                    "headers": {"Referer": url},
                    "quality": "HD",
                }
        
    except Exception:
        pass
    
    return None
```

---

## 🔧 Packer Unpacker (`modules/packer.py`)

```python
# -*- coding: utf-8 -*-
"""P.A.C.K.E.R. JavaScript unpacker"""

import re


def unpack(html: str) -> str:
    """Unpack P.A.C.K.E.R. obfuscated code."""
    pattern = r"eval\(function\(p,a,c,k,e,[rd]\)[\s\S]*?\.split\('\|'\)[^)]*\)\)"
    match = re.search(pattern, html)
    if not match:
        return ""
    
    try:
        args_pattern = r"\('([\s\S]*?)',\s*(\d+),\s*(\d+),\s*'([\s\S]*?)'\.split\('\|'\)"
        inner_match = re.search(args_pattern, match.group(0))
        if not inner_match:
            return ""
        
        p, a, c, k = inner_match.groups()
        radix = int(a)
        symtab = k.split("|")
        
        def _unbase_generic(str_val, radix):
            alphabet = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
            result = 0
            for char in str_val:
                pos = alphabet.find(char)
                if pos == -1:
                    return None
                result = result * radix + pos
            return result
        
        def replace_func(match):
            word = match.group(0)
            idx = _unbase_generic(word, radix)
            if idx is None or idx >= len(symtab):
                return word
            return symtab[idx] if symtab[idx] else word
        
        return re.sub(r'\b([0-9a-zA-Z]+)\b', replace_func, p)
    
    except Exception:
        return ""


def unpack_v2(data: str) -> str:
    """Alternative unpacker implementation."""
    pack_match = re.search(
        r"eval\(function\(p,a,c,k,e,[a-z]\)\{[^}]+\}\s*\('([\s\S]+?)',\s*(\d+),\s*(\d+),\s*'([\s\S]+?)'\.split\('\|'\)",
        data
    )
    if not pack_match:
        return ""
    
    try:
        payload = pack_match.group(1)
        radix = int(pack_match.group(2))
        symtab = pack_match.group(4).split('|')
        
        def _unbase(str_val, radix):
            alphabet = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
            result = 0
            for char in str_val:
                pos = alphabet.find(char)
                if pos == -1:
                    return None
                result = result * radix + pos
            return result
        
        def replace_func(match):
            word = match.group(0)
            idx = _unbase(word, radix)
            if idx is None or idx >= len(symtab):
                return word
            return symtab[idx] if symtab[idx] else word
        
        return re.sub(r'\b([0-9a-zA-Z]+)\b', replace_func, payload)
    
    except Exception:
        return ""
```

---

## 📊 Resolver Return Structure

All resolvers return the same structure:

```python
{
    "url": str,           # Direct playable URL
    "headers": dict,      # Headers needed for playback
    "quality": str,       # "HD", "720p", "1080p", etc.
}
```

---

## 📋 Supported Domains Matrix

| Domain | Resolver | Method |
|--------|----------|--------|
| StreamWish | `streamwish.py` | Packer unpack, m3u8 regex |
| VOE | `voe.py` | M3U8 extraction |
| Filemoon | `filemoon.py` | M3U8, base64 decode |
| VidHide | `vidhide.py` | Redirect chain, m3u8 |
| DoodStream | `dood.py` | Token extraction, redirect |
| MixDrop | `mixdrop.py` | JS extraction |
| UqLoad | `uqload.py` | Source tag |
| StreamTape | `streamtape.py` | Redirect + token |
| OK.ru | `okru.py` | Direct MP4 |
| GoodStream | `goodstream.py` | M3U8 from config |
| Fastream | `fastream.py` | M3U8 extraction |
| Vimeos | `vimeos.py` | JSON config |
| Fembed | `fembed.py` | API extraction |

---

## ✅ Resolver Checklist

- [ ] Resolver router covers all embed domains from site
- [ ] Each resolver returns dict with url, headers, quality
- [ ] Headers include Referer for protected streams
- [ ] Packer unpacker available for obfuscated JS
- [ ] HLS/m3u8 detection fallback
- [ ] Direct MP4 detection fallback