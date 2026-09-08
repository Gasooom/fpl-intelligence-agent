import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makeBuyCandidate, makeSellCandidate, makeTransferPair } from '../test/fixtures'
import { WhyThisDecision } from './WhyThisDecision'

describe('WhyThisDecision', () => {
  it('renders a side-by-side comparison built from real sell/buy fields under a "Why X -> Y?" heading', () => {
    const pair = makeTransferPair({
      sell: makeSellCandidate({
        web_name: 'Neto',
        expected_points: 1.71,
        fixture_difficulty: 5.0,
        risk_level: 'high',
        form: 3.3,
      }),
      buy: makeBuyCandidate({
        web_name: 'Gakpo',
        expected_points: 9.73,
        fixture_difficulty: 2.0,
        risk_level: 'medium',
        form: 9.3,
      }),
    })

    render(<WhyThisDecision bestTransfer={pair} />)

    expect(screen.getByText('Why Neto → Gakpo?')).toBeInTheDocument()
    expect(screen.getByText('Higher expected points')).toBeInTheDocument()
    expect(screen.getByText('9.73 vs 1.71')).toBeInTheDocument()
    expect(screen.getByText('Better fixture')).toBeInTheDocument()
    expect(screen.getByText('2.0 vs 5.0')).toBeInTheDocument()
    expect(screen.getByText('Lower risk')).toBeInTheDocument()
    expect(screen.getByText('Medium vs High')).toBeInTheDocument()
    expect(screen.getByText('Better recent form')).toBeInTheDocument()
    expect(screen.getByText('9.30 vs 3.30')).toBeInTheDocument()
  })

  it('keeps the backend free-text reasons available behind disclosure, not duplicated in the comparison', () => {
    // None of these three strings collide with the fixed comparison-row
    // labels ("Higher expected points", "Better fixture", etc.) that
    // the default sell/buy fixture also produces above this section -
    // getByText's exact match would otherwise find two elements.
    const pair = makeTransferPair({
      reasons: [
        'Higher expected points (9.73 vs 1.71)',
        'Better points-per-price value',
        'Stronger minutes confidence',
      ],
    })

    render(<WhyThisDecision bestTransfer={pair} />)

    expect(screen.getByText('Full reasoning')).toBeInTheDocument()
    // Every reason in the array must render, not just the first one -
    // a `.slice`/key-collision bug would silently drop the rest.
    expect(screen.getByText('Higher expected points (9.73 vs 1.71)')).toBeInTheDocument()
    expect(screen.getByText('Better points-per-price value')).toBeInTheDocument()
    expect(screen.getByText('Stronger minutes confidence')).toBeInTheDocument()
  })

  it('renders nothing when there is no best transfer', () => {
    const { container } = render(<WhyThisDecision bestTransfer={null} />)

    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when the pair has no comparable differences and no backend reasons', () => {
    const pair = makeTransferPair({
      sell: makeSellCandidate({ expected_points: 5, fixture_difficulty: 3, risk_level: 'medium', form: 5 }),
      buy: makeBuyCandidate({ expected_points: 5, fixture_difficulty: 3, risk_level: 'medium', form: 5 }),
      reasons: [],
    })
    const { container } = render(<WhyThisDecision bestTransfer={pair} />)

    expect(container).toBeEmptyDOMElement()
  })

  it('filters blank reason strings from Full reasoning rather than rendering empty bullets', () => {
    const pair = makeTransferPair({
      reasons: ['Better points-per-price value', '', '   ', 'Stronger minutes confidence'],
    })

    render(<WhyThisDecision bestTransfer={pair} />)

    expect(screen.getByText('Better points-per-price value')).toBeInTheDocument()
    expect(screen.getByText('Stronger minutes confidence')).toBeInTheDocument()
    expect(document.querySelectorAll('li').length).toBe(2)
  })

  it('hides Full reasoning entirely (never an empty list) when every reason is blank but comparison rows still exist', () => {
    const pair = makeTransferPair({
      sell: makeSellCandidate({ expected_points: 1.71 }),
      buy: makeBuyCandidate({ expected_points: 9.73 }),
      reasons: ['', '   '],
    })

    render(<WhyThisDecision bestTransfer={pair} />)

    expect(screen.getByText('Higher expected points')).toBeInTheDocument()
    expect(screen.queryByText('Full reasoning')).not.toBeInTheDocument()
  })
})
