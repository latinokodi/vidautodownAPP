# VidAutoDown

A modern video downloader built with Electron + React + Python.

## Features

- Download videos from 1000+ platforms using yt-dlp
- Download videos from 1000+ platforms using yt-dlp
- Multiple download strategies with automatic retry
- Concurrent downloads with configurable limits
- Real-time progress tracking
- Persistent task state
- Modern dark UI

## Requirements

- Python 3.10+
- Node.js 18+
- yt-dlp (installed automatically or via `pip install yt-dlp`)
- yt-dlp (installed automatically or via `pip install yt-dlp`)

## Quick Start

```bash
# Run the start script
start.bat
```

The script will:
1. Create a Python virtual environment
2. Install Python dependencies
3. Install Node.js dependencies
4. Build the frontend
5. Launch the application

## Development

```bash
# Create venv and install Python deps
python -m venv venv
venv\Scripts\activate
pip install -r backend/requirements.txt

# Install Node.js deps
npm install

# Run in development mode
npm run dev
```

## Architecture

```
├── backend/
│   └── server.py          # aiohttp server for yt-dlp operations
├── electron/
│   ├── main.js            # Electron main process
│   └── preload.js         # Context bridge for IPC
├── frontend/
│   └── src/
│       ├── App.jsx        # Main React component
│       └── styles/        # CSS styles
├── start.bat              # Windows startup script
└── package.json           # Node.js configuration
```

## How It Works

1. Electron spawns a Python subprocess running an aiohttp server
2. The React frontend communicates via WebSocket with the Python backend
3. The backend manages yt-dlp subprocesses and tracks download progress
4. State is persisted in SQLite database

## Strategies

The app uses different download strategies with automatic fallback:

1. **Strategy A**: Built-in downloader with concurrent fragments (4)
2. **Strategy B**: Fallback with minimal options (e.g. no recoding)
3. **Strategy C**: Safe fallback for sensitive platforms

## License

MIT