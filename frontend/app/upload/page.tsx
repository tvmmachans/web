'use client'

export default function UploadPage() {
  return (
    <div style={{ 
      minHeight: '100vh', 
      padding: '2rem',
      maxWidth: '800px',
      margin: '0 auto'
    }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>Upload Content</h1>
      
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <p style={{ marginBottom: '1rem', color: '#666' }}>
          Upload your video content for AI-powered processing and scheduling.
        </p>
        <p style={{ color: '#999', fontStyle: 'italic' }}>
          Upload functionality coming soon...
        </p>
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

