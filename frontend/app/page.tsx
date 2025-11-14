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

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const [apiConnected, setApiConnected] = useState(false)

  useEffect(() => {
    // Check backend health
    fetch(`${API_BASE_URL}/health`)
      .then(res => res.json())
      .then(data => {
        setHealthStatus(data.status || 'ok')
        setApiConnected(true)
      })
      .catch(err => {
        setHealthStatus('disconnected')
        setApiConnected(false)
        console.error('Backend connection error:', err)
      })
  }, [])

  return (
    <main style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '3rem',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        maxWidth: '600px',
        width: '100%'
      }}>
        <h1 style={{
          fontSize: '2.5rem',
          fontWeight: 'bold',
          marginBottom: '1rem',
          color: '#333',
          textAlign: 'center'
        }}>
          AI Social Media Manager
        </h1>
        
        <p style={{
          fontSize: '1.1rem',
          color: '#666',
          textAlign: 'center',
          marginBottom: '2rem'
        }}>
          Automated social media management with AI
        </p>

        <div style={{
          background: apiConnected ? '#10b981' : '#ef4444',
          color: 'white',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '2rem',
          textAlign: 'center'
        }}>
          <strong>Backend Status:</strong> {healthStatus}
          {apiConnected ? ' ✓' : ' ✗'}
        </div>

        <nav style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem'
        }}>
          <a 
            href="/upload"
            style={{
              padding: '1rem',
              background: '#667eea',
              color: 'white',
              borderRadius: '8px',
              textAlign: 'center',
              fontWeight: '600',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = '#5568d3'}
            onMouseLeave={(e) => e.currentTarget.style.background = '#667eea'}
          >
            Upload Content
          </a>
          
          <a 
            href="/schedule"
            style={{
              padding: '1rem',
              background: '#764ba2',
              color: 'white',
              borderRadius: '8px',
              textAlign: 'center',
              fontWeight: '600',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = '#653a8a'}
            onMouseLeave={(e) => e.currentTarget.style.background = '#764ba2'}
          >
            Schedule Posts
          </a>
          
          <a 
            href="/analytics"
            style={{
              padding: '1rem',
              background: '#10b981',
              color: 'white',
              borderRadius: '8px',
              textAlign: 'center',
              fontWeight: '600',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = '#059669'}
            onMouseLeave={(e) => e.currentTarget.style.background = '#10b981'}
          >
            View Analytics
          </a>
          
          <a 
            href="/settings"
            style={{
              padding: '1rem',
              background: '#f59e0b',
              color: 'white',
              borderRadius: '8px',
              textAlign: 'center',
              fontWeight: '600',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = '#d97706'}
            onMouseLeave={(e) => e.currentTarget.style.background = '#f59e0b'}
          >
            Settings & Configuration
          </a>
        </nav>

        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          background: '#f3f4f6',
          borderRadius: '8px',
          fontSize: '0.9rem',
          color: '#666'
        }}>
          <p><strong>API Endpoint:</strong> {API_BASE_URL}</p>
          <p style={{ marginTop: '0.5rem' }}>
            <strong>Status:</strong> {apiConnected ? 'Connected' : 'Not Connected'}
          </p>
        </div>
      </div>
    </main>
  )
}

