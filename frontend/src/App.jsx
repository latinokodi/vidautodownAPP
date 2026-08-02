import React, { useState, useEffect, useCallback, useRef, memo } from 'react';
import { 
  Search, Trash2, Play, Pause, RotateCcw, 
  XCircle, Settings, Download,
  Activity, Monitor, RefreshCw
} from 'lucide-react';

const WS_URL = 'ws://127.0.0.1:8765';

const STATUS_LABELS = {
  queued: 'STANDBY',
  'fetching-info': 'QUERYING',
  downloading: 'ACTIVE',
  paused: 'HALTED',
  completed: 'DONE',
  failed: 'FAULT',
  cancelled: 'VOID',
  merging: 'PROCESSING',
  info: 'QUERYING',
  incomplete: 'PARTIAL',
  'force-download': 'FORCED',
};

function App() {
  const [tasks, setTasks] = useState([]);
  const [settings, setSettings] = useState({
    destination: '',
    max_concurrent: 3,
    auto_delete: false,
    skip_duplicates: true,
    yt_dlp_available: false,
    total_added: 0,
    skipped: 0,
  });
  const [inputText, setInputText] = useState('');
  const [scraperUrl, setScraperUrl] = useState('');
  const [scraping, setScraping] = useState(false);
  const [scraperResults, setScraperResults] = useState(null);
  const [connected, setConnected] = useState(false);
  const [logs, setLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('downloads');
  const wsRef = useRef(null);
  const logsRef = useRef(null);

  const addLog = useCallback((message) => {
    const time = new Date().toLocaleTimeString('en-GB', { hour12: false });
    setLogs(prev => [...prev.slice(-100), { time, message }]);
  }, []);

  const sendCommand = useCallback((command, data = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command, ...data }));
    }
  }, []);

  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket(`${WS_URL}/ws`);
      ws.onopen = () => {
        setConnected(true);
        addLog('LINK ESTABLISHED');
        ws.send(JSON.stringify({ command: 'get_settings' }));
      };
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'refresh') setTasks(msg.data || []);
          else if (msg.type === 'progress') {
            setTasks(prev => prev.map(t => t.url === msg.data.url ? msg.data : t));
          } else if (msg.type === 'settings') setSettings(msg.data || {});
          else if (msg.type === 'result') {
            if (msg.command === 'add' && msg.data) {
              const { added, skipped_pre, total_added, skipped } = msg.data;
              if (added > 0) addLog(`ACCEPTED: ${added} URL(s)`);
              if (skipped_pre > 0) addLog(`FILTERED: ${skipped_pre} duplicate(s) in queue`);
              setSettings(prev => ({ ...prev, total_added: total_added ?? prev.total_added, skipped: skipped ?? prev.skipped }));
            }
          } else if (msg.type === 'crawl_start') {
            setScraping(true);
            setScraperResults({ count: 0, latest: '' });
            addLog(`CRAWL: ${msg.data.url}`);
          } else if (msg.type === 'crawl_progress') setScraperResults(prev => ({ ...prev, ...msg.data }));
          else if (msg.type === 'crawl_complete') {
            setScraping(false);
            const totalInfo = msg.data.total ? ` / ${msg.data.total}` : '';
            addLog(`CRAWL DONE: ${msg.data.urls.length}${totalInfo} items`);
            if (msg.data.urls.length > 0) {
              sendCommand('add', { 
                text: msg.data.urls.map(u => u.url).join('\n'),
                folder: msg.data.parent_title
              });
            }
          } else if (msg.type === 'crawl_error') { setScraping(false); addLog(`CRAWL FAULT: ${msg.data}`); }
          else if (msg.type === 'crawl_cancelled') { setScraping(false); addLog('CRAWL ABORTED'); }
        } catch (e) { console.error(e); }
      };
      ws.onclose = () => { setConnected(false); setTimeout(connectWebSocket, 2000); };
      wsRef.current = ws;
    } catch (err) { console.error(err); }
  }, [addLog, sendCommand]);

  useEffect(() => {
    connectWebSocket();
    return () => wsRef.current?.close();
  }, [connectWebSocket]);

  useEffect(() => {
    if (logsRef.current) logsRef.current.scrollTop = logsRef.current.scrollHeight;
  }, [logs]);

  const handlePaste = (e) => {
    const text = e.clipboardData.getData('text');
    if (text && text.includes('http')) {
      const isPornhubSearch = text.toLowerCase().includes('pornhub.com') && text.toLowerCase().includes('search');
      
      const isXvideosProfile = (() => {
        try {
          const urlObj = new URL(text.trim());
          const hostname = urlObj.hostname.toLowerCase();
          if (!hostname.includes('xvideos') && !hostname.includes('xnxx')) return false;
          const pathname = urlObj.pathname.replace(/^\/|\/$/g, '');
          if (!pathname) return false;
          const parts = pathname.split('/');
          const firstSegment = parts[0].toLowerCase();
          const systemPaths = new Set([
            'video', 'tags', 'c', 'best', 'new', 'channels-index', 'pornstars-index',
            'rss', 'manifest.json', 'account', 'switch-sexual-orientation', 'favorite',
            'my-feed', 'history', 'watch-later', 'change-currency', 'amateurs', 'pornstars',
            'channels', 'profiles', 'model', 'models', 'video-channels', 'uploads', 'outputs'
          ]);
          const channelPrefixes = new Set([
            'profiles', 'channels', 'model', 'models', 'amateurs', 'pornstars',
            'video-channels', 'amateur-channels', 'model-channels'
          ]);
          if (channelPrefixes.has(firstSegment)) return parts.length >= 2;
          if (systemPaths.has(firstSegment)) return false;
          if (/^video\d+/.test(firstSegment) || /^video\./.test(firstSegment)) return false;
          return true;
        } catch (err) { return false; }
      })();

      if (isPornhubSearch) {
        setScraperUrl(text);
        addLog('PORNHUB SEARCH — starting crawl');
        setActiveTab('downloads');
        setTimeout(() => sendCommand('crawl', { url: text }), 100);
      } else if (isXvideosProfile) {
        setScraperUrl(text);
        addLog('XVIDEOS PROFILE — starting crawl');
        setActiveTab('downloads');
        setTimeout(() => sendCommand('crawl', { url: text }), 100);
      } else {
        sendCommand('add', { text });
        addLog('URL PASTED — added to queue');
        setTimeout(() => setInputText(''), 100);
      }
    }
  };

  const handleScrape = () => { if (scraperUrl.trim()) sendCommand('crawl', { url: scraperUrl }); };
  const handleCancelScrape = () => sendCommand('cancel_crawl');
  
  const handleSelectFolder = async () => {
    if (window.electronAPI) {
      const folder = await window.electronAPI.selectFolder();
      if (folder) { sendCommand('set_destination', { path: folder }); addLog(`SET PATH: ${folder}`); }
    }
  };

  const activeTasks = tasks.filter(t => !['completed', 'cancelled', 'failed'].includes(t.status));
  const skippedTotal = settings.skipped || 0;
  const totalFiles = settings.total_added || 0;

  return (
    <div className="h-full w-full flex flex-col select-none font-display">
      {/* Header — matches bunkrscrOG Header.tsx layout */}
      <header className="glass-panel p-5 flex items-center justify-between">
        <div className="flex items-baseline gap-4">
          <div>
            <h1 className="font-display font-black text-2xl tracking-tight text-text-heading">
              VIDAUTO<span className="text-accent">DOWN</span>
            </h1>
            <div className="ascii-frame mt-1">[ REV 2.0 ]</div>
          </div>
          <div className="hidden md:block w-px h-10 bg-[var(--border-color)]" />
          <span className="hidden md:inline ascii-frame">
            QUEUE: {String(activeTasks.length).padStart(3, '0')}
          </span>
          <span className="hidden md:inline ascii-frame">
            SKIPPED: {String(skippedTotal).padStart(3, '0')}
          </span>
          <span className="hidden md:inline ascii-frame">
            TOTAL: {String(totalFiles).padStart(3, '0')}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 mr-3">
            <span className={`status-dot ${connected ? 'status-dot--online' : 'status-dot--offline'}`} />
            <span className="ascii-frame">{connected ? 'ONLINE' : 'OFFLINE'}</span>
          </div>
          <button onClick={() => sendCommand('clear_all')} className="btn">
            <Trash2 size={14} /> CLEAR ALL
          </button>
          {activeTasks.length > 0 && (
            <button onClick={() => sendCommand('cancel_all')} className="btn btn-danger">
              <XCircle size={14} /> CANCEL ALL
            </button>
          )}
        </div>
      </header>

      {/* Body */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Sidebar — matches tordownloaderElectron sidebar */}
        <aside className="w-56 border-r border-border bg-bg-panel flex flex-col shrink-0">
          <nav className="flex-1 p-4 space-y-1">
            <button
              className={`w-full text-left px-4 py-3 font-mono text-sm tracking-wide uppercase transition-colors ${activeTab === 'downloads' ? 'bg-accent/10 text-accent border-l-2 border-accent' : 'text-text-muted hover:text-text-main'}`}
              onClick={() => setActiveTab('downloads')}
            >
              <div className="flex items-center gap-2"><Download size={16}/> QUEUE</div>
              {activeTasks.length > 0 && (
                <span className="ml-auto bg-accent text-bg-deep px-2 py-0.5 text-xs font-bold">{activeTasks.length}</span>
              )}
            </button>
            <button
              className={`w-full text-left px-4 py-3 font-mono text-sm tracking-wide uppercase transition-colors ${activeTab === 'settings' ? 'bg-accent/10 text-accent border-l-2 border-accent' : 'text-text-muted hover:text-text-main'}`}
              onClick={() => setActiveTab('settings')}
            >
              <div className="flex items-center gap-2"><Settings size={16}/> CONFIG</div>
            </button>
            <button
              className={`w-full text-left px-4 py-3 font-mono text-sm tracking-wide uppercase transition-colors ${activeTab === 'logs' ? 'bg-accent/10 text-accent border-l-2 border-accent' : 'text-text-muted hover:text-text-main'}`}
              onClick={() => setActiveTab('logs')}
            >
              <div className="flex items-center gap-2"><Activity size={16}/> TELEMETRY</div>
            </button>
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-hidden flex flex-col min-w-0">
          <div className="flex-1 overflow-auto p-4">
            {activeTab === 'downloads' && (
              <DownloadsTab
                tasks={tasks}
                inputText={inputText}
                setInputText={setInputText}
                handlePaste={handlePaste}
                scraperUrl={scraperUrl}
                setScraperUrl={setScraperUrl}
                scraping={scraping}
                scraperResults={scraperResults}
                handleScrape={handleScrape}
                handleCancelScrape={handleCancelScrape}
                sendCommand={sendCommand}
              />
            )}
            {activeTab === 'settings' && (
              <SettingsTab
                settings={settings}
                sendCommand={sendCommand}
                handleSelectFolder={handleSelectFolder}
              />
            )}
            {activeTab === 'logs' && (
              <LogsTab
                logs={logs}
                setLogs={setLogs}
                logsRef={logsRef}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

/* ─── Downloads Tab ─── */
const DownloadsTab = memo(function DownloadsTab({
  tasks, inputText, setInputText, handlePaste,
  scraperUrl, setScraperUrl, scraping, scraperResults,
  handleScrape, handleCancelScrape, sendCommand
}) {
  const formatProgress = useCallback((p) => `${((p || 0) * 100).toFixed(1)}%`, []);

  return (
    <div className="h-full flex flex-col space-y-3 min-h-0">
      {/* Input row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Auto-add zone — matches bunkrscrOG AddUrlForm */}
        <section className="glass-panel p-4">
          <label className="section-label">[ AUTO-ADD ZONE ]</label>
          <div className="flex flex-col gap-3">
            <div className="flex gap-3">
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onPaste={handlePaste}
                placeholder="PASTE URLS HERE TO ADD THEM AUTOMATICALLY..."
                className="input-field flex-1"
                rows={3}
                style={{ resize: 'none' }}
              />
            </div>
          </div>
        </section>

        {/* Crawler */}
        <section className="glass-panel p-4">
          <label className="section-label">[ CRAWLER MODE ]</label>
          <div className="flex flex-col gap-3">
            <div className="flex gap-3">
              <input
                value={scraperUrl}
                onChange={(e) => setScraperUrl(e.target.value)}
                placeholder="PLAYLIST / PROFILE / SEARCH URL..."
                className="input-field flex-1"
              />
              <button
                onClick={scraping ? handleCancelScrape : handleScrape}
                className={scraping ? 'btn btn-accent' : 'btn'}
              >
                {scraping ? `ABORT (${scraperResults?.count || 0}${scraperResults?.total ? `/${scraperResults.total}` : ''})` : 'CRAWL'}
              </button>
            </div>
          </div>
        </section>
      </div>

      {/* Queue — matches bunkrscrOG QueueList */}
      <section className="glass-panel flex-1 flex flex-col overflow-hidden p-5 gap-3 min-h-0">
        <div className="flex items-center justify-between">
          <label className="section-label mb-0">[ DOWNLOAD QUEUE ]</label>
          <span className="ascii-frame">
            {tasks.length} ITEM{tasks.length !== 1 ? 'S' : ''}
          </span>
        </div>

        {tasks.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <p className="ascii-frame text-center leading-relaxed">
              /// QUEUE IS EMPTY ///<br />
              PASTE A URL TO BEGIN DOWNLOADING
            </p>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {tasks.map((task, i) => (
              <TaskCard
                key={task.url}
                task={task}
                formatProgress={formatProgress}
                index={i}
                onPause={() => sendCommand('pause', { url: task.url })}
                onResume={() => sendCommand('resume', { url: task.url })}
                onCancel={() => sendCommand('cancel', { url: task.url })}
                onRemove={() => sendCommand('remove', { url: task.url })}
                onRetry={() => sendCommand('retry', { url: task.url })}
                onForceDownload={() => sendCommand('force_download', { url: task.url })}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
});

/* ─── Task Card — matches bunkrscrOG QueueItemRow + tordownloader DownloadCard ─── */
const TaskCard = memo(function TaskCard({ task, formatProgress, index, onPause, onResume, onCancel, onRemove, onRetry, onForceDownload }) {
  const statusLabel = STATUS_LABELS[task.status] || task.status.toUpperCase();
  const isDownloading = task.status === 'downloading';
  const isIncomplete = task.status === 'incomplete';
  const isDuplicate = task.status === 'duplicate';
  const hostname = (() => {
    try { return new URL(task.url).hostname.replace('www.', ''); } catch { return ''; }
  })();

  const statusBadgeClass = (() => {
    if (isDownloading) return 'status-scraping';
    if (['completed'].includes(task.status)) return 'status-done';
    if (['failed', 'cancelled'].includes(task.status)) return 'status-failed';
    return 'status-pending';
  })();

  return (
    <div 
      className="queue-item bg-bg-card border border-border p-4 flex flex-col gap-3 card-enter"
      style={{ animationDelay: `${Math.min(index * 40, 240)}ms` }}
    >
      {/* Top: title + actions */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="font-mono text-sm text-text-heading truncate font-bold" title={task.title || task.url}>
            {task.title || 'RESOLVING METADATA...'}
          </p>
          <p className="font-mono text-xs text-text-muted truncate mt-0.5">
            {hostname}
            {task.size && <span className="ml-2">{task.size}</span>}
            {task.width && <span className="ml-2">{task.width}P</span>}
            {task.strategy && <span className="ml-2 text-accent">{task.strategy}</span>}
          </p>
          <div className="flex items-center gap-3 mt-1.5">
            <span className={`status-badge ${statusBadgeClass}`}>
              {isDownloading && <span className="inline-block w-1.5 h-1.5 rounded-none bg-accent pulse-subtle" />}
              {statusLabel}
            </span>
            {isIncomplete && task.existing_file && (
              <span className="ascii-frame text-accent">
                {(task.existing_file.size_ratio * 100).toFixed(0)}% EXISTS
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          {isIncomplete && (
            <button onClick={onForceDownload} className="btn btn-icon" title="Force overwrite incomplete">
              <RefreshCw size={14} />
            </button>
          )}
          {isDuplicate && (
            <button onClick={onForceDownload} className="btn btn-icon" title="Force download">
              <RefreshCw size={14} />
            </button>
          )}
          {['downloading', 'paused', 'queued'].includes(task.status) && (
            <button onClick={onCancel} className="btn btn-danger btn-icon">
              <XCircle size={14} />
            </button>
          )}
          {task.status === 'downloading' && (
            <button onClick={onPause} className="btn btn-icon">
              <Pause size={14} />
            </button>
          )}
          {task.status === 'paused' && (
            <button onClick={onResume} className="btn btn-icon text-success">
              <Play size={14} />
            </button>
          )}
          {task.status === 'failed' && (
            <button onClick={onRetry} className="btn btn-icon">
              <RotateCcw size={14} />
            </button>
          )}
          {['completed', 'cancelled', 'failed', 'duplicate', 'incomplete'].includes(task.status) && (
            <button onClick={onRemove} className="btn btn-danger btn-icon">
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Progress — matches tordownloader DownloadCard */}
      <div className="flex justify-between items-center text-xs font-mono font-bold uppercase tracking-widest">
        <span className={isDownloading ? 'text-accent' : 'text-text-muted'}>
          {formatProgress(task.progress)}
        </span>
        <div className="flex gap-4 text-text-muted" style={{ fontSize: '0.625rem' }}>
          {task.speed && <span>{task.speed}</span>}
          {task.eta && <span className="text-accent">ETA {task.eta}</span>}
        </div>
      </div>
      
      <div className="w-full h-1 bg-bg-deep border border-border overflow-hidden">
        <div className="h-full bg-accent transition-all duration-300" style={{ width: `${(task.progress || 0) * 100}%` }} />
      </div>
    </div>
  );
});

/* ─── Settings Tab — matches bunkrscrOG SettingsModal ─── */
const SettingsTab = memo(function SettingsTab({ settings, sendCommand, handleSelectFolder }) {
  return (
    <div className="h-full max-w-2xl space-y-4">
      <h2 className="font-display font-extrabold text-lg text-accent tracking-tight">
        [ SETTINGS ]
      </h2>

      <div className="glass-panel p-5 space-y-5">
        {/* Destination */}
        <div>
          <label className="section-label">DOWNLOAD PATH</label>
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              value={settings.destination || 'SYSTEM DEFAULT'}
              className="input-field flex-1 font-mono text-xs"
            />
            <button onClick={() => window.electronAPI.openFolder(settings.destination)} className="btn">VIEW</button>
            <button onClick={handleSelectFolder} className="btn btn-accent">CHANGE</button>
          </div>
        </div>

        {/* Max concurrency */}
        <div>
          <label className="section-label">MAX CONCURRENCY</label>
          <div className="flex gap-2">
            {[1, 2, 3, 5, 8].map(n => (
              <button 
                key={n}
                onClick={() => sendCommand('set_max_concurrent', { value: n })}
                className="btn flex-1"
                style={settings.max_concurrent === n ? { borderColor: 'var(--accent)', color: 'var(--accent)' } : {}}
              >
                {n}
              </button>
            ))}
          </div>
        </div>

        {/* Toggles */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-border">
          <label className="flex items-center gap-4 cursor-pointer">
            <div 
              onClick={() => sendCommand('set_auto_delete', { value: !settings.auto_delete })}
              className="relative w-12 h-6 cursor-pointer"
              style={{ background: settings.auto_delete ? 'var(--accent)' : 'var(--border-color)', border: '1px solid var(--border-color)' }}
            >
              <div 
                className="absolute top-0.5 w-5 h-5 transition-transform duration-150"
                style={{ 
                  left: settings.auto_delete ? 'calc(100% - 1.375rem)' : '0.125rem',
                  background: settings.auto_delete ? 'var(--bg-deep)' : 'var(--text-muted)',
                }}
              />
            </div>
            <div>
              <div className="font-mono text-[0.625rem] font-bold uppercase tracking-wider">AUTO FLUSH</div>
              <div className="ascii-frame mt-0.5">REMOVE ON COMPLETION</div>
            </div>
          </label>

          <label className="flex items-center gap-4 cursor-pointer">
            <div 
              onClick={() => sendCommand('set_skip_duplicates', { value: !settings.skip_duplicates })}
              className="relative w-12 h-6 cursor-pointer"
              style={{ background: settings.skip_duplicates ? 'var(--accent)' : 'var(--border-color)', border: '1px solid var(--border-color)' }}
            >
              <div 
                className="absolute top-0.5 w-5 h-5 transition-transform duration-150"
                style={{ 
                  left: settings.skip_duplicates ? 'calc(100% - 1.375rem)' : '0.125rem',
                  background: settings.skip_duplicates ? 'var(--bg-deep)' : 'var(--text-muted)',
                }}
              />
            </div>
            <div>
              <div className="font-mono text-[0.625rem] font-bold uppercase tracking-wider">SKIP DUPLICATES</div>
              <div className="ascii-frame mt-0.5">PREVENT RE-DOWNLOADS</div>
            </div>
          </label>
        </div>
      </div>
    </div>
  );
});

/* ─── Logs Tab — matches tordownloader LogPanel ─── */
const LogsTab = memo(function LogsTab({ logs, setLogs, logsRef }) {
  return (
    <div className="h-full flex flex-col min-h-0">
      <section className="glass-panel flex-1 flex flex-col overflow-hidden p-4">
        <div className="flex justify-between items-center pb-2 border-b border-border/50 mb-3">
          <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider">SYSTEM TELEMETRY</h3>
          <button onClick={() => setLogs([])} className="btn">FLUSH</button>
        </div>
        <div 
          ref={logsRef}
          className="flex-1 overflow-y-auto font-mono text-xs space-y-0.5"
        >
          {logs.map((log, i) => (
            <div key={i} className="flex gap-3 text-text-muted hover:text-text-main transition-colors">
              <span className="opacity-50 shrink-0">{log.time}</span>
              <span>{log.message}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
});

export default App;
