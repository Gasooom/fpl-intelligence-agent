import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { makeEvidenceBasis } from '../test/fixtures'
import { buildEvidenceFactors } from '../lib/evidenceFactors'
import { EvidenceStrength } from './EvidenceStrength'

describe('EvidenceStrength', () => {
  it('renders the backend "Low" label as "Evidence: Limited"', () => {
    render(
      <EvidenceStrength confidence="Low" basis={makeEvidenceBasis({ level: 'Low' })} />,
    )

    expect(screen.getByText(/evidence:/i)).toBeInTheDocument()
    expect(screen.getByText('Limited')).toBeInTheDocument()
    expect(screen.queryByText(/confidence/i)).not.toBeInTheDocument()
  })

  it('maps the other backend labels to evidence wording too', () => {
    const { rerender } = render(
      <EvidenceStrength confidence="Medium" basis={makeEvidenceBasis({ level: 'Medium' })} />,
    )
    expect(screen.getByText('Moderate')).toBeInTheDocument()

    rerender(
      <EvidenceStrength confidence="High" basis={makeEvidenceBasis({ level: 'High' })} />,
    )
    expect(screen.getByText('Strong')).toBeInTheDocument()
  })

  it('passes an unrecognized backend label straight through rather than guessing', () => {
    render(
      <EvidenceStrength confidence="Provisional" basis={makeEvidenceBasis()} />,
    )

    expect(screen.getByText('Provisional')).toBeInTheDocument()
  })

  it('asks "Why is the evidence limited?" only when the evidence is limited', () => {
    const { rerender } = render(
      <EvidenceStrength confidence="Low" basis={makeEvidenceBasis({ level: 'Low' })} />,
    )
    expect(screen.getByText('Why is the evidence limited?')).toBeInTheDocument()

    rerender(
      <EvidenceStrength confidence="High" basis={makeEvidenceBasis({ level: 'High' })} />,
    )
    expect(screen.queryByText('Why is the evidence limited?')).not.toBeInTheDocument()
    expect(screen.getByText('How is evidence strength measured?')).toBeInTheDocument()
  })

  it('states that limited evidence does not mean a weak recommendation', () => {
    render(<EvidenceStrength confidence="Low" basis={makeEvidenceBasis({ level: 'Low' })} />)

    expect(screen.getByText(/does not indicate a weak recommendation/i)).toBeInTheDocument()
  })

  it('exposes the explanation as a keyboard-reachable native disclosure', async () => {
    const user = userEvent.setup()
    render(<EvidenceStrength confidence="Low" basis={makeEvidenceBasis({ level: 'Low' })} />)

    const disclosure = screen.getByText('Why is the evidence limited?')

    // A native <summary> inside <details> is focusable and operable by
    // keyboard without any JS handling of its own, and announces its
    // own expanded/collapsed state.
    expect(disclosure.tagName).toBe('SUMMARY')
    expect(disclosure.closest('details')).not.toBeNull()

    await user.tab()
    expect(disclosure).toHaveFocus()
  })

  it('uses no color to convey evidence strength', () => {
    render(<EvidenceStrength confidence="Low" basis={makeEvidenceBasis({ level: 'Low' })} />)

    const label = screen.getByText('Limited')
    expect(label.className).not.toMatch(/risk-|eval-(positive|negative)/)
  })
})

describe('buildEvidenceFactors', () => {
  it('reports the real band counts and the real average, and nothing else', () => {
    const factors = buildEvidenceFactors(
      makeEvidenceBasis({
        level: 'Low',
        players_considered: 11,
        limited_sample_players: 7,
        partial_sample_players: 3,
        full_sample_players: 1,
        average_sample_confidence: 0.34,
        limited_sample_minutes: 450,
        medium_threshold: 0.5,
        high_threshold: 0.75,
      }),
    )

    expect(factors).toEqual([
      '7 of 11 selected players have under 450 minutes played this season.',
      '3 of 11 have a partial season of minutes behind their projection.',
      '1 of 11 have a full season of minutes behind their projection.',
      'Average playing-time evidence across the selected eleven is 34%.',
      'Moderate evidence begins at 50%, strong evidence at 75%.',
    ])
  })

  it('omits a band entirely rather than reporting a zero count', () => {
    const factors = buildEvidenceFactors(
      makeEvidenceBasis({
        players_considered: 11,
        limited_sample_players: 0,
        partial_sample_players: 0,
        full_sample_players: 11,
      }),
    )

    expect(factors.some((factor) => factor.includes('minutes played this season'))).toBe(false)
    expect(factors.some((factor) => factor.includes('partial season'))).toBe(false)
    expect(factors).toContain('11 of 11 have a full season of minutes behind their projection.')
  })

  it('says so plainly when there was nothing to measure, rather than showing zeros', () => {
    const factors = buildEvidenceFactors(
      makeEvidenceBasis({
        level: 'Low',
        players_considered: 0,
        limited_sample_players: 0,
        partial_sample_players: 0,
        full_sample_players: 0,
        average_sample_confidence: 0,
      }),
    )

    expect(factors).toEqual([
      'No starting eleven was available to measure playing-time evidence against.',
    ])
    expect(factors.join(' ')).not.toMatch(/0 of 0/)
  })

  it('quotes the thresholds the backend sent rather than hardcoded ones', () => {
    const factors = buildEvidenceFactors(
      makeEvidenceBasis({ medium_threshold: 0.4, high_threshold: 0.9 }),
    )

    expect(factors).toContain('Moderate evidence begins at 40%, strong evidence at 90%.')
  })

  it('renders every factor it built', () => {
    const basis = makeEvidenceBasis({
      level: 'Low',
      players_considered: 11,
      limited_sample_players: 7,
      partial_sample_players: 3,
      full_sample_players: 1,
      average_sample_confidence: 0.34,
    })

    render(<EvidenceStrength confidence="Low" basis={basis} />)

    for (const factor of buildEvidenceFactors(basis)) {
      expect(screen.getByText(factor)).toBeInTheDocument()
    }
  })
})
