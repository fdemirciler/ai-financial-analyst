import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for logging
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data)
    return Promise.reject(error)
  }
)

export const uploadFile = async (sessionId, file) => {
  const formData = new FormData()
  formData.append('session_id', sessionId)
  formData.append('file', file)

  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export const sendMessage = async (sessionId, message) => {
  const response = await api.post('/chat', {
    session_id: sessionId,
    message: message,
  })

  return response.data
}

export const getSessionInfo = async (sessionId) => {
  const response = await api.get(`/session/${sessionId}`)
  return response.data
}

export default api