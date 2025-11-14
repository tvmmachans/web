'use client'

import { useEffect, useState } from 'react'

// Get API URL from environment, add protocol if missing
const getApiUrl = () => {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  // If URL doesn't start with http:// or https://, add https://
  if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
    return `https://${url}`
  }
  return url
}

const API_BASE_URL = getApiUrl()

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_BASE_URL}/analytics/`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch analytics')
        return res.json()
      })
      .then(data => {
        setAnalytics(data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return (
    <div style={{ 
      minHeight: '100vh', 
      padding: '2rem',
      maxWidth: '1000px',
      margin: '0 auto'
    }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>Analytics</h1>
      
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        {loading && <p>Loading analytics...</p>}
        {error && (
          <div style={{ color: '#ef4444', marginBottom: '1rem' }}>
            Error: {error}
          </div>
        )}
        {analytics && (
          <div>
            <h2 style={{ marginBottom: '1rem' }}>Analytics Data</h2>
            <pre style={{
              background: '#f3f4f6',
              padding: '1rem',
              borderRadius: '4px',
              overflow: 'auto'
            }}>
              {JSON.stringify(analytics, null, 2)}
            </pre>
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

