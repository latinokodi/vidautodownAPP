# Video Auto Downloader

## What This Is

A Windows desktop application for downloading videos from YouTube and 1000+ other platforms. Users paste URLs or drag-and-drop to queue downloads with real-time progress tracking. Built with FastAPI backend, Next.js frontend, and PyWebView desktop wrapper.

## Core Value

One-click video downloads — paste a URL, get the video.

## Requirements

### Validated

- ✓ Download videos from YouTube and 1000+ sites via yt-dlp — existing
- ✓ Real-time download progress via WebSocket — existing
- ✓ Drag-and-drop URL input — existing
- ✓ Concurrent downloads with configurable limits — existing
- ✓ SQLite persistence for task state — existing
- ✓ Retry strategies with aria2c acceleration — existing
- ✓ Settings management (download path, concurrent limits, format) — existing

### Active

- [ ] **Link Crawler Tab** — New UI tab for URL crawling feature
- [ ] **Page URL Input** — Input field in crawler tab for entering video page URLs
- [ ] **URL Extraction** — Extract all yt-dlp-compatible video URLs from the provided page
- [ ] **Preview Modal** — Modal overlay showing extracted URLs as a list
- [ ] **URL Selection** — Checkboxes for each URL with bulk actions (select all, none, invert)
- [ ] **Queue Addition** — Add selected URLs to the download queue

### Out of Scope

- Video metadata fetching (title, thumbnail) in preview — adds latency, keep it simple
- Quality selector in preview — defer to existing download settings
- Crawl depth > 1 — only scan the provided page, don't follow links
- YouTube-specific logic — use yt-dlp's generic extraction

## Context

**Existing Architecture:**
- Backend: FastAPI with REST API + WebSocket, SQLite persistence, threading for concurrent downloads
- Frontend: Next.js with React, Zustand state management, Tailwind CSS
- Desktop: PyWebView wrapper for native Windows application

**yt-dlp Integration:**
- Current: Single URL downloads with progress parsing
- New: Use yt-dlp's `--flat-playlist` or `--print` to extract URLs without downloading

**State Management:**
- Backend: `DownloadController` singleton with thread-safe task dictionary
- Frontend: Zustand store with WebSocket sync

## Constraints

- **Platform**: Windows desktop (primary target)
- **Dependencies**: yt-dlp must support the target site
- **Performance**: URL extraction should be fast (no downloading during crawl)
- **UI**: Must fit within existing tab structure

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Separate tab for crawler | Keeps main download workflow focused, avoids UI clutter | — Pending |
| URL-only preview | Faster extraction, simpler UI, users can identify videos by URL | — Pending |
| yt-dlp generic extraction | Works with 1000+ sites, no site-specific code needed | — Pending |

---
*Last updated: 2026-03-17 after initialization*