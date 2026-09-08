import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  makeBuyCandidate,
  makeEvidenceBasis,
  makePlayer,
  makeSellCandidate,
  makeTransferPair,
} from '../test/fixtures'
import { PrimaryDecision } from './PrimaryDecision'

const managerContext = { freeTransfersAvailable: null, inTheBank: null }

/** The props every case needs but few care about, so each test states
 * only what it is actually exercising. */
const baseProps = {
  evidenceBasis: makeEvidenceBasis(),
  projectedGameweekPoints: 72.0,
  ...managerContext,
}

describe('PrimaryDecision', () => {
  it('renders gameweek, best transfer with priority, captain, vice-captain, and summary', () => {
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
        {...baseProps}
        gameweek={3}
        captain={captain}
        viceCaptain={viceCaptain}
        bestTransfer={bestTransfer}
        confidence="Low"
        summary="Captain: Cherki. Decision confidence: Low."
      />,
    )

    expect(screen.getByText('Gameweek 3')).toBeInTheDocument()
    expect(screen.getByText('Neto → Gakpo')).toBeInTheDocument()
    expect(screen.getByText(/\+9\.62 expected points/i)).toBeInTheDocument()
    expect(screen.getByText('essential')).toBeInTheDocument()
    expect(screen.getByText('Cherki')).toBeInTheDocument()
    expect(screen.getByText('Haaland')).toBeInTheDocument()
    expect(screen.getByText('Captain: Cherki. Decision confidence: Low.')).toBeInTheDocument()
  })

  // --- Executive summary: readable without knowing FPL shorthand ---

  it('leads with projected points in plain words, keeping xP only as secondary shorthand', () => {
    render(
      <PrimaryDecision
        {...baseProps}
        gameweek={5}
        captain={makePlayer({ web_name: 'Cherki' })}
        viceCaptain={makePlayer()}
        bestTransfer={null}
        confidence="High"
        summary=""
        projectedGameweekPoints={72.0}
      />,
    )

    expect(screen.getByText(/projected points/i)).toBeInTheDocument()
    expect(screen.getByText('72.00')).toBeInTheDocument()
    // The abbreviation stays available, but never as the only label.
    expect(screen.getByText('(xP)')).toBeInTheDocument()
  })

  it('renders the projected total exactly as the backend supplied it', () => {
    render(
      <PrimaryDecision
        {...baseProps}
        gameweek={5}
        captain={makePlayer()}
        viceCaptain={makePlayer()}
        bestTransfer={null}
        confidence="High"
        summary=""
        projectedGameweekPoints={58.41}
      />,
    )

    expect(screen.getByText('58.41')).toBeInTheDocument()
  })

  // --- Evidence terminology ---

  it('presents low backend confidence as "Evidence: Limited", never as low confidence', () => {
    render(
      <PrimaryDecision
        {...baseProps}
        gameweek={1}
        captain={makePlayer()}
        viceCaptain={makePlayer()}
        bestTransfer={null}
        confidence="Low"
        evidenceBasis={makeEvidenceBasis({ level: 'Low' })}
        summary=""
      />,
    )

    expect(screen.getByText('Limited')).toBeInTheDocument()
    expect(screen.queryByText(/low confidence/i)).not.toBeInTheDocument()
    expect(screen.queryByText('Low')).not.toBeInTheDocument()
  })

  it('shows an evidence label with the same neutral styling whatever its strength', () => {
    const props = {
      ...baseProps,
      gameweek: 1,
      captain: makePlayer(),
      viceCaptain: makePlayer(),
      bestTransfer: null,
      summary: '',
    }

    const { rerender } = render(
      <PrimaryDecision
        {...props}
        confidence="Low"
        evidenceBasis={makeEvidenceBasis({ level: 'Low' })}
      />,
    )
    const limitedClassName = screen.getByText('Limited').className

    rerender(
      <PrimaryDecision
        {...props}
        confidence="High"
        evidenceBasis={makeEvidenceBasis({ level: 'High' })}
      />,
    )
    const strongClassName = screen.getByText('Strong').className

    expect(limitedClassName).toBe(strongClassName)
    // Neither uses a risk color class - evidence has no color of its own.
    expect(limitedClassName).not.toMatch(/risk-/)
    expect(limitedClassName).not.toMatch(/eval-(positive|negative)/)
  })

  it('shows a neutral message when there is no best transfer, and never fabricates one', () => {
    render(
      <PrimaryDecision
        {...baseProps}
        gameweek={1}
        captain={makePlayer({ web_name: 'Cherki' })}
        viceCaptain={makePlayer({ web_name: 'Haaland' })}
        bestTransfer={null}
        confidence="High"
        summary="No transfer needed."
      />,
    )

    expect(screen.getByText(/no worthwhile transfer this gameweek/i)).toBeInTheDocument()
  })

  // --- Transfer economics (rendered from backend values only) ---

  it('shows the manager transfer context supplied by the backend', () => {
    render(
      <PrimaryDecision
        {...baseProps}
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
        {...baseProps}
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
        {...baseProps}
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
        {...baseProps}
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
        {...baseProps}
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
        {...baseProps}
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
