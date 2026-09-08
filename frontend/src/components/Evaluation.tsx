import type {
  CaptainEvaluationResponse,
  GameweekEvaluationResponse,
  StartingXIEvaluationResponse,
  TransferEvaluationResponse,
} from '../api/types'
import {
  capitalize,
  formatPoints,
  formatSigned,
  formatSignedInteger,
  outcomeToneClass,
  signToneClass,
} from '../lib/format'

interface EvaluationProps {
  evaluation: GameweekEvaluationResponse | undefined
  isFetching: boolean
  error: Error | null
}

interface Cell {
  label: string
  value: string
  tone?: string
}

/**
 * The three figures that carry this whole section: what was projected,
 * what actually happened, and the gap between them. Rendered as a
 * definition list so each number is programmatically tied to the word
 * that says which kind of number it is - the distinction this section
 * exists to make must survive being read by a screen reader, not just
 * by eye.
 */
function Triad({ cells }: { cells: Cell[] }) {
  return (
    <dl className="mt-3 grid grid-cols-3 gap-x-4 sm:gap-x-8">
      {cells.map((cell) => (
        <div key={cell.label}>
          <dt className="text-xs text-text-muted">{cell.label}</dt>
          <dd
            className={`mt-1 text-lg font-medium tabular-nums ${cell.tone ?? 'text-text'}`}
          >
            {cell.value}
          </dd>
        </div>
      ))}
    </dl>
  )
}

function Group({
  title,
  cells,
  footnote,
}: {
  title: string
  cells: Cell[]
  footnote?: string
}) {
  return (
    <div className="border-t border-border pt-5 first:border-t-0 first:pt-0">
      <h3 className="text-sm font-medium text-text">{title}</h3>
      <Triad cells={cells} />
      {footnote && <p className="mt-3 text-xs text-text-muted">{footnote}</p>}
    </div>
  )
}

function CaptainGroup({ captain }: { captain: CaptainEvaluationResponse }) {
  return (
    <Group
      title="Captain"
      cells={[
        { label: 'Predicted', value: captain.captain_web_name },
        { label: 'Actual points', value: String(captain.captain_actual_points) },
        {
          label: 'Result',
          value: capitalize(captain.outcome),
          tone: outcomeToneClass(captain.outcome),
        },
      ]}
      footnote={`Projected ${formatPoints(captain.captain_expected_points)} points · vice-captain ${captain.vice_captain_web_name} scored ${captain.vice_captain_actual_points}`}
    />
  )
}

function StartingXIGroup({ startingXi }: { startingXi: StartingXIEvaluationResponse }) {
  return (
    <Group
      title="Starting XI"
      cells={[
        {
          label: 'Expected points',
          value: formatPoints(startingXi.starting_xi_expected_total),
        },
        { label: 'Actual points', value: String(startingXi.starting_xi_actual_total) },
        // Deliberately neutral: a projection being off is a prediction
        // error, not a bad decision - coloring it would conflate the
        // two ideas this section exists to keep apart.
        { label: 'Prediction error', value: formatSigned(startingXi.prediction_error) },
      ]}
      footnote={`Bench scored ${startingXi.bench_actual_total} · starting XI outscored the bench by ${formatSignedInteger(startingXi.difference)}`}
    />
  )
}

function TransferGroup({ transfer }: { transfer: TransferEvaluationResponse }) {
  return (
    <Group
      // "Expected gain" is the backend's stored expected_improvement,
      // which is the recommendation's raw points delta (buy minus
      // sell) - never net_improvement, a blended selection-score
      // figure that is not comparable to actual points.
      title={`Best transfer — ${transfer.sell_web_name} → ${transfer.buy_web_name}`}
      cells={[
        { label: 'Expected gain', value: formatSigned(transfer.expected_improvement) },
        {
          label: 'Actual improvement',
          value: formatSignedInteger(transfer.actual_improvement),
          tone: signToneClass(transfer.actual_improvement),
        },
        { label: 'Prediction error', value: formatSigned(transfer.prediction_error) },
      ]}
      footnote={`Outcome: ${capitalize(transfer.direction)}`}
    />
  )
}

function Note({ children }: { children: React.ReactNode }) {
  return <p className="mt-4 max-w-xl text-sm leading-relaxed text-text-secondary">{children}</p>
}

/**
 * Prediction vs. what actually happened - the part of this product
 * that measures its own decisions rather than only making them.
 *
 * Every number here is computed by the backend from a decision
 * recorded before the gameweek and real results after it; nothing on
 * this screen is derived, re-totaled, or judged in the browser. When
 * there is nothing honest to show yet, the backend's own `message` is
 * rendered verbatim rather than a message invented here - and never as
 * zeros, which would read as a measured result of nothing.
 */
function EvaluationBody({ evaluation, isFetching, error }: EvaluationProps) {
  if (isFetching) {
    return <p className="mt-4 text-sm text-text-muted">Checking results…</p>
  }

  if (error) {
    return <Note>{error.message}</Note>
  }

  if (!evaluation) {
    return null
  }

  // "not_completed" and "no_snapshot" both mean there is genuinely
  // nothing to measure yet; the backend explains which, in its own
  // words.
  if (evaluation.status !== 'evaluated') {
    return <Note>{evaluation.message}</Note>
  }

  const decisionDate = evaluation.decision_generated_at?.slice(0, 10)

  return (
    <>
      <div className="mt-6 flex flex-col gap-5">
        {evaluation.starting_xi && <StartingXIGroup startingXi={evaluation.starting_xi} />}
        {evaluation.captain && <CaptainGroup captain={evaluation.captain} />}
        {evaluation.best_transfer && <TransferGroup transfer={evaluation.best_transfer} />}
      </div>
      {decisionDate && (
        <p className="mt-6 border-t border-border pt-4 text-xs text-text-muted">
          Decision recorded {decisionDate}, before this gameweek finished.
        </p>
      )}
    </>
  )
}

export function Evaluation(props: EvaluationProps) {
  return (
    <div>
      {/* The section label is the heading itself - this is a
          first-class part of the product, so it carries real heading
          weight rather than a decorative eyebrow above a question. */}
      <h2 className="text-xl font-semibold text-text">Decision evaluation</h2>
      <p className="mt-1.5 max-w-xl text-sm text-text-secondary">
        How did the system&apos;s previous decision perform? Recommendations are measured against
        real results, not just published.
      </p>
      <EvaluationBody {...props} />
    </div>
  )
}
