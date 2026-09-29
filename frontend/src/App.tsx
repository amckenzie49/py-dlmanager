import { useEffect, useState, type FormEvent } from 'react'
import { ArrowDownToLine, ArrowUpRight, Check, CircleAlert, Clock3, FileDown, Link2, LoaderCircle, Plus, RefreshCw } from 'lucide-react'
import { Link, NavLink, Route, Routes, useNavigate } from 'react-router-dom'

type SourceType = 'url' | 'info_hash' | 'magnet_link'

type Download = {
  id: string
  url: string | null
  info_hash: string | null
  magnet_link: string | null
  filename: string | null
  status: string
  error_message: string | null
  created_at: string
  file_url: string | null
}

const sourceOptions: { value: SourceType; label: string; placeholder: string; description: string }[] = [
  { value: 'url', label: 'Direct link', placeholder: 'https://example.com/file.zip', description: 'HTTP or HTTPS URL' },
  { value: 'magnet_link', label: 'Magnet link', placeholder: 'magnet:?xt=urn:btih:…', description: 'Torrent magnet URI' },
  { value: 'info_hash', label: 'Info hash', placeholder: 'Paste a torrent info hash', description: 'Torrent identifier' },
]

async function fetchDownloads(): Promise<Download[]> {
  const response = await fetch('/downloads')
  if (!response.ok) throw new Error(`Could not load downloads (${response.status}).`)
  const data: { downloads: Download[] } = await response.json()
  return data.downloads
}

function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/" aria-label="Download Manager home">
          <span className="brand-mark"><ArrowDownToLine size={19} strokeWidth={2.4} /></span>
          <span>downlink<span className="brand-period">.</span></span>
        </Link>
        <nav className="main-nav" aria-label="Main navigation">
          <NavLink end to="/">Add download</NavLink>
          <NavLink to="/status">Download status</NavLink>
        </nav>
        <span className="service-indicator"><i /> API proxy</span>
      </header>

      <main className="page-content">
        <Routes>
          <Route path="/" element={<AddDownloadPage />} />
          <Route path="/status" element={<DownloadStatusPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <footer className="footer"><span>DOWNLOAD MANAGER</span><span>Private queue <i /></span></footer>
    </div>
  )
}

function AddDownloadPage() {
  const [sourceType, setSourceType] = useState<SourceType>('url')
  const [source, setSource] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const selectedOption = sourceOptions.find((option) => option.value === sourceType)!

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError('')

    try {
      const response = await fetch('/downloads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [sourceType]: source.trim() }),
      })
      if (!response.ok) {
        const detail = await response.json().catch(() => null)
        throw new Error(detail?.detail ?? detail?.error ?? `Could not queue download (${response.status}).`)
      }
      navigate('/status')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="form-page">
      <div className="eyebrow"><span>01</span> NEW TRANSFER</div>
      <h1>Send something<br /><em>your way.</em></h1>
      <p className="page-intro">Drop in a source and we’ll take it from here.</p>

      <form className="queue-form" onSubmit={handleSubmit}>
        <fieldset className="source-fieldset">
          <legend>Choose a source</legend>
          <div className="source-options">
            {sourceOptions.map((option) => (
              <label className={`source-option ${sourceType === option.value ? 'selected' : ''}`} key={option.value}>
                <input
                  type="radio"
                  name="sourceType"
                  value={option.value}
                  checked={sourceType === option.value}
                  onChange={() => setSourceType(option.value)}
                />
                <span className="option-icon"><Link2 size={17} /></span>
                <span className="option-copy"><strong>{option.label}</strong><small>{option.description}</small></span>
                <span className="radio-indicator" />
              </label>
            ))}
          </div>
        </fieldset>

        <label className="input-label" htmlFor="download-source">{selectedOption.label}</label>
        <div className="input-wrap">
          <input
            autoComplete="off"
            id="download-source"
            name={sourceType}
            placeholder={selectedOption.placeholder}
            required
            type="text"
            value={source}
            onChange={(event) => setSource(event.target.value)}
          />
          <span className="input-glyph"><ArrowUpRight size={17} /></span>
        </div>
        <p className="field-note">One source per download. You can queue more at any time.</p>
        {error && <p className="form-error" role="alert"><CircleAlert size={16} />{error}</p>}
        <button className="primary-button" disabled={submitting} type="submit">
          {submitting ? <LoaderCircle className="spin" size={17} /> : <Plus size={18} />}
          {submitting ? 'Adding to queue' : 'Add to queue'}
          {!submitting && <span className="button-hint">↵</span>}
        </button>
      </form>
      <div className="form-footnote"><span className="footnote-line" />Downloads are stored in your private queue</div>
    </section>
  )
}

