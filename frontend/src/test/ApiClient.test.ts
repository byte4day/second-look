import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  api,
  INVALID_INPUT_MESSAGE,
  OFFLINE_MESSAGE,
  setApiErrorListener,
} from '../api/client.ts'

afterEach(() => {
  vi.unstubAllGlobals()
  setApiErrorListener(() => undefined)
})

describe('api client errors', () => {
  it('shows a calm offline banner when the network is down', async () => {
    const banner = vi.fn()
    setApiErrorListener(banner)
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))))

    await expect(api.listScenarios()).rejects.toThrow(OFFLINE_MESSAGE)
    expect(banner).toHaveBeenCalledWith(OFFLINE_MESSAGE)
  })

  it('turns a FastAPI 422 list detail into a plain message', async () => {
    const banner = vi.fn()
    setApiErrorListener(banner)
    const body = JSON.stringify({
      detail: [{ loc: ['body', 'text'], msg: 'String should have at most 200 characters' }],
    })
    vi.stubGlobal('fetch', vi.fn(async () => new Response(body, { status: 422 })))

    // createReport is silent: the page shows its own error, so no global banner.
    await expect(api.createReport('phone', 'england', 'x'.repeat(201))).rejects.toThrow(
      INVALID_INPUT_MESSAGE,
    )
    expect(banner).not.toHaveBeenCalled()

    await expect(api.listScenarios()).rejects.toThrow(INVALID_INPUT_MESSAGE)
    expect(banner).toHaveBeenCalledWith(INVALID_INPUT_MESSAGE)
  })
})
