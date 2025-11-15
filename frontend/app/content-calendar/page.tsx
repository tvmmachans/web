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

interface CalendarDay {
  date: string
  day_of_week: string
  trend?: {
    title: string
    platform: string
    viral_score: number
  }
  content_idea?: any
  script?: any
  scheduled_time: string
  status: string
}

export default function ContentCalendarPage() {
  const [calendar, setCalendar] = useState<CalendarDay[]>([])
  const [loading, setLoading] = useState(false)
  const [days, setDays] = useState(7)
  const [error, setError] = useState<string | null>(null)

  const fetchCalendar = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`${API_BASE_URL}/advanced/content/calendar?days=${days}`)
      if (!response.ok) throw new Error('Failed to fetch calendar')
      
      const data = await response.json()
      setCalendar(data.calendar?.days || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCalendar()
  }, [days])

  return (
    <div style={{ 
      minHeight: '100vh', 
      padding: '2rem',
      maxWidth: '1400px',
      margin: '0 auto',
      background: '#f5f5f5'
    }}>
      <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem', color: '#1a1a1a' }}>
        📅 AI Content Calendar
      </h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        AI-planned content schedule for the next {days} days
      </p>

      <div style={{ marginBottom: '2rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <label style={{ color: '#666' }}>Days to show:</label>
        <select
          value={days}
          onChange={(e) => setDays(parseInt(e.target.value))}
          style={{
            padding: '0.5rem',
            border: '1px solid #ddd',
            borderRadius: '4px'
          }}
        >
          <option value={7}>7 days</option>
          <option value={14}>14 days</option>
          <option value={30}>30 days</option>
        </select>
        <button
          onClick={fetchCalendar}
          style={{
            padding: '0.5rem 1rem',
            background: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Refresh
        </button>
      </div>

      {error && (
        <div style={{
          padding: '1rem',
          background: '#fee',
          border: '1px solid #fcc',
          borderRadius: '8px',
          color: '#c33',
          marginBottom: '2rem'
        }}>
          Error: {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>Loading calendar...</div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: '1.5rem'
        }}>
          {calendar.map((day, index) => (
            <div
              key={index}
              style={{
                background: 'white',
                padding: '1.5rem',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}
            >
              <div style={{ 
                fontSize: '1.2rem', 
                fontWeight: '600', 
                marginBottom: '0.5rem',
                color: '#667eea'
              }}>
                {day.day_of_week}
              </div>
              <div style={{ color: '#666', marginBottom: '1rem', fontSize: '0.9rem' }}>
                {new Date(day.date).toLocaleDateString()}
              </div>

              {day.trend && (
                <div style={{
                  padding: '1rem',
                  background: '#f3f4f6',
                  borderRadius: '8px',
                  marginBottom: '1rem'
                }}>
                  <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
                    📊 {day.trend.title}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>
                    Platform: {day.trend.platform}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>
                    Viral Score: {(day.trend.viral_score * 100).toFixed(0)}%
                  </div>
                </div>
              )}

              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>
                <strong>Scheduled:</strong> {new Date(day.scheduled_time).toLocaleTimeString()}
              </div>
              <div style={{
                display: 'inline-block',
                padding: '0.25rem 0.75rem',
                background: day.status === 'planned' ? '#10b981' : '#f59e0b',
                color: 'white',
                borderRadius: '4px',
                fontSize: '0.85rem',
                fontWeight: '600'
              }}>
                {day.status}
              </div>
            </div>
          ))}
        </div>
      )}

      {calendar.length === 0 && !loading && (
        <div style={{
          textAlign: 'center',
          padding: '3rem',
          background: 'white',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <p style={{ color: '#666' }}>No calendar entries found. Generate content to see the calendar.</p>
        </div>
      )}

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

