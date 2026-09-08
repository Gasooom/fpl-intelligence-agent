import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  makeCaptainEvaluation,
  makeEvaluatedGameweek,
  makeGameweekEvaluation,
  makeLatestCompletedEvaluation,
  makeStartingXIEvaluation,
  makeTransferEvaluation,
} from '../test/fixtures'
import { Evaluation } from './Evaluation'

const idle = { isFetching: false, error: null }
const idleLatest = { latestCompletedFetching: false, latestCompletedError: null }

describe('Evaluation', () => {
  it('presents itself as a first-class section, not a footnote', () => {
    render(<Evaluation evaluation={makeEvaluatedGameweek()} {...idle} />)

    const heading = screen.getByRole('heading', { name: /decision evaluation/i })
    expect(heading).toBeInTheDocument()
    expect(heading.tagName).toBe('H2')
    expect(screen.getByText(/how did the system's previous decision perform/i)).toBeInTheDocument()
  })

  // --- Non-evaluated states ---

  it('renders the backend message verbatim when the gameweek is not completed', () => {
    const evaluation = makeGameweekEvaluation({
      status: 'not_completed',
      message: 'Gameweek 5 is not completed yet. Evaluation becomes possible once it finishes.',
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.getByRole('heading', { name: /decision evaluation/i })).toBeInTheDocument()
    expect(screen.getByText(/gameweek 5 is not completed yet/i)).toBeInTheDocument()
  })

  it('renders the backend message verbatim when no decision snapshot was recorded', () => {
    const evaluation = makeGameweekEvaluation({
      status: 'no_snapshot',
      message:
        'Gameweek 3 has results, but no decision snapshot was recorded for this entry, so this decision cannot be evaluated.',
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.getByText(/no decision snapshot was recorded/i)).toBeInTheDocument()
  })

  it('shows no numbers at all in a non-evaluated state', () => {
    render(<Evaluation evaluation={makeGameweekEvaluation()} {...idle} />)

    expect(screen.queryByText(/actual points/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/expected points/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/prediction error/i)).not.toBeInTheDocument()
  })

  it('never renders fabricated zeros in place of a missing evaluation', () => {
    // A "no_snapshot" payload carries null groups; the section must
    // stay empty rather than rendering 0 / 0 / 0 cards that would read
    // as a measured result.
    const evaluation = makeGameweekEvaluation({
      status: 'no_snapshot',
      message: 'No decision snapshot was recorded for this entry.',
      captain: null,
      starting_xi: null,
      best_transfer: null,
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.queryByText('0')).not.toBeInTheDocument()
    expect(screen.queryByText('0.00')).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /starting xi/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /captain/i })).not.toBeInTheDocument()
  })

  // --- Evaluated state: expected vs actual vs error ---

  it('labels expected, actual, and prediction error distinctly for the starting XI', () => {
    const evaluation = makeEvaluatedGameweek({
      starting_xi: makeStartingXIEvaluation({
        starting_xi_expected_total: 60.5,
        starting_xi_actual_total: 55,
        bench_actual_total: 6,
        difference: 49,
        prediction_error: -5.5,
      }),
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.getByText('Expected points')).toBeInTheDocument()
    expect(screen.getByText('60.50')).toBeInTheDocument()
    expect(screen.getAllByText('Actual points').length).toBeGreaterThan(0)
    expect(screen.getByText('55')).toBeInTheDocument()
    expect(screen.getAllByText('Prediction error').length).toBeGreaterThan(0)
    expect(screen.getByText('-5.50')).toBeInTheDocument()
    expect(screen.getByText(/bench scored 6/i)).toBeInTheDocument()
    expect(screen.getByText(/outscored the bench by \+49/i)).toBeInTheDocument()
  })

  it('ties each evaluation figure to its own label for assistive technology', () => {
    const evaluation = makeEvaluatedGameweek({
      starting_xi: makeStartingXIEvaluation({ starting_xi_expected_total: 60.5 }),
      captain: null,
      best_transfer: null,
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    // A definition list keeps "Expected points" bound to 60.50 rather
    // than relying on visual column order alone.
    const term = screen.getByText('Expected points')
    expect(term.tagName).toBe('DT')
    expect(term.nextElementSibling?.tagName).toBe('DD')
    expect(term.nextElementSibling).toHaveTextContent('60.50')
  })

  it('renders captain prediction, actual points, and result from backend values', () => {
    const evaluation = makeEvaluatedGameweek({
      captain: makeCaptainEvaluation({
        captain_web_name: 'Cherki',
        captain_expected_points: 10.31,
        vice_captain_web_name: 'Haaland',
        captain_actual_points: 12,
        vice_captain_actual_points: 4,
        outcome: 'correct',
      }),
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.getByText('Predicted')).toBeInTheDocument()
    expect(screen.getByText('Cherki')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('Result')).toBeInTheDocument()
    expect(screen.getByText('Correct')).toBeInTheDocument()
    expect(screen.getByText(/projected 10\.31 points/i)).toBeInTheDocument()
    expect(screen.getByText(/vice-captain haaland scored 4/i)).toBeInTheDocument()
  })

  it('reports a captain outcome the backend did not call correct, without softening it', () => {
    const evaluation = makeEvaluatedGameweek({
      captain: makeCaptainEvaluation({ outcome: 'missed' }),
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.getByText('Missed')).toBeInTheDocument()
  })

  it('renders the transfer as expected gain vs actual improvement with its error', () => {
    const evaluation = makeEvaluatedGameweek({
      best_transfer: makeTransferEvaluation({
        sell_web_name: 'Neto',
        buy_web_name: 'Gakpo',
        expected_improvement: 8.13,
        actual_improvement: 6,
        prediction_error: -2.13,
        direction: 'positive',
      }),
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.getByRole('heading', { name: /neto → gakpo/i })).toBeInTheDocument()
    // "Expected gain" is the stored buy-minus-sell points delta, never
    // the blended net_improvement score.
    expect(screen.getByText('Expected gain')).toBeInTheDocument()
    expect(screen.getByText('+8.13')).toBeInTheDocument()
    expect(screen.getByText('Actual improvement')).toBeInTheDocument()
    expect(screen.getByText('+6')).toBeInTheDocument()
    expect(screen.getByText('-2.13')).toBeInTheDocument()
    expect(screen.getByText(/outcome: positive/i)).toBeInTheDocument()
  })

  it('colors a positive outcome and a negative one differently, and never colors prediction error', () => {
    const positive = makeEvaluatedGameweek({
      best_transfer: makeTransferEvaluation({
        direction: 'positive',
        actual_improvement: 6,
        prediction_error: -2.13,
      }),
    })
    const { rerender } = render(<Evaluation evaluation={positive} {...idle} />)
    const positiveClass = screen.getByText('+6').className
    const errorClass = screen.getByText('-2.13').className

    const negative = makeEvaluatedGameweek({
      best_transfer: makeTransferEvaluation({
        direction: 'negative',
        actual_improvement: -3,
        prediction_error: -2.13,
      }),
    })
    rerender(<Evaluation evaluation={negative} {...idle} />)
    const negativeClass = screen.getByText('-3').className

    expect(positiveClass).toContain('eval-positive')
    expect(negativeClass).toContain('eval-negative')
    // Prediction error is a projection miss, not a bad outcome - it
    // must not borrow the outcome colors.
    expect(errorClass).not.toMatch(/eval-(positive|negative)/)
  })

  it('communicates the outcome in words, not by color alone', () => {
    const evaluation = makeEvaluatedGameweek({
      best_transfer: makeTransferEvaluation({ direction: 'negative' }),
      captain: makeCaptainEvaluation({ outcome: 'missed' }),
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.getByText(/outcome: negative/i)).toBeInTheDocument()
    expect(screen.getByText('Missed')).toBeInTheDocument()
  })

  it('omits the transfer group entirely when no transfer was recommended', () => {
    const evaluation = makeEvaluatedGameweek({ best_transfer: null })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.queryByRole('heading', { name: /best transfer/i })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Captain' })).toBeInTheDocument()
  })

  it('notes when the decision was recorded, so the prediction visibly predates the result', () => {
    const evaluation = makeEvaluatedGameweek({
      decision_generated_at: '2026-08-10T09:00:00+00:00',
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.getByText(/decision recorded 2026-08-10/i)).toBeInTheDocument()
  })

  it('shows a quiet checking state while the evaluation request is in flight', () => {
    render(<Evaluation evaluation={undefined} isFetching error={null} />)

    expect(screen.getByText(/checking results/i)).toBeInTheDocument()
  })

  it('shows the error message honestly when the evaluation request fails', () => {
    render(
      <Evaluation
        evaluation={undefined}
        isFetching={false}
        error={new Error('Could not reach the decision API.')}
      />,
    )

    expect(screen.getByText(/could not reach the decision api/i)).toBeInTheDocument()
  })

  it('renders only the heading when there is no evaluation data at all', () => {
    render(<Evaluation evaluation={undefined} {...idle} />)

    expect(screen.getByRole('heading', { name: /decision evaluation/i })).toBeInTheDocument()
    expect(screen.queryByText(/actual points/i)).not.toBeInTheDocument()
  })

  // --- Current Gameweek / Latest Completed Evaluation ---

  it('labels the current gameweek section and shows its evaluation when available', () => {
    render(<Evaluation evaluation={makeEvaluatedGameweek()} {...idle} />)

    expect(screen.getByRole('heading', { name: 'Current Gameweek' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Captain' })).toBeInTheDocument()
    expect(screen.queryByText(/evaluation pending/i)).not.toBeInTheDocument()
  })

  it('shows a compact "Evaluation pending" state for a current gameweek that has not completed', () => {
    const evaluation = makeGameweekEvaluation({
      status: 'not_completed',
      message: 'Gameweek 6 is not completed yet.',
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.getByRole('heading', { name: 'Current Gameweek' })).toBeInTheDocument()
    expect(screen.getByText('Evaluation pending')).toBeInTheDocument()
    expect(screen.getByText(/gameweek 6 is not completed yet/i)).toBeInTheDocument()
  })

  it('does not show the pending badge for a no_snapshot current gameweek', () => {
    const evaluation = makeGameweekEvaluation({
      status: 'no_snapshot',
      message: 'No decision snapshot was recorded for this entry.',
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.queryByText('Evaluation pending')).not.toBeInTheDocument()
    expect(screen.getByText(/no decision snapshot was recorded/i)).toBeInTheDocument()
  })

  it('shows the latest completed evaluation, clearly labeled with its gameweek, when the current gameweek is pending', () => {
    const currentEvaluation = makeGameweekEvaluation({
      status: 'not_completed',
      message: 'Gameweek 6 is not completed yet.',
    })
    const latestCompleted = makeLatestCompletedEvaluation()

    render(
      <Evaluation
        evaluation={currentEvaluation}
        {...idle}
        latestCompleted={latestCompleted}
        {...idleLatest}
      />,
    )

    expect(screen.getByRole('heading', { name: 'Latest Completed Evaluation' })).toBeInTheDocument()
    expect(screen.getByText('Gameweek 3')).toBeInTheDocument()
    // The historical section carries its own real captain/starting XI
    // figures, distinct from the pending current-gameweek section.
    expect(screen.getAllByRole('heading', { name: 'Captain' })).toHaveLength(1)
    expect(screen.getByText('Evaluation pending')).toBeInTheDocument()
  })

  it('renders expected/actual/error for the latest completed evaluation', () => {
    const latestCompleted = makeLatestCompletedEvaluation({
      evaluation: makeEvaluatedGameweek({
        gameweek: 4,
        starting_xi: makeStartingXIEvaluation({
          starting_xi_expected_total: 60.5,
          starting_xi_actual_total: 55,
          prediction_error: -5.5,
        }),
      }),
    })

    render(
      <Evaluation
        evaluation={makeGameweekEvaluation({ status: 'not_completed' })}
        {...idle}
        latestCompleted={latestCompleted}
        {...idleLatest}
      />,
    )

    expect(screen.getByText('Gameweek 4')).toBeInTheDocument()
    expect(screen.getByText('Expected points')).toBeInTheDocument()
    expect(screen.getByText('60.50')).toBeInTheDocument()
    expect(screen.getByText('55')).toBeInTheDocument()
    expect(screen.getByText('-5.50')).toBeInTheDocument()
  })

  it('shows a truthful empty state when no historical evaluation exists yet', () => {
    render(
      <Evaluation
        evaluation={makeGameweekEvaluation({ status: 'not_completed' })}
        {...idle}
        latestCompleted={makeLatestCompletedEvaluation({ available: false, evaluation: null })}
        {...idleLatest}
      />,
    )

    expect(
      screen.getByText(/historical evaluation will appear after the first completed decision cycle/i),
    ).toBeInTheDocument()
    expect(screen.queryByText('Gameweek 3')).not.toBeInTheDocument()
  })

  it('never renders a gameweek label or numbers for the empty historical state', () => {
    render(
      <Evaluation
        evaluation={makeGameweekEvaluation({ status: 'not_completed' })}
        {...idle}
        latestCompleted={makeLatestCompletedEvaluation({ available: false, evaluation: null })}
        {...idleLatest}
      />,
    )

    expect(screen.queryByText('Expected points')).not.toBeInTheDocument()
    expect(screen.queryAllByRole('heading', { name: 'Captain' })).toHaveLength(0)
  })

  it('shows a quiet checking state for the latest completed evaluation while it loads', () => {
    render(
      <Evaluation
        evaluation={makeEvaluatedGameweek()}
        {...idle}
        latestCompleted={undefined}
        latestCompletedFetching
        latestCompletedError={null}
      />,
    )

    expect(screen.getByRole('heading', { name: 'Latest Completed Evaluation' })).toBeInTheDocument()
    expect(screen.getByText(/checking results/i)).toBeInTheDocument()
  })

  it('shows the error message honestly when the latest completed evaluation request fails', () => {
    render(
      <Evaluation
        evaluation={makeEvaluatedGameweek()}
        {...idle}
        latestCompleted={undefined}
        latestCompletedFetching={false}
        latestCompletedError={new Error('Could not reach the decision API.')}
      />,
    )

    expect(screen.getByText(/could not reach the decision api/i)).toBeInTheDocument()
  })

  it('omits the latest completed evaluation subsection entirely when the caller does not wire it up', () => {
    render(<Evaluation evaluation={makeEvaluatedGameweek()} {...idle} />)

    expect(
      screen.queryByRole('heading', { name: 'Latest Completed Evaluation' }),
    ).not.toBeInTheDocument()
  })
})
