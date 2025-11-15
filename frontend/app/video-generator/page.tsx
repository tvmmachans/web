"use client"

import { useState } from 'react'

const getApiUrl = () => {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  return `https://${url}`
}

const API_BASE_URL = getApiUrl()

export default function VideoGeneratorPage() {
  const [trendId, setTrendId] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const generateVideo = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`${API_BASE_URL}/ai/generate-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trend_id: trendId ? parseInt(trendId) : null,
        }),
      })

      if (!response.ok) throw new Error('Video generation failed')
      
      const data = await response.json()
      setResult(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      padding: '2rem',
      maxWidth: '1200px',
      margin: '0 auto',
      background: '#f5f5f5'
    }}>
      <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem', color: '#1a1a1a' }}>
        🎬 AI Video Generator
      </h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Generate complete videos from trends automatically
      </p>

      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Generate Video</h2>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', color: '#666' }}>
            Trend ID (optional):
          </label>
          <input
            type="text"
            value={trendId}
            onChange={(e) => setTrendId(e.target.value)}
            placeholder="Enter trend ID or leave empty for auto-discovery"
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '8px',
              fontSize: '1rem'
            }}
          />
        </div>

        <button
          onClick={generateVideo}
          disabled={loading}
          style={{
            padding: '0.75rem 2rem',
            background: loading ? '#ccc' : '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontWeight: '600',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '1rem'
          }}
        >
          {loading ? 'Generating...' : '🚀 Generate Video'}
        </button>

        {error && (
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            background: '#fee',
            border: '1px solid #fcc',
            borderRadius: '8px',
            color: '#c33'
          }}>
            Error: {error}
          </div>
        )}

        {result && (
          <div style={{
            marginTop: '2rem',
            padding: '1.5rem',
            background: '#f3f4f6',
            borderRadius: '8px'
          }}>
            <h3 style={{ marginBottom: '1rem' }}>Generation Result</h3>
            <div style={{ fontSize: '0.9rem', color: '#666' }}>
              <div><strong>Status:</strong> {result.status}</div>
              {result.video && (
                <>
                  <div style={{ marginTop: '0.5rem' }}>
                    <strong>Video URL:</strong> {result.video.video_url || 'Generating...'}
                  </div>
                  <div style={{ marginTop: '0.5rem' }}>
                    <strong>Thumbnail:</strong> {result.video.thumbnail_url || 'Generating...'}
                  </div>
                  <div style={{ marginTop: '0.5rem' }}>
                    <strong>Duration:</strong> {result.video.duration || 'N/A'} seconds
                  </div>
                </>
              )}
            </div>
          </div>
        )}
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

