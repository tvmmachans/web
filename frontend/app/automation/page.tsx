"use client"

import { useState, useEffect } from 'react'

const getApiUrl = () => {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  return `https://${url}`
}

const API_BASE_URL = getApiUrl()

interface AutomationStatus {
  running: boolean
  current_cycle: string | null
  status: string
  timestamp: string
}

interface CycleResult {
  cycle_id: string
  started_at: string
  completed_at?: string
  status: string
  phases: {
    discovery?: {
      status: string
      trends_found: number
      calendar_days: number
    }
    creation?: {
      status: string
      videos_created: number
      videos_failed: number
    }
    publishing?: {
      status: string
      published: number
      failed: number
    }
    tracking?: {
      status: string
      note: string
    }
  }
}

export default function AutomationPage() {
  const [status, setStatus] = useState<AutomationStatus | null>(null)
  const [cycleResult, setCycleResult] = useState<CycleResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(7)

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/agent/automation/status`)
      if (!response.ok) throw new Error('Failed to fetch status')
      const data = await response.json()
      setStatus(data)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const startAutomation = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE_URL}/agent/automation/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days }),
      })
      if (!response.ok) throw new Error('Failed to start automation')
      const data = await response.json()
      setCycleResult(data.result)
      await fetchStatus()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const stopAutomation = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/agent/automation/stop`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to stop automation')
      await fetchStatus()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000) // Poll every 5 seconds
    return () => clearInterval(interval)
  }, [])

  return (
    <div style={{ 
      minHeight: '100vh', 
      padding: '2rem',
      maxWidth: '1400px',
      margin: '0 auto',
      background: '#f5f5f5'
    }}>
      <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem', color: '#1a1a1a' }}>
        🤖 Automation Dashboard
      </h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Complete autonomous AI social media management system
      </p>

      {error && (
        <div style={{
          background: '#fee',
          border: '1px solid #fcc',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '2rem',
          color: '#c33'
        }}>
          Error: {error}
        </div>
      )}

      {/* Status Card */}
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>System Status</h2>
        {status ? (
          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
            <div>
              <div style={{ 
                display: 'inline-block',
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                background: status.running ? '#10b981' : '#ef4444',
                marginRight: '8px'
              }} />
              <span style={{ fontWeight: '600' }}>
                {status.running ? 'Running' : 'Idle'}
              </span>
            </div>
            {status.current_cycle && (
              <div>
                <span style={{ color: '#666' }}>Current Cycle: </span>
                <code style={{ background: '#f3f4f6', padding: '4px 8px', borderRadius: '4px' }}>
                  {status.current_cycle}
                </code>
              </div>
            )}
          </div>
        ) : (
          <p>Loading status...</p>
        )}
      </div>

      {/* Controls */}
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Controls</h2>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#666' }}>
              Days to Plan:
            </label>
            <input
              type="number"
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value) || 7)}
              min={1}
              max={30}
              style={{
                padding: '0.5rem',
                border: '1px solid #ddd',
                borderRadius: '4px',
                width: '80px'
              }}
            />
          </div>
          <button
            onClick={startAutomation}
            disabled={loading || status?.running}
            style={{
              padding: '0.75rem 1.5rem',
              background: status?.running ? '#ccc' : '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: '600',
              cursor: status?.running ? 'not-allowed' : 'pointer',
              transition: 'background 0.2s'
            }}
          >
            {loading ? 'Starting...' : '🚀 Start Automation'}
          </button>
          <button
            onClick={stopAutomation}
            disabled={loading || !status?.running}
            style={{
              padding: '0.75rem 1.5rem',
              background: !status?.running ? '#ccc' : '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: '600',
              cursor: !status?.running ? 'not-allowed' : 'pointer',
              transition: 'background 0.2s'
            }}
          >
            🛑 Stop Automation
          </button>
        </div>
      </div>

      {/* Cycle Results */}
      {cycleResult && (
        <div style={{
          background: 'white',
          padding: '2rem',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '2rem'
        }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Latest Cycle Results</h2>
          <div style={{ marginBottom: '1rem' }}>
            <strong>Cycle ID:</strong> <code>{cycleResult.cycle_id}</code>
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <strong>Status:</strong> <span style={{
              color: cycleResult.status === 'completed' ? '#10b981' : '#ef4444',
              fontWeight: '600'
            }}>
              {cycleResult.status}
            </span>
          </div>

          {/* Phases */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
            {cycleResult.phases.discovery && (
              <div style={{
                padding: '1rem',
                background: '#f3f4f6',
                borderRadius: '8px'
              }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>📊 Discovery</h3>
                <div style={{ fontSize: '0.9rem', color: '#666' }}>
                  <div>Trends Found: {cycleResult.phases.discovery.trends_found}</div>
                  <div>Calendar Days: {cycleResult.phases.discovery.calendar_days}</div>
                  <div style={{ marginTop: '0.5rem', color: '#10b981' }}>
                    ✓ {cycleResult.phases.discovery.status}
                  </div>
                </div>
              </div>
            )}

            {cycleResult.phases.creation && (
              <div style={{
                padding: '1rem',
                background: '#f3f4f6',
                borderRadius: '8px'
              }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>🎬 Creation</h3>
                <div style={{ fontSize: '0.9rem', color: '#666' }}>
                  <div>Videos Created: {cycleResult.phases.creation.videos_created}</div>
                  <div>Videos Failed: {cycleResult.phases.creation.videos_failed}</div>
                  <div style={{ marginTop: '0.5rem', color: '#10b981' }}>
                    ✓ {cycleResult.phases.creation.status}
                  </div>
                </div>
              </div>
            )}

            {cycleResult.phases.publishing && (
              <div style={{
                padding: '1rem',
                background: '#f3f4f6',
                borderRadius: '8px'
              }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>📡 Publishing</h3>
                <div style={{ fontSize: '0.9rem', color: '#666' }}>
                  <div>Published: {cycleResult.phases.publishing.published}</div>
                  <div>Failed: {cycleResult.phases.publishing.failed}</div>
                  <div style={{ marginTop: '0.5rem', color: '#10b981' }}>
                    ✓ {cycleResult.phases.publishing.status}
                  </div>
                </div>
              </div>
            )}

            {cycleResult.phases.tracking && (
              <div style={{
                padding: '1rem',
                background: '#f3f4f6',
                borderRadius: '8px'
              }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>📊 Tracking</h3>
                <div style={{ fontSize: '0.9rem', color: '#666' }}>
                  <div>{cycleResult.phases.tracking.note}</div>
                  <div style={{ marginTop: '0.5rem', color: '#10b981' }}>
                    ✓ {cycleResult.phases.tracking.status}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* System Overview */}
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>System Modules</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: '#f3f4f6', borderRadius: '8px' }}>
            <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>🧠 AI Content Brain</div>
            <div style={{ fontSize: '0.9rem', color: '#666' }}>
              Trend detection, idea generation, script writing
            </div>
          </div>
          <div style={{ padding: '1rem', background: '#f3f4f6', borderRadius: '8px' }}>
            <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>🎬 AI Video Factory</div>
            <div style={{ fontSize: '0.9rem', color: '#666' }}>
              Scene generation, voiceover, video editing
            </div>
          </div>
          <div style={{ padding: '1rem', background: '#f3f4f6', borderRadius: '8px' }}>
            <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>📡 Smart Publisher</div>
            <div style={{ fontSize: '0.9rem', color: '#666' }}>
              Platform management, scheduling, optimization
            </div>
          </div>
          <div style={{ padding: '1rem', background: '#f3f4f6', borderRadius: '8px' }}>
            <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>📊 Performance Optimizer</div>
            <div style={{ fontSize: '0.9rem', color: '#666' }}>
              Analytics, ML learning, A/B testing
            </div>
          </div>
        </div>
      </div>

      <a 
        href="/"
        style={{
          display: 'inline-block',
          marginTop: '2rem',
          color: '#667eea',
          textDecoration: 'underline'
        }}
      >
        ← Back to Home
      </a>
    </div>
  )
}

