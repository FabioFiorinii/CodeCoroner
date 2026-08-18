import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Input } from './Input'

describe('Input', () => {
  it('renders a label linked to the input', () => {
    render(<Input label="Email" />)
    const input = screen.getByLabelText('Email')
    expect(input).toBeDefined()
  })

  it('uses a label-derived id when no id is given', () => {
    render(<Input label="Project Name" />)
    expect(screen.getByLabelText('Project Name').getAttribute('id')).toBe('project-name')
  })

  it('renders an error message', () => {
    render(<Input label="Email" error="Required field" />)
    expect(screen.getByText('Required field')).toBeDefined()
  })

  it('renders without a label', () => {
    render(<Input placeholder="Search…" />)
    expect(screen.getByPlaceholderText('Search…')).toBeDefined()
  })
})