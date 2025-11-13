import { useRouter } from 'next/navigation'

export interface User {
  id: string
  email: string
  name: string
  avatar?: string
}

export const useAuth = () => {
  const router = useRouter()

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        throw new Error('Login failed')
      }

      const data = await response.json()

      // Store token
      localStorage.setItem('token', data.access_token)
      document.cookie = `token=${data.access_token}; path=/; max-age=86400`

      return data
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    document.cookie = 'token=; path=/; max-age=0'
    router.push('/login')
  }

  const getToken = (): string | null => {
    return localStorage.getItem('token') || getCookie('token')
  }

  const isAuthenticated = (): boolean => {
    return !!getToken()
  }

  return {
    login,
    logout,
    getToken,
    isAuthenticated,
  }
}

function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null
  return null
}

export const requireAuth = () => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token') || getCookie('token')
    if (!token) {
      window.location.href = '/login'
    }
  }
}
