import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ReasonList } from './ReasonList'

/** Every rendered bullet must carry visible text. This is the guard
 * that stopped the deployed dashboard showing rows of empty bullets. */
function bulletsIn(container: HTMLElement): string[] {
  return Array.from(container.querySelectorAll('li')).map((li) => li.textContent ?? '')
}

describe('ReasonList', () => {
  it('renders one bullet per real reason, each with visible text', () => {
    const { container } = render(
      <ReasonList reasons={['Higher expected points', 'Better fixture']} />,
    )

    expect(bulletsIn(container)).toEqual(['Higher expected points', 'Better fixture'])
  })

  it('never renders an empty bullet for blank, whitespace, null or undefined entries', () => {
    const { container } = render(
      <ReasonList
        reasons={['Real reason', '', '   ', null, undefined, '\n\t', 'Another real reason']}
      />,
    )

    expect(bulletsIn(container)).toEqual(['Real reason', 'Another real reason'])
    expect(bulletsIn(container).every((text) => text.trim().length > 0)).toBe(true)
  })

  it('shows a polished empty state instead of an empty list', () => {
    const { container } = render(<ReasonList reasons={['', '  ', null]} />)

    expect(container.querySelectorAll('li')).toHaveLength(0)
    expect(container.querySelector('ul')).toBeNull()
    expect(screen.getByText('No supporting reasoning is available.')).toBeInTheDocument()
  })

  it('handles a null or undefined collection without rendering a list', () => {
    const { container: nullContainer } = render(<ReasonList reasons={null} />)
    expect(nullContainer.querySelector('ul')).toBeNull()

    const { container: undefinedContainer } = render(<ReasonList reasons={undefined} />)
    expect(undefinedContainer.querySelector('ul')).toBeNull()
  })

  it('accepts a caller-supplied empty message', () => {
    render(<ReasonList reasons={[]} emptyMessage="Nothing recorded yet." />)

    expect(screen.getByText('Nothing recorded yet.')).toBeInTheDocument()
  })

  it('keeps duplicate reason text rather than collapsing repeated entries', () => {
    // Several buy candidates genuinely share wording such as "Better
    // points-per-price value"; keying on text alone dropped rows the
    // backend actually returned.
    const { container } = render(
      <ReasonList
        reasons={['Better points-per-price value', 'Better fixture', 'Better points-per-price value']}
      />,
    )

    expect(bulletsIn(container)).toHaveLength(3)
  })

  it('renders the backend wording verbatim', () => {
    const reason = 'Higher expected points (8.08 vs 1.92)'
    render(<ReasonList reasons={[reason]} />)

    expect(screen.getByText(reason)).toBeInTheDocument()
  })
})
