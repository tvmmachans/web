'use client'

import { useState } from 'react'

export default function SettingsPage() {
  const [personalInfo, setPersonalInfo] = useState({
    name: '',
    email: '',
    company: '',
    phone: '',
    timezone: 'UTC',
  })

  const [apiKeys, setApiKeys] = useState({
    openaiKey: '',
    youtubeClientId: '',
    youtubeClientSecret: '',
    instagramAccessToken: '',
  })

  const [socialAccounts, setSocialAccounts] = useState({
    youtubeChannel: '',
    instagramAccount: '',
    twitterHandle: '',
  })

  const [preferences, setPreferences] = useState({
    language: 'en',
    theme: 'light',
    notifications: true,
    autoPost: false,
  })

  const handlePersonalInfoChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setPersonalInfo({
      ...personalInfo,
      [e.target.name]: e.target.value
    })
  }

  const handleApiKeysChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setApiKeys({
      ...apiKeys,
      [e.target.name]: e.target.value
    })
  }

  const handleSocialAccountsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSocialAccounts({
      ...socialAccounts,
      [e.target.name]: e.target.value
    })
  }

  const handlePreferencesChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const value = e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : e.target.value
    setPreferences({
      ...preferences,
      [e.target.name]: value
    })
  }

  const handleSave = async (section: string) => {
    // TODO: Implement API calls to save settings
    alert(`${section} settings saved!`)
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      padding: '2rem',
      maxWidth: '1200px',
      margin: '0 auto',
      background: '#f5f5f5'
    }}>
      <h1 style={{ fontSize: '2.5rem', marginBottom: '2rem', color: '#333' }}>Settings</h1>

      {/* Personal Information Section */}
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', color: '#667eea' }}>
          Personal Information
        </h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              Full Name *
            </label>
            <input
              type="text"
              name="name"
              value={personalInfo.name}
              onChange={handlePersonalInfoChange}
              placeholder="Enter your full name"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              Email Address *
            </label>
            <input
              type="email"
              name="email"
              value={personalInfo.email}
              onChange={handlePersonalInfoChange}
              placeholder="your.email@example.com"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              Company/Organization
            </label>
            <input
              type="text"
              name="company"
              value={personalInfo.company}
              onChange={handlePersonalInfoChange}
              placeholder="Your company name"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              Phone Number
            </label>
            <input
              type="tel"
              name="phone"
              value={personalInfo.phone}
              onChange={handlePersonalInfoChange}
              placeholder="+1 (555) 123-4567"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              Timezone *
            </label>
            <select
              name="timezone"
              value={personalInfo.timezone}
              onChange={handlePersonalInfoChange}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">Eastern Time (ET)</option>
              <option value="America/Chicago">Central Time (CT)</option>
              <option value="America/Denver">Mountain Time (MT)</option>
              <option value="America/Los_Angeles">Pacific Time (PT)</option>
              <option value="Europe/London">London (GMT)</option>
              <option value="Europe/Paris">Paris (CET)</option>
              <option value="Asia/Kolkata">India (IST)</option>
              <option value="Asia/Tokyo">Tokyo (JST)</option>
            </select>
          </div>
        </div>

        <button
          onClick={() => handleSave('Personal Information')}
          style={{
            marginTop: '1.5rem',
            padding: '0.75rem 2rem',
            background: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '1rem',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          Save Personal Information
        </button>
      </div>

      {/* API Keys Section */}
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', color: '#667eea' }}>
          API Keys & Credentials
        </h2>
        <p style={{ color: '#666', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          Enter your API keys and credentials. These are stored securely and encrypted.
        </p>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              OpenAI API Key *
            </label>
            <input
              type="password"
              name="openaiKey"
              value={apiKeys.openaiKey}
              onChange={handleApiKeysChange}
              placeholder="sk-..."
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              YouTube Client ID
            </label>
            <input
              type="text"
              name="youtubeClientId"
              value={apiKeys.youtubeClientId}
              onChange={handleApiKeysChange}
              placeholder="Your YouTube Client ID"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              YouTube Client Secret
            </label>
            <input
              type="password"
              name="youtubeClientSecret"
              value={apiKeys.youtubeClientSecret}
              onChange={handleApiKeysChange}
              placeholder="Your YouTube Client Secret"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              Instagram Access Token
            </label>
            <input
              type="password"
              name="instagramAccessToken"
              value={apiKeys.instagramAccessToken}
              onChange={handleApiKeysChange}
              placeholder="Your Instagram Access Token"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>
        </div>

        <button
          onClick={() => handleSave('API Keys')}
          style={{
            marginTop: '1.5rem',
            padding: '0.75rem 2rem',
            background: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '1rem',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          Save API Keys
        </button>
      </div>

      {/* Social Media Accounts Section */}
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', color: '#667eea' }}>
          Social Media Accounts
        </h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              YouTube Channel ID
            </label>
            <input
              type="text"
              name="youtubeChannel"
              value={socialAccounts.youtubeChannel}
              onChange={handleSocialAccountsChange}
              placeholder="UCxxxxxxxxxxxxxxxxxxxxx"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              Instagram Account
            </label>
            <input
              type="text"
              name="instagramAccount"
              value={socialAccounts.instagramAccount}
              onChange={handleSocialAccountsChange}
              placeholder="@your_instagram_handle"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              Twitter/X Handle
            </label>
            <input
              type="text"
              name="twitterHandle"
              value={socialAccounts.twitterHandle}
              onChange={handleSocialAccountsChange}
              placeholder="@your_twitter_handle"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>
        </div>

        <button
          onClick={() => handleSave('Social Media Accounts')}
          style={{
            marginTop: '1.5rem',
            padding: '0.75rem 2rem',
            background: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '1rem',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          Save Social Media Accounts
        </button>
      </div>

      {/* Preferences Section */}
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', color: '#667eea' }}>
          Preferences
        </h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              Language
            </label>
            <select
              name="language"
              value={preferences.language}
              onChange={handlePreferencesChange}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="ml">Malayalam</option>
              <option value="hi">Hindi</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#555' }}>
              Theme
            </label>
            <select
              name="theme"
              value={preferences.theme}
              onChange={handlePreferencesChange}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto (System)</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <input
              type="checkbox"
              name="notifications"
              checked={preferences.notifications}
              onChange={handlePreferencesChange}
              style={{ width: '20px', height: '20px', cursor: 'pointer' }}
            />
            <label style={{ fontWeight: '600', color: '#555', cursor: 'pointer' }}>
              Enable Email Notifications
            </label>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <input
              type="checkbox"
              name="autoPost"
              checked={preferences.autoPost}
              onChange={handlePreferencesChange}
              style={{ width: '20px', height: '20px', cursor: 'pointer' }}
            />
            <label style={{ fontWeight: '600', color: '#555', cursor: 'pointer' }}>
              Enable Auto-Posting
            </label>
          </div>
        </div>

        <button
          onClick={() => handleSave('Preferences')}
          style={{
            marginTop: '1.5rem',
            padding: '0.75rem 2rem',
            background: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '1rem',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          Save Preferences
        </button>
      </div>

      {/* Navigation */}
      <div style={{ marginTop: '2rem' }}>
        <a 
          href="/"
          style={{
            display: 'inline-block',
            padding: '0.75rem 1.5rem',
            background: '#f3f4f6',
            color: '#667eea',
            borderRadius: '6px',
            textDecoration: 'none',
            fontWeight: '600'
          }}
        >
          ← Back to Home
        </a>
      </div>
    </div>
  )
}

