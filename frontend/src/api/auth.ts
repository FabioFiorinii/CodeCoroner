import apiClient from './client'

export async function login(email: string, password: string) {
  const { data } = await apiClient.post('/auth/login/', { email, password })
  localStorage.setItem('access_token', data.access)
  localStorage.setItem('refresh_token', data.refresh)
  return data
}

export async function register(email: string, username: string, password: string) {
  const { data } = await apiClient.post('/auth/register/', { email, username, password })
  return data
}

export async function getMe() {
  const { data } = await apiClient.get('/auth/me/')
  return data
}

export function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  window.location.href = '/login'
}
