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

function Metric({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div>
      <p className="text-xs text-text-muted">{label}</p>
      <p className={`mt-0.5 text-sm ${tone ?? 'text-text'}`}>{value}</p>
    </div>
  )
}

function Group({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-t border-border pt-5 first:border-t-0 first:pt-0 sm:border-t-0 sm:pt-0">
      <p className="text-sm font-medium text-text">{title}</p>
      <div className="mt-3 flex flex-col gap-3">{children}</div>
    </div>
  )
}

function CaptainGroup({ captain }: { captain: CaptainEvaluationResponse }) {
  return (
    <Group title="Captain">
      <Metric label="Predicted" value={captain.captain_web_name} />
      <Metric
        label="Expected"
        value={`${formatPoints(captain.captain_expected_points)} expected points`}
      />
      <Metric label="Actual" value={`${captain.captain_actual_points} actual points`} />
      <Metric
        label="Vice-captain"
        value={`${captain.vice_captain_web_name} — ${captain.vice_captain_actual_points} actual points`}
      />
      <Metric
        label="Result"
        value={capitalize(captain.outcome)}
        tone={outcomeToneClass(captain.outcome)}
      />
    </Group>
  )
}

function StartingXIGroup({ startingXi }: { startingXi: StartingXIEvaluationResponse }) {
  return (
    <Group title="Starting XI">
      <Metric
        label="Expected"
        value={`${formatPoints(startingXi.starting_xi_expected_total)} expected points`}
      />
      <Metric label="Actual" value={`${startingXi.starting_xi_actual_total} actual points`} />
      <Metric label="Bench" value={`${startingXi.bench_actual_total} actual points`} />
      <Metric
        label="XI advantage over bench"
        value={`${formatSignedInteger(startingXi.difference)} actual points`}
        tone={signToneClass(startingXi.difference)}
      />
      {/* Deliberately neutral: a projection being off is a prediction
          error, not a bad decision - coloring it would conflate the
          two ideas this section exists to keep apart. */}
      <Metric label="Prediction error" value={formatSigned(startingXi.prediction_error)} />
    </Group>
  )
}

function TransferGroup({ transfer }: { transfer: TransferEvaluationResponse }) {
  return (
    <Group title="Best transfer">
      <Metric label="Transfer" value={`${transfer.sell_web_name} → ${transfer.buy_web_name}`} />
      <Metric
        label="Expected"
        value={`${formatSigned(transfer.expected_improvement)} expected points`}
      />
      <Metric
        label="Actual"
        value={`${formatSignedInteger(transfer.actual_improvement)} actual points`}
      />
      <Metric label="Prediction error" value={formatSigned(transfer.prediction_error)} />
      <Metric
        label="Outcome"
        value={capitalize(transfer.direction)}
        tone={outcomeToneClass(transfer.direction)}
      />
    </Group>
  )
}

/**
 * Prediction vs. what actually happened - the part of this product
 * that measures its own decisions rather than just making them.
 *
 * Every number here is computed by the backend from a decision
 * snapshot recorded before the gameweek and real FPL results after
 * it; nothing on this screen is derived, re-totaled, or judged in the
 * browser. When there is nothing honest to show yet, the backend's own
 * `message` is rendered verbatim rather than a message invented here.
 */
function Note({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-4 max-w-xl text-sm leading-relaxed text-text-secondary">{children}</p>
  )
}

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
      <div className="mt-5 flex flex-col gap-5 sm:grid sm:grid-cols-3 sm:gap-6">
        {evaluation.captain && <CaptainGroup captain={evaluation.captain} />}
        {evaluation.starting_xi && <StartingXIGroup startingXi={evaluation.starting_xi} />}
        {evaluation.best_transfer && <TransferGroup transfer={evaluation.best_transfer} />}
      </div>
      {decisionDate && (
        <p className="mt-6 text-xs text-text-muted">
          Decision recorded {decisionDate}, before this gameweek finished.
        </p>
      )}
    </>
  )
}

export function Evaluation(props: EvaluationProps) {
  return (
    <div>
      <h2 className="text-base font-medium text-text">Decision evaluation</h2>
      <p className="mt-1 text-sm text-text-muted">How did the prediction perform?</p>
      <EvaluationBody {...props} />
    </div>
  )
}
