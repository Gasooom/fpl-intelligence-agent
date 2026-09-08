import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makeBuyCandidate, makeSellCandidate, makeTransferPair } from '../test/fixtures'
import { OtherTransferOptions } from './OtherTransferOptions'

describe('OtherTransferOptions', () => {
  it('lists the transfer_recommendations pairs other than best_transfer, in backend order', () => {
    const bestTransfer = makeTransferPair({
      sell: makeSellCandidate({ player_id: 20, web_name: 'Neto' }),
      buy: makeBuyCandidate({ player_id: 21, web_name: 'Gakpo' }),
    })
    const pairTwo = makeTransferPair({
      sell: makeSellCandidate({ player_id: 30, web_name: 'Coppola' }),
      buy: makeBuyCandidate({ player_id: 31, web_name: 'Gvardiol' }),
      expected_point_gain: 4.2,
      priority: 'recommended',
    })
    const pairThree = makeTransferPair({
      sell: makeSellCandidate({ player_id: 40, web_name: 'Joao Pedro' }),
      buy: makeBuyCandidate({ player_id: 41, web_name: 'Isak' }),
      expected_point_gain: 2.1,
      priority: 'optional',
    })

    const { container } = render(
      <OtherTransferOptions
        transferRecommendations={[bestTransfer, pairTwo, pairThree]}
        bestTransfer={bestTransfer}
        freeTransfersAvailable={1}
      />,
    )

    expect(screen.getByRole('heading', { name: /alternative transfers \(2\)/i })).toBeInTheDocument()
    expect(screen.queryByText('Neto → Gakpo')).not.toBeInTheDocument()
    expect(screen.getByText('Coppola → Gvardiol')).toBeInTheDocument()
    expect(screen.getByText('Joao Pedro → Isak')).toBeInTheDocument()

    const text = container.textContent ?? ''
    expect(text.indexOf('Coppola')).toBeLessThan(text.indexOf('Joao Pedro'))
  })

  it('explains that each option is a separate one-transfer move, and states the free-transfer count', () => {
    const bestTransfer = makeTransferPair()
    const other = makeTransferPair({
      sell: makeSellCandidate({ player_id: 30, web_name: 'Armstrong' }),
      buy: makeBuyCandidate({ player_id: 31, web_name: 'B.Fernandes' }),
    })

    render(
      <OtherTransferOptions
        transferRecommendations={[bestTransfer, other]}
        bestTransfer={bestTransfer}
        freeTransfersAvailable={2}
      />,
    )

    expect(screen.getByText(/each option is a separate one-transfer move/i)).toBeInTheDocument()
    expect(screen.getByText(/your available free transfers: 2/i)).toBeInTheDocument()
  })

  it('says free transfers are "not supplied" honestly, rather than assuming a number', () => {
    const bestTransfer = makeTransferPair()
    const other = makeTransferPair({
      sell: makeSellCandidate({ player_id: 30, web_name: 'Armstrong' }),
      buy: makeBuyCandidate({ player_id: 31, web_name: 'B.Fernandes' }),
    })

    render(
      <OtherTransferOptions
        transferRecommendations={[bestTransfer, other]}
        bestTransfer={bestTransfer}
        freeTransfersAvailable={null}
      />,
    )

    expect(screen.getByText(/your available free transfers: not supplied/i)).toBeInTheDocument()
  })

  it('shows expected improvement and priority per pair, collapsed reasons by default', () => {
    const bestTransfer = makeTransferPair({ sell: makeSellCandidate({ player_id: 20 }), buy: makeBuyCandidate({ player_id: 21 }) })
    const other = makeTransferPair({
      sell: makeSellCandidate({ player_id: 30, web_name: 'Armstrong' }),
      buy: makeBuyCandidate({ player_id: 31, web_name: 'B.Fernandes' }),
      expected_point_gain: 3.5,
      priority: 'recommended',
      reasons: ['Higher expected points'],
    })

    render(
      <OtherTransferOptions
        transferRecommendations={[bestTransfer, other]}
        bestTransfer={bestTransfer}
        freeTransfersAvailable={1}
      />,
    )

    expect(screen.getByText(/\+3\.50 expected/)).toBeInTheDocument()
    expect(screen.getByText('recommended')).toBeInTheDocument()
    expect(screen.getByText('Higher expected points')).not.toBeVisible()
  })

  it('reveals every reason in a multi-item array once its row is expanded', () => {
    const bestTransfer = makeTransferPair({ sell: makeSellCandidate({ player_id: 20 }), buy: makeBuyCandidate({ player_id: 21 }) })
    const other = makeTransferPair({
      sell: makeSellCandidate({ player_id: 30, web_name: 'Armstrong' }),
      buy: makeBuyCandidate({ player_id: 31, web_name: 'B.Fernandes' }),
      reasons: ['Higher expected points', 'Lower risk', 'Stronger minutes confidence'],
    })

    render(
      <OtherTransferOptions
        transferRecommendations={[bestTransfer, other]}
        bestTransfer={bestTransfer}
        freeTransfersAvailable={1}
      />,
    )

    expect(screen.getByText('Higher expected points')).not.toBeVisible()

    screen.getByText('Armstrong → B.Fernandes').click()

    expect(screen.getByText('Higher expected points')).toBeVisible()
    expect(screen.getByText('Lower risk')).toBeVisible()
    expect(screen.getByText('Stronger minutes confidence')).toBeVisible()
  })

  it('shows an honest fallback instead of empty bullets when a pair has no reasons', () => {
    const bestTransfer = makeTransferPair({ sell: makeSellCandidate({ player_id: 20 }), buy: makeBuyCandidate({ player_id: 21 }) })
    const other = makeTransferPair({
      sell: makeSellCandidate({ player_id: 30, web_name: 'Armstrong' }),
      buy: makeBuyCandidate({ player_id: 31, web_name: 'B.Fernandes' }),
      reasons: [],
    })

    render(
      <OtherTransferOptions
        transferRecommendations={[bestTransfer, other]}
        bestTransfer={bestTransfer}
        freeTransfersAvailable={1}
      />,
    )

    screen.getByText('Armstrong → B.Fernandes').click()

    expect(screen.getByText('No supporting reasoning is available.')).toBeVisible()
    expect(document.querySelectorAll('li').length).toBe(0)
  })

  it('filters blank reason strings rather than rendering them as empty bullets', () => {
    const bestTransfer = makeTransferPair({ sell: makeSellCandidate({ player_id: 20 }), buy: makeBuyCandidate({ player_id: 21 }) })
    const other = makeTransferPair({
      sell: makeSellCandidate({ player_id: 30, web_name: 'Armstrong' }),
      buy: makeBuyCandidate({ player_id: 31, web_name: 'B.Fernandes' }),
      reasons: ['Higher expected points', '', '   '],
    })

    render(
      <OtherTransferOptions
        transferRecommendations={[bestTransfer, other]}
        bestTransfer={bestTransfer}
        freeTransfersAvailable={1}
      />,
    )

    screen.getByText('Armstrong → B.Fernandes').click()

    expect(screen.getByText('Higher expected points')).toBeVisible()
    expect(document.querySelectorAll('li').length).toBe(1)
  })

  it('renders nothing when there are no other pairs beyond the best transfer', () => {
    const bestTransfer = makeTransferPair()
    const { container } = render(
      <OtherTransferOptions
        transferRecommendations={[bestTransfer]}
        bestTransfer={bestTransfer}
        freeTransfersAvailable={1}
      />,
    )

    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when there are no transfer recommendations at all', () => {
    const { container } = render(
      <OtherTransferOptions transferRecommendations={[]} bestTransfer={null} freeTransfersAvailable={null} />,
    )

    expect(container).toBeEmptyDOMElement()
  })

  it('shows expected_point_gain, never net_improvement, so the same pair reads identically here and in the hero card', () => {
    // A deliberately different net_improvement proves the component
    // reads expected_point_gain, not the selection-score delta.
    const bestTransfer = makeTransferPair({ sell: makeSellCandidate({ player_id: 20 }), buy: makeBuyCandidate({ player_id: 21 }) })
    const other = makeTransferPair({
      sell: makeSellCandidate({ player_id: 30, web_name: 'Armstrong' }),
      buy: makeBuyCandidate({ player_id: 31, web_name: 'B.Fernandes' }),
      expected_point_gain: 5.0,
      net_improvement: 9.9,
    })

    render(
      <OtherTransferOptions
        transferRecommendations={[bestTransfer, other]}
        bestTransfer={bestTransfer}
        freeTransfersAvailable={1}
      />,
    )

    expect(screen.getByText(/\+5\.00 expected/)).toBeInTheDocument()
    expect(screen.queryByText(/\+9\.90 expected/)).not.toBeInTheDocument()
  })
})
