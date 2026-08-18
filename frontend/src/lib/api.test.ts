import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, api } from './api'

describe('api client', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('performs a GET with the base path and bearer token', async () => {
    localStorage.setItem('access_token', 'tok-123')
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: '1' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const data = await api.get<{ id: string }>('/repositories/')

    expect(data).toEqual({ id: '1' })
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/v1/repositories/')
    expect(init.headers.Authorization).toBe('Bearer tok-123')
    expect(init.headers['Content-Type']).toBe('application/json')
  })

  it('sends a JSON body on POST', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({ id: 'x' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await api.post('/analyses/', { title: 't' })

    const [, init] = fetchMock.mock.calls[0]
    expect(init.method).toBe('POST')
    expect(init.body).toBe('{"title":"t"}')
  })

  it('throws ApiError with the server detail message on failure', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Invalid credentials' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const error = await api.get('/auth/me/').catch((e) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 401, message: 'Invalid credentials' })
  })

  it('falls back to the first field value when no detail is present', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ email: ['Enter a valid email.'] }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const error = (await api.post('/auth/register/', {}).catch((e) => e)) as Error

    expect(error.message).toBe('Enter a valid email.')
  })

  it('returns undefined for 204 responses', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 204 })
    vi.stubGlobal('fetch', fetchMock)

    const data = await api.delete('/repositories/1/')

    expect(data).toBeUndefined()
  })
})