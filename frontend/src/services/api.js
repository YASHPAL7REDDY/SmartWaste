import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sw_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('sw_token')
      localStorage.removeItem('sw_role')
      localStorage.removeItem('sw_user_id')
      localStorage.removeItem('sw_name')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export { api }