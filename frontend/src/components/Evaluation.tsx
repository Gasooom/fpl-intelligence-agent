import type {
  CaptainEvaluationResponse,
  GameweekEvaluationResponse,
  LatestCompletedEvaluationResponse,
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
  /** Omit entirely (leave undefined) when the caller isn't wiring up
   * historical evaluation at all - the "Latest Completed Evaluation"
   * subsection then simply does not render, so existing callers keep
   * working unchanged. */
  latestCompleted?: LatestCompletedEvaluationResponse
  latestCompletedFetching?: boolean
  latestCompletedError?: Error | null
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
      <h4 className="text-sm font-medium text-text">{title}</h4>
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

/** A compact, honest status pill - never a number, since there is
 * nothing to measure yet. Reserved for "not_completed": a gameweek that
 * genuinely has not been played, as distinct from "no_snapshot" (a
 * different, already-explained situation that isn't "pending"). */
function EvaluationPendingBadge() {
  return (
    <span className="inline-block rounded-full border border-border-strong px-2.5 py-0.5 text-xs font-medium text-text-secondary">
      Evaluation pending
    </span>
  )
}

/** The evaluation body shared by both the current-gameweek and
 * latest-completed-evaluation subsections: a quiet loading state, an
 * honest error, an honest non-evaluated message, or the full set of
 * expected/actual/error groups. Every number is computed by the
 * backend from a decision recorded before the gameweek and real results
 * after it; nothing here is derived, re-totaled, or judged in the
 * browser. When there is nothing honest to show yet, the backend's own
 * `message` is rendered verbatim rather than a message invented here -
 * and never as zeros, which would read as a measured result of nothing.
 */
function EvaluationOutcome({
  evaluation,
  isFetching,
  error,
  pendingBadge = false,
}: {
  evaluation: GameweekEvaluationResponse | undefined
  isFetching: boolean
  error: Error | null
  pendingBadge?: boolean
}) {
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
    return (
      <div className="mt-3">
        {pendingBadge && evaluation.status === 'not_completed' && <EvaluationPendingBadge />}
        <Note>{evaluation.message}</Note>
      </div>
    )
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

/**
 * This gameweek's own decision measured against real results, or an
 * honest "Evaluation pending" state when it has not finished yet.
 */
function CurrentGameweekSection({
  evaluation,
  isFetching,
  error,
}: Pick<EvaluationProps, 'evaluation' | 'isFetching' | 'error'>) {
  return (
    <div>
      <h3 className="text-sm font-medium text-text-secondary">Current Gameweek</h3>
      <EvaluationOutcome evaluation={evaluation} isFetching={isFetching} error={error} pendingBadge />
    </div>
  )
}

/**
 * A previous, genuinely evaluable gameweek - shown so the evaluation
 * capability stays visible even while the current gameweek can't be
 * measured yet. The backend alone decides which gameweek this is (it
 * is always strictly before the current one, and always has both a
 * recorded snapshot and finished results); this component only renders
 * whatever it is told, and never invents a number when there is
 * nothing real to show.
 */
function LatestCompletedSection({
  latestCompleted,
  latestCompletedFetching,
  latestCompletedError,
}: {
  latestCompleted: LatestCompletedEvaluationResponse | undefined
  latestCompletedFetching: boolean
  latestCompletedError: Error | null
}) {
  if (latestCompleted === undefined && !latestCompletedFetching && !latestCompletedError) {
    return null
  }

  const evaluation = latestCompleted?.evaluation ?? undefined
  const gameweekLabel = evaluation ? `Gameweek ${evaluation.gameweek}` : null

  return (
    <div className="mt-6 border-t border-border pt-5">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-sm font-medium text-text-secondary">Latest Completed Evaluation</h3>
        {gameweekLabel && <span className="text-xs text-text-muted">{gameweekLabel}</span>}
      </div>
      {latestCompleted && !latestCompleted.available && !latestCompletedFetching ? (
        <Note>Historical evaluation will appear after the first completed decision cycle.</Note>
      ) : (
        <EvaluationOutcome
          evaluation={evaluation}
          isFetching={latestCompletedFetching}
          error={latestCompletedError}
        />
      )}
    </div>
  )
}

export function Evaluation({
  evaluation,
  isFetching,
  error,
  latestCompleted,
  latestCompletedFetching = false,
  latestCompletedError = null,
}: EvaluationProps) {
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
      <div className="mt-4">
        <CurrentGameweekSection evaluation={evaluation} isFetching={isFetching} error={error} />
        <LatestCompletedSection
          latestCompleted={latestCompleted}
          latestCompletedFetching={latestCompletedFetching}
          latestCompletedError={latestCompletedError}
        />
      </div>
    </div>
  )
}
