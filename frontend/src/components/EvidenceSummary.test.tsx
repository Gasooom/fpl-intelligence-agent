import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makeBuyCandidate, makeSellCandidate, makeTransferPair } from '../test/fixtures'
import { EvidenceSummary } from './EvidenceSummary'

describe('EvidenceSummary', () => {
  it('shows captain, vice-captain, and best-transfer evidence by default, with the rest behind View all evidence', () => {
    const bestTransfer = makeTransferPair({
      sell: makeSellCandidate({ player_id: 20, web_name: 'Neto' }),
      buy: makeBuyCandidate({ player_id: 21, web_name: 'Gakpo' }),
    })

    render(
      <EvidenceSummary
        evidence={[
          { player_id: 11, decision: 'captain', score: 8.65, reasons: ['Highest captaincy score'] },
          { player_id: 10, decision: 'vice_captain', score: 7.35, reasons: ['Second-highest captaincy score'] },
          { player_id: 20, decision: 'sell', score: 6.4, reasons: ['High overall risk'] },
          { player_id: 21, decision: 'buy', score: 10.2, reasons: ['Higher expected points'] },
          // Not relevant to captain/vice/best transfer - should be hidden by default.
          { player_id: 99, decision: 'sell', score: 5.0, reasons: ['Unrelated sell reason'] },
        ]}
        nameLookup={new Map([[11, 'Cherki'], [10, 'Haaland'], [20, 'Neto'], [21, 'Gakpo'], [99, 'Other Player']])}
        captainId={11}
        viceCaptainId={10}
        bestTransfer={bestTransfer}
      />,
    )

    expect(screen.getByText('Captain — Cherki')).toBeInTheDocument()
    expect(screen.getByText('Highest captaincy score')).toBeInTheDocument()
    expect(screen.getByText('Vice-captain — Haaland')).toBeInTheDocument()
    expect(screen.getByText('Second-highest captaincy score')).toBeInTheDocument()
    expect(screen.getByText('Best transfer — Neto → Gakpo')).toBeInTheDocument()
    expect(screen.getByText('High overall risk')).toBeInTheDocument()
    expect(screen.getByText('Higher expected points')).toBeInTheDocument()

    // The unrelated entry sits inside the closed <details> - present in
    // the DOM (native <details> behavior) but not visible until expanded.
    expect(screen.getByText('Unrelated sell reason')).not.toBeVisible()
    expect(screen.getByText('View all evidence')).toBeInTheDocument()
  })

  it('renders every reason in a multi-item reasons array, not just the first', () => {
    render(
      <EvidenceSummary
        evidence={[
          {
            player_id: 11,
            decision: 'captain',
            score: 8.65,
            reasons: [
              'Highest captaincy score',
              '10.31 expected points',
              'Fixture difficulty 2.0',
              'Strong recent form (8.3)',
            ],
          },
        ]}
        nameLookup={new Map([[11, 'Cherki']])}
        captainId={11}
        viceCaptainId={-1}
        bestTransfer={null}
      />,
    )

    expect(screen.getByText('Highest captaincy score')).toBeInTheDocument()
    expect(screen.getByText('10.31 expected points')).toBeInTheDocument()
    expect(screen.getByText('Fixture difficulty 2.0')).toBeInTheDocument()
    expect(screen.getByText('Strong recent form (8.3)')).toBeInTheDocument()
  })

  it('drops "X vs Y" comparative reasons from the best-transfer group, since WhyThisDecision already shows that comparison', () => {
    const bestTransfer = makeTransferPair({
      sell: makeSellCandidate({ player_id: 20, web_name: 'Neto' }),
      buy: makeBuyCandidate({ player_id: 21, web_name: 'Gakpo' }),
    })

    render(
      <EvidenceSummary
        evidence={[
          {
            player_id: 21,
            decision: 'buy',
            score: 10.2,
            reasons: ['Higher expected points (9.73 vs 1.71)', 'Better points-per-price value'],
          },
        ]}
        nameLookup={new Map([[20, 'Neto'], [21, 'Gakpo']])}
        captainId={-1}
        viceCaptainId={-1}
        bestTransfer={bestTransfer}
      />,
    )

    expect(screen.getByText('Better points-per-price value')).toBeInTheDocument()
    expect(screen.queryByText('Higher expected points (9.73 vs 1.71)')).not.toBeInTheDocument()
  })

  it('reveals the rest of the evidence when "View all evidence" is expanded', async () => {
    render(
      <EvidenceSummary
        evidence={[
          { player_id: 11, decision: 'captain', score: 8.65, reasons: ['Highest captaincy score'] },
          { player_id: 99, decision: 'must_play', score: 3.0, reasons: ['Unrelated must-play reason'] },
        ]}
        nameLookup={new Map([[11, 'Cherki'], [99, 'Other Player']])}
        captainId={11}
        viceCaptainId={-1}
        bestTransfer={null}
      />,
    )

    const details = screen.getByText('View all evidence').closest('details')
    expect(details).not.toBeNull()
    expect(details).not.toHaveAttribute('open')

    // Native <details> keeps its content in the DOM even collapsed.
    expect(screen.getByText('Unrelated must-play reason')).toBeInTheDocument()
    expect(screen.getByText(/must_play — Other Player/)).toBeInTheDocument()
  })

  it('does not render a "View all evidence" disclosure when everything is already highlighted', () => {
    render(
      <EvidenceSummary
        evidence={[{ player_id: 11, decision: 'captain', score: 8.65, reasons: ['Highest captaincy score'] }]}
        nameLookup={new Map([[11, 'Cherki']])}
        captainId={11}
        viceCaptainId={-1}
        bestTransfer={null}
      />,
    )

    expect(screen.queryByText('View all evidence')).not.toBeInTheDocument()
  })

  it('shows an honest fallback instead of empty bullets when a matched entry has no reasons', () => {
    render(
      <EvidenceSummary
        evidence={[{ player_id: 11, decision: 'captain', score: 8.65, reasons: [] }]}
        nameLookup={new Map([[11, 'Cherki']])}
        captainId={11}
        viceCaptainId={-1}
        bestTransfer={null}
      />,
    )

    expect(screen.getByText('Captain — Cherki')).toBeInTheDocument()
    expect(screen.getByText('No supporting reasoning is available.')).toBeInTheDocument()
    expect(document.querySelectorAll('li').length).toBe(0)
  })

  it('filters blank reason strings rather than rendering them as empty bullets', () => {
    render(
      <EvidenceSummary
        evidence={[
          {
            player_id: 11,
            decision: 'captain',
            score: 8.65,
            reasons: ['Highest captaincy score', '', '   ', '10.31 expected points'],
          },
        ]}
        nameLookup={new Map([[11, 'Cherki']])}
        captainId={11}
        viceCaptainId={-1}
        bestTransfer={null}
      />,
    )

    expect(screen.getByText('Highest captaincy score')).toBeInTheDocument()
    expect(screen.getByText('10.31 expected points')).toBeInTheDocument()
    expect(document.querySelectorAll('li').length).toBe(2)
  })

  it('shows a fallback line for a "View all evidence" entry with no reasons, not an empty bullet', () => {
    render(
      <EvidenceSummary
        evidence={[
          { player_id: 11, decision: 'captain', score: 8.65, reasons: ['Highest captaincy score'] },
          { player_id: 99, decision: 'must_play', score: 3.0, reasons: [] },
        ]}
        nameLookup={new Map([[11, 'Cherki'], [99, 'Other Player']])}
        captainId={11}
        viceCaptainId={-1}
        bestTransfer={null}
      />,
    )

    expect(screen.getByText(/must_play — Other Player/)).toBeInTheDocument()
    expect(screen.getByText('No supporting reasoning is available.')).toBeInTheDocument()
  })

  it('shows a deliberate empty state for an empty evidence array', () => {
    render(
      <EvidenceSummary
        evidence={[]}
        nameLookup={new Map()}
        captainId={11}
        viceCaptainId={10}
        bestTransfer={null}
      />,
    )

    expect(screen.getByText(/no supporting evidence is available/i)).toBeInTheDocument()
  })
})
