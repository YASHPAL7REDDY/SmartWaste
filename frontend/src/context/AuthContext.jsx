import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [role, setRole] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(() => localStorage.getItem('sw_token'))

  const fetchUser = useCallback(async () => {
    if (!token) {
      setLoading(false)
      return
    }
    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
    } catch (error) {
      logout()
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  function getUserIdFromToken(token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.sub
    } catch {
      return null
    }
  }

  const login = async (email, password, roleParam) => {
    // Determine the correct login endpoint based on role
    let endpoint = '/auth/login'
    let payload = { email, password, role: roleParam }
    
    if (roleParam === 'collector') {
      endpoint = '/collector/login'
      payload = { email_or_mobile: email, password }
    } else if (roleParam === 'admin') {
      endpoint = '/auth/admin-login'
      payload = { email, password }
    }
    
    const response = await api.post(endpoint, payload)
    const data = response.data
    const access_token = data.access_token
    const responseRole = data.role || roleParam
    const userData = data.user || { id: data.user_id, name: data.name }
    
    localStorage.setItem('sw_token', access_token)
    localStorage.setItem('sw_role', responseRole)
    localStorage.setItem('sw_user_id', userData.id)
    localStorage.setItem('sw_name', userData.name)
    setToken(access_token)
    setRole(responseRole)
    await fetchUser()
    return data
  }

  const logout = () => {
    localStorage.removeItem('sw_token')
    localStorage.removeItem('sw_role')
    localStorage.removeItem('sw_user_id')
    localStorage.removeItem('sw_name')
    setToken(null)
    setRole(null)
    setUser(null)
  }

  const register = async (userData) => {
    const response = await api.post('/auth/register', userData)
    // After registration, we need to log in to get a token
    const loginResponse = await api.post('/auth/login', { email: userData.email, password: userData.password, role: 'user' })
    const data = loginResponse.data
    const access_token = data.access_token
    const responseRole = data.role || 'user'
    const userDataResponse = data.user || { id: data.user_id, name: data.name }
    
    localStorage.setItem('sw_token', access_token)
    localStorage.setItem('sw_role', responseRole)
    localStorage.setItem('sw_user_id', userDataResponse.id)
    localStorage.setItem('sw_name', userDataResponse.name)
    setToken(access_token)
    setRole(responseRole)
    await fetchUser()
    return loginResponse.data
  }

  const value = {
    user,
    role,
    token,
    loading,
    login,
    logout,
    register,
    isAuthenticated: !!token,
    isUser: role === 'user',
    isCollector: role === 'collector',
    isAdmin: role === 'admin',
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}