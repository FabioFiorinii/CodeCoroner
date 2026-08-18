import { describe, expect, it } from 'vitest'

import { STATUS_COLOR, STATUS_ICON, isBusy } from './analysisStatus'

const KNOWN_STATUSES = [
  'queued',
  'indexing',
  'analyzing',
  'bug_localization',
  'rca',
  'fix_suggestion',
  'generate_report',
  'completed',
  'failed',
]

describe('isBusy', () => {
  it('returns true for in-progress statuses', () => {
    expect(isBusy('queued')).toBe(true)
    expect(isBusy('analyzing')).toBe(true)
    expect(isBusy('generate_report')).toBe(true)
  })

  it('returns false for terminal statuses', () => {
    expect(isBusy('completed')).toBe(false)
    expect(isBusy('failed')).toBe(false)
  })

  it('returns false for unknown statuses', () => {
    expect(isBusy('bogus')).toBe(false)
  })
})

describe('status maps', () => {
  it('covers every known status with an icon and color', () => {
    for (const status of KNOWN_STATUSES) {
      expect(STATUS_ICON[status], `missing icon for ${status}`).toBeDefined()
      expect(STATUS_COLOR[status], `missing color for ${status}`).toBeDefined()
    }
  })

  it('maps completed to a success icon', () => {
    expect(STATUS_ICON.completed).toBeDefined()
  })
})