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

export default function PlatformManagerPage() {
  const [contentId, setContentId] = useState<string>('')
  const [platforms, setPlatforms] = useState<string[]>(['youtube', 'instagram'])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const togglePlatform = (platform: string) => {
    if (platforms.includes(platform)) {
      setPlatforms(platforms.filter(p => p !== platform))
    } else {
      setPlatforms([...platforms, platform])
    }
  }

  const bulkPublish = async () => {
    if (!contentId) {
      setError('Content ID is required')
      return
    }

    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`${API_BASE_URL}/advanced/platforms/bulk-publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content_id: parseInt(contentId),
          platforms: platforms,
        }),
      })

      if (!response.ok) throw new Error('Bulk publish failed')
      
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
        📡 Platform Manager
      </h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Manage and publish content across multiple platforms
      </p>

      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Bulk Publish</h2>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', color: '#666' }}>
            Content ID:
          </label>
          <input
            type="text"
            value={contentId}
            onChange={(e) => setContentId(e.target.value)}
            placeholder="Enter content ID"
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '8px',
              fontSize: '1rem'
            }}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', color: '#666' }}>
            Select Platforms:
          </label>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {['youtube', 'instagram', 'twitter'].map(platform => (
              <label
                key={platform}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 1rem',
                  background: platforms.includes(platform) ? '#667eea' : '#f3f4f6',
                  color: platforms.includes(platform) ? 'white' : '#666',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: platforms.includes(platform) ? '600' : '400'
                }}
              >
                <input
                  type="checkbox"
                  checked={platforms.includes(platform)}
                  onChange={() => togglePlatform(platform)}
                  style={{ cursor: 'pointer' }}
                />
                {platform.charAt(0).toUpperCase() + platform.slice(1)}
              </label>
            ))}
          </div>
        </div>

        <button
          onClick={bulkPublish}
          disabled={loading || !contentId || platforms.length === 0}
          style={{
            padding: '0.75rem 2rem',
            background: (loading || !contentId || platforms.length === 0) ? '#ccc' : '#10b981',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontWeight: '600',
            cursor: (loading || !contentId || platforms.length === 0) ? 'not-allowed' : 'pointer',
            fontSize: '1rem'
          }}
        >
          {loading ? 'Publishing...' : '🚀 Publish to Selected Platforms'}
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
            <h3 style={{ marginBottom: '1rem' }}>Publishing Results</h3>
            <div style={{ fontSize: '0.9rem', color: '#666' }}>
              <div><strong>Posted to:</strong> {result.publish_result?.posted_platforms?.join(', ') || 'None'}</div>
              {result.publish_result?.failed_platforms?.length > 0 && (
                <div style={{ marginTop: '0.5rem', color: '#c33' }}>
                  <strong>Failed:</strong> {result.publish_result.failed_platforms.join(', ')}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Platform Status</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          {['youtube', 'instagram', 'twitter'].map(platform => (
            <div
              key={platform}
              style={{
                padding: '1rem',
                background: '#f3f4f6',
                borderRadius: '8px',
                textAlign: 'center'
              }}
            >
              <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
                {platform.charAt(0).toUpperCase() + platform.slice(1)}
              </div>
              <div style={{
                display: 'inline-block',
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                background: '#10b981',
                marginRight: '8px'
              }} />
              <span style={{ fontSize: '0.9rem', color: '#666' }}>Connected</span>
            </div>
          ))}
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

