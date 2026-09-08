import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makeBuyCandidate, makePlayer, makeSellCandidate, makeTransferPair } from '../test/fixtures'
import { PrimaryDecision } from './PrimaryDecision'

const managerContext = { freeTransfersAvailable: null, inTheBank: null }

describe('PrimaryDecision', () => {
  it('renders gameweek, best transfer with priority, captain, vice-captain, confidence, and summary', () => {
    const captain = makePlayer({ web_name: 'Cherki' })
    const viceCaptain = makePlayer({ web_name: 'Haaland' })
    const bestTransfer = makeTransferPair({
      sell: makeSellCandidate({ web_name: 'Neto' }),
      buy: makeBuyCandidate({ web_name: 'Gakpo' }),
      expected_point_gain: 9.62,
      priority: 'essential',
    })

    render(
      <PrimaryDecision
        gameweek={3}
        captain={captain}
        viceCaptain={viceCaptain}
        bestTransfer={bestTransfer}
        confidence="Low"
        summary="Captain: Cherki. Decision confidence: Low."
        {...managerContext}
      />,
    )

    expect(screen.getByText('Gameweek 3')).toBeInTheDocument()
    expect(screen.getByText('Neto → Gakpo')).toBeInTheDocument()
    expect(screen.getByText(/\+9\.62 expected points/i)).toBeInTheDocument()
    expect(screen.getByText('essential')).toBeInTheDocument()
    expect(screen.getByText('Cherki')).toBeInTheDocument()
    expect(screen.getByText('Haaland')).toBeInTheDocument()
    expect(screen.getByText('Low')).toBeInTheDocument()
    expect(screen.getByText('Captain: Cherki. Decision confidence: Low.')).toBeInTheDocument()
  })

  it('shows a neutral message when there is no best transfer, and never fabricates one', () => {
    render(
      <PrimaryDecision
        gameweek={1}
        captain={makePlayer({ web_name: 'Cherki' })}
        viceCaptain={makePlayer({ web_name: 'Haaland' })}
        bestTransfer={null}
        confidence="High"
        summary="No transfer needed."
        {...managerContext}
      />,
    )

    expect(screen.getByText(/no worthwhile transfer this gameweek/i)).toBeInTheDocument()
  })

  it('displays Low confidence with the same neutral styling as High - confidence is not a warning', () => {
    const props = {
      gameweek: 1,
      captain: makePlayer(),
      viceCaptain: makePlayer(),
      bestTransfer: null,
      summary: '',
      ...managerContext,
    }

    const { rerender } = render(<PrimaryDecision {...props} confidence="Low" />)
    const lowClassName = screen.getByText('Low').className

    rerender(<PrimaryDecision {...props} confidence="High" />)
    const highClassName = screen.getByText('High').className

    expect(lowClassName).toBe(highClassName)
    // Neither uses a risk color class - confidence has no color of its own.
    expect(lowClassName).not.toMatch(/risk-/)
  })

  // --- Transfer economics (rendered from backend values only) ---

  it('shows the manager transfer context supplied by the backend', () => {
    render(
      <PrimaryDecision
        gameweek={3}
        captain={makePlayer()}
        viceCaptain={makePlayer()}
        bestTransfer={null}
        confidence="High"
        summary=""
        freeTransfersAvailable={1}
        inTheBank={2.5}
      />,
    )

    expect(screen.getByText('Free transfers')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('In the bank')).toBeInTheDocument()
    expect(screen.getByText('£2.5m')).toBeInTheDocument()
  })

  it('says so honestly when the free-transfer count and bank are unknown', () => {
    render(
      <PrimaryDecision
        gameweek={3}
        captain={makePlayer()}
        viceCaptain={makePlayer()}
        bestTransfer={null}
        confidence="High"
        summary=""
        freeTransfersAvailable={null}
        inTheBank={null}
      />,
    )

    expect(screen.getByText('Not supplied')).toBeInTheDocument()
    expect(screen.getByText('Unknown')).toBeInTheDocument()
  })

  it('renders a free transfer as costing nothing, with net value equal to the gain', () => {
    const bestTransfer = makeTransferPair({
      expected_point_gain: 9.64,
      hit_cost: 0,
      net_value: 9.64,
    })

    render(
      <PrimaryDecision
        gameweek={3}
        captain={makePlayer()}
        viceCaptain={makePlayer()}
        bestTransfer={bestTransfer}
        confidence="Low"
        summary=""
        freeTransfersAvailable={1}
        inTheBank={0.5}
      />,
    )

    expect(screen.getByText('Expected gain')).toBeInTheDocument()
    expect(screen.getByText('Transfer cost')).toBeInTheDocument()
    expect(screen.getByText('Free')).toBeInTheDocument()
    expect(screen.getByText('Net expected value')).toBeInTheDocument()
    expect(screen.getAllByText('+9.64').length).toBe(2) // gain and net value
  })

  it('renders a hit as a real points cost, with the reduced net value', () => {
    const bestTransfer = makeTransferPair({
      expected_point_gain: 9.64,
      hit_cost: 4,
      net_value: 5.64,
    })

    render(
      <PrimaryDecision
        gameweek={3}
        captain={makePlayer()}
        viceCaptain={makePlayer()}
        bestTransfer={bestTransfer}
        confidence="Low"
        summary=""
        freeTransfersAvailable={0}
        inTheBank={0.5}
      />,
    )

    expect(screen.getByText('-4 points')).toBeInTheDocument()
    expect(screen.getByText('+9.64')).toBeInTheDocument()
    expect(screen.getByText('+5.64')).toBeInTheDocument()
  })

  it('never recomputes the economics - it renders exactly what the backend returned', () => {
    // net_value deliberately inconsistent with gain - hit_cost, proving
    // the component displays backend values rather than deriving them.
    const bestTransfer = makeTransferPair({
      expected_point_gain: 10,
      hit_cost: 4,
      net_value: 999.99,
    })

    render(
      <PrimaryDecision
        gameweek={3}
        captain={makePlayer()}
        viceCaptain={makePlayer()}
        bestTransfer={bestTransfer}
        confidence="Low"
        summary=""
        freeTransfersAvailable={0}
        inTheBank={0.5}
      />,
    )

    expect(screen.getByText('+999.99')).toBeInTheDocument()
  })

  it('omits the economics block entirely when the backend could not compute it', () => {
    const bestTransfer = makeTransferPair({ hit_cost: null, net_value: null })

    render(
      <PrimaryDecision
        gameweek={3}
        captain={makePlayer()}
        viceCaptain={makePlayer()}
        bestTransfer={bestTransfer}
        confidence="Low"
        summary=""
        freeTransfersAvailable={null}
        inTheBank={null}
      />,
    )

    expect(screen.queryByText('Transfer cost')).not.toBeInTheDocument()
    expect(screen.queryByText('Net expected value')).not.toBeInTheDocument()
  })
})
