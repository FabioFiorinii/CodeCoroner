import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from './authStore'

vi.mock('../lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import { api } from '../lib/api'

const mockedGet = vi.mocked(api.get)
const mockedPost = vi.mocked(api.post)

const USER = {
  id: 'u1',
  email: 'a@t.com',
  username: 'alice',
  is_active: true,
  is_superuser: false,
  date_joined: '2026-01-01T00:00:00Z',
  groups: [],
}

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    })
  })

  it('login stores tokens and the user', async () => {
    mockedPost.mockResolvedValue({
      access: 'access-tok',
      refresh: 'refresh-tok',
      user: USER,
    })

    await useAuthStore.getState().login('a@t.com', 'secret')

    expect(localStorage.getItem('access_token')).toBe('access-tok')
    expect(localStorage.getItem('refresh_token')).toBe('refresh-tok')
    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(true)
    expect(state.user).toEqual(USER)
    expect(state.error).toBeNull()
  })

  it('login failure sets the error and rethrows', async () => {
    mockedPost.mockRejectedValue(new Error('Invalid credentials'))

    await expect(useAuthStore.getState().login('a@t.com', 'bad')).rejects.toThrow(
      'Invalid credentials',
    )
    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.error).toBe('Invalid credentials')
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('logout clears tokens and auth state', async () => {
    localStorage.setItem('access_token', 'x')
    localStorage.setItem('refresh_token', 'y')
    useAuthStore.setState({ user: USER, isAuthenticated: true })

    useAuthStore.getState().logout()

    expect(localStorage.getItem('access_token')).toBeNull()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('fetchMe without a token resets auth state without calling the API', async () => {
    useAuthStore.setState({ user: USER, isAuthenticated: true })

    await useAuthStore.getState().fetchMe()

    expect(mockedGet).not.toHaveBeenCalled()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('fetchMe with a valid token loads the user', async () => {
    localStorage.setItem('access_token', 'valid-tok')
    mockedGet.mockResolvedValue(USER)

    await useAuthStore.getState().fetchMe()

    expect(mockedGet).toHaveBeenCalledWith('/auth/me/')
    expect(useAuthStore.getState().user).toEqual(USER)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('fetchMe clears the token when the request fails', async () => {
    localStorage.setItem('access_token', 'expired-tok')
    mockedGet.mockRejectedValue(new Error('unauthorized'))

    await useAuthStore.getState().fetchMe()

    expect(localStorage.getItem('access_token')).toBeNull()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })
})