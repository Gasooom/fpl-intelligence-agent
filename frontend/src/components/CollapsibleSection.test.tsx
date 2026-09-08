import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { CollapsibleSection } from './CollapsibleSection'

describe('CollapsibleSection', () => {
  it('renders its label and content inside a native disclosure', () => {
    render(
      <CollapsibleSection summary="Full reasoning">
        <p>Real supporting detail.</p>
      </CollapsibleSection>,
    )

    expect(screen.getByText('Full reasoning')).toBeInTheDocument()
    expect(screen.getByText('Real supporting detail.')).toBeInTheDocument()
  })

  it('suppresses the browser default summary marker', () => {
    // A <summary> is display:list-item, and the CSS reset only clears
    // list styling from ul/ol/menu - without list-none the browser
    // draws its own marker beside the label, which reads as a stray
    // empty bullet on the dashboard.
    render(
      <CollapsibleSection summary="View all evidence">
        <p>Detail.</p>
      </CollapsibleSection>,
    )

    const summary = screen.getByText('View all evidence')
    expect(summary.tagName).toBe('SUMMARY')
    expect(summary.className).toContain('list-none')
    expect(summary.className).toContain('[&::-webkit-details-marker]:hidden')
  })

  it('keeps the disclosure collapsed until opened, without hiding its label', () => {
    render(
      <CollapsibleSection summary="Show all 8">
        <p>Hidden until expanded.</p>
      </CollapsibleSection>,
    )

    const summary = screen.getByText('Show all 8')
    expect(summary.closest('details')).not.toHaveAttribute('open')
    expect(summary).toHaveTextContent('Show all 8')
  })
})
