import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  makeCaptainEvaluation,
  makeEvaluatedGameweek,
  makeGameweekEvaluation,
  makeStartingXIEvaluation,
  makeTransferEvaluation,
} from '../test/fixtures'
import { Evaluation } from './Evaluation'

const idle = { isFetching: false, error: null }

describe('Evaluation', () => {
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
  })

  it('renders captain prediction, actual points, and outcome from backend values', () => {
    const evaluation = makeEvaluatedGameweek({
      captain: makeCaptainEvaluation({
        captain_web_name: 'Cherki',
        vice_captain_web_name: 'Haaland',
        captain_actual_points: 12,
        vice_captain_actual_points: 4,
        outcome: 'correct',
      }),
    })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.getByText('Cherki')).toBeInTheDocument()
    expect(screen.getByText('12 actual points')).toBeInTheDocument()
    expect(screen.getByText('Haaland — 4 actual points')).toBeInTheDocument()
    expect(screen.getByText('Correct')).toBeInTheDocument()
  })

  it('distinguishes expected from actual points in the starting XI figures', () => {
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

    // Never an ambiguous bare "pts" in this section - each figure says
    // which kind of points it is.
    expect(screen.getByText('60.50 expected points')).toBeInTheDocument()
    expect(screen.getByText('55 actual points')).toBeInTheDocument()
    expect(screen.getByText('6 actual points')).toBeInTheDocument()
    expect(screen.getByText('+49 actual points')).toBeInTheDocument()
    expect(screen.getByText('-5.50')).toBeInTheDocument()
  })

  it('renders the transfer as expected vs actual improvement with its direction', () => {
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

    expect(screen.getByText('Neto → Gakpo')).toBeInTheDocument()
    expect(screen.getByText('+8.13 expected points')).toBeInTheDocument()
    expect(screen.getByText('+6 actual points')).toBeInTheDocument()
    expect(screen.getByText('-2.13')).toBeInTheDocument()
    expect(screen.getByText('Positive')).toBeInTheDocument()
  })

  it('colors a positive outcome and a negative one differently, and never colors prediction error', () => {
    const positive = makeEvaluatedGameweek({
      best_transfer: makeTransferEvaluation({ direction: 'positive', prediction_error: -2.13 }),
    })
    const { rerender } = render(<Evaluation evaluation={positive} {...idle} />)
    const positiveClass = screen.getByText('Positive').className
    const errorClass = screen.getByText('-2.13').className

    const negative = makeEvaluatedGameweek({
      best_transfer: makeTransferEvaluation({ direction: 'negative', prediction_error: -2.13 }),
    })
    rerender(<Evaluation evaluation={negative} {...idle} />)
    const negativeClass = screen.getByText('Negative').className

    expect(positiveClass).toContain('eval-positive')
    expect(negativeClass).toContain('eval-negative')
    // Prediction error is a projection miss, not a bad outcome - it
    // must not borrow the outcome colors.
    expect(errorClass).not.toMatch(/eval-(positive|negative)/)
  })

  it('omits the transfer group entirely when no transfer was recommended', () => {
    const evaluation = makeEvaluatedGameweek({ best_transfer: null })

    render(<Evaluation evaluation={evaluation} {...idle} />)

    expect(screen.queryByText(/best transfer/i)).not.toBeInTheDocument()
    expect(screen.getByText('Captain')).toBeInTheDocument()
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
})
