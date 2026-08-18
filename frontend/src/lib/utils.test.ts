import { describe, expect, it } from 'vitest'

import { cn } from './utils'

describe('cn', () => {
  it('merges conditional class names', () => {
    const include = true
    const exclude = false
    expect(cn('a', include && 'b', exclude && 'c')).toBe('a b')
  })

  it('resolves tailwind-merge conflicts with the last class winning', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4')
  })

  it('handles empty inputs', () => {
    expect(cn()).toBe('')
  })
})