import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type {
  GameweekDecisionResponse,
  GameweekEvaluationResponse,
  LatestCompletedEvaluationResponse,
} from './api/types'
import App from './App'
import {
  makeEvaluatedGameweek,
  makeEvidenceBasis,
  makeGameweekDecision,
  makeGameweekEvaluation,
  makeLatestCompletedEvaluation,
  makeSquadPlayerEvaluations,
} from './test/fixtures'
import { renderWithProviders } from './test/renderWithProviders'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  })
}

/** The page calls three endpoints; route each to its own payload so a
 * test never accidentally feeds one endpoint's body to another query.
 * The latest-completed endpoint has its own envelope shape and must be
 * matched before the plain evaluation path, which its URL also starts
 * with. Defaults to "no completed gameweek on record yet", the honest
 * state for an entry whose first decision cycle has not finished. */
function mockApi(options: {
  decision?: GameweekDecisionResponse
  evaluation?: GameweekEvaluationResponse
  latestCompleted?: LatestCompletedEvaluationResponse
} = {}) {
  const decision = options.decision ?? makeGameweekDecision()
  const evaluation = options.evaluation ?? makeGameweekEvaluation()
  const latestCompleted =
    options.latestCompleted ?? { available: false, evaluation: null }

  vi.mocked(fetch).mockImplementation((input) => {
    const url = String(input)
    if (url.includes('/latest-completed')) {
      return Promise.resolve(jsonResponse(latestCompleted))
    }
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
    // The default fixture's "High" confidence, shown as evidence
    // wording rather than as a confidence verdict.
    expect(screen.getByText('Strong')).toBeInTheDocument()
    expect(screen.queryByText('High')).not.toBeInTheDocument()
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
    expect(screen.getByText('Correct')).toBeInTheDocument()
    expect(screen.getByText(/outcome: positive/i)).toBeInTheDocument()
    // Expected, actual, and error each carry their own label.
    expect(screen.getByText('Expected points')).toBeInTheDocument()
    expect(screen.getAllByText('Actual points').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Prediction error').length).toBeGreaterThan(0)
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

    const heading = await screen.findByRole('heading', { name: /player predictions/i })
    expect(heading).toBeInTheDocument()
    for (const player of [...squad.startingXi, ...squad.bench]) {
      expect(screen.getByText(player.web_name)).toBeInTheDocument()
    }
    // Labeled with the gameweek these rows actually belong to.
    expect(heading.parentElement).toHaveTextContent('Gameweek 5')
  })

  it('falls back to the latest completed gameweek player table while the current one is pending', async () => {
    const squad = makeSquadPlayerEvaluations()
    mockApi({
      // The current gameweek carries no player rows at all.
      evaluation: makeGameweekEvaluation({ status: 'not_completed' }),
      latestCompleted: makeLatestCompletedEvaluation({
        evaluation: makeEvaluatedGameweek({
          gameweek: 3,
          starting_xi_players: squad.startingXi,
          bench_players: squad.bench,
        }),
      }),
    })
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    const heading = await screen.findByRole('heading', { name: /player predictions/i })
    for (const player of [...squad.startingXi, ...squad.bench]) {
      expect(screen.getByText(player.web_name)).toBeInTheDocument()
    }
    // The table must name the gameweek it came from, never the pending
    // current one.
    expect(heading.parentElement).toHaveTextContent('Gameweek 3')
    expect(heading.parentElement).not.toHaveTextContent('Gameweek 5')
  })

  it('does not render player predictions for a gameweek that cannot be evaluated', async () => {
    mockApi()
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    await screen.findByRole('heading', { name: /decision evaluation/i })
    expect(screen.queryByRole('heading', { name: /player predictions/i })).not.toBeInTheDocument()
  })

  it('renders no player table at all when neither the current nor a completed gameweek has results', async () => {
    mockApi({
      evaluation: makeGameweekEvaluation({ status: 'not_completed' }),
      latestCompleted: { available: false, evaluation: null },
    })
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    await screen.findByRole('heading', { name: /decision evaluation/i })
    expect(screen.queryByRole('heading', { name: /player predictions/i })).not.toBeInTheDocument()
    // The honest empty state stays in place rather than a padded table.
    expect(
      screen.getByText(/historical evaluation will appear after the first completed decision cycle/i),
    ).toBeInTheDocument()
  })

  it('shows the captain’s expected points alongside the actual in the evaluation', async () => {
    mockApi({ evaluation: makeEvaluatedGameweek() })
    renderWithProviders(<App />)

    await submitEntryForm('8731757')

    await screen.findByRole('heading', { name: /decision evaluation/i })
    expect(screen.getByText(/projected 10\.31 points/i)).toBeInTheDocument()
    // "12" also appears in the per-player predictions table below, so
    // this asserts the figure in the evaluation triad specifically.
    expect(
      screen.getAllByText('12').some((element) => element.tagName === 'DD'),
    ).toBe(true)
  })


  // --- Production regression guards ---
  //
  // These mirror the shape of a real gameweek-2 response (an
  // early-season squad with a thin minutes sample, one unavailable
  // pick, and a gameweek that cannot yet be evaluated), which is where
  // the deployed dashboard showed empty bullets and stale wording.

  it('renders real evidence factors, never empty bullets, when evidence is limited', async () => {
    mockApi({
      decision: makeGameweekDecision({
        confidence: 'Low',
        evidence_basis: makeEvidenceBasis({
          level: 'Low',
          average_sample_confidence: 0.25,
          players_considered: 11,
          limited_sample_players: 11,
          partial_sample_players: 0,
          full_sample_players: 0,
          limited_sample_minutes: 450,
        }),
      }),
    })
    renderWithProviders(<App />)

    await submitEntryForm('8731757', '2')
    await screen.findByText('Recommended plan')

    expect(screen.getByText('Limited')).toBeInTheDocument()
    expect(screen.getByText('Why is the evidence limited?')).toBeInTheDocument()

    // The real sentences, built from the real basis values.
    expect(
      screen.getByText('11 of 11 selected players have under 450 minutes played this season.'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Average playing-time evidence across the selected eleven is 25%.'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Moderate evidence begins at 50%, strong evidence at 75%.'),
    ).toBeInTheDocument()

    // A band with a zero count contributes no bullet at all.
    expect(screen.queryByText(/0 of 11/)).not.toBeInTheDocument()
  })

  it('never renders an empty list item anywhere on the dashboard', async () => {
    mockApi({
      decision: makeGameweekDecision({
        confidence: 'Low',
        evidence_basis: makeEvidenceBasis({ level: 'Low' }),
        // Blank strings the backend could emit must never become bullets.
        evidence: [
          { player_id: 11, decision: 'captain', score: 9, reasons: ['Highest captaincy score', ''] },
          { player_id: 10, decision: 'vice_captain', score: 8, reasons: ['   ', ''] },
          { player_id: 21, decision: 'buy', score: 7, reasons: [] },
        ],
      }),
    })
    renderWithProviders(<App />)

    await submitEntryForm('8731757', '2')
    await screen.findByText('Recommended plan')

    const bullets = Array.from(document.querySelectorAll('li'))
    expect(bullets.length).toBeGreaterThan(0)
    for (const bullet of bullets) {
      expect((bullet.textContent ?? '').trim()).not.toBe('')
    }
  })

  it('shows a polished empty state instead of empty bullets when reasoning is blank', async () => {
    mockApi({
      decision: makeGameweekDecision({
        evidence: [
          { player_id: 11, decision: 'captain', score: 9, reasons: ['', '  '] },
        ],
      }),
    })
    renderWithProviders(<App />)

    await submitEntryForm('8731757', '2')
    await screen.findByText('Recommended plan')

    expect(screen.getAllByText('No supporting reasoning is available.').length).toBeGreaterThan(0)
  })

  it('shows no old confidence terminology anywhere in the user-facing dashboard', async () => {
    mockApi({
      decision: makeGameweekDecision({
        confidence: 'Low',
        evidence_basis: makeEvidenceBasis({ level: 'Low' }),
      }),
    })
    renderWithProviders(<App />)

    await submitEntryForm('8731757', '2')
    await screen.findByText('Recommended plan')

    const pageText = document.body.textContent ?? ''
    expect(pageText).not.toMatch(/decision confidence/i)
    expect(pageText).not.toMatch(/low confidence/i)
    expect(pageText).not.toMatch(/confidence:\s*low/i)
    expect(pageText).toContain('Evidence:')
    expect(pageText).toContain('Limited')
  })

  it('renders the bench exactly as the API returns it, even when a pick is unavailable', async () => {
    // An unavailable squad member (transferred abroad, injured out, or
    // removed from the game) is excluded by the engine, so a 15-man
    // squad legitimately yields 11 starters and 3 bench players. The
    // UI must report that honestly rather than padding to 4.
    const full = makeGameweekDecision()
    mockApi({
      decision: makeGameweekDecision({
        bench: full.bench.slice(0, 3),
      }),
    })
    renderWithProviders(<App />)

    await submitEntryForm('8731757', '2')
    await screen.findByText('Recommended plan')

    const benchHeading = screen.getByRole('heading', { name: /^bench/i })
    expect(benchHeading).toHaveTextContent('3')
    expect(benchHeading).not.toHaveTextContent('4')
  })

  it('renders a full four-man bench unchanged when the API returns four', async () => {
    mockApi()
    renderWithProviders(<App />)

    await submitEntryForm('8731757', '2')
    await screen.findByText('Recommended plan')

    expect(screen.getByRole('heading', { name: /^bench/i })).toHaveTextContent('4')
  })

  it('keeps the not-completed evaluation message truthful and fabricates nothing', async () => {
    const message =
      'Gameweek 2 has results, but no decision snapshot was recorded for this entry, so this decision cannot be evaluated.'
    mockApi({
      evaluation: makeGameweekEvaluation({ status: 'no_snapshot', message }),
    })
    renderWithProviders(<App />)

    await submitEntryForm('8731757', '2')
    await screen.findByRole('heading', { name: /decision evaluation/i })

    expect(screen.getByText(message)).toBeInTheDocument()
    expect(screen.queryByText('Prediction error')).not.toBeInTheDocument()
    expect(screen.queryByText('Expected points')).not.toBeInTheDocument()
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
