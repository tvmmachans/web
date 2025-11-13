import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token') || getCookie('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      document.cookie = 'token=; path=/; max-age=0'
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null
  return null
}

// API endpoints
export const apiEndpoints = {
  // Analytics
  analytics: '/analytics',
  advancedAnalytics: '/analytics/advanced',

  // Upload
  uploadVideo: '/upload/video',

  // Schedule
  schedulePost: '/schedule/post',
  getScheduledPosts: '/schedule/posts',

  // Generate
  generateCaption: '/generate/caption',
  generateHashtags: '/generate/hashtags',

  // Insights
  insights: '/insights',

  // Auth
  login: '/auth/login',
  register: '/auth/register',
  refresh: '/auth/refresh',
}

export default api