function DownloadStatusPage() {
  const [downloads, setDownloads] = useState<Download[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  async function loadDownloads(isRefresh = false) {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError('')
    try {
      setDownloads(await fetchDownloads())
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Could not load downloads.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => { void loadDownloads() }, [])

  return (
    <section className="status-page">
      <div className="status-heading">
        <div>
          <div className="eyebrow"><span>02</span> YOUR TRANSFERS</div>
          <h1>Download <em>status.</em></h1>
          <p className="page-intro">Every file in your queue, all in one place.</p>
        </div>
        <div className="heading-actions">
          <button aria-label="Refresh downloads" className="icon-button" disabled={refreshing || loading} onClick={() => void loadDownloads(true)} title="Refresh downloads" type="button">
            <RefreshCw className={refreshing ? 'spin' : ''} size={17} />
          </button>
          <Link className="small-add-button" to="/"><Plus size={16} /> Add download</Link>
        </div>
      </div>

      <div className="queue-summary">
        <span><b>{downloads.length.toString().padStart(2, '0')}</b> IN QUEUE</span>
        <span><i className="summary-dot" />Live from API</span>
      </div>

      <div className="download-list" aria-live="polite">
        {loading && <div className="list-message"><LoaderCircle className="spin" size={20} />Loading your downloads…</div>}
        {!loading && error && <div className="list-message error-message"><CircleAlert size={19} /><span>{error}</span><button onClick={() => void loadDownloads()} type="button">Try again</button></div>}
        {!loading && !error && downloads.length === 0 && (
          <div className="empty-state">
            <span className="empty-icon"><FileDown size={23} /></span>
            <h2>Nothing in the queue yet</h2>
            <p>Add a link, magnet, or info hash to get started.</p>
            <Link to="/">Add your first download <ArrowUpRight size={15} /></Link>
          </div>
        )}
        {!loading && !error && downloads.map((download, index) => (
          <DownloadRow download={download} index={index} key={download.id} />
        ))}
      </div>
    </section>
  )
}

function DownloadRow({ download, index }: { download: Download; index: number }) {
  const source = download.filename || download.url || download.magnet_link || download.info_hash || 'Untitled download'
  const displaySource = source.startsWith('magnet:') ? 'Magnet link' : source
  const date = new Date(download.created_at)
  const status = download.status.toLowerCase()
  const sourceKind = download.url ? 'URL' : download.magnet_link ? 'MAGNET' : download.info_hash ? 'INFO HASH' : 'DOWNLOAD'

  return (
    <article className="download-row" style={{ animationDelay: `${Math.min(index * 45, 360)}ms` }}>
      <div className={`download-icon status-${status}`}>
        {status === 'completed' ? <Check size={19} /> : status === 'failed' ? <CircleAlert size={19} /> : status === 'pending' ? <Clock3 size={19} /> : <ArrowDownToLine size={19} />}
      </div>
      <div className="download-details">
        <div className="download-title-line"><h2 title={source}>{displaySource}</h2><span className="source-tag">{sourceKind}</span></div>
        <p>{date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}{download.error_message ? ` · ${download.error_message}` : ''}</p>
      </div>
      <div className="download-end">
        <span className={`status-label status-text-${status}`}><i />{download.status}</span>
        {download.file_url && <a aria-label="Open downloaded file" className="file-link" href={download.file_url} rel="noreferrer" target="_blank" title="Open downloaded file"><ArrowUpRight size={17} /></a>}
      </div>
    </article>
  )
}

function NotFoundPage() {
  return <section className="not-found"><div className="eyebrow">NOT FOUND</div><h1>This page<br /><em>isn’t here.</em></h1><Link className="small-add-button" to="/">Back to queue</Link></section>
}

export default App