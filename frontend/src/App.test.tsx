import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { GameweekDecisionResponse, GameweekEvaluationResponse } from './api/types'
import App from './App'
import {
  makeEvaluatedGameweek,
  makeGameweekDecision,
  makeGameweekEvaluation,
  makeSquadPlayerEvaluations,
} from './test/fixtures'
import { renderWithProviders } from './test/renderWithProviders'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  })
}

/** The page calls two endpoints; route each to its own payload so a
 * test never accidentally feeds a decision body to the evaluation
 * query (or vice versa). */
function mockApi(options: {
  decision?: GameweekDecisionResponse
  evaluation?: GameweekEvaluationResponse
} = {}) {
  const decision = options.decision ?? makeGameweekDecision()
  const evaluation = options.evaluation ?? makeGameweekEvaluation()

  vi.mocked(fetch).mockImplementation((input) => {
    const url = String(input)
    if (url.includes('/api/v1/evaluation/')) {
      return Promise.resolve(jsonResponse(evaluation))
    }
    return Promise.resolve(jsonResponse(decision))
  })
}

async function submitEntryForm(entryId: string, gameweek?: string) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText(/fpl entry id/i), entryId)
  if (gameweek) {
    await user.type(screen.getByLabelText(/gameweek/i), gameweek)
  }
  await user.click(screen.getByRole('button', { name: /^analyze$/i }))
}

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows the entry form and a purposeful empty state before any query has run', () => {
    renderWithProviders(<App />)

    expect(screen.getByLabelText(/fpl entry id/i)).toBeInTheDocument()
    expect(screen.getByText(/enter your fpl entry id above/i)).toBeInTheDocument()
  })

  it('triggers a request to the correct entry_id and gameweek when submitted', async () => {
    mockApi()
    renderWithProviders(<App />)

    await submitEntryForm('8731757', '5')

    await waitFor(() => expect(fetch).toHaveBeenCalled())
    const requestedUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(requestedUrl).toContain('/api/v1/decision/8731757')
    expect(requestedUrl).toContain('gameweek=5')
  })

  it('omits the gameweek query parameter entirely when not supplied', async () => {
    mockApi()
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    await waitFor(() => expect(fetch).toHaveBeenCalled())
    const requestedUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(requestedUrl).toContain('/api/v1/decision/8731757')
    expect(requestedUrl).not.toContain('gameweek')
  })

  it('shows a loading state while the request is in flight', async () => {
    let resolveFetch!: (value: Response) => void
    vi.mocked(fetch).mockReturnValue(
      new Promise((resolve) => {
        resolveFetch = resolve
      }),
    )
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    expect(await screen.findByRole('status')).toBeInTheDocument()
    expect(screen.getByText(/analyzing your gameweek/i)).toBeInTheDocument()

    resolveFetch(jsonResponse(makeGameweekDecision()))
  })

  it('shows the backend detail message on a 400 response', async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ detail: 'Gameweek 99 was not found.' }, 400),
    )
    renderWithProviders(<App />)

    await submitEntryForm('8731757', '99')

    expect(await screen.findByRole('alert')).toHaveTextContent('Gameweek 99 was not found.')
  })

  it('shows the backend detail message on a 422 validation response', async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ detail: [{ msg: 'Input should be a valid integer' }] }, 422),
    )
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    expect(await screen.findByRole('alert')).toHaveTextContent('Input should be a valid integer')
  })

  it('shows a network-failure message when the request itself fails', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'))
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    expect(await screen.findByRole('alert')).toHaveTextContent(/could not reach the decision api/i)
  })

  it('renders the primary decision wired to real response data', async () => {
    mockApi()
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    expect(await screen.findByText('Recommended plan')).toBeInTheDocument()
    expect(screen.getByText('Gameweek 5')).toBeInTheDocument()
    expect(screen.getAllByText('Captain Player').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Vice Player').length).toBeGreaterThan(0)
    expect(screen.getByText('High')).toBeInTheDocument() // confidence, default fixture
  })

  it('renders the Starting XI and Bench counts', async () => {
    mockApi()
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    const xiHeading = await screen.findByRole('heading', { name: /starting xi/i })
    expect(xiHeading).toHaveTextContent('11')
    const benchHeading = screen.getByRole('heading', { name: /^bench/i })
    expect(benchHeading).toHaveTextContent('4')
  })

  it('renders Decision evidence and Full candidate pools wired to the same response', async () => {
    mockApi()
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    expect(await screen.findByRole('heading', { name: /decision evidence/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /full candidate pools/i })).toBeInTheDocument()
    // The sell/buy candidate pool legitimately overlaps with best_transfer's
    // own sell/buy players in the fixture - both are correct, distinct views.
    expect(screen.getAllByText(/weak player/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/strong target/i).length).toBeGreaterThan(0)
  })

  it('sends the free-transfer count to the decision API when the manager supplies it', async () => {
    mockApi()
    renderWithProviders(<App />)

    const user = userEvent.setup()
    await user.type(screen.getByLabelText(/fpl entry id/i), '8731757')
    await user.type(screen.getByLabelText(/free transfers/i), '1')
    await user.click(screen.getByRole('button', { name: /^analyze$/i }))

    await waitFor(() => {
      const urls = vi.mocked(fetch).mock.calls.map((call) => String(call[0]))
      expect(urls.some((url) => url.includes('free_transfers_available=1'))).toBe(true)
    })
  })

  it('omits the free-transfer parameter entirely when it is not supplied', async () => {
    mockApi()
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    await waitFor(() => expect(fetch).toHaveBeenCalled())
    const decisionUrl = String(vi.mocked(fetch).mock.calls[0][0])
    expect(decisionUrl).not.toContain('free_transfers_available')
  })

  it('renders backend-supplied transfer economics without recomputing them', async () => {
    const decision = makeGameweekDecision({
      free_transfers_available: 0,
      in_the_bank: 1.5,
    })
    mockApi({
      decision: {
        ...decision,
        best_transfer: {
          ...decision.best_transfer!,
          expected_point_gain: 9.64,
          hit_cost: 4,
          net_value: 5.64,
        },
      },
    })
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    expect(await screen.findByText('Transfer cost')).toBeInTheDocument()
    expect(screen.getByText('-4 points')).toBeInTheDocument()
    expect(screen.getByText('+5.64')).toBeInTheDocument()
    expect(screen.getByText('£1.5m')).toBeInTheDocument()
  })

  it('renders the backend explanation verbatim when a gameweek cannot be evaluated yet', async () => {
    mockApi()
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    expect(
      await screen.findByRole('heading', { name: /decision evaluation/i }),
    ).toBeInTheDocument()
    expect(screen.getByText(/gameweek 5 is not completed yet/i)).toBeInTheDocument()
  })

  it('requests the evaluation for the gameweek the decision actually resolved to', async () => {
    mockApi()
    renderWithProviders(<App />)

    // No gameweek typed: the decision resolves to gameweek 5 (fixture),
    // and the evaluation must ask for that same gameweek rather than
    // repeating the blank input.
    await submitEntryForm('8731757')

    await waitFor(() => {
      const urls = vi.mocked(fetch).mock.calls.map((call) => String(call[0]))
      expect(urls.some((url) => url.includes('/api/v1/evaluation/8731757?gameweek=5'))).toBe(true)
    })
  })

  it('renders real prediction-vs-actual figures when the backend returns an evaluation', async () => {
    mockApi({ evaluation: makeEvaluatedGameweek() })
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    expect(
      await screen.findByRole('heading', { name: /decision evaluation/i }),
    ).toBeInTheDocument()
    expect(screen.getByText('12 actual points')).toBeInTheDocument()
    expect(screen.getByText('Correct')).toBeInTheDocument()
    expect(screen.getByText('Positive')).toBeInTheDocument()
  })

  it('renders the full squad player predictions when a gameweek has been evaluated', async () => {
    const squad = makeSquadPlayerEvaluations()
    mockApi({
      evaluation: makeEvaluatedGameweek({
        starting_xi_players: squad.startingXi,
        bench_players: squad.bench,
      }),
    })
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    expect(await screen.findByRole('heading', { name: /player predictions/i })).toBeInTheDocument()
    for (const player of [...squad.startingXi, ...squad.bench]) {
      expect(screen.getByText(player.web_name)).toBeInTheDocument()
    }
  })

  it('does not render player predictions for a gameweek that cannot be evaluated', async () => {
    mockApi()
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    await screen.findByRole('heading', { name: /decision evaluation/i })
    expect(screen.queryByRole('heading', { name: /player predictions/i })).not.toBeInTheDocument()
  })

  it('shows the captain’s expected points alongside the actual in the evaluation', async () => {
    mockApi({ evaluation: makeEvaluatedGameweek() })
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    await screen.findByRole('heading', { name: /decision evaluation/i })
    expect(screen.getByText('10.31 expected points')).toBeInTheDocument()
    expect(screen.getByText('12 actual points')).toBeInTheDocument()
  })

  it('renders Other transfer options for transfer_recommendations beyond best_transfer, in backend order', async () => {
    const decision = makeGameweekDecision()
    const secondPair = {
      ...decision.best_transfer!,
      sell: { ...decision.best_transfer!.sell, player_id: 30, web_name: 'Coppola' },
      buy: { ...decision.best_transfer!.buy, player_id: 31, web_name: 'Gvardiol' },
      net_improvement: 4.2,
      priority: 'recommended',
    }
    mockApi({
      decision: {
        ...decision,
        transfer_recommendations: [decision.best_transfer!, secondPair],
      },
    })
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    expect(await screen.findByRole('heading', { name: /alternative transfers/i })).toBeInTheDocument()
    expect(screen.getByText('Coppola → Gvardiol')).toBeInTheDocument()
  })
})
